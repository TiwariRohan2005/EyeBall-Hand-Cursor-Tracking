import time
import logging
from .db import DatabaseManager

logger = logging.getLogger(__name__)

class NotesRepository:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def add_note(self, note_data: dict) -> int:
        now = time.time()
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                '''
                INSERT INTO notes (title, content, category, created_by_user_id, created_at, updated_at, is_bookmarked)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    note_data.get('title'),
                    note_data.get('content'),
                    note_data.get('category'),
                    note_data.get('created_by_user_id'),
                    now, now,
                    note_data.get('is_bookmarked', 0)
                )
            )
            return cursor.lastrowid

    def update_note(self, note_id: int, note_data: dict) -> bool:
        now = time.time()
        fields = []
        values = []
        for key in ['title', 'content', 'category', 'is_bookmarked']:
            if key in note_data:
                fields.append(f"{key} = ?")
                values.append(note_data[key])
                
        if not fields:
            return False
            
        fields.append("updated_at = ?")
        values.append(now)
        values.append(note_id)
        
        query = f"UPDATE notes SET {', '.join(fields)} WHERE id = ?"
        with self.db.get_connection() as conn:
            cursor = conn.execute(query, tuple(values))
            return cursor.rowcount > 0

    def delete_note(self, note_id: int, user_id: str) -> bool:
        with self.db.get_connection() as conn:
            # Enforce user_id matching to prevent cross-deletion unless owner logic wraps it
            cursor = conn.execute("DELETE FROM notes WHERE id = ? AND created_by_user_id = ?", (note_id, user_id))
            return cursor.rowcount > 0

    def get_note(self, note_id: int) -> dict:
        with self.db.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def search_notes(self, user_id: str, query: str = "") -> list:
        with self.db.get_connection() as conn:
            if not query:
                cursor = conn.execute("SELECT * FROM notes WHERE created_by_user_id = ? ORDER BY updated_at DESC", (user_id,))
            else:
                q = f"%{query}%"
                cursor = conn.execute(
                    "SELECT * FROM notes WHERE created_by_user_id = ? AND (title LIKE ? OR content LIKE ? OR category LIKE ?) ORDER BY updated_at DESC",
                    (user_id, q, q, q)
                )
            return [dict(r) for r in cursor.fetchall()]
