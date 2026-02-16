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
                                stats TEXT,
                                scouted BOOLEAN DEFAULT 0,
                                notes TEXT,
                                games_watched TEXT,
                                grade TEXT,
                                grade_secondary TEXT,
                                scout_date TEXT                       
                        )
                ''')

                cursor.execute("PRAGMA table_info(players)")
                existing_columns = [row[1] for row in cursor.fetchall()]
                if 'stats' not in existing_columns:
                        cursor.execute('ALTER TABLE players ADD COLUMN stats TEXT')
                if 'games_watched' not in existing_columns:
                        cursor.execute('ALTER TABLE players ADD COLUMN games_watched TEXT')
                if 'grade_secondary' not in existing_columns:
                        cursor.execute('ALTER TABLE players ADD COLUMN grade_secondary TEXT')

                cursor.execute('''
                        CREATE TABLE IF NOT EXISTS big_boards (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                board_type TEXT NOT NULL,
                                position TEXT,
                                UNIQUE(board_type, position)
                        )
                ''')

                cursor.execute('''
                        CREATE TABLE IF NOT EXISTS big_board_entries (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                board_id INTEGER NOT NULL,
                                player_id INTEGER NOT NULL,
                                rank_order INTEGER NOT NULL,
                                UNIQUE(board_id, player_id),
                                FOREIGN KEY(board_id) REFERENCES big_boards(id) ON DELETE CASCADE,
                                FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE
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
                                                INSERT INTO players
                                                (rank, name, position, positional_rank, school, height, weight, jersey_number, player_url, stats)
                                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                                ON CONFLICT(name) DO UPDATE SET
                                                        rank = excluded.rank,
                                                        position = excluded.position,
                                                        positional_rank = excluded.positional_rank,
                                                        school = excluded.school,
                                                        height = excluded.height,
                                                        weight = excluded.weight,
                                                        jersey_number = excluded.jersey_number,
                                                        player_url = excluded.player_url,
                                                        stats = excluded.stats
                                        ''', (rank, name, position, positional_rank, school, height, weight, jersey_number, player_url, stats_json))

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
        
        def get_filtered_players(self, positions=None, max_rank=None, include_scouted=False, search_term=None, name_search=None, school=None):
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

                if search_term:
                        query += ' AND (name LIKE ? OR school LIKE ?)'
                        like_term = f'%{search_term}%'
                        params.extend([like_term, like_term])

                if name_search:
                        query += ' AND name LIKE ?'
                        params.append(f'%{name_search}%')

                if school:
                        query += ' AND school = ?'
                        params.append(school)
                
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
                row = cursor.fetchone()
                if not row:
                        conn.close()
                        return None

                player = dict(zip(columns, row))
                #Parse JSON Stats
                if player.get('stats'):
                        try:
                                player['stats'] = json.loads(player['stats'])
                        except:
                                player['stats'] = {}

                conn.close()
                return player

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

        def update_games_watched(self, player_id, games_watched):
                """Update games watched notes on a player"""
                conn = self.get_connection()
                cursor = conn.cursor()

                cursor.execute('''
                        UPDATE players
                        SET games_watched = ?
                        WHERE ID = ?
                ''', (games_watched, player_id))

                conn.commit()
                conn.close()
        
        def update_grade(self, player_id, grade, slot='primary'):
                """Update grade on a player (primary or secondary)"""
                conn = self.get_connection()
                cursor= conn.cursor()

                if slot == 'secondary':
                        cursor.execute('''
                                UPDATE players
                                SET grade_secondary = ?
                                WHERE ID = ?
                        ''', (grade, player_id))
                else:
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

        def get_all_schools(self):
                """Get list of all unique schools"""
                conn = self.get_connection()
                cursor = conn.cursor()

                cursor.execute('SELECT DISTINCT school FROM players WHERE school IS NOT NULL AND school != "" ORDER BY school')
                schools = [row[0] for row in cursor.fetchall() if row[0]]

                conn.close()
                return schools
        
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

        def add_player(self, player_data):
                """Add a player manually from settings tab"""
                conn = self.get_connection()
                cursor = conn.cursor()

                try:
                        cursor.execute('''
                                INSERT INTO players (
                                        rank, name, position, school, height, weight,
                                        jersey_number, player_url, notes, grade, scouted, scout_date
                                )
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                                player_data.get('rank'),
                                player_data.get('name'),
                                player_data.get('position'),
                                player_data.get('school'),
                                player_data.get('height'),
                                player_data.get('weight'),
                                player_data.get('jersey_number'),
                                player_data.get('player_url'),
                                player_data.get('notes', ''),
                                player_data.get('grade', ''),
                                1 if player_data.get('scouted') else 0,
                                datetime.now().isoformat() if player_data.get('scouted') else None
                        ))
                        conn.commit()
                        player_id = cursor.lastrowid
                        conn.close()
                        return {'success': True, 'player_id': player_id}
                except sqlite3.IntegrityError as e:
                        conn.close()
                        return {'success': False, 'error': str(e)}

        def _get_or_create_big_board_id(self, cursor, board_type='overall', position=None):
                cursor.execute(
                        'SELECT id FROM big_boards WHERE board_type = ? AND ((position IS NULL AND ? IS NULL) OR position = ?)',
                        (board_type, position, position)
                )
                existing = cursor.fetchone()
                if existing:
                        return existing[0]

                cursor.execute(
                        'INSERT INTO big_boards (board_type, position) VALUES (?, ?)',
                        (board_type, position)
                )
                return cursor.lastrowid

        def _grade_priority(self, grade):
                if not grade:
                        return (9, 999)
                grade = grade.strip()
                grade_lower = grade.lower()

                # Poker chip system (best to worst): Purple, Black, Blue, Green, Red, White
                poker_map = {
                        'purple': 0,
                        'black': 1,
                        'blue': 2,
                        'green': 3,
                        'red': 4,
                        'white': 5
                }
                if grade_lower.startswith('poker chip - '):
                        chip = grade_lower.replace('poker chip - ', '').strip()
                        return (0, poker_map.get(chip, 99))

                # Numerical system: 100-0, higher is better
                if grade_lower.startswith('numerical - '):
                        numeric_text = grade_lower.replace('numerical - ', '').strip()
                        try:
                                numeric_grade = int(numeric_text)
                                numeric_grade = max(0, min(100, numeric_grade))
                                return (1, 100 - numeric_grade)
                        except ValueError:
                                return (9, 999)

                # Alphabet system: A+ through F-
                alpha_order = [
                        'A+', 'A', 'A-',
                        'B+', 'B', 'B-',
                        'C+', 'C', 'C-',
                        'D+', 'D', 'D-',
                        'F+', 'F', 'F-'
                ]
                if grade_lower.startswith('alphabet - '):
                        alpha = grade.replace('Alphabet - ', '').strip().upper()
                        if alpha in alpha_order:
                                return (2, alpha_order.index(alpha))
                        return (9, 999)

                if grade_lower == 'udfa (undrafted free agent)' or grade_lower == 'udfa':
                        return (3, 100)

                round_map = {
                        'early-round 1': 10,
                        'mid-round 1': 11,
                        'late-round 1': 12,
                        'early-round 2': 20,
                        'mid-round 2': 21,
                        'late-round 2': 22,
                        'early-round 3': 30,
                        'mid-round 3': 31,
                        'late-round 3': 32,
                        'early-round 4': 40,
                        'mid-round 4': 41,
                        'late-round 4': 42,
                        'early-round 5': 50,
                        'mid-round 5': 51,
                        'late-round 5': 52,
                        'early-round 6': 60,
                        'mid-round 6': 61,
                        'late-round 6': 62,
                        'early-round 7': 70,
                        'mid-round 7': 71,
                        'late-round 7': 72
                }
                if grade_lower in round_map:
                        return (3, round_map.get(grade_lower, 999))

                return (9, 999)

        def get_big_board(self, board_type='overall', position=None):
                """Get board entries for overall or positional board"""
                conn = self.get_connection()
                cursor = conn.cursor()
                board_id = self._get_or_create_big_board_id(cursor, board_type, position)

                cursor.execute('''
                        SELECT e.id AS entry_id, e.rank_order, p.*
                        FROM big_board_entries e
                        JOIN players p ON p.id = e.player_id
                        WHERE e.board_id = ?
                        ORDER BY e.rank_order ASC
                ''', (board_id,))
                rows = cursor.fetchall()

                columns = [description[0] for description in cursor.description]
                board_entries = [dict(zip(columns, row)) for row in rows]
                conn.close()
                return board_entries

        def add_player_to_big_board(self, player_id, board_type='overall', position=None):
                """Add player into board using grade-first default insertion"""
                conn = self.get_connection()
                cursor = conn.cursor()
                board_id = self._get_or_create_big_board_id(cursor, board_type, position)

                cursor.execute(
                        'SELECT id FROM big_board_entries WHERE board_id = ? AND player_id = ?',
                        (board_id, player_id)
                )
                if cursor.fetchone():
                        conn.close()
                        return {'success': False, 'error': 'Player already exists on this board'}

                cursor.execute('SELECT grade, rank, name FROM players WHERE id = ?', (player_id,))
                target_player = cursor.fetchone()
                if not target_player:
                        conn.close()
                        return {'success': False, 'error': 'Player not found'}

                target_priority = self._grade_priority(target_player[0])
                target_rank = target_player[1] if target_player[1] is not None else 9999
                target_name = target_player[2] or ''

                cursor.execute('''
                        SELECT e.player_id, e.rank_order, p.grade, p.rank, p.name
                        FROM big_board_entries e
                        JOIN players p ON p.id = e.player_id
                        WHERE e.board_id = ?
                        ORDER BY e.rank_order ASC
                ''', (board_id,))
                existing = cursor.fetchall()

                insert_rank = len(existing) + 1
                for _, rank_order, grade, rank, name in existing:
                        priority = self._grade_priority(grade)
                        this_rank = rank if rank is not None else 9999
                        this_name = name or ''
                        if (target_priority, target_rank, target_name) < (priority, this_rank, this_name):
                                insert_rank = rank_order
                                break

                cursor.execute(
                        'UPDATE big_board_entries SET rank_order = rank_order + 1 WHERE board_id = ? AND rank_order >= ?',
                        (board_id, insert_rank)
                )
                cursor.execute(
                        'INSERT INTO big_board_entries (board_id, player_id, rank_order) VALUES (?, ?, ?)',
                        (board_id, player_id, insert_rank)
                )
                conn.commit()
                conn.close()
                return {'success': True}

        def reorder_big_board(self, ordered_player_ids, board_type='overall', position=None):
                """Persist drag-and-drop order for board entries"""
                conn = self.get_connection()
                cursor = conn.cursor()
                board_id = self._get_or_create_big_board_id(cursor, board_type, position)

                for index, player_id in enumerate(ordered_player_ids, start=1):
                        cursor.execute(
                                'UPDATE big_board_entries SET rank_order = ? WHERE board_id = ? AND player_id = ?',
                                (index, board_id, player_id)
                        )

                conn.commit()
                conn.close()
                return {'success': True}

        def remove_player_from_big_board(self, player_id, board_type='overall', position=None):
                """Remove player from board and compress order"""
                conn = self.get_connection()
                cursor = conn.cursor()
                board_id = self._get_or_create_big_board_id(cursor, board_type, position)

                cursor.execute(
                        'DELETE FROM big_board_entries WHERE board_id = ? AND player_id = ?',
                        (board_id, player_id)
                )

                cursor.execute(
                        'SELECT player_id FROM big_board_entries WHERE board_id = ? ORDER BY rank_order ASC',
                        (board_id,)
                )
                remaining = [row[0] for row in cursor.fetchall()]
                for index, pid in enumerate(remaining, start=1):
                        cursor.execute(
                                'UPDATE big_board_entries SET rank_order = ? WHERE board_id = ? AND player_id = ?',
                                (index, board_id, pid)
                        )

                conn.commit()
                conn.close()
                return {'success': True}

        def auto_sort_big_board(self, board_type='overall', position=None):
                """Auto-sort board entries by recorded player grades"""
                conn = self.get_connection()
                cursor = conn.cursor()
                board_id = self._get_or_create_big_board_id(cursor, board_type, position)

                cursor.execute('''
                        SELECT e.player_id, p.grade, p.rank, p.name
                        FROM big_board_entries e
                        JOIN players p ON p.id = e.player_id
                        WHERE e.board_id = ?
                ''', (board_id,))
                entries = cursor.fetchall()

                sorted_entries = sorted(
                        entries,
                        key=lambda row: (
                                self._grade_priority(row[1]),
                                row[2] if row[2] is not None else 9999,
                                row[3] or ''
                        )
                )

                for index, (player_id, _, _, _) in enumerate(sorted_entries, start=1):
                        cursor.execute(
                                'UPDATE big_board_entries SET rank_order = ? WHERE board_id = ? AND player_id = ?',
                                (index, board_id, player_id)
                        )

                conn.commit()
                conn.close()
                return {'success': True}
