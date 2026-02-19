import sqlite3
import json
import re
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
                if 'tankathon_rank' not in existing_columns:
                        cursor.execute('ALTER TABLE players ADD COLUMN tankathon_rank INTEGER')
                if 'weighted_avg_rank' not in existing_columns:
                        cursor.execute('ALTER TABLE players ADD COLUMN weighted_avg_rank REAL')

                cursor.execute('''
                        CREATE TABLE IF NOT EXISTS rank_boards (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                board_key TEXT NOT NULL UNIQUE,
                                board_name TEXT NOT NULL,
                                source_type TEXT NOT NULL DEFAULT 'imported',
                                weight REAL NOT NULL DEFAULT 1.0,
                                is_primary INTEGER NOT NULL DEFAULT 0,
                                created_at TEXT
                        )
                ''')

                cursor.execute('''
                        CREATE TABLE IF NOT EXISTS player_board_ranks (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                player_id INTEGER NOT NULL,
                                board_id INTEGER NOT NULL,
                                board_rank REAL NOT NULL,
                                UNIQUE(player_id, board_id),
                                FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE,
                                FOREIGN KEY(board_id) REFERENCES rank_boards(id) ON DELETE CASCADE
                        )
                ''')

                cursor.execute('CREATE INDEX IF NOT EXISTS idx_player_board_ranks_board_id ON player_board_ranks(board_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_player_board_ranks_player_id ON player_board_ranks(player_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_player_board_ranks_board_rank ON player_board_ranks(board_id, board_rank)')

                cursor.execute('''
                        INSERT OR IGNORE INTO rank_boards (board_key, board_name, source_type, weight, is_primary, created_at)
                        VALUES ('tankathon', 'Tankathon Big Board', 'tankathon', 1.0, 0, ?)
                ''', (datetime.now().isoformat(),))

                cursor.execute('''
                        INSERT OR IGNORE INTO rank_boards (board_key, board_name, source_type, weight, is_primary, created_at)
                        VALUES ('consensus_2026', 'Consensus Big Board 2026', 'consensus', 1.0, 1, ?)
                ''', (datetime.now().isoformat(),))

                cursor.execute('''
                        UPDATE rank_boards
                        SET is_primary = CASE WHEN board_key = 'consensus_2026' THEN 1 ELSE 0 END
                        WHERE board_key IN ('consensus_2026', 'tankathon')
                ''')

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

                cursor.execute('CREATE INDEX IF NOT EXISTS idx_players_rank ON players(rank)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_players_scouted_rank ON players(scouted, rank)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_players_school ON players(school)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_big_board_entries_board_rank ON big_board_entries(board_id, rank_order)')

                conn.commit()
                conn.close()

        @staticmethod
        def _slugify_board_key(name):
                cleaned = re.sub(r'[^a-z0-9]+', '_', (name or '').lower()).strip('_')
                if not cleaned:
                        cleaned = 'imported_board'
                return cleaned[:70]

        def _get_or_create_rank_board(self, cursor, board_key, board_name, source_type='imported', weight=1.0, is_primary=0):
                cursor.execute('SELECT id FROM rank_boards WHERE board_key = ?', (board_key,))
                existing = cursor.fetchone()
                if existing:
                        cursor.execute('''
                                UPDATE rank_boards
                                SET board_name = ?, source_type = ?, weight = ?, is_primary = ?
                                WHERE board_key = ?
                        ''', (board_name, source_type, weight, is_primary, board_key))
                        return existing[0]

                cursor.execute('''
                        INSERT INTO rank_boards (board_key, board_name, source_type, weight, is_primary, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                ''', (board_key, board_name, source_type, weight, is_primary, datetime.now().isoformat()))
                return cursor.lastrowid

        def _ensure_player_exists_by_name(self, cursor, player_name):
                cursor.execute('SELECT id FROM players WHERE name = ?', (player_name,))
                existing = cursor.fetchone()
                if existing:
                        return existing[0]

                cursor.execute('INSERT INTO players (name) VALUES (?)', (player_name,))
                return cursor.lastrowid

        def _upsert_board_rank_entries(self, cursor, board_key, board_name, entries, source_type='imported', weight=1.0, is_primary=0):
                board_id = self._get_or_create_rank_board(
                        cursor,
                        board_key=board_key,
                        board_name=board_name,
                        source_type=source_type,
                        weight=weight,
                        is_primary=is_primary
                )

                cursor.execute('DELETE FROM player_board_ranks WHERE board_id = ?', (board_id,))

                cursor.execute('SELECT id, name FROM players')
                existing_players = cursor.fetchall()
                normalized_lookup = {}
                for existing_player_id, existing_name in existing_players:
                        normalized_name = self._normalize_player_name(existing_name)
                        if normalized_name and normalized_name not in normalized_lookup:
                                normalized_lookup[normalized_name] = existing_player_id

                matched_count = 0
                new_player_count = 0
                seen_player_ids = set()

                for entry in entries:
                        player_name = (entry.get('name') or '').strip()
                        rank_value = entry.get('rank')
                        if not player_name or rank_value is None:
                                continue

                        cursor.execute('SELECT id FROM players WHERE name = ?', (player_name,))
                        existing_player = cursor.fetchone()
                        if existing_player:
                                player_id = existing_player[0]
                        else:
                                normalized_name = self._normalize_player_name(player_name)
                                player_id = normalized_lookup.get(normalized_name)
                                if not player_id:
                                        player_id = self._ensure_player_exists_by_name(cursor, player_name)
                                        new_player_count += 1
                                        if normalized_name:
                                                normalized_lookup[normalized_name] = player_id

                        if player_id in seen_player_ids:
                                continue
                        seen_player_ids.add(player_id)

                        cursor.execute('''
                                INSERT INTO player_board_ranks (player_id, board_id, board_rank)
                                VALUES (?, ?, ?)
                        ''', (player_id, board_id, float(rank_value)))
                        matched_count += 1

                return {
                        'board_id': board_id,
                        'matched_count': matched_count,
                        'new_player_count': new_player_count
                }

        def recalculate_default_rankings(self):
                """Recalculate displayed rankings using primary board first, then weighted average, then Tankathon fallback."""
                conn = self.get_connection()
                cursor = conn.cursor()

                cursor.execute('''
                        SELECT id, board_key, weight, is_primary
                        FROM rank_boards
                ''')
                board_rows = cursor.fetchall()
                board_key_by_id = {row[0]: row[1] for row in board_rows}
                board_weight_by_id = {row[0]: float(row[2] or 0.0) for row in board_rows}
                primary_board_id = next((row[0] for row in board_rows if row[3] == 1), None)

                cursor.execute('''
                        SELECT player_id, board_id, board_rank
                        FROM player_board_ranks
                ''')
                rank_rows = cursor.fetchall()

                ranks_by_player = {}
                weighted_sum = {}
                weighted_total = {}

                for player_id, board_id, board_rank in rank_rows:
                        ranks_by_player.setdefault(player_id, {})[board_id] = float(board_rank)
                        weight = board_weight_by_id.get(board_id, 0.0)
                        if weight > 0:
                                weighted_sum[player_id] = weighted_sum.get(player_id, 0.0) + (float(board_rank) * weight)
                                weighted_total[player_id] = weighted_total.get(player_id, 0.0) + weight

                weighted_avg_by_player = {
                        player_id: (weighted_sum[player_id] / weighted_total[player_id])
                        for player_id in weighted_sum
                        if weighted_total.get(player_id, 0) > 0
                }

                cursor.execute('''
                        SELECT id, name, tankathon_rank
                        FROM players
                ''')
                players = cursor.fetchall()

                player_sort_rows = []
                for player_id, name, tankathon_rank in players:
                        per_player_ranks = ranks_by_player.get(player_id, {})

                        primary_rank = None
                        if primary_board_id is not None and primary_board_id in per_player_ranks:
                                primary_rank = per_player_ranks.get(primary_board_id)

                        weighted_rank = weighted_avg_by_player.get(player_id)
                        tankathon_fallback = float(tankathon_rank) if tankathon_rank is not None else None

                        effective_rank = primary_rank
                        if effective_rank is None:
                                effective_rank = weighted_rank
                        if effective_rank is None:
                                effective_rank = tankathon_fallback

                        if effective_rank is None:
                                sort_rank = 999999.0
                        else:
                                sort_rank = float(effective_rank)

                        player_sort_rows.append((player_id, name or '', sort_rank, weighted_rank))

                player_sort_rows.sort(key=lambda row: (row[2], row[1]))

                for index, (player_id, _, _, weighted_rank) in enumerate(player_sort_rows, start=1):
                        cursor.execute('''
                                UPDATE players
                                SET rank = ?, weighted_avg_rank = ?
                                WHERE id = ?
                        ''', (index, weighted_rank, player_id))

                conn.commit()
                conn.close()

                self.calculate_positional_ranks()
                return len(player_sort_rows)
        
        def import_players_from_json (self, json_file='nfl_big_board.json', recalculate_rankings=True):
                """Import players from the JSON generated from Tankathon Webscraper"""
                try:
                        with open(json_file, 'r', encoding ='utf-8') as f:
                                players = json.load(f)

                        conn = self.get_connection()
                        cursor = conn.cursor()

                        imported = 0
                        board_entries = []
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
                                                (rank, tankathon_rank, name, position, positional_rank, school, height, weight, jersey_number, player_url, stats)
                                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                                ON CONFLICT(name) DO UPDATE SET
                                                        tankathon_rank = excluded.tankathon_rank,
                                                        position = excluded.position,
                                                        positional_rank = excluded.positional_rank,
                                                        school = excluded.school,
                                                        height = excluded.height,
                                                        weight = excluded.weight,
                                                        jersey_number = excluded.jersey_number,
                                                        player_url = excluded.player_url,
                                                        stats = excluded.stats
                                        ''', (rank, rank, name, position, positional_rank, school, height, weight, jersey_number, player_url, stats_json))

                                        board_entries.append({'name': name, 'rank': rank})

                                        imported += 1

                                except Exception as e:
                                        print(f"Error importing player {player.get('name')}: {e}")
                                        return {'success': False, 'error': f"Error importing player {player.get('name')}: {e}", 'imported': imported}

                        self._upsert_board_rank_entries(
                                cursor,
                                board_key='tankathon',
                                board_name='Tankathon Big Board',
                                entries=board_entries,
                                source_type='tankathon',
                                weight=1.0,
                                is_primary=0
                        )

                        conn.commit()
                        conn.close()
                        if recalculate_rankings:
                                self.recalculate_default_rankings()

                        print(f"imported {imported} players from Tankathon JSON")
                        return {
                                'success': True,
                                'imported': imported,
                                'recalculated': bool(recalculate_rankings)
                        }
                
                except Exception as e:
                        print(f"Error importing from JSON: {e}")
                        return {'success': False, 'error': str(e), 'imported': 0}

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
                                except Exception:
                                        player['stats'] = {}
                        players.append(player)

                conn.close()
                return players
        
        def get_filtered_players(self, positions=None, max_rank=None, include_scouted=False, search_term=None, name_search=None, school=None, watch_list_only=False):
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

                if watch_list_only:
                        query += '''
                                AND EXISTS (
                                        SELECT 1
                                        FROM big_board_entries e
                                        JOIN big_boards b ON b.id = e.board_id
                                        WHERE e.player_id = players.id
                                          AND b.board_type = 'watchlist'
                                          AND b.position IS NULL
                                )
                        '''
                
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
                                except Exception:
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
                        except Exception:
                                player['stats'] = {}

                cursor.execute('''
                        SELECT e.rank_order
                        FROM big_board_entries e
                        JOIN big_boards b ON b.id = e.board_id
                        WHERE e.player_id = ?
                          AND b.board_type = 'overall'
                          AND b.position IS NULL
                        LIMIT 1
                ''', (player_id,))
                personal_rank_row = cursor.fetchone()
                player['personal_big_board_rank'] = personal_rank_row[0] if personal_rank_row else None

                cursor.execute('''
                        SELECT MIN(e.rank_order)
                        FROM big_board_entries e
                        JOIN big_boards b ON b.id = e.board_id
                        WHERE e.player_id = ?
                          AND b.board_type = 'position'
                ''', (player_id,))
                personal_pos_rank_row = cursor.fetchone()
                player['personal_pos_rank'] = personal_pos_rank_row[0] if personal_pos_rank_row and personal_pos_rank_row[0] is not None else None

                cursor.execute('''
                        SELECT e.rank_order
                        FROM big_board_entries e
                        JOIN big_boards b ON b.id = e.board_id
                        WHERE e.player_id = ?
                          AND b.board_type = 'watchlist'
                          AND b.position IS NULL
                        LIMIT 1
                ''', (player_id,))
                watchlist_rank_row = cursor.fetchone()
                player['watchlist_rank'] = watchlist_rank_row[0] if watchlist_rank_row else None
                player['in_watch_list'] = bool(watchlist_rank_row)

                player['board_ranks'] = self.get_player_board_ranks(player_id, conn=conn)
                player['weighted_average_rank'] = player.get('weighted_avg_rank')

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

                watch_list_board_id = self._get_or_create_big_board_id(cursor, board_type='watchlist', position=None)
                cursor.execute(
                        'DELETE FROM big_board_entries WHERE board_id = ? AND player_id = ?',
                        (watch_list_board_id, player_id)
                )

                cursor.execute(
                        'SELECT player_id FROM big_board_entries WHERE board_id = ? ORDER BY rank_order ASC, id ASC',
                        (watch_list_board_id,)
                )
                remaining = [row[0] for row in cursor.fetchall()]
                for index, pid in enumerate(remaining, start=1):
                        cursor.execute(
                                'UPDATE big_board_entries SET rank_order = ? WHERE board_id = ? AND player_id = ?',
                                (index, watch_list_board_id, pid)
                        )

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

        def update_player_profile(self, player_id, profile_data):
                """Update editable player profile fields from scout report modal."""
                conn = self.get_connection()
                cursor = conn.cursor()

                stats_text = (profile_data.get('stats_json') or '').strip()
                parsed_stats = {}
                if stats_text:
                        parsed_stats = json.loads(stats_text)
                        if not isinstance(parsed_stats, dict):
                                raise ValueError('Stats JSON must be an object (key/value pairs).')

                cursor.execute('''
                        UPDATE players
                        SET
                                position = ?,
                                school = ?,
                                height = ?,
                                weight = ?,
                                jersey_number = ?,
                                player_url = ?,
                                stats = ?
                        WHERE id = ?
                ''', (
                        (profile_data.get('position') or '').strip(),
                        (profile_data.get('school') or '').strip(),
                        (profile_data.get('height') or '').strip(),
                        (profile_data.get('weight') or '').strip(),
                        (profile_data.get('jersey_number') or '').strip(),
                        (profile_data.get('player_url') or '').strip(),
                        json.dumps(parsed_stats),
                        player_id
                ))

                conn.commit()
                conn.close()

        def get_rank_boards_config(self):
                conn = self.get_connection()
                cursor = conn.cursor()

                cursor.execute('''
                        SELECT b.id, b.board_key, b.board_name, b.source_type, b.weight, b.is_primary,
                               COUNT(pbr.id) AS player_count
                        FROM rank_boards b
                        LEFT JOIN player_board_ranks pbr ON pbr.board_id = b.id
                        GROUP BY b.id, b.board_key, b.board_name, b.source_type, b.weight, b.is_primary
                        ORDER BY b.is_primary DESC, b.board_name ASC
                ''')

                rows = cursor.fetchall()
                conn.close()

                return [
                        {
                                'id': row[0],
                                'board_key': row[1],
                                'board_name': row[2],
                                'source_type': row[3],
                                'weight': row[4],
                                'is_primary': bool(row[5]),
                                'player_count': row[6]
                        }
                        for row in rows
                ]

        def update_rank_board_weights(self, board_updates):
                if not isinstance(board_updates, list):
                        return {'success': False, 'error': 'board_updates must be a list.'}

                conn = self.get_connection()
                cursor = conn.cursor()

                target_primary_key = None
                for update in board_updates:
                        board_key = (update.get('board_key') or '').strip()
                        if not board_key:
                                continue

                        if update.get('is_primary'):
                                target_primary_key = board_key

                        raw_weight = update.get('weight', 1)
                        try:
                                weight = float(raw_weight)
                        except (TypeError, ValueError):
                                weight = 1.0

                        if weight < 0:
                                weight = 0.0

                        cursor.execute('''
                                UPDATE rank_boards
                                SET weight = ?
                                WHERE board_key = ?
                        ''', (weight, board_key))

                if target_primary_key:
                        cursor.execute('UPDATE rank_boards SET is_primary = 0')
                        cursor.execute('UPDATE rank_boards SET is_primary = 1 WHERE board_key = ?', (target_primary_key,))

                conn.commit()
                conn.close()

                self.recalculate_default_rankings()
                return {'success': True}

        def remove_rank_board(self, board_key):
                board_key = (board_key or '').strip()
                if not board_key:
                        return {'success': False, 'error': 'board_key is required.'}

                protected_keys = {'consensus_2026', 'tankathon'}
                if board_key in protected_keys:
                        return {'success': False, 'error': 'Core rank boards cannot be removed.'}

                conn = self.get_connection()
                cursor = conn.cursor()

                cursor.execute('SELECT board_key, source_type, is_primary FROM rank_boards WHERE board_key = ?', (board_key,))
                board_row = cursor.fetchone()
                if not board_row:
                        conn.close()
                        return {'success': False, 'error': 'Board not found.'}

                _, source_type, is_primary = board_row
                if source_type != 'imported':
                        conn.close()
                        return {'success': False, 'error': 'Only imported boards can be removed.'}

                cursor.execute('DELETE FROM rank_boards WHERE board_key = ?', (board_key,))

                if is_primary:
                        cursor.execute('SELECT board_key FROM rank_boards ORDER BY board_name ASC LIMIT 1')
                        fallback = cursor.fetchone()
                        if fallback:
                                cursor.execute('UPDATE rank_boards SET is_primary = 0')
                                cursor.execute('UPDATE rank_boards SET is_primary = 1 WHERE board_key = ?', (fallback[0],))

                conn.commit()
                conn.close()

                self.recalculate_default_rankings()
                return {'success': True}

        def get_player_board_ranks(self, player_id, conn=None):
                owns_conn = conn is None
                if owns_conn:
                        conn = self.get_connection()
                cursor = conn.cursor()

                cursor.execute('''
                        SELECT b.board_key, b.board_name, b.source_type, b.weight, b.is_primary, pbr.board_rank
                        FROM player_board_ranks pbr
                        JOIN rank_boards b ON b.id = pbr.board_id
                        WHERE pbr.player_id = ?
                        ORDER BY b.is_primary DESC, pbr.board_rank ASC, b.board_name ASC
                ''', (player_id,))
                rows = cursor.fetchall()

                if owns_conn:
                        conn.close()

                return [
                        {
                                'board_key': row[0],
                                'board_name': row[1],
                                'source_type': row[2],
                                'weight': row[3],
                                'is_primary': bool(row[4]),
                                'rank': row[5]
                        }
                        for row in rows
                ]

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
                                        rank, tankathon_rank, name, position, school, height, weight,
                                        jersey_number, player_url, notes, grade, scouted, scout_date
                                )
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                                player_data.get('rank'),
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
                        self.recalculate_default_rankings()
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
                        SELECT e.id AS entry_id, e.rank_order, p.*, pbr.board_rank AS consensus_rank
                        FROM big_board_entries e
                        JOIN players p ON p.id = e.player_id
                        LEFT JOIN rank_boards rb ON rb.board_key = 'consensus_2026'
                        LEFT JOIN player_board_ranks pbr ON pbr.player_id = p.id AND pbr.board_id = rb.id
                        WHERE e.board_id = ?
                        ORDER BY e.rank_order ASC
                ''', (board_id,))
                rows = cursor.fetchall()

                columns = [description[0] for description in cursor.description]
                board_entries = [dict(zip(columns, row)) for row in rows]

                cursor.execute('''
                        SELECT p.name, pbr.board_rank
                        FROM player_board_ranks pbr
                        JOIN rank_boards rb ON rb.id = pbr.board_id
                        JOIN players p ON p.id = pbr.player_id
                        WHERE rb.board_key = 'consensus_2026'
                ''')
                consensus_rows = cursor.fetchall()
                consensus_by_normalized_name = {}
                for consensus_name, consensus_rank in consensus_rows:
                        normalized_name = self._normalize_player_name(consensus_name)
                        if not normalized_name:
                                continue

                        rank_value = float(consensus_rank)
                        existing_rank = consensus_by_normalized_name.get(normalized_name)
                        if existing_rank is None or rank_value < existing_rank:
                                consensus_by_normalized_name[normalized_name] = rank_value

                for player in board_entries:
                        if player.get('consensus_rank') is not None:
                                continue
                        normalized_name = self._normalize_player_name(player.get('name'))
                        if normalized_name in consensus_by_normalized_name:
                                player['consensus_rank'] = consensus_by_normalized_name[normalized_name]

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

        def get_watch_list(self):
                """Get ranked personal watch list entries."""
                return self.get_big_board(board_type='watchlist', position=None)

        def add_player_to_watch_list(self, player_id):
                """Add player to personal watch list at the bottom."""
                conn = self.get_connection()
                cursor = conn.cursor()

                board_id = self._get_or_create_big_board_id(cursor, board_type='watchlist', position=None)

                cursor.execute(
                        'SELECT 1 FROM big_board_entries WHERE board_id = ? AND player_id = ?',
                        (board_id, player_id)
                )
                if cursor.fetchone():
                        conn.close()
                        return {'success': False, 'error': 'Player is already on your watch list.'}

                cursor.execute('SELECT id FROM players WHERE id = ?', (player_id,))
                if not cursor.fetchone():
                        conn.close()
                        return {'success': False, 'error': 'Player not found.'}

                cursor.execute('SELECT COALESCE(MAX(rank_order), 0) FROM big_board_entries WHERE board_id = ?', (board_id,))
                max_rank = cursor.fetchone()[0] or 0

                cursor.execute(
                        'INSERT INTO big_board_entries (board_id, player_id, rank_order) VALUES (?, ?, ?)',
                        (board_id, player_id, max_rank + 1)
                )

                conn.commit()
                conn.close()
                return {'success': True}

        def reorder_watch_list(self, ordered_player_ids):
                """Persist drag-and-drop order for watch list."""
                return self.reorder_big_board(ordered_player_ids, board_type='watchlist', position=None)

        def remove_player_from_watch_list(self, player_id):
                """Remove player from watch list and compress ranks."""
                return self.remove_player_from_big_board(player_id, board_type='watchlist', position=None)

        @staticmethod
        def _normalize_player_name(name):
                if not name:
                        return ''

                normalized = name.lower().strip()
                normalized = normalized.replace('.', ' ')
                normalized = normalized.replace(',', ' ')
                normalized = re.sub(r'\b(jr|sr|ii|iii|iv|v)\b', '', normalized)
                normalized = re.sub(r'[^a-z0-9\s-]', '', normalized)
                normalized = re.sub(r'\s+', ' ', normalized)

                tokens = normalized.strip().split()
                collapsed_tokens = []
                index = 0
                while index < len(tokens):
                        token = tokens[index]
                        if len(token) == 1 and token.isalpha():
                                initials = [token]
                                index += 1
                                while index < len(tokens) and len(tokens[index]) == 1 and tokens[index].isalpha():
                                        initials.append(tokens[index])
                                        index += 1
                                collapsed_tokens.append(''.join(initials))
                                continue

                        collapsed_tokens.append(token)
                        index += 1

                normalized = ' '.join(collapsed_tokens)
                return normalized.strip()

        @staticmethod
        def _parse_big_board_text(board_text):
                """Parse text lines into ordered (rank, name) entries."""
                entries = []
                if not board_text:
                        return entries

                lines = board_text.splitlines()
                for line in lines:
                        raw = (line or '').strip()
                        if not raw:
                                continue

                        match = re.match(r'^\s*(\d+)\s*[\.)\-:]?\s*(.+?)\s*$', raw)
                        if match:
                                rank_value = int(match.group(1))
                                name = match.group(2).strip()
                        else:
                                rank_value = len(entries) + 1
                                name = raw

                        if not name:
                                continue

                        entries.append({'rank': rank_value, 'name': name})

                return entries

        def import_external_big_boards(self, boards, weighting_mode='equal'):
                """Import multiple external boards and store each board independently."""
                if not isinstance(boards, list) or len(boards) == 0:
                        return {'success': False, 'error': 'At least one board is required.'}

                conn = self.get_connection()
                cursor = conn.cursor()

                board_summaries = []
                unmatched_names = set()
                total_new_players = 0

                for board in boards:
                        board_name = (board.get('name') or 'Unnamed Board').strip() if isinstance(board, dict) else 'Unnamed Board'
                        board_text = board.get('text', '') if isinstance(board, dict) else ''
                        board_key = self._slugify_board_key(board_name)
                        if not board_key.startswith('imported_'):
                                board_key = f'imported_{board_key}'

                        parsed_entries = self._parse_big_board_text(board_text)
                        if not parsed_entries:
                                continue

                        if weighting_mode == 'weighted':
                                raw_weight = board.get('weight', 1) if isinstance(board, dict) else 1
                                try:
                                        board_weight = float(raw_weight)
                                except (TypeError, ValueError):
                                        board_weight = 1.0
                        else:
                                board_weight = 1.0

                        if board_weight <= 0:
                                board_weight = 1.0

                        normalized_entries = []
                        for entry in parsed_entries:
                                entry_name = (entry.get('name') or '').strip()
                                if not entry_name:
                                        continue
                                normalized_entries.append({'name': entry_name, 'rank': entry.get('rank')})

                        upsert_result = self._upsert_board_rank_entries(
                                cursor,
                                board_key=board_key,
                                board_name=board_name,
                                entries=normalized_entries,
                                source_type='imported',
                                weight=board_weight,
                                is_primary=0
                        )
                        total_new_players += upsert_result['new_player_count']

                        board_summaries.append({
                                'name': board_name,
                                'board_key': board_key,
                                'entries': len(parsed_entries),
                                'matched': upsert_result['matched_count'],
                                'weight': board_weight
                        })

                if not board_summaries:
                        conn.close()
                        return {'success': False, 'error': 'No valid board entries were found in uploaded files.'}

                conn.commit()
                conn.close()
                player_count = self.recalculate_default_rankings()

                return {
                        'success': True,
                        'mode': weighting_mode,
                        'boards_processed': len(board_summaries),
                        'boards': board_summaries,
                        'players_ranked_from_import': player_count,
                        'players_total_ranked': player_count,
                        'new_players_added': total_new_players,
                        'positional_rank_updates': player_count,
                        'unmatched_count': len(unmatched_names),
                        'unmatched_examples': sorted(list(unmatched_names))[:10]
                }

        def import_consensus_board(self, players, board_key='consensus_2026', board_name='Consensus Big Board 2026'):
                """Import consensus board ranks, creating missing players without overwriting Tankathon detail fields."""
                if not isinstance(players, list) or not players:
                        return {'success': False, 'error': 'No consensus players provided.'}

                conn = self.get_connection()
                cursor = conn.cursor()

                cursor.execute('SELECT id, name, position, school FROM players')
                existing_players = cursor.fetchall()
                normalized_lookup = {}
                for existing_id, existing_name, _, _ in existing_players:
                        normalized_name = self._normalize_player_name(existing_name)
                        if normalized_name and normalized_name not in normalized_lookup:
                                normalized_lookup[normalized_name] = (existing_id, existing_name)

                normalized_entries = []
                for player in players:
                        name = (player.get('name') or '').strip()
                        rank = player.get('rank')
                        if not name or rank is None:
                                continue

                        position = (player.get('position') or '').strip()
                        school = (player.get('school') or '').strip()

                        cursor.execute('SELECT id, name FROM players WHERE name = ?', (name,))
                        exact_match = cursor.fetchone()
                        canonical_name = name

                        if exact_match:
                                player_id = exact_match[0]
                                canonical_name = exact_match[1]
                        else:
                                normalized_name = self._normalize_player_name(name)
                                normalized_match = normalized_lookup.get(normalized_name)
                                if normalized_match:
                                        player_id = normalized_match[0]
                                        canonical_name = normalized_match[1]
                                else:
                                        cursor.execute('INSERT INTO players (name, position, school) VALUES (?, ?, ?)', (name, position, school))
                                        player_id = cursor.lastrowid
                                        canonical_name = name
                                        if normalized_name:
                                                normalized_lookup[normalized_name] = (player_id, canonical_name)

                        cursor.execute('''
                                UPDATE players
                                SET position = CASE
                                        WHEN (position IS NULL OR position = '') AND ? != ''
                                        THEN ? ELSE position
                                END,
                                school = CASE
                                        WHEN (school IS NULL OR school = '') AND ? != ''
                                        THEN ? ELSE school
                                END
                                WHERE id = ?
                        ''', (position, position, school, school, player_id))

                        normalized_entries.append({'name': canonical_name, 'rank': rank})

                if not normalized_entries:
                        conn.close()
                        return {'success': False, 'error': 'No valid consensus entries found.'}

                cursor.execute('UPDATE rank_boards SET is_primary = 0')
                upsert_result = self._upsert_board_rank_entries(
                        cursor,
                        board_key=board_key,
                        board_name=board_name,
                        entries=normalized_entries,
                        source_type='consensus',
                        weight=1.0,
                        is_primary=1
                )

                conn.commit()
                conn.close()
                ranked_count = self.recalculate_default_rankings()

                return {
                        'success': True,
                        'board_key': board_key,
                        'board_name': board_name,
                        'entries_imported': upsert_result['matched_count'],
                        'new_players_added': upsert_result['new_player_count'],
                        'players_total_ranked': ranked_count
                }

        def import_nflmock_url_board(self, players, board_name):
                """Import a non-consensus NFLMockDraftDatabase board by URL into selectable rank boards."""
                if not isinstance(players, list) or not players:
                        return {'success': False, 'error': 'No players provided from source board.'}

                normalized_board_name = (board_name or '').strip() or 'Imported NFLMockDraftDatabase Board'
                board_key = self._slugify_board_key(normalized_board_name)

                conn = self.get_connection()
                cursor = conn.cursor()

                cursor.execute('SELECT id, name, position, school FROM players')
                existing_players = cursor.fetchall()
                normalized_lookup = {}
                for existing_id, existing_name, _, _ in existing_players:
                        normalized_name = self._normalize_player_name(existing_name)
                        if normalized_name and normalized_name not in normalized_lookup:
                                normalized_lookup[normalized_name] = (existing_id, existing_name)

                normalized_entries = []
                for player in players:
                        name = (player.get('name') or '').strip()
                        rank = player.get('rank')
                        if not name or rank is None:
                                continue

                        position = (player.get('position') or '').strip()
                        school = (player.get('school') or '').strip()

                        cursor.execute('SELECT id, name FROM players WHERE name = ?', (name,))
                        exact_match = cursor.fetchone()
                        canonical_name = name

                        if exact_match:
                                player_id = exact_match[0]
                                canonical_name = exact_match[1]
                        else:
                                normalized_name = self._normalize_player_name(name)
                                normalized_match = normalized_lookup.get(normalized_name)
                                if normalized_match:
                                        player_id = normalized_match[0]
                                        canonical_name = normalized_match[1]
                                else:
                                        cursor.execute('INSERT INTO players (name, position, school) VALUES (?, ?, ?)', (name, position, school))
                                        player_id = cursor.lastrowid
                                        canonical_name = name
                                        if normalized_name:
                                                normalized_lookup[normalized_name] = (player_id, canonical_name)

                        cursor.execute('''
                                UPDATE players
                                SET position = CASE
                                        WHEN (position IS NULL OR position = '') AND ? != ''
                                        THEN ? ELSE position
                                END,
                                school = CASE
                                        WHEN (school IS NULL OR school = '') AND ? != ''
                                        THEN ? ELSE school
                                END
                                WHERE id = ?
                        ''', (position, position, school, school, player_id))

                        normalized_entries.append({'name': canonical_name, 'rank': rank})

                if not normalized_entries:
                        conn.close()
                        return {'success': False, 'error': 'No valid entries found in source board.'}

                upsert_result = self._upsert_board_rank_entries(
                        cursor,
                        board_key=board_key,
                        board_name=normalized_board_name,
                        entries=normalized_entries,
                        source_type='imported',
                        weight=1.0,
                        is_primary=0
                )

                conn.commit()
                conn.close()
                ranked_count = self.recalculate_default_rankings()

                return {
                        'success': True,
                        'board_key': board_key,
                        'board_name': normalized_board_name,
                        'entries_imported': upsert_result['matched_count'],
                        'new_players_added': upsert_result['new_player_count'],
                        'players_total_ranked': ranked_count
                }

        def merge_player_name_duplicates(self):
                """Merge duplicate players that normalize to the same name and rewire references."""
                conn = self.get_connection()
                cursor = conn.cursor()

                def value_score(player_row):
                        score = 0
                        if player_row.get('scouted'):
                                score += 5
                        for key in ['position', 'school', 'height', 'weight', 'player_url', 'stats', 'notes', 'games_watched', 'grade', 'grade_secondary']:
                                if (player_row.get(key) or '').strip():
                                        score += 1
                        return score

                def choose_rank_value(current_value, incoming_value):
                        current_num = None
                        incoming_num = None
                        try:
                                current_num = float(current_value) if current_value is not None else None
                        except Exception:
                                current_num = None
                        try:
                                incoming_num = float(incoming_value) if incoming_value is not None else None
                        except Exception:
                                incoming_num = None

                        if incoming_num is None:
                                return current_value
                        if current_num is None:
                                return incoming_value
                        return incoming_value if incoming_num < current_num else current_value

                try:
                        cursor.execute('SELECT * FROM players')
                        columns = [description[0] for description in cursor.description]
                        players = [dict(zip(columns, row)) for row in cursor.fetchall()]

                        groups = {}
                        for player in players:
                                normalized_name = self._normalize_player_name(player.get('name'))
                                if not normalized_name:
                                        continue
                                groups.setdefault(normalized_name, []).append(player)

                        duplicate_groups = [group for group in groups.values() if len(group) > 1]
                        if not duplicate_groups:
                                conn.close()
                                return {
                                        'success': True,
                                        'groups_merged': 0,
                                        'players_removed': 0,
                                        'output': 'No duplicate player name variants found.'
                                }

                        merged_groups = 0
                        players_removed = 0

                        text_fields = ['position', 'positional_rank', 'school', 'height', 'weight', 'jersey_number', 'player_url', 'stats', 'notes', 'games_watched', 'grade', 'grade_secondary', 'scout_date']

                        for group in duplicate_groups:
                                canonical = sorted(
                                        group,
                                        key=lambda row: (
                                                -value_score(row),
                                                0 if row.get('name') == self._normalize_player_name(row.get('name')) else 1,
                                                row.get('id')
                                        )
                                )[0]
                                canonical_id = canonical['id']

                                for duplicate in group:
                                        duplicate_id = duplicate['id']
                                        if duplicate_id == canonical_id:
                                                continue

                                        for field in text_fields:
                                                canonical_value = (canonical.get(field) or '').strip()
                                                duplicate_value = (duplicate.get(field) or '').strip()
                                                if not canonical_value and duplicate_value:
                                                        canonical[field] = duplicate_value

                                        canonical['rank'] = choose_rank_value(canonical.get('rank'), duplicate.get('rank'))
                                        canonical['tankathon_rank'] = choose_rank_value(canonical.get('tankathon_rank'), duplicate.get('tankathon_rank'))
                                        canonical['weighted_avg_rank'] = choose_rank_value(canonical.get('weighted_avg_rank'), duplicate.get('weighted_avg_rank'))
                                        canonical['scouted'] = 1 if canonical.get('scouted') or duplicate.get('scouted') else 0

                                        cursor.execute('SELECT board_id, rank_order FROM big_board_entries WHERE player_id = ?', (duplicate_id,))
                                        duplicate_board_entries = cursor.fetchall()
                                        for board_id, rank_order in duplicate_board_entries:
                                                cursor.execute(
                                                        'SELECT id FROM big_board_entries WHERE board_id = ? AND player_id = ?',
                                                        (board_id, canonical_id)
                                                )
                                                existing_entry = cursor.fetchone()
                                                if existing_entry:
                                                        cursor.execute('DELETE FROM big_board_entries WHERE board_id = ? AND player_id = ?', (board_id, duplicate_id))
                                                else:
                                                        cursor.execute(
                                                                'UPDATE big_board_entries SET player_id = ? WHERE board_id = ? AND player_id = ?',
                                                                (canonical_id, board_id, duplicate_id)
                                                        )

                                        cursor.execute('SELECT board_id, board_rank FROM player_board_ranks WHERE player_id = ?', (duplicate_id,))
                                        duplicate_board_ranks = cursor.fetchall()
                                        for board_id, duplicate_board_rank in duplicate_board_ranks:
                                                cursor.execute(
                                                        'SELECT id, board_rank FROM player_board_ranks WHERE board_id = ? AND player_id = ?',
                                                        (board_id, canonical_id)
                                                )
                                                existing_rank = cursor.fetchone()
                                                if existing_rank:
                                                        existing_rank_id, existing_rank_value = existing_rank
                                                        merged_rank = min(float(existing_rank_value), float(duplicate_board_rank))
                                                        cursor.execute(
                                                                'UPDATE player_board_ranks SET board_rank = ? WHERE id = ?',
                                                                (merged_rank, existing_rank_id)
                                                        )
                                                        cursor.execute(
                                                                'DELETE FROM player_board_ranks WHERE board_id = ? AND player_id = ?',
                                                                (board_id, duplicate_id)
                                                        )
                                                else:
                                                        cursor.execute(
                                                                'UPDATE player_board_ranks SET player_id = ? WHERE board_id = ? AND player_id = ?',
                                                                (canonical_id, board_id, duplicate_id)
                                                        )

                                        cursor.execute('DELETE FROM players WHERE id = ?', (duplicate_id,))
                                        players_removed += 1

                                cursor.execute('''
                                        UPDATE players
                                        SET rank = ?,
                                            position = ?,
                                            positional_rank = ?,
                                            school = ?,
                                            height = ?,
                                            weight = ?,
                                            jersey_number = ?,
                                            player_url = ?,
                                            stats = ?,
                                            scouted = ?,
                                            notes = ?,
                                            games_watched = ?,
                                            grade = ?,
                                            grade_secondary = ?,
                                            scout_date = ?,
                                            tankathon_rank = ?,
                                            weighted_avg_rank = ?
                                        WHERE id = ?
                                ''', (
                                        canonical.get('rank'),
                                        canonical.get('position'),
                                        canonical.get('positional_rank'),
                                        canonical.get('school'),
                                        canonical.get('height'),
                                        canonical.get('weight'),
                                        canonical.get('jersey_number'),
                                        canonical.get('player_url'),
                                        canonical.get('stats'),
                                        canonical.get('scouted'),
                                        canonical.get('notes'),
                                        canonical.get('games_watched'),
                                        canonical.get('grade'),
                                        canonical.get('grade_secondary'),
                                        canonical.get('scout_date'),
                                        canonical.get('tankathon_rank'),
                                        canonical.get('weighted_avg_rank'),
                                        canonical_id
                                ))

                                merged_groups += 1

                        cursor.execute('SELECT id FROM big_boards')
                        board_ids = [row[0] for row in cursor.fetchall()]
                        for board_id in board_ids:
                                cursor.execute(
                                        'SELECT id FROM big_board_entries WHERE board_id = ? ORDER BY rank_order ASC, id ASC',
                                        (board_id,)
                                )
                                entry_ids = [row[0] for row in cursor.fetchall()]
                                for index, entry_id in enumerate(entry_ids, start=1):
                                        cursor.execute('UPDATE big_board_entries SET rank_order = ? WHERE id = ?', (index, entry_id))

                        conn.commit()
                        conn.close()
                        ranked_count = self.recalculate_default_rankings()

                        return {
                                'success': True,
                                'groups_merged': merged_groups,
                                'players_removed': players_removed,
                                'players_total_ranked': ranked_count,
                                'output': f'Merged {players_removed} duplicate players across {merged_groups} normalized-name groups.'
                        }
                except Exception as error:
                        conn.rollback()
                        conn.close()
                        return {'success': False, 'error': str(error)}

        def export_big_board_text(self, scope='overall', position=None):
                """Export rankings in '#. player name' format."""
                conn = self.get_connection()
                cursor = conn.cursor()

                board_type = 'position' if scope == 'position' else 'overall'
                normalized_position = position if board_type == 'position' else None
                board_id = self._get_or_create_big_board_id(cursor, board_type=board_type, position=normalized_position)

                cursor.execute('''
                        SELECT p.name
                        FROM big_board_entries e
                        JOIN players p ON p.id = e.player_id
                        WHERE e.board_id = ?
                        ORDER BY e.rank_order ASC, e.id ASC
                ''', (board_id,))

                names = [row[0] for row in cursor.fetchall() if row and row[0]]
                conn.close()

                lines = [f"{index}. {name}" for index, name in enumerate(names, start=1)]
                return '\n'.join(lines)
