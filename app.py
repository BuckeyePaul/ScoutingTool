from flask import Flask, render_template, jsonify, request, Response
from database import ScoutDatabase
from consensus_scraper import scrape_consensus_big_board_2026, scrape_nflmockdraftdatabase_big_board
import random
import urllib.parse
import subprocess
import sys
from pathlib import Path

app = Flask(__name__)
db = ScoutDatabase()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/positions')
def get_positions():
    """Get all available positions"""
    positions = db.get_all_positions()
    return jsonify(positions)

@app.route('/api/schools')
def get_schools():
    """Get all available schools"""
    schools = db.get_all_schools()
    return jsonify(schools)

@app.route('/api/stats')
def get_stats():
    """Get database statistics"""
    stats = db.get_db_stats()
    return jsonify(stats)

@app.route('/api/players')
def get_players():
    """Get filtered players"""
    positions = request.args.getlist('positions[]')
    max_rank = request.args.get('max_rank', type=int)
    search_term = request.args.get('search', '').strip()
    name_search = request.args.get('name', '').strip()
    school = request.args.get('school', '').strip()
    include_scouted = request.args.get('include_scouted', 'false').lower() == 'true'
 
    players = db.get_filtered_players(
        positions=positions if positions else None,
        max_rank=max_rank,
        include_scouted=include_scouted,
        search_term=search_term if search_term else None,
        name_search=name_search if name_search else None,
        school=school if school else None
    )
 
    return jsonify(players)

@app.route('/api/random')
def get_random_player():
    """Get a random player based on filters"""
    positions = request.args.getlist('positions[]')
    max_rank = request.args.get('max_rank', type=int)
 
    players = db.get_filtered_players(
        positions=positions if positions else None,
        max_rank=max_rank,
        include_scouted=False
    )
 
    if not players:
        return jsonify({'error': 'No players available with current filters'}), 404
 
    # Select random player
    selected_player = random.choice(players)
 
    # Enhance with external links
    selected_player['sports_reference_url'] = generate_sports_reference_url(selected_player)
    selected_player['espn_url'] = generate_espn_url(selected_player)
 
    return jsonify(selected_player)

@app.route('/api/player/<int:player_id>')
def get_player(player_id):
    """Get specific player details"""
    player = db.get_player_by_id(player_id)
 
    if not player:
        return jsonify({'error': 'Player not found'}), 404
 
    # Add external links
    player['sports_reference_url'] = generate_sports_reference_url(player)
    player['espn_url'] = generate_espn_url(player)
 
    return jsonify(player)

@app.route('/api/player/<int:player_id>/scout', methods=['POST'])
def mark_scouted(player_id):
    """Mark player as scouted"""
    db.mark_as_scouted(player_id)
    return jsonify({'success': True})

@app.route('/api/player/<int:player_id>/unscout', methods=['POST'])
def unmark_scouted(player_id):
    """Unmark player as scouted"""
    db.unmark_as_scouted(player_id)
    return jsonify({'success': True})

@app.route('/api/player/<int:player_id>/notes', methods=['POST'])
def update_notes(player_id):
    """Update player notes"""
    data = request.get_json()
    notes = data.get('notes', '')
    db.update_notes(player_id, notes)
    return jsonify({'success': True})

@app.route('/api/player/<int:player_id>/grade', methods=['POST'])
def update_grade(player_id):
    """Update player grade"""
    data = request.get_json() or {}
    grade = data.get('grade', '')
    slot = data.get('slot', 'primary')
    db.update_grade(player_id, grade, slot=slot)
    return jsonify({'success': True})

@app.route('/api/player/<int:player_id>/games-watched', methods=['POST'])
def update_games_watched(player_id):
    """Update games watched for a player"""
    data = request.get_json()
    games_watched = data.get('games_watched', '')
    db.update_games_watched(player_id, games_watched)
    return jsonify({'success': True})

@app.route('/api/player/<int:player_id>/profile', methods=['POST'])
def update_player_profile(player_id):
    """Update editable player profile fields"""
    data = request.get_json() or {}
    try:
        db.update_player_profile(player_id, data)
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

    return jsonify({'success': True})

@app.route('/api/settings/player', methods=['POST'])
def add_player_from_settings():
    """Add a new player manually from settings"""
    data = request.get_json() or {}

    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'error': 'Player name is required'}), 400

    player_data = {
        'rank': data.get('rank'),
        'name': name,
        'position': (data.get('position') or '').strip(),
        'school': (data.get('school') or '').strip(),
        'height': (data.get('height') or '').strip(),
        'weight': (data.get('weight') or '').strip(),
        'jersey_number': (data.get('jersey_number') or '').strip(),
        'player_url': (data.get('player_url') or '').strip(),
        'notes': (data.get('notes') or '').strip(),
        'grade': (data.get('grade') or '').strip(),
        'scouted': bool(data.get('scouted', False))
    }

    result = db.add_player(player_data)
    if not result.get('success'):
        return jsonify(result), 400
    return jsonify(result)

@app.route('/api/bigboard')
def get_big_board():
    """Get overall or positional big board"""
    board_type = request.args.get('type', 'overall')
    position = request.args.get('position') if board_type == 'position' else None
    board = db.get_big_board(board_type=board_type, position=position)
    return jsonify(board)

@app.route('/api/bigboard/add', methods=['POST'])
def add_to_big_board():
    """Add player to big board"""
    data = request.get_json() or {}
    player_id = data.get('player_id')
    board_type = data.get('type', 'overall')
    position = data.get('position') if board_type == 'position' else None

    if not player_id:
        return jsonify({'success': False, 'error': 'player_id is required'}), 400

    result = db.add_player_to_big_board(player_id, board_type=board_type, position=position)
    status_code = 200 if result.get('success') else 400
    return jsonify(result), status_code

@app.route('/api/bigboard/reorder', methods=['POST'])
def reorder_big_board():
    """Persist big board order"""
    data = request.get_json() or {}
    ordered_player_ids = data.get('player_ids', [])
    board_type = data.get('type', 'overall')
    position = data.get('position') if board_type == 'position' else None

    if not isinstance(ordered_player_ids, list):
        return jsonify({'success': False, 'error': 'player_ids must be a list'}), 400

    result = db.reorder_big_board(ordered_player_ids, board_type=board_type, position=position)
    return jsonify(result)

@app.route('/api/bigboard/remove', methods=['POST'])
def remove_from_big_board():
    """Remove player from big board"""
    data = request.get_json() or {}
    player_id = data.get('player_id')
    board_type = data.get('type', 'overall')
    position = data.get('position') if board_type == 'position' else None

    if not player_id:
        return jsonify({'success': False, 'error': 'player_id is required'}), 400

    result = db.remove_player_from_big_board(player_id, board_type=board_type, position=position)
    return jsonify(result)

@app.route('/api/bigboard/autosort', methods=['POST'])
def autosort_big_board():
    """Auto-sort big board by recorded grades"""
    data = request.get_json() or {}
    board_type = data.get('type', 'overall')
    position = data.get('position') if board_type == 'position' else None

    result = db.auto_sort_big_board(board_type=board_type, position=position)
    return jsonify(result)

@app.route('/api/settings/refresh-logos', methods=['POST'])
def refresh_logos():
    """Run logo downloader script"""
    try:
        script_path = Path(__file__).with_name('download_logos.py')
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
            timeout=300
        )

        output = (result.stdout or '') + ('\n' + result.stderr if result.stderr else '')
        return jsonify({
            'success': result.returncode == 0,
            'output': output.strip()
        }), (200 if result.returncode == 0 else 500)
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Logo refresh timed out'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings/update-rankings', methods=['POST'])
def update_rankings():
    """Run Tankathon webscraper to refresh rankings"""
    try:
        script_path = Path(__file__).with_name('webscraper.py')
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
            timeout=600
        )

        output = (result.stdout or '') + ('\n' + result.stderr if result.stderr else '')
        return jsonify({
            'success': result.returncode == 0,
            'output': output.strip()
        }), (200 if result.returncode == 0 else 500)
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Ranking update timed out'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings/import-big-boards', methods=['POST'])
def import_big_boards():
    """Import external big board text files and normalize rankings"""
    data = request.get_json() or {}
    boards = data.get('boards', [])
    weighting_mode = (data.get('weighting_mode') or 'equal').strip().lower()
    if weighting_mode not in {'equal', 'weighted'}:
        weighting_mode = 'equal'

    result = db.import_external_big_boards(boards, weighting_mode=weighting_mode)
    status_code = 200 if result.get('success') else 400
    return jsonify(result), status_code

@app.route('/api/settings/import-consensus-board', methods=['POST'])
def import_consensus_board():
    """Scrape and import consensus board data"""
    try:
        players = scrape_consensus_big_board_2026()
        if not players:
            return jsonify({'success': False, 'error': 'No players found from consensus source.'}), 502

        result = db.import_consensus_board(players)
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings/import-nflmock-board-url', methods=['POST'])
def import_nflmock_board_url():
    """Scrape and import an NFLMockDraftDatabase big board URL."""
    data = request.get_json() or {}
    board_url = (data.get('url') or '').strip()
    custom_board_name = (data.get('board_name') or '').strip()
    if not board_url:
        return jsonify({'success': False, 'error': 'Board URL is required.'}), 400

    try:
        scraped = scrape_nflmockdraftdatabase_big_board(board_url)
        players = scraped.get('players') or []
        scraped_name = scraped.get('board_name') or 'Imported NFLMockDraftDatabase Board'
        board_name = custom_board_name or scraped_name

        if not players:
            return jsonify({'success': False, 'error': 'No players found from the provided board URL.'}), 502

        result = db.import_nflmock_url_board(players, board_name)
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings/merge-player-duplicates', methods=['POST'])
def merge_player_duplicates():
    """Merge duplicate players created from name variants (suffix/punctuation/casing)."""
    result = db.merge_player_name_duplicates()
    status_code = 200 if result.get('success') else 400
    return jsonify(result), status_code

@app.route('/api/settings/rank-boards')
def get_rank_boards():
    """Get board rank settings including weights and primary board"""
    boards = db.get_rank_boards_config()
    return jsonify({'success': True, 'boards': boards})

@app.route('/api/settings/rank-boards', methods=['POST'])
def update_rank_boards():
    """Update board weights and primary board selection"""
    data = request.get_json() or {}
    board_updates = data.get('boards', [])
    result = db.update_rank_board_weights(board_updates)
    status_code = 200 if result.get('success') else 400
    return jsonify(result), status_code

@app.route('/api/settings/export-big-board')
def export_big_board():
    """Export normalized rankings in text format"""
    scope = (request.args.get('scope') or 'overall').strip().lower()
    if scope not in {'overall', 'position'}:
        scope = 'overall'

    position = (request.args.get('position') or '').strip()
    if scope == 'position' and not position:
        return jsonify({'success': False, 'error': 'Position is required for positional export.'}), 400

    board_text = db.export_big_board_text(scope=scope, position=position if scope == 'position' else None)
    filename = f"big_board_{position.lower()}.txt" if scope == 'position' else 'big_board_overall.txt'

    return Response(
        board_text,
        mimetype='text/plain; charset=utf-8',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )

def generate_sports_reference_url(player):
    """Generate Sports Reference URL for player"""
    # Pro Football Reference URL structure: https://www.pro-football-reference.com/players/
    # For college players, we'll try college football reference
    # Format: https://www.sports-reference.com/cfb/players/[name].html
    if player.get('name'):
        # Clean name and create URL-friendly version
        name = player['name'].lower()
        # Remove suffixes like Jr., Sr., III
        name = name.replace(' jr.', '').replace(' sr.', '').replace(' iii', '').replace(' ii', '')
        # Replace spaces and special characters
        name_parts = name.split()
        if len(name_parts) >= 2:
            # Format: firstname-lastname
            url_name = '-'.join(name_parts)
            return f"https://www.sports-reference.com/cfb/search/search.fcgi?search={urllib.parse.quote(player['name'])}"
    return None

def generate_espn_url(player):
    """Generate ESPN URL for player"""
    if player.get('name'):
        # ESPN search URL - just the player's name
        return f"https://www.espn.com/search/_/q/{urllib.parse.quote(player['name'])}"
    return None

if __name__ == '__main__':
    print("Starting NFL Draft Scout Randomizer...")
    print("Open your browser to: http://localhost:5000")
    app.run(debug=True, port=5000)
