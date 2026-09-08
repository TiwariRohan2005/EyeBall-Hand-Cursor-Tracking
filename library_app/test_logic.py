import os
import sys
import tempfile

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from library_app.models import LibraryModel, StorageManager
from library_app.database.db import DatabaseManager
from library_app.database.repository import LibraryRepository

def test_models_and_storage(tmp_path):
    import unittest.mock
    
    db_file = tmp_path / "test_library.db"
    
    with unittest.mock.patch('library_app.models.DatabaseManager') as mock_db, \
         unittest.mock.patch('library_app.models.migrate_from_json'):
        mock_instance = DatabaseManager(str(db_file))
        mock_db.return_value = mock_instance
        model = LibraryModel()
        
    model.repo.add_book({'book_code': 'B1', 'title': 'Book A', 'status': 'Available'})
    model.repo.add_book({'book_code': 'B2', 'title': 'Book B', 'status': 'Available'})
    model.reload_books()
    
    assert len(model.books) == 2
    assert model.get_current_book().title == "Book A"
    
    # Test navigation
    model.next_book()
    assert model.get_current_book().title == "Book B"
    model.prev_book()
    assert model.get_current_book().title == "Book A"
    
    # Test issue
    # For issue, we need permission. We will set role manually.
    model.role = "OWNER"
    
    success = model.issue_current_book()
    assert success == True
    assert model.get_current_book().status == "Issued"
    
    stats = model.get_summary_stats()
    assert stats['issued'] == 1
    
    # Test return
    success_return = model.return_current_book()
    assert success_return == True
    assert model.get_current_book().status == "Available"
    
    stats2 = model.get_summary_stats()
    assert stats2['issued'] == 0
    
    print("Library logical tests passed!")

if __name__ == "__main__":
    test_models_and_storage()
