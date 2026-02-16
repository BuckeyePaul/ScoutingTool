from flask import Flask, render_template, jsonify, request
from database import ScoutDatabase
import random
import urllib.parse

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

@app.route('/api/stats')
def get_stats():
  """Get database statistics"""
  stats = db.get_stats()
  return jsonify(stats)

@app.route('/api/players')
def get_players():
  """Get filtered players"""
  positions = request.args.getlist('positions[]')
  max_rank = request.args.get('max_rank', type=int)
  include_scouted = request.args.get('include_scouted', 'false').lower() == 'true'
 
  players = db.get_filtered_players(
    positions=positions if positions else None,
    max_rank=max_rank,
    include_scouted=include_scouted
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
  data = request.get_json()
  grade = data.get('grade', '')
  db.update_grade(player_id, grade)
  return jsonify({'success': True})

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