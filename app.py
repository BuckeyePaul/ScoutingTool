from flask import Flask, render_template, jsonify, request, Response
from database import ScoutDatabase
from consensus_scraper import scrape_consensus_big_board_2026, scrape_nflmockdraftdatabase_big_board
from webscraper import scrape_nfl_big_board, save_to_json as save_tankathon_json
from download_logos import get_schools_from_database, get_schools_from_json, get_school_logos
import random
import urllib.parse
import os
import sys
import signal
import threading
import time
from pathlib import Path

def _runtime_base_path():
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


BASE_PATH = _runtime_base_path()

app = Flask(
    __name__,
    template_folder=str(BASE_PATH / 'templates'),
    static_folder=str(BASE_PATH / 'static')
)
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
    watch_list_only = request.args.get('watch_list_only', 'false').lower() == 'true'
 
    players = db.get_filtered_players(
        positions=positions if positions else None,
        max_rank=max_rank,
        include_scouted=include_scouted,
        search_term=search_term if search_term else None,
        name_search=name_search if name_search else None,
        school=school if school else None,
        watch_list_only=watch_list_only
    )
 
    return jsonify(players)

@app.route('/api/random')
def get_random_player():
    """Get a random player based on filters"""
    positions = request.args.getlist('positions[]')
    max_rank = request.args.get('max_rank', type=int)
    watch_list_only = request.args.get('watch_list_only', 'false').lower() == 'true'
 
    players = db.get_filtered_players(
        positions=positions if positions else None,
        max_rank=max_rank,
        include_scouted=False,
        watch_list_only=watch_list_only
    )
 
    if not players:
        return jsonify({'error': 'No players available with current filters'}), 404
 
    # Select random player
    selected_player = random.choice(players)
    selected_player = db.get_player_by_id(selected_player['id']) or selected_player
 
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


@app.route('/api/watchlist')
def get_watch_list():
    """Get personal watch list entries."""
    return jsonify(db.get_watch_list())


@app.route('/api/watchlist/add', methods=['POST'])
def add_to_watch_list():
    """Add player to personal watch list."""
    data = request.get_json() or {}
    player_id = data.get('player_id')
    if not player_id:
        return jsonify({'success': False, 'error': 'player_id is required'}), 400

    result = db.add_player_to_watch_list(player_id)
    status_code = 200 if result.get('success') else 400
    return jsonify(result), status_code


@app.route('/api/watchlist/reorder', methods=['POST'])
def reorder_watch_list():
    """Persist watch list drag-and-drop order."""
    data = request.get_json() or {}
    ordered_player_ids = data.get('player_ids', [])
    if not isinstance(ordered_player_ids, list):
        return jsonify({'success': False, 'error': 'player_ids must be a list'}), 400

    return jsonify(db.reorder_watch_list(ordered_player_ids))


@app.route('/api/watchlist/remove', methods=['POST'])
def remove_from_watch_list():
    """Remove player from personal watch list."""
    data = request.get_json() or {}
    player_id = data.get('player_id')
    if not player_id:
        return jsonify({'success': False, 'error': 'player_id is required'}), 400

    return jsonify(db.remove_player_from_watch_list(player_id))

@app.route('/api/settings/refresh-logos', methods=['POST'])
def refresh_logos():
    """Refresh school logos using in-process downloader logic."""
    try:
        schools = get_schools_from_database() or get_schools_from_json()
        if not schools:
            return jsonify({'success': False, 'error': 'No schools found to refresh logos.'}), 400

        get_school_logos(schools)
        return jsonify({
            'success': True,
            'output': f'Logo refresh complete for {len(schools)} schools.'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings/update-rankings', methods=['POST'])
def update_rankings():
    """Fetch Tankathon data and import without recalculating rankings."""
    try:
        players_data = scrape_nfl_big_board()
        if not players_data:
            return jsonify({'success': False, 'error': 'Failed to fetch Tankathon big board data.'}), 502

        output_json_path = Path.cwd() / 'nfl_big_board.json'
        save_tankathon_json(players_data, filename=str(output_json_path))

        import_result = db.import_players_from_json(str(output_json_path), recalculate_rankings=False)
        if not import_result.get('success'):
            return jsonify({
                'success': False,
                'error': import_result.get('error') or 'Tankathon import failed after fetch.'
            }), 500

        return jsonify({
            'success': True,
            'output': f"Fetched {len(players_data)} Tankathon players and imported {import_result.get('imported', 0)} without recalculating ranks."
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/system/shutdown', methods=['POST'])
def shutdown_system():
    """Shut down local app process."""

    shutdown_func = request.environ.get('werkzeug.server.shutdown')
    if shutdown_func:
        shutdown_func()
        return jsonify({'success': True, 'output': 'Server is shutting down.'})

    def _terminate_process():
        time.sleep(0.25)
        pid = os.getpid()
        try:
            os.kill(pid, signal.SIGTERM)
        except Exception:
            pass
        time.sleep(0.15)
        os._exit(0)

    threading.Thread(target=_terminate_process, daemon=True).start()
    return jsonify({'success': True, 'output': 'Application process is shutting down.'})

@app.route('/api/settings/recalculate-player-rankings', methods=['POST'])
def recalculate_player_rankings():
    """Recalculate default and positional player rankings."""
    try:
        ranked_count = db.recalculate_default_rankings()
        return jsonify({
            'success': True,
            'output': f'Recalculated rankings for {ranked_count} players.'
        })
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

@app.route('/api/settings/rank-boards/remove', methods=['POST'])
def remove_rank_board():
    """Remove an imported rank board from settings."""
    data = request.get_json() or {}
    board_key = data.get('board_key', '')
    result = db.remove_rank_board(board_key)
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
