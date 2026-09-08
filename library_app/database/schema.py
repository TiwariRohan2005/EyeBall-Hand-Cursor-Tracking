SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_code TEXT UNIQUE NOT NULL,
    isbn TEXT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    category TEXT,
    publisher TEXT,
    publication_year INTEGER,
    description TEXT,
    status TEXT NOT NULL,
    issued_to_user_id TEXT,
    issued_by_user_id TEXT,
    issue_timestamp REAL,
    return_timestamp REAL,
    created_at REAL,
    updated_at REAL
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    display_name TEXT,
    role TEXT NOT NULL,
    active INTEGER DEFAULT 1,
    created_at REAL,
    updated_at REAL
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    user_id TEXT,
    staff_user_id TEXT,
    timestamp REAL NOT NULL,
    notes TEXT,
    FOREIGN KEY(book_id) REFERENCES books(id)
);

CREATE INDEX IF NOT EXISTS idx_books_code ON books(book_code);
CREATE INDEX IF NOT EXISTS idx_books_isbn ON books(isbn);
CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);
CREATE INDEX IF NOT EXISTS idx_books_author ON books(author);
CREATE INDEX IF NOT EXISTS idx_books_category ON books(category);
CREATE INDEX IF NOT EXISTS idx_books_status ON books(status);
CREATE INDEX IF NOT EXISTS idx_books_issued_to ON books(issued_to_user_id);
CREATE INDEX IF NOT EXISTS idx_books_issued_by ON books(issued_by_user_id);

CREATE INDEX IF NOT EXISTS idx_trans_book ON transactions(book_id);
CREATE INDEX IF NOT EXISTS idx_trans_user ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_trans_time ON transactions(timestamp);

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT,
    category TEXT,
    created_by_user_id TEXT NOT NULL,
    created_at REAL,
    updated_at REAL,
    is_bookmarked INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_notes_user ON notes(created_by_user_id);
"""
