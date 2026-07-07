# Kanban Database Schema (SQLite)

## Overview

Per project requirements, persistence is handled by a local SQLite database. The schema mirrors the current in-memory structures while preparing for multi-user support. All tables use simple integer primary keys with `AUTOINCREMENT`. Foreign keys enforce referential integrity.

Database file path: `backend/data/kanban.db` (created automatically if missing).

## Entity Relationship Diagram

```mermaid
erDiagram
    users ||--o{ boards : "owns"
    boards ||--o{ columns : "has"
    columns ||--o{ cards : "contains"
    users ||--o{ sessions : "auth"

    users {
      INTEGER id PK
      TEXT username UNIQUE
      TEXT password_hash
      TEXT created_at
      TEXT updated_at
    }

    boards {
      INTEGER id PK
      INTEGER user_id FK
      TEXT title
      INTEGER sort_order
      TEXT created_at
      TEXT updated_at
    }

    columns {
      INTEGER id PK
      INTEGER board_id FK
      TEXT title
      INTEGER position
      TEXT created_at
      TEXT updated_at
    }

    cards {
      INTEGER id PK
      INTEGER column_id FK
      TEXT title
      TEXT details
      INTEGER position
      TEXT created_at
      TEXT updated_at
    }

    sessions {
      TEXT token PK
      INTEGER user_id FK
      TEXT created_at
      TEXT expires_at
    }
```

## Table Definitions

### `users`
| Column        | Type   | Constraints                                  |
|---------------|--------|-----------------------------------------------|
| `id`          | INTEGER| PRIMARY KEY AUTOINCREMENT                     |
| `username`    | TEXT   | UNIQUE NOT NULL                               |
| `password_hash`| TEXT  | NOT NULL                                      |
| `created_at`  | TEXT   | ISO timestamp, default `CURRENT_TIMESTAMP`    |
| `updated_at`  | TEXT   | ISO timestamp                                 |

### `boards`
| Column        | Type    | Constraints                                  |
|---------------|---------|-----------------------------------------------|
| `id`          | INTEGER | PRIMARY KEY AUTOINCREMENT                     |
| `user_id`     | INTEGER | NOT NULL REFERENCES `users`(`id`) ON DELETE CASCADE |
| `title`       | TEXT    | NOT NULL                                      |
| `sort_order`  | INTEGER | Default 0 (future multi-board ordering)      |
| `created_at`  | TEXT    | ISO timestamp                                 |
| `updated_at`  | TEXT    | ISO timestamp                                 |

### `columns`
| Column     | Type    | Constraints                                     |
|------------|---------|--------------------------------------------------|
| `id`       | INTEGER | PRIMARY KEY AUTOINCREMENT                        |
| `board_id` | INTEGER | NOT NULL REFERENCES `boards`(`id`) ON DELETE CASCADE |
| `title`    | TEXT    | NOT NULL                                         |
| `position` | INTEGER | NOT NULL (0-based ordering)                      |
| `created_at` | TEXT  |                                                  |
| `updated_at` | TEXT  |                                                  |

### `cards`
| Column     | Type    | Constraints                                      |
|------------|---------|---------------------------------------------------|
| `id`       | INTEGER | PRIMARY KEY AUTOINCREMENT                         |
| `column_id`| INTEGER | NOT NULL REFERENCES `columns`(`id`) ON DELETE CASCADE |
| `title`    | TEXT    | NOT NULL                                          |
| `details`  | TEXT    | NOT NULL DEFAULT ''                               |
| `position` | INTEGER | NOT NULL (ordering within column)                 |
| `created_at` | TEXT  |                                                   |
| `updated_at` | TEXT  |                                                   |

### `sessions`
| Column       | Type  | Constraints                                      |
|--------------|-------|---------------------------------------------------|
| `token`      | TEXT  | PRIMARY KEY                                      |
| `user_id`    | INTEGER | NOT NULL REFERENCES `users`(`id`) ON DELETE CASCADE |
| `created_at` | TEXT  | NOT NULL (timestamp when session issued)         |
| `expires_at` | TEXT  | NULLABLE (optional expiration)                    |

## Example Seed Data (SQL)

```sql
INSERT INTO users(username, password_hash) VALUES
  -- sha256("password") -> 5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8
  ('user', '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8');

INSERT INTO boards(user_id, title) VALUES (1, 'Kanban Studio');

INSERT INTO columns(board_id, title, position) VALUES
  (1, 'Backlog', 0),
  (1, 'Discovery', 1),
  (1, 'In Progress', 2),
  (1, 'Review', 3),
  (1, 'Done', 4);

INSERT INTO cards(column_id, title, details, position) VALUES
  (1, 'Align roadmap themes', '...', 0),
  (1, 'Gather customer signals', '...', 1),
  (2, 'Prototype analytics view', '...', 0);
```

## Planned API Usage (for Part 6+)
- `POST /api/login` / `POST /api/logout` use `users` + `sessions` tables.
- `GET /api/boards/me` joins `boards`,`columns`,`cards` to hydrate UI.
- `PUT /api/boards/{boardId}` updates titles/ordering (writes to respective tables).
- Later AI endpoints will snapshot board JSON by querying the same tables.

## Testing Strategy
- Migrate tests to run inside Docker container (using `docker compose run --rm app uv run pytest`).
- Unit tests for low-level DB helpers (`backend/database.py`).
- Integration tests hitting FastAPI routes once Part 6 is implemented.

## Pending Sign-off
This schema replaces the prior JSON approach. Awaiting user approval (per Plan Part 5) before implementing backend routes or migrations.

### Auth alignment (Part 4 vs Part 6)

- Part 4 remains a purely frontend guard (local `useState`) to keep the MVP flow simple until backend auth lands.
- Part 6 will introduce real authentication via the `users` + `sessions` tables (`POST /api/login` issuing bearer tokens stored server-side).
- During the transition, the frontend will first integrate with backend auth; once that happens, the temporary frontend-only gate will be replaced by API-backed login/logout, ensuring there is a single source of truth.