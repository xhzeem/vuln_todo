import sqlite3

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            bio TEXT DEFAULT ''
        )
    ''')

    # Create tasks table
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Insert a dummy user
    try:
        c.execute("INSERT INTO users (username, password, bio) VALUES ('admin', 'admin123', 'Administrator of the system.')")
        c.execute("INSERT INTO tasks (user_id, title, description) VALUES (1, 'Initial Setup', 'Make sure the server is configured properly.')")
    except sqlite3.IntegrityError:
        pass # User might already exist

    conn.commit()
    conn.close()
    print("Database initialized.")

if __name__ == '__main__':
    init_db()
