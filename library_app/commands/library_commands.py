from .command import Command
from library_app.permissions import Permission

def register_library_commands(registry, app_instance):
    """
    Registers Library contextual intents onto app.py UI actions tightly coupled.
    """
    registry.register_command(
        Command(
            id="LIBRARY_SELECT_BOOK_UP",
            display_name="Select Book Up",
            context="LIBRARY",
            required_permission=Permission.BOOK_VIEW,
            handler=app_instance.select_book_up,
            description="Selects the book above in the grid",
            is_safe=True
        ), mapped_intents=["SELECT_BOOK_UP"]
    )
    
    registry.register_command(
        Command(
            id="LIBRARY_SELECT_BOOK_DOWN",
            display_name="Select Book Down",
            context="LIBRARY",
            required_permission=Permission.BOOK_VIEW,
            handler=app_instance.select_book_down,
            description="Selects the book below in the grid",
            is_safe=True
        ), mapped_intents=["SELECT_BOOK_DOWN"]
    )

    registry.register_command(
        Command(
            id="LIBRARY_SELECT_BOOK_LEFT",
            display_name="Select Book Left",
            context="LIBRARY",
            required_permission=Permission.BOOK_VIEW,
            handler=app_instance.select_book_left,
            description="Selects the book to the left",
            is_safe=True
        ), mapped_intents=["SELECT_BOOK_LEFT"]
    )

    registry.register_command(
        Command(
            id="LIBRARY_SELECT_BOOK_RIGHT",
            display_name="Select Book Right",
            context="LIBRARY",
            required_permission=Permission.BOOK_VIEW,
            handler=app_instance.select_book_right,
            description="Selects the book to the right",
            is_safe=True
        ), mapped_intents=["SELECT_BOOK_RIGHT"]
    )
    
    registry.register_command(
        Command(
            id="LIBRARY_ISSUE_BOOK",
            display_name="Issue Book",
            context="LIBRARY",
            required_permission=Permission.BOOK_ISSUE,
            handler=app_instance.model.issue_current_book,
            description="Issues the currently selected book",
            is_safe=False
        ),
        mapped_intents=["ISSUE_BOOK"]
    )

    registry.register_command(
        Command(
            id="LIBRARY_RETURN_BOOK",
            display_name="Return Book",
            context="LIBRARY",
            required_permission=Permission.BOOK_RETURN,
            handler=app_instance.model.return_current_book,
            description="Returns the currently selected book",
            is_safe=False
        ),
        mapped_intents=["RETURN_BOOK"]
    )
