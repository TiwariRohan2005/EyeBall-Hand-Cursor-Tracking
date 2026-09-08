import unittest
import tempfile
import os

from library_app.database.db import DatabaseManager
from library_app.database.repository import LibraryRepository
from library_app.database.migrations import seed_default_books

class TestLibraryDB(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = DatabaseManager(self.temp_db.name)
        self.db.init_db()
        self.repo = LibraryRepository(self.db)
        
    def tearDown(self):
        os.unlink(self.temp_db.name)
        
    def test_db_initialization(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='books'")
            self.assertIsNotNone(cursor.fetchone())

    def test_add_and_retrieve_book(self):
        book_id = self.repo.add_book({
            'book_code': 'TEST_CODE',
            'title': 'Test Title',
            'author': 'Test Author'
        })
        self.assertIsNotNone(book_id)
        
        book = self.repo.get_book(book_id)
        self.assertEqual(book['book_code'], 'TEST_CODE')
        self.assertEqual(book['title'], 'Test Title')
        
    def test_prevent_duplicate_code(self):
        self.repo.add_book({
            'book_code': 'UNIQ_1',
            'title': 'T1'
        })
        with self.assertRaises(Exception):
            self.repo.add_book({
                'book_code': 'UNIQ_1',  # duplicate
                'title': 'T2'
            })
            
    def test_issue_available_book(self):
        book_id = self.repo.add_book({
            'book_code': 'TEST',
            'title': 'T1'
        })
        
        res = self.repo.issue_book(book_id, user_id='U1')
        self.assertTrue(res)
        
        book = self.repo.get_book(book_id)
        self.assertEqual(book['status'], 'Issued')
        self.assertEqual(book['issued_to_user_id'], 'U1')
        self.assertIsNotNone(book['issue_timestamp'])
        
        history = self.repo.get_book_history(book_id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['action'], 'ISSUE')
        
    def test_prevent_issue_already_issued(self):
        book_id = self.repo.add_book({'book_code': 'TEST2', 'title': 'T1'})
        self.repo.issue_book(book_id, user_id='U1')
        
        with self.assertRaises(ValueError) as ctx:
            self.repo.issue_book(book_id, user_id='U2')
        self.assertIn("not AVAILABLE", str(ctx.exception))
        
    def test_return_issued_book(self):
        book_id = self.repo.add_book({'book_code': 'TEST3', 'title': 'T1'})
        self.repo.issue_book(book_id, user_id='U1')
        
        res = self.repo.return_book(book_id)
        self.assertTrue(res)
        
        book = self.repo.get_book(book_id)
        self.assertEqual(book['status'], 'Available')
        self.assertIsNone(book['issued_to_user_id'])
        
        history = self.repo.get_book_history(book_id)
        self.assertEqual(len(history), 2)
        
    def test_rollback_on_failed_transaction(self):
        book_id = self.repo.add_book({'book_code': 'UNIQUE_CODE', 'title': 'T1'})
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE books SET title = 'NEW TITLE' WHERE id = ?", (book_id,))
                
                # Intentional error: violates UNIQUE constraint
                cursor.execute("INSERT INTO books (book_code, title, author, status) VALUES (?, ?, ?, ?)", ('UNIQUE_CODE', 'T2', 'A', 'Available'))
        except Exception:
            pass
            
        book = self.repo.get_book(book_id)
        # Should be rolled back
        self.assertEqual(book['title'], 'T1')

    def test_registration_limits(self):
        # 1. Register first Owner -> SUCCESS
        self.repo.add_user("test_owner_1", role="OWNER")
        
        # 2. Register second Owner -> DENIED
        with self.assertRaises(PermissionError):
            self.repo.add_user("test_owner_2", role="OWNER")
            
        # 3. Register Staff 1 through 10 -> SUCCESS
        for i in range(1, 11):
            self.repo.add_user(f"staff_user_{i}", role="STAFF")
            
        # 5. Register Staff 11 -> DENIED
        with self.assertRaises(PermissionError):
            self.repo.add_user("staff_user_11", role="STAFF")

    def test_cross_staff_return_and_lifecycle_reporting(self):
        # Setup: Users
        self.repo.add_user("staff_2", role="STAFF")
        self.repo.add_user("staff_4", role="STAFF")
        
        # Setup: Books
        book_a = self.repo.add_book({'book_code': 'BK_A', 'title': 'Book A'})
        book_b = self.repo.add_book({'book_code': 'BK_B', 'title': 'Book B'})
        
        # Stage 1: Staff 2 issues Book A to Student X
        self.repo.issue_book(book_a, user_id='Student X', staff_user_id='staff_2')
        
        # Stage 2: Staff 2 issues Book B to Student Y
        self.repo.issue_book(book_b, user_id='Student Y', staff_user_id='staff_2')
        
        # Stage 3: Staff 4 returns Book A (Cross-Staff Return!)
        res = self.repo.return_book(book_a, user_id='Student X', staff_user_id='staff_4')
        self.assertTrue(res) # MUST be allowed
        
        book_a_record = self.repo.get_book(book_a)
        self.assertEqual(book_a_record['status'], 'Available')
        
        # Reporting Scope Verification:
        # Generate Staff 4 Report Scope
        s4_txns = self.repo.get_lifecycle_transactions('staff_4')
        # Staff 4 should see ONLY Book A (Complete lifecycle)
        s4_bids = set([t['book_id'] for t in s4_txns])
        self.assertIn(book_a, s4_bids)
        self.assertNotIn(book_b, s4_bids)
        
        # Generate Staff 2 Report Scope
        s2_txns = self.repo.get_lifecycle_transactions('staff_2')
        s2_bids = set([t['book_id'] for t in s2_txns])
        self.assertIn(book_a, s2_bids)
        self.assertIn(book_b, s2_bids)
        
        # Verify original ISSUE transaction remains unchanged for Book A
        book_a_history = self.repo.get_book_history(book_a)
        # Should have RETURN (by staff 4) then ISSUE (by staff 2)
        self.assertEqual(book_a_history[0]['action'], 'RETURN')
        self.assertEqual(book_a_history[0]['staff_user_id'], 'staff_4')
        
        self.assertEqual(book_a_history[1]['action'], 'ISSUE')
        self.assertEqual(book_a_history[1]['staff_user_id'], 'staff_2')
        self.assertEqual(book_a_history[1]['user_id'], 'Student X')
        
if __name__ == '__main__':
    unittest.main()
