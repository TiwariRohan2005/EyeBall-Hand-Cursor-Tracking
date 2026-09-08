import os
import json
import logging
from .db import DatabaseManager
from .repository import LibraryRepository

logger = logging.getLogger(__name__)

def migrate_from_json(db: DatabaseManager, json_path: str = "library_session.json"):
    """
    Migrates library_session.json into the SQLite database.
    If database contains books, skips.
    If json does not exist, seeds default books instead.
    """
    repo = LibraryRepository(db)
    
    # Check if database already has data
    if len(repo.list_books()) > 0:
        logger.info("Database already contains books. Skipping JSON migration.")
        return
        
    if not os.path.exists(json_path):
        logger.info(f"Existing JSON file '{json_path}' not found. Seeding default books.")
        seed_default_books(repo)
        return
        
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        books = data.get('books', [])
        logger.info(f"Migration started: porting {len(books)} books from JSON.")
        
        for i, b in enumerate(books):
            title = b.get('title', f"Book {i}")
            status = b.get('status', 'Available')
            # Fix case match issues
            if not status or not isinstance(status, str): 
                status = "Available"
                
            book_data = {
                'book_code': f"B-{i:04d}",
                'title': title,
                'author': 'Unknown',
                'status': status.capitalize(),
                'issue_timestamp': b.get('issue_timestamp'),
                'return_timestamp': b.get('return_timestamp')
            }
            book_id = repo.add_book(book_data)
            
            # If the book was issued according to JSON state, logging it as a migrated issue transaction
            if status.capitalize() == 'Issued':
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO transactions (book_id, action, timestamp, notes) VALUES (?, 'ISSUE', ?, ?)",
                        (book_id, b.get('issue_timestamp', 0) or 0, 'Migrated from JSON (Issued State)')
                    )
        
        logger.info("JSON migration completed.")
    except Exception as e:
        logger.error(f"Migration from JSON failed: {e}")
        raise

def seed_default_books(repo: LibraryRepository):
    """
    Creates a sample collection of 26 books for testing/development.
    """
    logger.info("Seeding database with default A-Z books.")
    for i in range(26):
        title = f"Book {chr(65 + i)}"
        book_data = {
            'book_code': f"SEED-{chr(65 + i)}",
            'title': title,
            'author': "Default Author",
            'status': "Available"
        }
        repo.add_book(book_data)
        logger.info(f"Seeded: {title}")
