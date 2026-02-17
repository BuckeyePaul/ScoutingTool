import json
import re
import time
from html import unescape
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

CONSENSUS_URL = 'https://www.nflmockdraftdatabase.com/big-boards/2026/consensus-big-board-2026'
BIG_BOARDS_INDEX_URL = 'https://www.nflmockdraftdatabase.com/big-boards/2026'


def create_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=4,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def _normalize_name(name):
    normalized = (name or '').strip()
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized


def _extract_entries_from_json_blobs(html):
    entries = []

    json_blocks = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, flags=re.S | re.I)
    for block in json_blocks:
        try:
            payload = json.loads(block)
        except Exception:
            continue

        def walk(node):
            if isinstance(node, dict):
                possible_name = node.get('name') or node.get('player') or node.get('player_name')
                possible_rank = node.get('rank') or node.get('overall_rank') or node.get('consensus_rank')
                if possible_name is not None and possible_rank is not None:
                    try:
                        rank_value = int(float(str(possible_rank).strip()))
                        entries.append({'rank': rank_value, 'name': _normalize_name(str(possible_name))})
                    except Exception:
                        pass
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        walk(payload)

    return entries


def _extract_entries_from_react_props(soup):
    entries = []
    seen = set()

    react_nodes = soup.select('div[data-react-props]')
    for node in react_nodes:
        raw_props = node.get('data-react-props') or ''
        if not raw_props:
            continue

        try:
            payload = json.loads(unescape(raw_props))
        except Exception:
            continue

        selections = (((payload or {}).get('mock') or {}).get('selections') or [])
        if not selections:
            selections = ((payload or {}).get('selections') or [])
        if not selections:
            selections = (((payload or {}).get('big_board') or {}).get('selections') or [])
        if not selections:
            selections = (((payload or {}).get('bigBoard') or {}).get('selections') or [])

        for selection in selections:
            player = (selection or {}).get('player') or {}
            name = _normalize_name(player.get('name') or (selection or {}).get('name'))
            rank_value = (selection or {}).get('pick') or (selection or {}).get('rank') or (selection or {}).get('overall_rank')
            if not name or rank_value is None:
                continue

            try:
                parsed_rank = int(float(rank_value))
            except Exception:
                continue

            key = name.lower()
            if key in seen:
                continue
            seen.add(key)

            entries.append({
                'rank': parsed_rank,
                'name': name,
                'position': _normalize_name(player.get('position', '') or (selection or {}).get('position', '')),
                'school': _normalize_name((((player.get('college') or {}).get('name')) or (selection or {}).get('school') or ''))
            })

    return entries


def _extract_board_name(soup, fallback='Imported NFLMockDraftDatabase Board'):
    title_node = soup.find('title')
    if title_node:
        title_text = _normalize_name(title_node.get_text(' ', strip=True))
        if title_text:
            title_text = re.sub(r'\s*\|\s*NFL Mock Draft Database.*$', '', title_text, flags=re.I)
            if title_text:
                return title_text

    for selector in ['h1', '.page-title', '.big-board-title', '[data-testid="page-title"]']:
        node = soup.select_one(selector)
        if not node:
            continue
        title_text = _normalize_name(node.get_text(' ', strip=True))
        if title_text:
            return title_text
    return fallback


def _extract_entries_from_table(soup):
    entries = []
    seen = set()

    for row in soup.select('tr'):
        cells = row.find_all(['td', 'th'])
        if len(cells) < 2:
            continue

        rank_value = None
        player_name = ''
        position = ''
        school = ''

        for idx, cell in enumerate(cells):
            text = _normalize_name(cell.get_text(' ', strip=True))
            if not text:
                continue

            if rank_value is None:
                rank_match = re.match(r'^(\d{1,3})$', text)
                if rank_match:
                    rank_value = int(rank_match.group(1))
                    continue

            if not player_name:
                link = cell.find('a')
                candidate = _normalize_name(link.get_text(' ', strip=True) if link else text)
                if re.search(r'[A-Za-z]{2,}\s+[A-Za-z]{2,}', candidate):
                    player_name = candidate
                    continue

            if not position and re.match(r'^[A-Z]{1,5}(?:/[A-Z]{1,5})?$', text):
                position = text
                continue

            if not school and idx >= 2 and len(text) >= 3:
                school = text

        if rank_value is None or not player_name:
            continue

        key = (rank_value, player_name.lower())
        if key in seen:
            continue
        seen.add(key)

        entries.append({
            'rank': rank_value,
            'name': player_name,
            'position': position,
            'school': school
        })

    return entries


def _extract_entries_from_text(html):
    entries = []
    seen_names = set()

    text = BeautifulSoup(html, 'html.parser').get_text('\n', strip=True)
    for line in text.splitlines():
        cleaned = _normalize_name(line)
        match = re.match(r'^(\d{1,3})\s*[\.|\)|-]?\s*([A-Za-z\'\-\. ]{4,})$', cleaned)
        if not match:
            continue

        rank_value = int(match.group(1))
        name = _normalize_name(match.group(2))
        if name.lower() in seen_names:
            continue

        seen_names.add(name.lower())
        entries.append({'rank': rank_value, 'name': name})

    return entries


def scrape_consensus_big_board_2026(url=CONSENSUS_URL):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    session = create_session()
    response = None

    for attempt in range(4):
        try:
            if attempt > 0:
                time.sleep(1.5 * attempt)
            response = session.get(url, headers=headers, timeout=35, allow_redirects=True)
            response.raise_for_status()
            break
        except requests.RequestException:
            if attempt == 3:
                raise

    html = response.text if response is not None else ''
    soup = BeautifulSoup(html, 'html.parser')

    entries = _extract_entries_from_react_props(soup)
    if len(entries) < 20:
        entries = _extract_entries_from_table(soup)
    if len(entries) < 20:
        entries = _extract_entries_from_json_blobs(html)
    if len(entries) < 20:
        entries = _extract_entries_from_text(html)

    normalized = []
    seen = set()
    for entry in entries:
        rank = entry.get('rank')
        name = _normalize_name(entry.get('name'))
        if rank is None or not name:
            continue

        try:
            rank_value = int(float(rank))
        except Exception:
            continue

        key = name.lower()
        if key in seen:
            continue
        seen.add(key)

        normalized.append({
            'rank': rank_value,
            'name': name,
            'position': _normalize_name(entry.get('position', '')),
            'school': _normalize_name(entry.get('school', ''))
        })

    normalized.sort(key=lambda row: (row['rank'], row['name']))
    return normalized


def scrape_nflmockdraftdatabase_big_board(url):
    parsed_url = (url or '').strip()
    if not parsed_url:
        raise ValueError('A board URL is required.')

    if 'nflmockdraftdatabase.com' not in parsed_url.lower() or '/big-boards/' not in parsed_url.lower():
        raise ValueError('URL must be an NFLMockDraftDatabase big board link.')

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    session = create_session()
    response = None

    for attempt in range(4):
        try:
            if attempt > 0:
                time.sleep(1.5 * attempt)
            response = session.get(parsed_url, headers=headers, timeout=35, allow_redirects=True)
            response.raise_for_status()
            break
        except requests.RequestException:
            if attempt == 3:
                raise

    html = response.text if response is not None else ''
    soup = BeautifulSoup(html, 'html.parser')
    board_name = _extract_board_name(soup)
    if board_name == 'Imported NFLMockDraftDatabase Board':
        try:
            slug = (urlparse(parsed_url).path or '').rstrip('/').split('/')[-1]
            if slug:
                pretty_slug = _normalize_name(slug.replace('-', ' ')).title()
                board_name = pretty_slug
        except Exception:
            pass

    entries = _extract_entries_from_react_props(soup)
    if len(entries) < 20:
        entries = _extract_entries_from_table(soup)
    if len(entries) < 20:
        entries = _extract_entries_from_json_blobs(html)
    if len(entries) < 20:
        entries = _extract_entries_from_text(html)

    normalized = []
    seen = set()
    for entry in entries:
        rank = entry.get('rank')
        name = _normalize_name(entry.get('name'))
        if rank is None or not name:
            continue

        try:
            rank_value = int(float(rank))
        except Exception:
            continue

        key = name.lower()
        if key in seen:
            continue
        seen.add(key)

        normalized.append({
            'rank': rank_value,
            'name': name,
            'position': _normalize_name(entry.get('position', '')),
            'school': _normalize_name(entry.get('school', ''))
        })

    normalized.sort(key=lambda row: (row['rank'], row['name']))
    return {
        'board_name': board_name,
        'players': normalized,
        'source_url': parsed_url
    }
