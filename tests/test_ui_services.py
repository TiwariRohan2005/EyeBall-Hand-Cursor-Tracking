import unittest
import tempfile
import os

from library_app.database.db import DatabaseManager
from library_app.database.repository import LibraryRepository
from library_app.models import LibraryModel

class TestUIServices(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        
        import unittest.mock
        self.patcher1 = unittest.mock.patch('library_app.models.DatabaseManager')
        self.patcher2 = unittest.mock.patch('library_app.models.migrate_from_json')
        self.mock_db_class = self.patcher1.start()
        self.mock_migrate = self.patcher2.start()
        
        self.mock_db_instance = DatabaseManager(self.temp_db.name)
        self.mock_db_instance.init_db()
        self.mock_db_class.return_value = self.mock_db_instance
        
        self.model = LibraryModel(current_user_id="U1")
        
        # Populate with 25 books
        for i in range(25):
            self.model.repo.add_book({
                'book_code': f'B{i}', 
                'title': f'Title {i}',
                'status': 'Issued' if i % 2 == 0 else 'Available'
            })
            
    def tearDown(self):
        self.patcher1.stop()
        self.patcher2.stop()
        if os.path.exists(self.temp_db.name):
            try:
                os.unlink(self.temp_db.name)
            except:
                pass
                
    def test_pagination(self):
        self.model.page_size = 10
        self.model.reload_books()
        
        self.assertEqual(len(self.model.books), 10)
        self.assertEqual(self.model.total_pages, 3)
        self.assertEqual(self.model.total_filtered, 25)
        
        self.model.page = 3
        self.model.reload_books()
        self.assertEqual(len(self.model.books), 5)
        
    def test_search(self):
        self.model.search_query = "Title 10"
        self.model.reload_books()
        self.assertEqual(len(self.model.books), 1)
        self.assertEqual(self.model.books[0].book_code, "B10")
        
    def test_filter(self):
        self.model.status_filter = "Available"
        self.model.reload_books()
        # odd numbers 1..23 -> 12 available books
        self.assertEqual(self.model.total_filtered, 12)
        
    def test_issue_return(self):
        self.model.search_query = "Title 13" # Available
        self.model.reload_books()
        
        self.assertEqual(len(self.model.books), 1)
        self.model.current_index = 0
        
        # Issue
        res = self.model.issue_current_book()
        self.assertTrue(res)
        self.assertEqual(self.model.books[0].status, "Issued")
        
        # Return
        res_return = self.model.return_current_book()
        self.assertTrue(res_return)
        self.assertEqual(self.model.books[0].status, "Available")

if __name__ == '__main__':
    unittest.main()
