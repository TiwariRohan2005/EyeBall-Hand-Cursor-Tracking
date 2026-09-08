from .command import Command
from library_app.permissions import Permission

def register_notes_commands(registry, notes_ui):
    """
    Registers Notes contextual intents onto notes_ui actions tightly coupled.
    """
    registry.register_command(
        Command(
            id="NOTES_NEXT_NOTE",
            display_name="Next Note",
            context="STUDY_NOTES",
            required_permission=Permission.BOOK_VIEW, # Reusing simple read access
            handler=notes_ui.next_note,
            description="Navigates to next note",
            is_safe=True
        ),
        mapped_intents=["NEXT_NOTE", "CURSOR_RIGHT"]
    )
    
    registry.register_command(
        Command(
            id="NOTES_PREV_NOTE",
            display_name="Previous Note",
            context="STUDY_NOTES",
            required_permission=Permission.BOOK_VIEW,
            handler=notes_ui.prev_note,
            description="Navigates to previous note",
            is_safe=True
        ),
        mapped_intents=["PREVIOUS_NOTE", "CURSOR_LEFT"]
    )
    
    registry.register_command(
        Command(
            id="NOTES_NEW",
            display_name="New Note",
            context="STUDY_NOTES",
            required_permission=Permission.BOOK_VIEW, # Everyone can create notes
            handler=notes_ui.new_note,
            description="Creates a blank note",
            is_safe=True
        ),
        mapped_intents=["NEW_NOTE"]
    )
    
    registry.register_command(
        Command(
            id="NOTES_SAVE",
            display_name="Save Note",
            context="STUDY_NOTES",
            required_permission=Permission.BOOK_VIEW,
            handler=notes_ui.save_note,
            description="Saves current note",
            is_safe=True
        ),
        mapped_intents=["SAVE_NOTE"]
    )
    
    registry.register_command(
        Command(
            id="NOTES_DELETE",
            display_name="Delete Note",
            context="STUDY_NOTES",
            required_permission=Permission.BOOK_VIEW,
            handler=notes_ui.delete_note,
            description="Deletes current note",
            is_safe=False # Needs confirmation
        ),
        mapped_intents=["DELETE_NOTE"]
    )
    
    registry.register_command(
        Command(
            id="NOTES_SWITCH_LIBRARY",
            display_name="To Library",
            context="STUDY_NOTES",
            required_permission=Permission.BOOK_VIEW,
            handler=notes_ui.switch_to_library,
            description="Returns to Library dashboard",
            is_safe=True
        ),
        mapped_intents=["SWITCH_CONTEXT"]
    )
    
    registry.register_command(
        Command(
            id="LIBRARY_SWITCH_NOTES",
            display_name="To Notes",
            context="LIBRARY",
            required_permission=Permission.BOOK_VIEW,
            handler=notes_ui.switch_to_notes,
            description="Switches to Notes dashboard",
            is_safe=True
        ),
        mapped_intents=["SWITCH_CONTEXT"]
    )
