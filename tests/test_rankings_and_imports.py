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


if __name__ == '__main__':
    unittest.main()
