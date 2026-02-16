import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import urllib3
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Disable SSL warnings when verify=False is used
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def create_session():
  """Create a requests session with retry logic"""
  session = requests.Session()
  
  # Configure retry strategy
  retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"]
  )
  
  adapter = HTTPAdapter(max_retries=retry_strategy)
  session.mount("http://", adapter)
  session.mount("https://", adapter)
  
  return session


def scrape_nfl_big_board():
  """
  Scrapes all player information from Tankathon NFL Big Board
  """
  url = "https://tankathon.com/nfl/big_board"
  
  # Add comprehensive headers to mimic a real browser
  headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0',
  }
  
  # Retry logic for connection errors
  max_retries = 5
  retry_delay = 2 # seconds
  
  for attempt in range(max_retries):
    try:
      # Create session with retry logic
      session = create_session()
      
      # Add a small delay before request
      time.sleep(1)
      
      print(f"Attempt {attempt + 1} of {max_retries}...")
      
      # Fetch the webpage with SSL verification disabled and timeout
      response = session.get(url, headers=headers, verify=False, timeout=30)
      response.raise_for_status()
      
      # If here, the request was successful
      break
      
    except (requests.exceptions.ConnectionError, 
        requests.exceptions.ChunkedEncodingError,
        requests.exceptions.Timeout,
        ConnectionResetError,
        urllib3.exceptions.ProtocolError) as e:
      if attempt < max_retries - 1:
        print(f"Connection error on attempt {attempt + 1}: {type(e).__name__}")
        print(f"Retrying in {retry_delay} seconds...")
        time.sleep(retry_delay)
        retry_delay *= 2 # Exponential backoff
      else:
        print(f"Failed after {max_retries} attempts")
        raise
    except requests.RequestException as e:
      print(f"Request error: {e}")
      raise
  
  try:
    
    # Parse the HTML
    soup = BeautifulSoup(response.content, 'html.parser')
    
    players = []
    seen_players = set() # Track unique player names to avoid duplicates
    
    # Find all player entries
    player_rows = soup.find_all('div', class_='mock-row nfl')
    
    for row in player_rows:
      player_data = {}
      
      # Extract rank from mock-row-pick-number
      rank_elem = row.find('div', class_='mock-row-pick-number')
      if rank_elem:
        player_data['rank'] = rank_elem.text.strip()
      
      # Extract position from data-pos attribute
      if row.has_attr('data-pos'):
        player_data['position'] = row['data-pos']
      
      # Extract positional rank from data-posrank attribute
      if row.has_attr('data-posrank'):
        player_data['positional_rank'] = row['data-posrank']
      
      # Extract player URL and name
      player_link = row.find('a', class_='primary-hover', href=lambda x: x and '/nfl/players/' in x)
      if player_link:
        player_data['player_url'] = 'https://tankathon.com' + player_link['href']
      
      # Extract player name from mock-row-name
      name_elem = row.find('div', class_='mock-row-name')
      if name_elem:
        player_data['name'] = name_elem.text.strip()
      
      # Extract school from mock-row-school-position (format: "LB | Ohio State ")
      school_position_elem = row.find('div', class_='mock-row-school-position')
      if school_position_elem:
        text = school_position_elem.text.strip()
        parts = text.split('|')
        if len(parts) == 2:
          player_data['school'] = parts[1].strip()
      
      # Try to extract jersey number if available
      jersey_elem = row.find('div', class_='jersey-number')
      if jersey_elem:
        player_data['jersey_number'] = jersey_elem.text.strip().replace('#', '')
      # Alternative: check if jersey is in player URL or data attributes
      elif row.has_attr('data-jersey'):
        player_data['jersey_number'] = row['data-jersey']
      
      # Extract physical measurements
      measurements_div = row.find('div', class_='mock-row-measurements')
      if measurements_div:
        height_weight = measurements_div.find('div', class_='section height-weight')
        if height_weight:
          divs = height_weight.find_all('div', recursive=False)
          if len(divs) >= 2:
            player_data['height'] = divs[0].text.strip()
            weight_text = divs[1].text.strip()
            player_data['weight'] = weight_text.replace('lbs', '').strip()
      
      # Extract stats from mock-row-stats-container
      stats_container = row.find('div', class_='mock-row-stats-container')
      if stats_container:
        stat_divs = stats_container.find_all('div', class_='stat')
        for stat in stat_divs:
          label_elem = stat.find('div', class_='label')
          value_elem = stat.find('div', class_='value total')
          
          if label_elem and value_elem:
            label = label_elem.text.strip().lower().replace(' ', '_')
            value = value_elem.text.strip()
            player_data[label] = value
      
      # Only add player if we have a name and haven't seen it before
      if player_data.get('name') and player_data['name'] not in seen_players:
        players.append(player_data)
        seen_players.add(player_data['name'])
    
    
    return players
  
  except requests.RequestException as e:
    print(f"Error fetching the webpage: {e}")
    return None
  except Exception as e:
    print(f"Error parsing the webpage: {e}")
    return None

def save_to_json(data, filename='nfl_big_board.json'):
  """Save data to JSON file"""
  with open(filename, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
  print(f"Data saved to {filename}")


if __name__ == "__main__":
  print("Scraping NFL Big Board from Tankathon...")
  
  # Scrape the data
  players_data = scrape_nfl_big_board()
  
  if players_data:

    # Save to JSON
    save_to_json(players_data)
        
    print(f"\nSuccessfully scraped {len(players_data)} players!")
    
    # Initialize database and import data
    print("\nInitializing scout database...")
    try:
      from database import ScoutDatabase
      db = ScoutDatabase()
      imported = db.import_players_from_json()
      print(f"Database initialized with {imported} new players!")
      
      # Calculate positional ranks
      print("\nCalculating positional ranks...")
      db.calculate_positional_ranks()
      
      print("\nYou can now run the scout application with: python app.py")
    except Exception as e:
      print(f"Warning: Could not initialize database: {e}")
      print("You can manually import data later by running:")
      print(" from database import ScoutDatabase")
      print(" db = ScoutDatabase()")
      print(" db.import_players_from_json()")
  else:
    print("Failed to scrape data. Please check the website structure.")