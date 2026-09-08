import unittest
import tempfile
import os

from library_app.database.db import DatabaseManager
from library_app.database.repository import LibraryRepository
from library_app.models import LibraryModel

class TestRBAC(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        
        # Instantiate model directly wrapping temp DB. 
        self.model = LibraryModel()
        
        self.model.db = DatabaseManager(self.temp_db.name)
        self.model.db.init_db()
        self.model.repo = LibraryRepository(self.model.db)
        
        # create users
        self.model.repo.add_user("OwnerUser", role="OWNER")
        self.model.repo.add_user("StaffUser1", role="STAFF")
        self.model.repo.add_user("StaffUser2", role="STAFF")
        
        # Populate with 3 books
        for i in range(3):
            self.model.repo.add_book({
                'book_code': f'B{i}', 
                'title': f'Title {i}',
                'status': 'Available'
            })
            
    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            try:
                os.unlink(self.temp_db.name)
            except:
                pass
                
    def test_owner_permissions(self):
        self.model.set_user("OwnerUser")
        
        self.model.search_query = "Title 0"
        self.model.reload_books()
        self.assertEqual(self.model.books[0].status, "Available")
        
        # Owner issues
        res = self.model.issue_current_book()
        self.assertTrue(res)
        
        # Owner returns
        res_r = self.model.return_current_book()
        self.assertTrue(res_r)
        
    def test_staff_restricted_returns(self):
        # Staff 1 issues a book
        self.model.set_user("StaffUser1")
        self.model.search_query = "Title 0"
        self.model.reload_books()
        
        res = self.model.issue_current_book()
        self.assertTrue(res)
        
        # Switch to Staff 2
        self.model.set_user("StaffUser2")
        self.model.reload_books()
        self.assertEqual(self.model.books[0].status, "Issued")
        
        # Staff 2 tries to return Staff 1's book - should succeed gracefully because of ANY cross-staff rule in PR
        res = self.model.return_current_book()
        self.assertTrue(res)
            
        # Book should now be returned safely by StaffUser2
        self.assertEqual(self.model.books[0].status, "Available")
        
    def test_owner_override_returns(self):
        # Staff 1 issues a book
        self.model.set_user("StaffUser1")
        self.model.search_query = "Title 1"
        self.model.reload_books()
        
        self.assertTrue(self.model.issue_current_book())
        
        # Switch to Owner
        self.model.set_user("OwnerUser")
        self.model.reload_books()
        
        # Owner should be able to return Staff 1's book
        self.assertTrue(self.model.return_current_book())

if __name__ == '__main__':
    unittest.main()
