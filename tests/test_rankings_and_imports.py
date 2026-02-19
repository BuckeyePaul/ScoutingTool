import os
import sqlite3
import tempfile
import unittest

from database import ScoutDatabase


class RankingsAndImportsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, 'test_scout.db')
        self.db = ScoutDatabase(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def test_import_external_boards_equal_mode_sets_uniform_weights(self):
        boards = [
            {
                'name': 'Board Alpha',
                'text': '1. Player One\n2. Player Two',
                'weight': 3
            },
            {
                'name': 'Board Beta',
                'text': '1. Player Two\n2. Player One',
                'weight': 9
            }
        ]

        result = self.db.import_external_big_boards(boards, weighting_mode='equal')
        self.assertTrue(result['success'])
        self.assertEqual(result['boards_processed'], 2)

        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT board_name, weight
            FROM rank_boards
            WHERE board_name IN ('Board Alpha', 'Board Beta')
            ORDER BY board_name
            """
        )
        rows = cursor.fetchall()
        conn.close()

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0], 'Board Alpha')
        self.assertEqual(rows[1][0], 'Board Beta')
        self.assertAlmostEqual(float(rows[0][1]), 1.0)
        self.assertAlmostEqual(float(rows[1][1]), 1.0)

    def test_import_external_boards_weighted_mode_respects_weights(self):
        boards = [
            {
                'name': 'Board Gamma',
                'text': '1. Player Three\n2. Player Four',
                'weight': 2.5
            },
            {
                'name': 'Board Delta',
                'text': '1. Player Four\n2. Player Three',
                'weight': 0.5
            }
        ]

        result = self.db.import_external_big_boards(boards, weighting_mode='weighted')
        self.assertTrue(result['success'])

        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT board_name, weight
            FROM rank_boards
            WHERE board_name IN ('Board Gamma', 'Board Delta')
            ORDER BY board_name
            """
        )
        rows = cursor.fetchall()
        conn.close()

        self.assertEqual(len(rows), 2)
        weights = {name: float(weight) for name, weight in rows}
        self.assertAlmostEqual(weights['Board Gamma'], 2.5)
        self.assertAlmostEqual(weights['Board Delta'], 0.5)

    def test_primary_board_then_fallback_to_tankathon_rank(self):
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO players (name, tankathon_rank)
            VALUES ('Primary Prospect', NULL), ('Fallback Prospect', 5)
            """
        )
        conn.commit()
        conn.close()

        consensus_import = self.db.import_consensus_board([
            {'rank': 1, 'name': 'Primary Prospect', 'position': 'QB', 'school': 'Test U'}
        ])
        self.assertTrue(consensus_import['success'])

        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("SELECT name, rank FROM players ORDER BY rank ASC")
        ranked_players = cursor.fetchall()
        conn.close()

        self.assertEqual(ranked_players[0][0], 'Primary Prospect')
        self.assertEqual(ranked_players[1][0], 'Fallback Prospect')

    def test_merge_duplicates_is_idempotent(self):
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO players (name, notes, scouted)
            VALUES ('Ruben Bain Jr.', '', 0), ('Ruben Bain', 'Scouted note', 1)
            """
        )
        conn.commit()
        conn.close()

        first_merge = self.db.merge_player_name_duplicates()
        self.assertTrue(first_merge['success'])
        self.assertGreaterEqual(first_merge['players_removed'], 1)

        second_merge = self.db.merge_player_name_duplicates()
        self.assertTrue(second_merge['success'])
        self.assertEqual(second_merge['groups_merged'], 0)
        self.assertEqual(second_merge['players_removed'], 0)

    def test_merge_duplicates_collapses_initial_variants(self):
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO players (name, school)
            VALUES ('L.T. Overton', 'Alabama'), ('LT Overton', '')
            """
        )
        conn.commit()
        conn.close()

        merge_result = self.db.merge_player_name_duplicates()
        self.assertTrue(merge_result['success'])
        self.assertGreaterEqual(merge_result['players_removed'], 1)

        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("SELECT name, school FROM players WHERE LOWER(name) LIKE '%overton%'")
        rows = cursor.fetchall()
        conn.close()

        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0][0] in ('L.T. Overton', 'LT Overton'))
        self.assertEqual(rows[0][1], 'Alabama')

    def test_export_big_board_text_uses_personal_board_order(self):
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO players (name, rank, position) VALUES ('Alpha Prospect', 10, 'QB')")
        alpha_id = cursor.lastrowid
        cursor.execute("INSERT INTO players (name, rank, position) VALUES ('Beta Prospect', 1, 'QB')")
        beta_id = cursor.lastrowid
        conn.commit()
        conn.close()

        self.db.add_player_to_big_board(alpha_id, board_type='overall')
        self.db.add_player_to_big_board(beta_id, board_type='overall')
        self.db.reorder_big_board([alpha_id, beta_id], board_type='overall')

        export_text = self.db.export_big_board_text(scope='overall')
        self.assertEqual(export_text.splitlines(), ['1. Alpha Prospect', '2. Beta Prospect'])

    def test_watch_list_add_reorder_and_remove(self):
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO players (name, position) VALUES ('Watch Prospect A', 'WR')")
        a_id = cursor.lastrowid
        cursor.execute("INSERT INTO players (name, position) VALUES ('Watch Prospect B', 'CB')")
        b_id = cursor.lastrowid
        conn.commit()
        conn.close()

        add_a = self.db.add_player_to_watch_list(a_id)
        add_b = self.db.add_player_to_watch_list(b_id)
        self.assertTrue(add_a['success'])
        self.assertTrue(add_b['success'])

        watch_list = self.db.get_watch_list()
        self.assertEqual([row['id'] for row in watch_list], [a_id, b_id])

        reorder_result = self.db.reorder_watch_list([b_id, a_id])
        self.assertTrue(reorder_result['success'])
        watch_list = self.db.get_watch_list()
        self.assertEqual([row['id'] for row in watch_list], [b_id, a_id])

        remove_result = self.db.remove_player_from_watch_list(b_id)
        self.assertTrue(remove_result['success'])
        watch_list = self.db.get_watch_list()
        self.assertEqual([row['id'] for row in watch_list], [a_id])

    def test_mark_scouted_removes_from_watch_list(self):
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO players (name, position, scouted) VALUES ('Watch Scout Prospect', 'RB', 0)")
        player_id = cursor.lastrowid
        conn.commit()
        conn.close()

        add_result = self.db.add_player_to_watch_list(player_id)
        self.assertTrue(add_result['success'])
        self.assertEqual(len(self.db.get_watch_list()), 1)

        self.db.mark_as_scouted(player_id)

        watch_list = self.db.get_watch_list()
        self.assertEqual(len(watch_list), 0)

        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute('SELECT scouted FROM players WHERE id = ?', (player_id,))
        row = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], 1)

    def test_get_filtered_players_watch_list_only(self):
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO players (name, position, scouted) VALUES ('Watch Filter A', 'QB', 0)")
        watch_id = cursor.lastrowid
        cursor.execute("INSERT INTO players (name, position, scouted) VALUES ('Watch Filter B', 'QB', 0)")
        non_watch_id = cursor.lastrowid
        conn.commit()
        conn.close()

        self.db.add_player_to_watch_list(watch_id)

        all_qbs = self.db.get_filtered_players(positions=['QB'], include_scouted=False)
        watch_only_qbs = self.db.get_filtered_players(positions=['QB'], include_scouted=False, watch_list_only=True)

        all_ids = {player['id'] for player in all_qbs}
        watch_only_ids = {player['id'] for player in watch_only_qbs}

        self.assertIn(watch_id, all_ids)
        self.assertIn(non_watch_id, all_ids)
        self.assertIn(watch_id, watch_only_ids)
        self.assertNotIn(non_watch_id, watch_only_ids)

    def test_remove_imported_rank_board(self):
        boards = [
            {
                'name': 'Temp Imported Board',
                'text': '1. Prospect One\n2. Prospect Two',
                'weight': 1
            }
        ]
        import_result = self.db.import_external_big_boards(boards, weighting_mode='equal')
        self.assertTrue(import_result['success'])

        remove_result = self.db.remove_rank_board('imported_temp_imported_board')
        self.assertTrue(remove_result['success'])

        config = self.db.get_rank_boards_config()
        board_keys = {board['board_key'] for board in config}
        self.assertNotIn('imported_temp_imported_board', board_keys)

        protected_remove = self.db.remove_rank_board('consensus_2026')
        self.assertFalse(protected_remove['success'])


if __name__ == '__main__':
    unittest.main()
