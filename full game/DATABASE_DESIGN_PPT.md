# EscapeX Database Design - Presentation

---

## Slide 1: Overview
**EscapeX Database Architecture**

- **Database Type**: SQLite 3
- **Purpose**: Track user progress & scores
- **File**: `escapex.db`
- **Integration**: Works alongside MongoDB for authentication

---

## Slide 2: Database Structure
**3 Core Tables**

```
┌──────────┐      ┌──────────┐      ┌──────────┐
│  users   │      │ progress │      │  scores  │
├──────────┤      ├──────────┤      ├──────────┤
│ id       │◄─────│ user_id  │      │ user_id  │
│ username │      │ lang     │      │ lang     │
│ email    │      │ level    │      │ score    │
│ password │      └──────────┘      └──────────┘
└──────────┘
```

---

## Slide 3: Users Table
**User Account Storage**

| Field | Type | Purpose |
|-------|------|---------|
| `id` | INTEGER | Primary Key |
| `username` | TEXT | Unique login name |
| `email` | TEXT | User email |
| `password` | TEXT | Login password |

**Key**: Mirrored from MongoDB for SQLite operations

---

## Slide 4: Progress Table
**Level Completion Tracking**

| Field | Purpose |
|-------|---------|
| `user_id` | Which user |
| `lang` | Language (c, cpp, java, php, python) |
| `level` | Level number (1-10) |
| `completed_at` | Timestamp |

**Unique Constraint**: One entry per user/language/level

---

## Slide 5: Scores Table
**Cumulative Score Storage**

| Field | Purpose |
|-------|---------|
| `user_id` | Which user |
| `lang` | Programming language |
| `total_score` | Cumulative points |
| `updated_at` | Last update time |

**Unique Constraint**: One score per user per language

---

## Slide 6: Score Calculation
**How Scores Work**

- **Base Points**: 10 per level (normal), 30 per level (boss)
- **Penalties**:
  - Hint used: -5 points per click
  - Show answer: Level score = 0
- **Accumulation**: Scores add up across games

---

## Slide 7: Key Functions
**Database Operations**

**User Management**
- `create_user()` - Add new user
- `get_user_by_username()` - Find user

**Progress**
- `mark_level_completed()` - Record completion
- `get_progress_for_user()` - Get all progress

**Scores**
- `add_score()` - Add points
- `get_leaderboard()` - Top players

---

## Slide 8: Data Flow
**Game Completion → Leaderboard**

```
1. User completes quiz
   ↓
2. Score calculated (with penalties)
   ↓
3. POST /api/submit-score
   ↓
4. add_score() updates database
   ↓
5. Leaderboard shows updated rankings
```

---

## Slide 9: Leaderboard Query
**Top Players Display**

```sql
SELECT u.username, SUM(s.total_score) AS score
FROM users u
JOIN scores s ON u.id = s.user_id
GROUP BY u.id
ORDER BY score DESC
LIMIT 20
```

**Result**: Top 20 players sorted by highest total score

---

## Slide 10: Summary
**Key Points**

✅ **3 Tables**: users, progress, scores  
✅ **Foreign Keys**: Data integrity  
✅ **Unique Constraints**: Prevent duplicates  
✅ **Score Accumulation**: Additive scoring system  
✅ **Leaderboard**: Real-time rankings  

**Database File**: `escapex.db` (SQLite)

---

## End

