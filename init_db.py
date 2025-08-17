import sqlite3

def init_database():
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        
        # Create users table with only necessary fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                messages INTEGER DEFAULT 0,
                voice_time INTEGER DEFAULT 0,
                money INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        print("Empty database created successfully!")

if __name__ == "__main__":
    init_database()
