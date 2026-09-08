import os
import sqlite3
import random
import time

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'library.db')

BOOKS = [
    # Computer Science
    ("Design Patterns", "Erich Gamma", "Computer Science", "Addison-Wesley", 1994, "Elements of Reusable Object-Oriented Software"),
    ("Clean Code", "Robert C. Martin", "Programming", "Prentice Hall", 2008, "A Handbook of Agile Software Craftsmanship"),
    ("The Pragmatic Programmer", "Andrew Hunt", "Programming", "Addison-Wesley", 1999, "Your journey to mastery"),
    ("Introduction to Algorithms", "Thomas H. Cormen", "Computer Science", "MIT Press", 2009, "Comprehensive algorithm study"),
    ("Artificial Intelligence: A Modern Approach", "Stuart Russell", "Artificial Intelligence", "Pearson", 2020, "Leading AI textbook"),
    ("Deep Learning", "Ian Goodfellow", "Machine Learning", "MIT Press", 2016, "Foundation of Deep Learning architectures"),
    ("Hands-On Machine Learning", "Aurélien Géron", "Machine Learning", "O'Reilly", 2019, "Scikit-Learn, Keras, and TensorFlow"),
    ("Pattern Recognition and Machine Learning", "Christopher Bishop", "Machine Learning", "Springer", 2006, "Advanced ML text"),
    ("Data Science from Scratch", "Joel Grus", "Data Science", "O'Reilly", 2019, "First principles with Python"),
    ("Python Data Science Handbook", "Jake VanderPlas", "Data Science", "O'Reilly", 2016, "Numpy, Pandas, Matplotlib, Scikit-learn"),
    
    # Cyber Security
    ("Applied Cryptography", "Bruce Schneier", "Cyber Security", "Wiley", 1996, "Protocols, Algorithms, and Source Code"),
    ("Hacking: The Art of Exploitation", "Jon Erickson", "Cyber Security", "No Starch Press", 2008, "Security fundamentals"),
    ("The Web Application Hacker's Handbook", "Dafydd Stuttard", "Cyber Security", "Wiley", 2011, "Finding and exploiting flaws"),
    ("Practical Malware Analysis", "Michael Sikorski", "Cyber Security", "No Starch Press", 2012, "Dissecting malicious software"),
    ("Social Engineering", "Christopher Hadnagy", "Cyber Security", "Wiley", 2010, "The art of human hacking"),
    
    # Information Technology & Architecture
    ("Designing Data-Intensive Applications", "Martin Kleppmann", "Database Systems", "O'Reilly", 2017, "Scalable, reliable, and maintainable systems"),
    ("Site Reliability Engineering", "Niall Richard Murphy", "Information Technology", "O'Reilly", 2016, "How Google runs production systems"),
    ("The Phoenix Project", "Gene Kim", "Information Technology", "IT Revolution", 2013, "A novel about IT, DevOps, and helping your business win"),
    ("Database Internals", "Alex Petrov", "Database Systems", "O'Reilly", 2019, "A deep dive into how distributed data systems work"),
    ("Refactoring", "Martin Fowler", "Software Engineering", "Addison-Wesley", 2018, "Improving the design of existing code"),
    
    # Web Development
    ("Eloquent JavaScript", "Marijn Haverbeke", "Web Development", "No Starch", 2018, "A modern introduction to programming"),
    ("You Don't Know JS", "Kyle Simpson", "Web Development", "O'Reilly", 2015, "Up & Going"),
    ("JavaScript: The Good Parts", "Douglas Crockford", "Web Development", "O'Reilly", 2008, "Unearthing the excellence in JS"),
    ("Learning React", "Alex Banks", "Web Development", "O'Reilly", 2020, "Modern patterns for developing react apps"),
    ("Node.js Design Patterns", "Mario Casciaro", "Web Development", "Packt", 2020, "Master asynchronous programming"),
    
    # Mathematics & Physics
    ("Calculus", "James Stewart", "Mathematics", "Cengage", 2015, "Early transcendentals"),
    ("Linear Algebra Done Right", "Sheldon Axler", "Mathematics", "Springer", 2015, "Undergraduate mathematics"),
    ("Principles of Quantum Mechanics", "R. Shankar", "Physics", "Springer", 1994, "Classical and quantum foundations"),
    ("Introduction to Electrodynamics", "David J. Griffiths", "Physics", "Pearson", 2012, "Standard text on electrodynamics"),
    ("Classical Mechanics", "John R. Taylor", "Physics", "University Science Books", 2005, "Accessible coverage of mechanics"),
    
    # Business, Management & Psychology
    ("The Lean Startup", "Eric Ries", "Business", "Crown Business", 2011, "How today's entrepreneurs use continuous innovation"),
    ("Zero to One", "Peter Thiel", "Business", "Crown Business", 2014, "Notes on startups, or how to build the future"),
    ("Thinking, Fast and Slow", "Daniel Kahneman", "Psychology", "Farrar", 2011, "Two systems that drive the way we think"),
    ("Drive", "Daniel H. Pink", "Psychology", "Riverhead", 2009, "The surprising truth about what motivates us"),
    ("Good to Great", "Jim Collins", "Management", "HarperBusiness", 2001, "Why some companies make the leap"),
    ("The Innovator's Dilemma", "Clayton M. Christensen", "Management", "Harvard Business", 1997, "When new technologies cause great firms to fail"),
    
    # Literature & History
    ("1984", "George Orwell", "Literature", "Secker & Warburg", 1949, "Dystopian social science fiction"),
    ("Sapiens: A Brief History of Humankind", "Yuval Noah Harari", "History", "Harvill Secker", 2011, "Evolution of humans"),
    ("Guns, Germs, and Steel", "Jared Diamond", "History", "W. W. Norton", 1997, "The fates of human societies"),
    ("A Brief History of Time", "Stephen Hawking", "Science", "Bantam", 1988, "From the Big Bang to Black Holes"),
    
    # Adding more generated diverse technical books (100+ Total required)
]

# Dynamically generate 60 more unique books to exceed 100 comfortably
tech_topics = ["Docker", "Kubernetes", "AWS", "Azure", "GCP", "Rust", "Go", "C++", "C#", "Java", "Swift", "Kotlin"]
concepts = ["Mastery", "Fundamentals", "Advanced", "In Action", "Cookbook", "Design Patterns", "Internals", "Practical", "Definitive Guide"]
authors = ["Jane Smith", "John Doe", "Alice Johnson", "Bob Brown", "Charlie Davis", "Eve Wilson", "Grace Taylor", "Mallory Moore"]
pubs = ["O'Reilly", "Packt", "Manning", "Wiley", "Apress", "Springer"]

for i in range(1, 65):
    topic = random.choice(tech_topics)
    concept = random.choice(concepts)
    BOOKS.append(
        (f"{topic} {concept} Vol {i}", random.choice(authors), "Information Technology", random.choice(pubs), random.randint(2010, 2024), f"An extensive guide on {topic}")
    )

def seed_books():
    print(f"Connecting to database at {DB_PATH}...")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Ensure table exists
    cursor.execute("""
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
    """)
    conn.commit()

    # Get max existing sequence to prevent B-0100 clashes
    cursor.execute("SELECT book_code FROM books WHERE book_code LIKE 'B-%'")
    existing_codes = [row[0] for row in cursor.fetchall()]
    
    max_seq = 0
    for code in existing_codes:
        try:
            num = int(code.split('-')[1])
            if num > max_seq:
                max_seq = num
        except:
            pass

    # Ensure idempotency by hashing titles or checking existence
    cursor.execute("SELECT title FROM books")
    existing_titles = set(row[0].lower() for row in cursor.fetchall())
    
    added_count = 0
    now = time.time()
    
    for b in BOOKS:
        title = b[0]
        if title.lower() in existing_titles:
            continue
            
        max_seq += 1
        book_code = f"B-{(1000 + max_seq)}"

        author = b[1]
        category = b[2]
        publisher = b[3]
        year = b[4]
        desc = b[5]
        
        cursor.execute('''
            INSERT INTO books (book_code, title, author, category, publisher, publication_year, description, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (book_code, title, author, category, publisher, year, desc, 'Available', now, now))
        
        existing_titles.add(title.lower())
        added_count += 1

    conn.commit()
    conn.close()
    
    print(f"Seeding complete. Added {added_count} new unique books safely.")

if __name__ == "__main__":
    seed_books()
