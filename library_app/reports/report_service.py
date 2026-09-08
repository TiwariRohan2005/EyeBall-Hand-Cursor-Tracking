import os
import time
import logging
from library_app.permissions import PermissionManager, Permission
from .excel_exporter import ExcelExporter
from library_app.database.repository import LibraryRepository

logger = logging.getLogger(__name__)

class ReportService:
    def __init__(self, repo: LibraryRepository):
        self.repo = repo
        self.reports_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'reports'))
        os.makedirs(self.reports_dir, exist_ok=True)
        
    def generate_report(self, requestor_role: str, requestor_id: str) -> tuple[str, bool]:
        # Check permissions
        if PermissionManager.has_permission(requestor_role, Permission.EXPORT_FULL_REPORT):
            filename = "TrueEyeball_Library_Report.xlsx"
            filepath = os.path.join(self.reports_dir, filename)
            is_new = not os.path.exists(filepath)
            
            inventory = self.repo.list_books()
            transactions = self.repo.get_all_transactions()
            
            summary = {
                "total_books": len(inventory),
                "available_books": sum(1 for b in inventory if b.get('status') == 'Available'),
                "issued_books": sum(1 for b in inventory if b.get('status') == 'Issued'),
                "total_transactions": len(transactions),
                "generated_by_role": "OWNER",
                "generated_by": requestor_id,
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            logger.info("REPORT_GENERATED Full Export by OWNER")
            try:
                ExcelExporter.generate_workbook(filepath, inventory, transactions, summary, staff_only=False)
            except PermissionError:
                raise PermissionError(f"Please close {filename} and try exporting again.")
                
            return filepath, is_new
            
        elif PermissionManager.has_permission(requestor_role, Permission.EXPORT_OWN_REPORT):
            filename = "TrueEyeball_Staff_Report.xlsx"
            filepath = os.path.join(self.reports_dir, filename)
            is_new = not os.path.exists(filepath)
            
            transactions = self.repo.get_lifecycle_transactions(requestor_id)
            books_involved = set(t['book_id'] for t in transactions)
            inventory = []
            for bid in books_involved:
                b = self.repo.get_book(bid)
                if b: inventory.append(b)
                
            summary = {
                "my_books_managed": len(inventory),
                "my_total_transactions": len(transactions),
                "issues": sum(1 for t in transactions if t.get('action') == 'ISSUE'),
                "returns": sum(1 for t in transactions if t.get('action') == 'RETURN'),
                "generated_by_role": "STAFF",
                "generated_by": requestor_id,
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            logger.info(f"REPORT_GENERATED Staff Export by {requestor_id}")
            try:
                ExcelExporter.generate_workbook(filepath, inventory, transactions, summary, staff_only=True)
            except PermissionError:
                raise PermissionError(f"Please close {filename} and try exporting again.")
                
            return filepath, is_new
            
        else:
            PermissionManager.require_permission(requestor_role, Permission.EXPORT_FULL_REPORT)
