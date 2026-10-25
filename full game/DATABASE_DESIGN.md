# EscapeX Database Design

## Overview
- **Database Type**: SQLite 3
- **Database File**: `escapex.db`
- **ORM**: None (raw SQLite via `sqlite3` module)
- **Connection Management**: Flask `g` object (per-request connection)

---

## Database Schema

### Table: `users`
Stores user account information (mirrored from MongoDB for SQLite operations).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique user identifier |
| `username` | TEXT | UNIQUE, NOT NULL | User's login username |
| `email` | TEXT | NULL | User's email address |
| `password` | TEXT | NOT NULL | User's password (plaintext - should be hashed) |

**Indexes:**
- Primary key on `id`
- Unique index on `username`

**Relationships:**
- One-to-many with `progress` table
- One-to-many with `scores` table

---

### Table: `progress`
Tracks which levels each user has completed for each programming language.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique progress record ID |
| `user_id` | INTEGER | NOT NULL, FOREIGN KEY → users(id) | Reference to user |
| `lang` | TEXT | NOT NULL | Programming language (e.g., "c", "cpp", "java", "php", "python") |
| `level` | INTEGER | NOT NULL | Level number (1-10) |
| `completed_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Timestamp when level was completed |

**Indexes:**
- Primary key on `id`
- **Composite UNIQUE constraint** on `(user_id, lang, level)` - prevents duplicate progress entries

**Relationships:**
- Many-to-one with `users` table

**Example Data:**
```
user_id=1, lang="python", level=5 → User 1 completed Python level 5
user_id=1, lang="python", level=6 → User 1 completed Python level 6
user_id=1, lang="c", level=1 → User 1 completed C level 1
```

---

### Table: `scores`
Stores cumulative scores per user per programming language.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique score record ID |
| `user_id` | INTEGER | NOT NULL, FOREIGN KEY → users(id) | Reference to user |
| `lang` | TEXT | NOT NULL | Programming language (e.g., "c", "cpp", "java", "php", "python") |
| `total_score` | INTEGER | NOT NULL, DEFAULT 0 | Cumulative score for this language |
| `updated_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Last update timestamp |

**Indexes:**
- Primary key on `id`
- **Composite UNIQUE constraint** on `(user_id, lang)` - one score record per user per language

**Relationships:**
- Many-to-one with `users` table

**Score Calculation Logic:**
- Base score: 10 points per level (normal), 30 points per level (boss levels: 5, 10)
- Deductions:
  - Each hint used: -5 points per hint click
  - Showing answer: entire level score becomes 0
- Scores are **additive** - when a game completes, `add_score()` adds the final score to existing `total_score`

**Example Data:**
```
user_id=1, lang="python", total_score=85 → User 1 has 85 points total in Python
user_id=1, lang="c", total_score=120 → User 1 has 120 points total in C
```

---

## Entity Relationship Diagram (ERD)

```
┌─────────────┐
│   users     │
├─────────────┤
│ id (PK)     │◄────┐
│ username    │     │
│ email       │     │
│ password    │     │
└─────────────┘     │
                    │
        ┌───────────┴───────────┐
        │                       │
        │                       │
┌───────▼────────┐    ┌─────────▼────────┐
│   progress     │    │    scores       │
├────────────────┤    ├─────────────────┤
│ id (PK)        │    │ id (PK)         │
│ user_id (FK)   │    │ user_id (FK)    │
│ lang           │    │ lang            │
│ level          │    │ total_score     │
│ completed_at   │    │ updated_at      │
└────────────────┘    └─────────────────┘
```

---

## Key Database Functions

### User Management
- `create_user(username, email, password_hash)` - Insert new user
- `get_user_by_username(username)` - Find user by username
- `get_user_by_id(user_id)` - Find user by ID

### Progress Tracking
- `mark_level_completed(user_id, lang, level)` - Record level completion (INSERT OR IGNORE)
- `get_progress_for_user(user_id)` - Get all completed levels grouped by language
- `get_total_levels_completed(user_id)` - Count total completed levels

### Score Management
- `add_score(user_id, lang, points)` - Add points to user's language score (INSERT with ON CONFLICT UPDATE)
- `get_scores_for_user(user_id)` - Get all language scores for a user
- `get_leaderboard(limit=20)` - Get top users by total score (SUM across all languages)
- `get_total_score_by_username(username)` - Get total score for a specific username

---

## Data Flow

### User Registration/Login
1. User signs up/logs in via MongoDB (`users` collection)
2. Flask mirrors user to SQLite `users` table if not exists
3. Session stores `user_id` and `username` from SQLite

### Game Completion Flow
1. User completes quiz game (e.g., Python quiz)
2. JavaScript calculates final score (with hint/answer penalties)
3. Frontend calls `/api/submit-score` POST endpoint
4. Backend calls `add_score(session["user_id"], lang, score)`
5. SQLite updates `scores` table (INSERT or UPDATE existing row)

### Leaderboard Display
1. User visits `/ai-leaderboard`
2. Backend calls `get_leaderboard(limit=20)`
3. SQL query: `SELECT u.username, SUM(s.total_score) AS score FROM users u JOIN scores s ON u.id = s.user_id GROUP BY u.id ORDER BY score DESC LIMIT 20`
4. Template renders sorted leaderboard

---

## Constraints & Business Rules

1. **One score per user per language**: `UNIQUE(user_id, lang)` in `scores` table
2. **One progress entry per user per language per level**: `UNIQUE(user_id, lang, level)` in `progress` table
3. **Foreign key integrity**: `user_id` must exist in `users` table
4. **Score accumulation**: Scores are added, not replaced (ON CONFLICT UPDATE adds to existing)
5. **Leaderboard sorting**: Highest total score first (SUM across all languages)

---

## Database File Location
- **Path**: `escapex.db` (in project root: `P:\full game\escapex.db`)
- **Created**: Automatically on first `init_db(app)` call
- **Backup**: Consider backing up this file regularly

---

## Notes
- **Dual Database System**: MongoDB handles authentication, SQLite handles game data (scores/progress)
- **Session Management**: Flask sessions store `user_id` and `username` for SQLite operations
- **Password Storage**: Currently plaintext (should be hashed with bcrypt/argon2)
- **Language Codes**: Use lowercase strings: "c", "cpp", "java", "php", "python"

