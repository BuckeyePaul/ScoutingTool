import sqlite3
import json
from datetime import datetime

class ScoutDatabase:
    def __init__(self, db_name='scout_database.db'):
        self.db_name = db_name
        self.init_database()

    def get_connection(self):
        """Create connection to the database"""
        return sqlite3.connect(self.db_name)

    def init_database(self):
        """Initalize the database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rank INTEGER,
                name TEXT NOT NULL UNIQUE,
                position TEXT,
                positional_rank TEXT,
                school TEXT,
                height TEXT,
                weight TEXT,
                jersey_number TEXT,
                player_url TEXT,
                scouted BOOLEAN DEFAULT 0,
                notes TEXT,
                grade TEXT,
                scout_date TEXT                       
            )
        ''')

        conn.commit()
        conn.close()
    
    def import_players_from_json (self, json_file='nfl_big_board.json'):
        """Import players from the JSON generated from Tankathon Webscraper"""
        try:
            with open(json_file, 'r', encoding ='utf-8') as f:
                players = json.load(f)

            conn = self.get_connection()
            cursor = conn.cursor()

            imported = 0
            for player in players:
                try:
                    #Get basic info
                    rank = int(player.get('rank', 0))
                    name = player.get('name', '')
                    position = player.get('position', '')
                    positional_rank = player.get('positional_rank', '')
                    school = player.get('school', '')
                    height = player.get('height', '')
                    weight = player.get('weight', '')
                    jersey_number = player.get('jersey_number', '')
                    player_url = player.get('player_url', '')

                    #Store additional stats as JSON
                    stats = {}
                    for key, value in player.items():
                        if key not in ['rank', 'name', 'position', 'positional_rank', 'school', 'height', 'weight', 'jersey_number', 'player_url']:
                            stats[key] = value
                    stats_json = json.dumps(stats)

                    cursor.execute('''
                        INSERT OR IGNORE INTO players
                        (rank, name, position, positional_rank, school, height, weight, jersey_number, player_url)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (rank, name, position, positional_rank, school, height, weight, jersey_number, player_url))

                    if cursor.rowcount > 0:
                        imported += 1

                except Exception as e:
                    print(f"Error importing player {player.get('name')}: {e}")
                    return 0

            conn.commit()
            conn.close()
            print(f"imported {imported} new players")
            return imported
        
        except Exception as e:
            print(f"Error importing from JSON: {e}")
            return 0

    def calculate_positional_ranks(self):
        """Calculate positional ranks for players based on overall rank within each position"""
        conn = self.get_connection()
        cursor = conn.cursor()

        #Get all players ordered by rank
        cursor.execute('SELECT id, rank, position FROM players ORDER BY rank')
        players = cursor.fetchall()

        #Group players by positiona and track positional rank
        position_counters = {}
        updates = []

        for player_id, rank, position in players:
            if not position: #skip players without position
                continue

            #For multi-position players (e.g. EDGE/LB) use first position
            primary_position = position.split('/')[0].strip()

            #Increment counter for position
            if primary_position not in position_counters:
                position_counters[primary_position] = 0
            position_counters[primary_position] += 1

            #Store update
            updates.append((str(position_counters[primary_position]), player_id))
        
        #Update all positional ranks
        cursor.executemany('UPDATE players SET positional_rank = ? WHERE id = ?', updates)
        conn.commit()

        print(f"Calculated positional ranks for {len(updates)} players across {len(position_counters)} positions")
        conn.close()
        return len(updates)
    
    def get_all_players(self):
        """Get all players from database"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM players ORDER BY rank')
        columns = [description[0] for description in cursor.description]
        players = []

        for row in cursor.fetchall():
            player = dict(zip(columns, row))
            #Parse JSON Stats
            if player.get('stats'):
                try:
                    player['stats'] = json.loads(player['stats'])
                except:
                    player['stats'] = {}
            players.append(player)

        conn.close()
        return players
    
    def get_filtered_players(self, positions=None, max_rank=None, include_scouted=False):
        """Get filtered players based on criteria"""
        conn = self.get_connection()
        cursor = conn.cursor()

        #Base query to dynamically built based on selections
        query = "SELECT * FROM players WHERE 1=1"
        params = []

        if positions and len(positions) > 0:
            #Build condition to match players with multiple positions (e.g. EDGE/LB)
            position_conditions = []
            for pos in positions:
                position_conditions.append('position LIKE ?')
                params.append(f'%{pos}%')
            query += f' AND ({ " OR ".join(position_conditions)})'

        if max_rank:
            query += ' AND rank <= ?'
            params.append(max_rank)
        
        if not include_scouted:
            query += ' AND scouted = 0'
        
        query += ' ORDER BY rank'

        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        players = []

        for row in cursor.fetchall():
            player = dict(zip(columns, row))
            #Parse JSON Stats
            if player.get('stats'):
                try:
                    player['stats'] = json.loads(player['stats'])
                except:
                    player['stats'] = {}
            players.append(player)

        conn.close()
        return players
    

    def get_player_by_id(self, player_id):
        """Get a specific player by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM players WHERE id = ?', (player_id,))
        columns = [description[0] for description in cursor.description]
        players = []

        for row in cursor.fetchall():
            player = dict(zip(columns, row))
            #Parse JSON Stats
            if player.get('stats'):
                try:
                    player['stats'] = json.loads(player['stats'])
                except:
                    player['stats'] = {}
            players.append(player)

        conn.close()
        return players

    def mark_as_scouted(self, player_id):
        """Mark a player as being scouted"""
        conn = self.get_connection()
        cursor= conn.cursor()

        cursor.execute('''
            UPDATE players
            SET scouted = 1, scout_date = ?
            WHERE ID = ?
        ''', (datetime.now().isoformat(), player_id))

        conn.commit()
        conn.close()
    
    def unmark_as_scouted(self, player_id):
        """Unmark a player as being scouted"""
        conn = self.get_connection()
        cursor= conn.cursor()

        cursor.execute('''
            UPDATE players
            SET scouted = 0, scout_date = NULL
            WHERE ID = ?
        ''', (player_id,))

        conn.commit()
        conn.close()

    def update_notes(self, player_id, notes):
        """Update notes on a player"""
        conn = self.get_connection()
        cursor= conn.cursor()

        cursor.execute('''
            UPDATE players
            SET notes = ?
            WHERE ID = ?
        ''', (notes, player_id))

        conn.commit()
        conn.close()
    
    def update_grade(self, player_id, grade):
        """Update grade on a player"""
        conn = self.get_connection()
        cursor= conn.cursor()

        cursor.execute('''
            UPDATE players
            SET grade = ?
            WHERE ID = ?
        ''', (grade, player_id))

        conn.commit()
        conn.close()

    def get_all_positions(self):
        """Get list of all unique positions"""
        conn = self.get_connection()
        cursor= conn.cursor()

        cursor.execute('SELECT DISTINCT position FROM players ORDER BY position')
        all_positions = set()

        for row in cursor.fetchall():
            if row[0]:
                if '/' in row[0]:
                    positions = row[0].split('/')
                    for pos in positions: 
                        all_positions.add(pos.strip())
                else: 
                    all_positions.add(row[0])

        conn.close()
        return sorted(list(all_positions))
    
    def get_db_stats(self):
        """Get database statistics"""
        conn = self.get_connection()
        cursor= conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM players')
        total = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM players WHERE scouted = 1')
        scouted = cursor.fetchone()[0]

        conn.close()

        return {
            'total_players': total,
            'scouted': scouted,
            'remaining': total - scouted
        }