import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
logger = logging.getLogger(__name__)
DB_PATH = Path(__file__).parent.parent.parent / "data" / "research_history.db"
class ResearchMemory:
    def __init__(self):
        self._init_db()
    def _init_db(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                final_report TEXT,
                quality_score INTEGER,
                iterations INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sub_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                question TEXT,
                search_query TEXT,
                summary TEXT,
                FOREIGN KEY (session_id) REFERENCES research_sessions(id)
            )
        """)
        conn.commit()
        conn.close()
        logger.info(f"Research memory initialized at {DB_PATH}")
    def save_session(self, topic: str, report: str, score: int, iterations: int,
                     sub_questions: List[Dict]) -> int:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO research_sessions (topic, final_report, quality_score, iterations) VALUES (?, ?, ?, ?)",
            (topic, report, score, iterations)
        )
        session_id = cursor.lastrowid
        for sq in sub_questions:
            cursor.execute(
                "INSERT INTO sub_questions (session_id, question, search_query, summary) VALUES (?, ?, ?, ?)",
                (session_id, sq.get("question", ""), sq.get("search_query", ""), sq.get("summary", ""))
            )
        conn.commit()
        conn.close()
        logger.info(f"Saved research session {session_id}: {topic[:50]}")
        return session_id
    def find_related_research(self, topic: str, limit: int = 3) -> List[Dict]:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        keywords = [w.lower() for w in topic.split() if len(w) > 3]
        if not keywords:
            conn.close()
            return []
        conditions = " OR ".join(["LOWER(topic) LIKE ?" for _ in keywords])
        params = [f"%{kw}%" for kw in keywords]
        rows = conn.execute(
            f"SELECT * FROM research_sessions WHERE {conditions} ORDER BY created_at DESC LIMIT ?",
            params + [limit]
        ).fetchall()
        conn.close()
        return [dict(row) for row in rows]
    def get_session(self, session_id: int) -> Optional[Dict]:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM research_sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if row:
            session = dict(row)
            sqs = conn.execute(
                "SELECT * FROM sub_questions WHERE session_id = ?", (session_id,)
            ).fetchall()
            session["sub_questions"] = [dict(sq) for sq in sqs]
            conn.close()
            return session
        conn.close()
        return None
    def get_recent_sessions(self, limit: int = 10) -> List[Dict]:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, topic, quality_score, iterations, created_at FROM research_sessions ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
        conn.close()
        return [dict(row) for row in rows]
if __name__ == "__main__":
    memory = ResearchMemory()
    session_id = memory.save_session(
        topic="Impact of AI on healthcare",
        report="# Research Report\n\nAI is transforming healthcare...",
        score=8,
        iterations=2,
        sub_questions=[
            {"question": "How is AI used in diagnostics?", "search_query": "AI diagnostics healthcare 2025"},
            {"question": "What are the risks?", "search_query": "AI healthcare risks concerns"}
        ]
    )
    print(f"Saved session {session_id}")
    related = memory.find_related_research("AI in medical diagnostics")
    print(f"Found {len(related)} related sessions")
    for r in related:
        print(f"  - {r['topic']} (score: {r['quality_score']})")
