import unittest
from library_app.commands.command_registry import CommandRegistry
from library_app.commands.command import Command
from library_app.permissions import Permission

class DummyApp:
    def handler(self):
        return "OK"
    def restricted_handler(self):
        return "RESTRICTED API"

class TestCommandCenter(unittest.TestCase):
    def setUp(self):
        self.registry = CommandRegistry()
        self.app = DummyApp()
        
        self.registry.register_command(
            Command("LIB_NEXT", "Next Book", "LIBRARY", Permission.BOOK_VIEW, self.app.handler, "Desc"),
            ["NEXT"]
        )
        self.registry.register_command(
            Command("LIB_DELETE", "Delete Book", "LIBRARY", Permission.BOOK_DELETE, self.app.restricted_handler, "Desc", False),
            ["DELETE"]
        )
        self.registry.register_command(
            Command("NOTES_NEXT", "Next Note", "STUDY_NOTES", Permission.BOOK_VIEW, self.app.handler, "Desc"),
            ["NEXT"]
        )

    def test_intent_mapping(self):
        lib_cmd = self.registry.resolve_intent("LIBRARY", "NEXT")
        notes_cmd = self.registry.resolve_intent("STUDY_NOTES", "NEXT")
        
        self.assertEqual(lib_cmd.id, "LIB_NEXT")
        self.assertEqual(notes_cmd.id, "NOTES_NEXT")
        
    def test_permissions_gate(self):
        # Staff firing safe command
        lib_cmd = self.registry.resolve_intent("LIBRARY", "NEXT")
        res1 = self.registry.execute_command(lib_cmd.id, "STAFF")
        self.assertEqual(res1['status'], "success")
        
        # Staff firing destructive command
        del_cmd = self.registry.resolve_intent("LIBRARY", "DELETE")
        res2 = self.registry.execute_command(del_cmd.id, "STAFF")
        self.assertEqual(res2['status'], "denied")
        
        # Owner firing destructive command
        res3 = self.registry.execute_command(del_cmd.id, "OWNER")
        self.assertEqual(res3['status'], "success")
        
    def test_palette_visibility(self):
        staff_cmds = self.registry.get_available_commands("LIBRARY", "STAFF")
        self.assertEqual(len(staff_cmds), 1)
        self.assertEqual(staff_cmds[0].id, "LIB_NEXT")
        
        owner_cmds = self.registry.get_available_commands("LIBRARY", "OWNER")
        self.assertEqual(len(owner_cmds), 2)

if __name__ == '__main__':
    unittest.main()
