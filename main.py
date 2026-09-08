import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from library_app.app import LibraryApp

if __name__ == "__main__":
    app = LibraryApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
