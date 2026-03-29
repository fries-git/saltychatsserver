import threading
import time
import uuid
from typing import Dict, List, Optional, Tuple

from .database import init_db, execute, fetchone, fetchall, _json_dumps, _json_loads

_lock = threading.RLock()


def init_polls_db():
    init_db()
    conn = execute("""
        CREATE TABLE IF NOT EXISTS polls (
            id TEXT PRIMARY KEY,
            message_id TEXT NOT NULL,
            channel TEXT,
            thread_id TEXT,
            question TEXT NOT NULL,
            options TEXT NOT NULL,
            allow_multiselect INTEGER DEFAULT 0,
            expires_at REAL,
            created_by TEXT NOT NULL,
            created_at REAL NOT NULL,
            ended INTEGER DEFAULT 0,
            ended_at REAL,
            UNIQUE(message_id)
        )
    """)
    execute("""
        CREATE TABLE IF NOT EXISTS poll_votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            poll_id TEXT NOT NULL,
            option_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            voted_at REAL NOT NULL,
            UNIQUE(poll_id, option_id, user_id),
            FOREIGN KEY (poll_id) REFERENCES polls(id) ON DELETE CASCADE
        )
    """)
    execute("CREATE INDEX IF NOT EXISTS idx_polls_message ON polls(message_id)")
    execute("CREATE INDEX IF NOT EXISTS idx_poll_votes_poll ON poll_votes(poll_id)")


def create_poll(message_id: str, question: str, options: List[dict], 
                channel: str = None, thread_id: str = None,
                allow_multiselect: bool = False, expires_at: float = None,
                created_by: str = None) -> str:
    init_polls_db()
    
    poll_id = str(uuid.uuid4())
    now = time.time()
    
    for i, opt in enumerate(options):
        if "id" not in opt:
            opt["id"] = str(i)
    
    with _lock:
        execute(
            """INSERT INTO polls (id, message_id, channel, thread_id, question, options, 
               allow_multiselect, expires_at, created_by, created_at, ended, ended_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, NULL)""",
            (poll_id, message_id, channel, thread_id, question, _json_dumps(options),
             1 if allow_multiselect else 0, expires_at, created_by, now)
        )
    
    return poll_id


def get_poll(poll_id: str) -> Optional[dict]:
    init_polls_db()
    
    row = fetchone("SELECT * FROM polls WHERE id = ?", (poll_id,))
    if not row:
        return None
    
    return {
        "id": row["id"],
        "message_id": row["message_id"],
        "channel": row["channel"],
        "thread_id": row["thread_id"],
        "question": row["question"],
        "options": _json_loads(row["options"]) or [],
        "allow_multiselect": bool(row["allow_multiselect"]),
        "expires_at": row["expires_at"],
        "created_by": row["created_by"],
        "created_at": row["created_at"],
        "ended": bool(row["ended"]),
        "ended_at": row["ended_at"]
    }


def get_poll_by_message(message_id: str) -> Optional[dict]:
    init_polls_db()
    
    row = fetchone("SELECT * FROM polls WHERE message_id = ?", (message_id,))
    if not row:
        return None
    
    return {
        "id": row["id"],
        "message_id": row["message_id"],
        "channel": row["channel"],
        "thread_id": row["thread_id"],
        "question": row["question"],
        "options": _json_loads(row["options"]) or [],
        "allow_multiselect": bool(row["allow_multiselect"]),
        "expires_at": row["expires_at"],
        "created_by": row["created_by"],
        "created_at": row["created_at"],
        "ended": bool(row["ended"]),
        "ended_at": row["ended_at"]
    }


def vote_poll(poll_id: str, option_id: str, user_id: str) -> Tuple[bool, Optional[str]]:
    init_polls_db()
    
    poll = get_poll(poll_id)
    if not poll:
        return False, "Poll not found"
    
    if poll["ended"]:
        return False, "Poll has ended"
    
    if poll["expires_at"] and time.time() > poll["expires_at"]:
        return False, "Poll has expired"
    
    valid_option = False
    for opt in poll["options"]:
        if opt.get("id") == option_id:
            valid_option = True
            break
    
    if not valid_option:
        return False, f"Invalid option: {option_id}"
    
    with _lock:
        if not poll["allow_multiselect"]:
            existing_votes = fetchall(
                "SELECT option_id FROM poll_votes WHERE poll_id = ? AND user_id = ?",
                (poll_id, user_id)
            )
            for vote in existing_votes:
                if vote["option_id"] != option_id:
                    execute(
                        "DELETE FROM poll_votes WHERE poll_id = ? AND user_id = ? AND option_id = ?",
                        (poll_id, user_id, vote["option_id"])
                    )
        
        try:
            execute(
                "INSERT INTO poll_votes (poll_id, option_id, user_id, voted_at) VALUES (?, ?, ?, ?)",
                (poll_id, option_id, user_id, time.time())
            )
        except Exception:
            pass
    
    return True, None


def remove_vote(poll_id: str, option_id: str, user_id: str) -> bool:
    init_polls_db()
    
    poll = get_poll(poll_id)
    if not poll:
        return False
    
    if poll["ended"]:
        return False
    
    with _lock:
        result = execute(
            "DELETE FROM poll_votes WHERE poll_id = ? AND option_id = ? AND user_id = ?",
            (poll_id, option_id, user_id)
        )
        return result.rowcount > 0


def get_poll_results(poll_id: str) -> Optional[dict]:
    init_polls_db()
    
    poll = get_poll(poll_id)
    if not poll:
        return None
    
    votes = fetchall("SELECT option_id, user_id FROM poll_votes WHERE poll_id = ?", (poll_id,))
    
    results = {}
    for opt in poll["options"]:
        results[opt.get("id")] = {
            "id": opt.get("id"),
            "text": opt.get("text"),
            "emoji": opt.get("emoji"),
            "votes": 0,
            "voters": []
        }
    
    for vote in votes:
        option_id = vote["option_id"]
        if option_id in results:
            results[option_id]["votes"] += 1
            results[option_id]["voters"].append(vote["user_id"])
    
    total_votes = len(votes)
    
    return {
        "poll_id": poll_id,
        "question": poll["question"],
        "allow_multiselect": poll["allow_multiselect"],
        "ended": poll["ended"],
        "ended_at": poll["ended_at"],
        "total_votes": total_votes,
        "results": list(results.values())
    }


def end_poll(poll_id: str) -> bool:
    init_polls_db()
    
    poll = get_poll(poll_id)
    if not poll:
        return False
    
    if poll["ended"]:
        return False
    
    now = time.time()
    
    with _lock:
        execute(
            "UPDATE polls SET ended = 1, ended_at = ? WHERE id = ?",
            (now, poll_id)
        )
    
    return True


def delete_poll(poll_id: str) -> bool:
    init_polls_db()
    
    with _lock:
        execute("DELETE FROM poll_votes WHERE poll_id = ?", (poll_id,))
        result = execute("DELETE FROM polls WHERE id = ?", (poll_id,))
        return result.rowcount > 0


def get_user_vote(poll_id: str, user_id: str) -> List[str]:
    init_polls_db()
    
    votes = fetchall(
        "SELECT option_id FROM poll_votes WHERE poll_id = ? AND user_id = ?",
        (poll_id, user_id)
    )
    return [v["option_id"] for v in votes]


def is_poll_expired(poll_id: str) -> bool:
    poll = get_poll(poll_id)
    if not poll:
        return True
    
    if poll["ended"]:
        return True
    
    if poll["expires_at"] and time.time() > poll["expires_at"]:
        return True
    
    return False


def cleanup_expired_polls() -> int:
    init_polls_db()
    
    now = time.time()
    expired = fetchall(
        "SELECT id FROM polls WHERE expires_at IS NOT NULL AND expires_at < ? AND ended = 0",
        (now,)
    )
    
    count = 0
    for poll in expired:
        if end_poll(poll["id"]):
            count += 1
    
    return count
