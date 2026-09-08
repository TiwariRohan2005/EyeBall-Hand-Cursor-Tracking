import unittest
import tempfile
import os

from library_app.database.db import DatabaseManager
from library_app.database.repository import LibraryRepository
from library_app.permissions import PermissionManager, Permission

class TestUserManagement(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        
        self.db = DatabaseManager(self.temp_db.name)
        self.db.init_db()
        self.repo = LibraryRepository(self.db)
        
        # 1 owner initially
        self.repo.add_user("test_owner", role="OWNER")
        self.repo.add_user("test_staff1", role="STAFF")
        self.repo.add_user("test_staff2", role="STAFF")
        
        self.repo.add_book({
            'book_code': 'B1', 
            'title': 'Test Report Book',
            'status': 'Available'
        })
        
    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            try:
                os.unlink(self.temp_db.name)
            except:
                pass
                
    def test_owner_can_deactivate_staff(self):
        # 1. OWNER can deactivate STAFF.
        self.repo.deactivate_user("test_staff1")
        user = self.repo.get_user_by_username("test_staff1")
        self.assertEqual(user['active'], 0)
        
    def test_staff_cannot_deactivate_staff_or_owner(self):
        # 2. STAFF cannot deactivate STAFF. 3. STAFF cannot deactivate OWNER.
        # Enforced at the UI/App level via PermissionManager MANAGE_STAFF token.
        with self.assertRaises(PermissionError):
            PermissionManager.require_permission("STAFF", Permission.MANAGE_STAFF)
            
    def test_deactivated_staff_no_longer_counts(self):
        # 6. Deactivated STAFF no longer counts toward the 10 active STAFF limit.
        for i in range(3, 11):
            self.repo.add_user(f"staff{i}", role="STAFF")
        
        # Now we have 10 staff (2 + 8). Next one should fail.
        with self.assertRaises(PermissionError):
            self.repo.add_user("staff11", role="STAFF")
            
        # Deactivate one
        self.repo.deactivate_user("test_staff1")
        
        # Now we can add one successfully since test_staff1 is excluded from active count
        self.repo.add_user("staff11", role="STAFF")
        counts = self.repo.get_role_counts()
        self.assertEqual(counts['STAFF'], 10)
        
    def test_historical_transactions_remain(self):
        # 7. Historical transactions remain intact after STAFF deactivation.
        book = self.repo.get_book_by_code('B1')
        self.repo.issue_book(book['id'], user_id="student1", staff_user_id="test_staff1")
        
        # Deactivate test_staff1 softly
        self.repo.deactivate_user("test_staff1")
        
        # Ensure transactions query still pulls their foreign keys without crashes
        txns = self.repo.get_all_transactions()
        self.assertEqual(len(txns), 1)
        self.assertEqual(txns[0]['staff_user_id'], "test_staff1")
        
    def test_owner_limit_remains_enforced(self):
        # 9. OWNER=1 limit remains enforced on active.
        with self.assertRaises(PermissionError):
            self.repo.add_user("owner2", role="OWNER")
            
        self.repo.deactivate_user("test_owner")
        counts = self.repo.get_role_counts()
        self.assertEqual(counts.get('OWNER', 0), 0)
        
        # Allow one more since original was removed
        self.repo.add_user("owner2", role="OWNER")
        counts = self.repo.get_role_counts()
        self.assertEqual(counts.get('OWNER', 0), 1)

    def test_reactivation_restores_staff(self):
        # 11. Reactivating a deactivated STAFF correctly restores the active count.
        self.repo.deactivate_user("test_staff2")
        counts = self.repo.get_role_counts()
        self.assertEqual(counts['STAFF'], 1)
        
        self.repo.activate_user("test_staff2")
        counts2 = self.repo.get_role_counts()
        self.assertEqual(counts2['STAFF'], 2)

if __name__ == '__main__':
    unittest.main()
