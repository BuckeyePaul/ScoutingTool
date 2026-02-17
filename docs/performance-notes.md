# Performance and Query Notes

## Added SQLite Indexes

The app now creates these additional indexes during database initialization:

- `idx_players_rank` on `players(rank)`
- `idx_players_scouted_rank` on `players(scouted, rank)`
- `idx_players_school` on `players(school)`
- `idx_player_board_ranks_board_rank` on `player_board_ranks(board_id, board_rank)`
- `idx_big_board_entries_board_rank` on `big_board_entries(board_id, rank_order)`

## Query Paths and Expected Behavior

### Player Search and Lists
- Endpoints that call `get_filtered_players` and `get_all_players` primarily order by `rank` and often filter on `scouted` and `school`.
- `idx_players_rank` and `idx_players_scouted_rank` reduce sort/filter cost for these common cases.

### Big Board Rendering
- `get_big_board` and board reorder flows operate by `board_id` and `rank_order`.
- `idx_big_board_entries_board_rank` improves ordered board retrieval and rank-compression operations.

### Rank Board and Consensus Views
- Consensus and board-rank displays query `player_board_ranks` by `board_id`, often with rank ordering.
- `idx_player_board_ranks_board_rank` improves this path and keeps board-rank lookups predictable as imported board count grows.

## Notes on LIKE Filters
- Position and name filters currently use wildcard `LIKE` patterns that may include leading `%`.
- Leading-wildcard patterns generally do not use standard B-tree indexes in SQLite.
- This is acceptable at current project scale; if dataset size grows substantially, consider FTS (SQLite FTS5) for name/school text search.

## Operational Guidance
- Index creation uses `CREATE INDEX IF NOT EXISTS`, so existing databases can adopt these changes safely.
- Re-running app startup is sufficient to create missing indexes.
- Keep import/recalc operations batched in single transactions for best write performance and consistency.
