import time
import logging
from dataclasses import dataclass
from typing import List, Optional, Any, Dict
import math

from library_app.database.db import DatabaseManager
from library_app.database.repository import LibraryRepository
from library_app.database.migrations import migrate_from_json
from library_app.permissions import PermissionManager, Permission

logger = logging.getLogger(__name__)

@dataclass
class Book:
    id: int
    book_code: str
    title: str
    status: str
    author: str = "Unknown"
    category: Optional[str] = None
    isbn: Optional[str] = None
    publisher: Optional[str] = None
    publication_year: Optional[int] = None
    description: Optional[str] = None
    issued_to_user_id: Optional[str] = None
    issue_timestamp: Optional[float] = None
    return_timestamp: Optional[float] = None

class LibraryModel:
    """
    Controller / Model proxy for the scalable UI. It handles filtering, searching,
    pagination, and UI state tracking on top of the generic SQLite repository.
    """
    def __init__(self, current_user_id: str = None):
        self.current_user_id = None
        self.role = None
        
        self.db = DatabaseManager()
        self.db.init_db()
        self.repo = LibraryRepository(self.db)
        
        # Ensure migration runs once
        migrate_from_json(self.db, "library_session.json")
        
        self.set_user(current_user_id)
        
        # UI State
        self.books: List[Book] = []
        self.current_index = 0 # Index within the CURRENT page
        
        # Pagination & Filters
        self.page = 1
        self.page_size = 8
        self.total_pages = 1
        self.total_filtered = 0
        self.search_query = ""
        self.status_filter = "All"
        self.category_filter = "All"
        
        self.reload_books()

    def _dict_to_book(self, b: Dict[str, Any]) -> Book:
        return Book(
            id=b['id'],
            book_code=b['book_code'],
            title=b['title'],
            status=b['status'],
            author=b.get('author', 'Unknown'),
            category=b.get('category'),
            isbn=b.get('isbn'),
            publisher=b.get('publisher'),
            publication_year=b.get('publication_year'),
            description=b.get('description'),
            issued_to_user_id=b.get('issued_to_user_id'),
            issue_timestamp=b.get('issue_timestamp'),
            return_timestamp=b.get('return_timestamp')
        )
        
    def set_user(self, user_id: str):
        if self.current_user_id != user_id:
            self.current_user_id = user_id
            if user_id:
                u = self.repo.get_user_by_username(user_id)
                self.role = u['role'] if u else "STAFF" # Safe default
            else:
                self.role = None
        
    def reload_books(self):
        """Fetches books matching current filters and search query, then paginates them."""
        # Due to constraints, we fetch filtered then paginate in memory/model to keep it simple,
        # but realistically for "unlimited practical inventory" the search and pagination 
        # should happen directly in SQL using LIMIT and OFFSET. We'll do it elegantly here:
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM books WHERE 1=1"
            params = []
            
            if self.search_query:
                query += " AND (title LIKE ? OR author LIKE ? OR book_code LIKE ? OR isbn LIKE ?)"
                pattern = f"%{self.search_query}%"
                params.extend([pattern, pattern, pattern, pattern])
                
            if self.status_filter != "All":
                query += " AND status = ?"
                params.append(self.status_filter)
                
            # First get total count
            count_query = query.replace("SELECT *", "SELECT COUNT(*)")
            cursor.execute(count_query, params)
            self.total_filtered = cursor.fetchone()[0]
            
            self.total_pages = max(1, math.ceil(self.total_filtered / self.page_size))
            if self.page > self.total_pages:
                self.page = self.total_pages
                
            # Now fetch page items
            query += " ORDER BY title ASC LIMIT ? OFFSET ?"
            params.extend([self.page_size, (self.page - 1) * self.page_size])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            self.books = [self._dict_to_book(dict(r)) for r in rows]
            
            # Bound current_index
            if self.books:
                if self.current_index >= len(self.books):
                    self.current_index = len(self.books) - 1
            else:
                self.current_index = 0

    def get_summary_stats(self) -> Dict[str, int]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM books")
            total = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM books WHERE status = 'Available'")
            available = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM books WHERE status = 'Issued'")
            issued = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM transactions")
            transactions = cursor.fetchone()[0]
            
            return {
                "total": total,
                "available": available,
                "issued": issued,
                "transactions": transactions
            }

    def get_current_book(self) -> Optional[Book]:
        if not self.books:
            return None
        return self.books[self.current_index]
        
    def next_book(self):
        if not self.books: return
        self.current_index += 1
        if self.current_index >= len(self.books):
            # Try to paginate forward
            if self.page < self.total_pages:
                self.page += 1
                self.current_index = 0
                self.reload_books()
            else:
                self.current_index = len(self.books) - 1
        
    def prev_book(self):
        if not self.books: return
        self.current_index -= 1
        if self.current_index < 0:
            if self.page > 1:
                self.page -= 1
                self.reload_books()
                self.current_index = len(self.books) - 1
            else:
                self.current_index = 0
            
    def issue_current_book(self) -> bool:
        PermissionManager.require_permission(self.role, Permission.BOOK_ISSUE)
        
        book = self.get_current_book()
        if book and book.status == "Available":
            try:
                # Issue to an anonymous student by default when using AI gestures, tracking Operator precisely
                self.repo.issue_book(book.id, user_id="Library_Borrower", staff_user_id=self.current_user_id)
                self.reload_books() 
                return True
            except Exception as e:
                logger.error(f"Failed to issue book: {e}")
        return False
        
    def return_current_book(self) -> bool:
        PermissionManager.require_permission(self.role, Permission.BOOK_RETURN)
        
        book = self.get_current_book()
        if book and book.status == "Issued":
            try:
                # Any Staff can return any book. No longer blocking cross-staff returns.
                self.repo.return_book(book.id, user_id="Library_Borrower", staff_user_id=self.current_user_id)
                self.reload_books()
                return True
            except Exception as e:
                logger.error(f"Failed to return book: {e}")
                raise
        return False

# Retaining stub to avoid import breaking elsewhere
class StorageManager:
    def __init__(self, filepath=""): pass
    def save(self, model: LibraryModel): pass

class NotesModel:
    def __init__(self, db_manager):
        from library_app.database.notes_repository import NotesRepository
        self.repo = NotesRepository(db_manager)
        self.notes = []
        self.current_user_id = None
        self.current_index = 0
        
    def reload_notes(self):
        if not self.current_user_id:
            self.notes = []
            return
        self.notes = self.repo.search_notes(self.current_user_id)
        if self.current_index >= len(self.notes):
            self.current_index = max(0, len(self.notes) - 1)
            
    def get_current_note(self):
        if 0 <= self.current_index < len(self.notes):
            return self.notes[self.current_index]
        return None
        
    def next_note(self):
        if self.notes and self.current_index < len(self.notes) - 1:
            self.current_index += 1
            
    def prev_note(self):
        if self.notes and self.current_index > 0:
            self.current_index -= 1
