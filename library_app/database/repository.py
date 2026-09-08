import time
import logging
from typing import List, Dict, Optional, Any
from .db import DatabaseManager

logger = logging.getLogger(__name__)

class LibraryRepository:
    """Handles all CRUD operations for the Library Management System SQLite database."""
    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_role_counts(self) -> Dict[str, int]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT role, COUNT(id) FROM users WHERE active = 1 GROUP BY role")
            counts = {'OWNER': 0, 'STAFF': 0}
            for row in cursor.fetchall():
                if row[0] in counts:
                    counts[row[0]] = row[1]
            return counts
            
    def deactivate_user(self, username: str):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET active = 0 WHERE username = ?", (username,))
            
    def activate_user(self, username: str):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET active = 1 WHERE username = ?", (username,))

    def add_user(self, username: str, role: str = "STAFF", display_name: str = None) -> int:
        role = role.upper()
        # Enforce hard capacity boundaries inside Repo
        counts = self.get_role_counts()
        
        if role == "OWNER" and counts["OWNER"] >= 1:
            raise PermissionError("Owner account already exists. Only one Owner is permitted.")
            
        if role == "STAFF" and counts["STAFF"] >= 10:
            raise PermissionError("Staff limit reached. A maximum of 10 Staff members is allowed.")
            
        # Dynamically allocate Unique Identity Name if just generic STAFF
        if not display_name:
            if role == "STAFF":
                display_name = f"STAFF{counts['STAFF'] + 1:03d}"
            else:
                display_name = "OWNER"

        query = '''
            INSERT INTO users (username, display_name, role, active, created_at, updated_at)
            VALUES (?, ?, ?, 1, ?, ?)
        '''
        now = time.time()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (username, display_name, role, now, now))
            logger.info(f"Successfully minted role {role} for internal user: {username}")
            return cursor.lastrowid
            
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
            
    def list_users(self) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            return [dict(r) for r in cursor.fetchall()]

    def add_book(self, book_data: Dict[str, Any]) -> int:
        query = '''
            INSERT INTO books (
                book_code, isbn, title, author, category, publisher, 
                publication_year, description, status, 
                issued_to_user_id, issued_by_user_id, issue_timestamp, return_timestamp,
                created_at, updated_at
            ) VALUES (
                :book_code, :isbn, :title, :author, :category, :publisher,
                :publication_year, :description, :status, 
                :issued_to_user_id, :issued_by_user_id, :issue_timestamp, :return_timestamp,
                :created_at, :updated_at
            )
        '''
        now = time.time()
        
        # Ensure book code is unique, empty string becomes None to not violate constraints if generating? 
        # But we made it NOT NULL, so it has to exist.
        if 'book_code' not in book_data or not book_data['book_code']:
            raise ValueError("book_code is required")
            
        if not book_data.get('title'):
            raise ValueError("title is required")
            
        data = {
            'book_code': book_data['book_code'],
            'isbn': book_data.get('isbn'),
            'title': book_data['title'],
            'author': book_data.get('author', 'Unknown'),
            'category': book_data.get('category'),
            'publisher': book_data.get('publisher'),
            'publication_year': book_data.get('publication_year'),
            'description': book_data.get('description'),
            'status': book_data.get('status', 'Available'),
            'issued_to_user_id': book_data.get('issued_to_user_id'),
            'issued_by_user_id': book_data.get('issued_by_user_id'),
            'issue_timestamp': book_data.get('issue_timestamp'),
            'return_timestamp': book_data.get('return_timestamp'),
            'created_at': book_data.get('created_at', now),
            'updated_at': now
        }
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, data)
                logger.info(f"Book added: {data['title']} ({data['book_code']})")
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to add book: {e}")
            raise
            
    def get_book(self, book_id: int) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
            
    def get_book_by_code(self, book_code: str) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM books WHERE book_code = ?", (book_code,))
            row = cursor.fetchone()
            return dict(row) if row else None
            
    def list_books(self) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM books ORDER BY id ASC")
            return [dict(r) for r in cursor.fetchall()]

    def search_books(self, query: str) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            search_pattern = f"%{query}%"
            cursor.execute(
                "SELECT * FROM books WHERE title LIKE ? OR author LIKE ? ORDER BY id ASC", 
                (search_pattern, search_pattern)
            )
            return [dict(r) for r in cursor.fetchall()]

    def filter_books_by_status(self, status: str) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM books WHERE status = ? ORDER BY id ASC", (status,))
            return [dict(r) for r in cursor.fetchall()]
            
    def filter_books_by_category(self, category: str) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM books WHERE category = ? ORDER BY id ASC", (category,))
            return [dict(r) for r in cursor.fetchall()]

    def update_book(self, book_id: int, update_data: Dict[str, Any]) -> bool:
        if not update_data:
            return False
            
        update_data['updated_at'] = time.time()
        fields = []
        values = []
        for k, v in update_data.items():
            fields.append(f"{k} = ?")
            values.append(v)
        values.append(book_id)
        
        query = f"UPDATE books SET {', '.join(fields)} WHERE id = ?"
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, values)
                if cursor.rowcount > 0:
                    logger.info(f"Book update successful for id: {book_id}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to update book {book_id}: {e}")
            raise
            
    def delete_book(self, book_id: int) -> bool:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
                if cursor.rowcount > 0:
                    logger.info(f"Book deleted successfully for id: {book_id}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to delete book {book_id}: {e}")
            raise
            
    def issue_book(self, book_id: int, user_id: str, staff_user_id: str = None) -> bool:
        if not user_id:
            raise ValueError("user_id is required to issue a book")

        now = time.time()
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check status
                cursor.execute("SELECT status FROM books WHERE id = ?", (book_id,))
                row = cursor.fetchone()
                if not row:
                    raise ValueError("Book does not exist")
                if row['status'] != 'Available':
                    raise ValueError("Book is not AVAILABLE")
                    
                # Update book attributes atomically
                cursor.execute('''
                    UPDATE books 
                    SET status = 'Issued', 
                        issued_to_user_id = ?, 
                        issued_by_user_id = ?, 
                        issue_timestamp = ?, 
                        updated_at = ?
                    WHERE id = ?
                ''', (user_id, staff_user_id, now, now, book_id))
                
                # Create historical transaction
                cursor.execute('''
                    INSERT INTO transactions (book_id, action, user_id, staff_user_id, timestamp)
                    VALUES (?, 'ISSUE', ?, ?, ?)
                ''', (book_id, user_id, staff_user_id, now))
                
                logger.info(f"Book {book_id} issued to {user_id}")
                return True
        except Exception as e:
            logger.error(f"Transaction failed for issue_book {book_id}: {e}")
            raise
            
    def return_book(self, book_id: int, user_id: str = None, staff_user_id: str = None) -> bool:
        now = time.time()
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check current status
                cursor.execute("SELECT status FROM books WHERE id = ?", (book_id,))
                row = cursor.fetchone()
                if not row:
                    raise ValueError("Book does not exist")
                if row['status'] != 'Issued':
                    raise ValueError("Book is not ISSUED")
                    
                # Store return details atomically
                cursor.execute('''
                    UPDATE books 
                    SET status = 'Available', 
                        issued_to_user_id = NULL, 
                        issued_by_user_id = NULL, 
                        return_timestamp = ?, 
                        updated_at = ?
                    WHERE id = ?
                ''', (now, now, book_id))
                
                cursor.execute('''
                    INSERT INTO transactions (book_id, action, user_id, staff_user_id, timestamp)
                    VALUES (?, 'RETURN', ?, ?, ?)
                ''', (book_id, user_id, staff_user_id, now))
                
                logger.info(f"Book {book_id} returned")
                return True
        except Exception as e:
            logger.error(f"Transaction failed for return_book {book_id}: {e}")
            raise

    def get_book_history(self, book_id: int) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions WHERE book_id = ? ORDER BY timestamp DESC", (book_id,))
            return [dict(r) for r in cursor.fetchall()]

    def get_all_transactions(self) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions ORDER BY timestamp DESC")
            return [dict(r) for r in cursor.fetchall()]

    def get_user_transactions(self, user_id: str) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
            return [dict(r) for r in cursor.fetchall()]

    def get_lifecycle_transactions(self, staff_user_id: str) -> List[Dict[str, Any]]:
        query = '''
            SELECT t.* FROM transactions t
            JOIN (
                SELECT DISTINCT book_id FROM transactions WHERE staff_user_id = ?
            ) as my_books ON t.book_id = my_books.book_id
            ORDER BY t.timestamp DESC
        '''
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (staff_user_id,))
            return [dict(r) for r in cursor.fetchall()]

    def get_currently_issued_books(self) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM books WHERE status = 'Issued' ORDER BY issue_timestamp DESC")
            return [dict(r) for r in cursor.fetchall()]
