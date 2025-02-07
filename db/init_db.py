import sqlite3  # Ensure this is at the top of the script

# Create the database files and tables
def init_db():
    # Create and initialize users database
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Create the users table if it doesn't exist
    cursor.execute(''' 
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )''')
    conn.commit()
    conn.close()

    # Create and initialize posts database
    conn = sqlite3.connect('posts.db')
    cursor = conn.cursor()

    # Create posts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT,
        username TEXT,
        description TEXT,
        file_path TEXT,
        FOREIGN KEY(username) REFERENCES users(username)
    )''')

    # Create comments table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        comment TEXT NOT NULL,
        FOREIGN KEY(post_id) REFERENCES posts(id),
        FOREIGN KEY(username) REFERENCES users(username)
    )''')

    # Create likes table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        FOREIGN KEY(post_id) REFERENCES posts(id),
        FOREIGN KEY(username) REFERENCES users(username)
    )''')

    conn.commit()
    conn.close()

# Insert a new post into the database
def add_post(subject, username, description, file_path=None):
    conn = sqlite3.connect('posts.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO posts (subject, username, description, file_path)
    VALUES (?, ?, ?, ?)''', (subject, username, description, file_path))
    
    conn.commit()
    conn.close()

# Insert a comment into the database
def add_comment(post_id, username, comment):
    conn = sqlite3.connect('posts.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO comments (post_id, username, comment)
    VALUES (?, ?, ?)''', (post_id, username, comment))
    
    conn.commit()
    conn.close()

# Insert a like into the database
def add_like(post_id, username):
    conn = sqlite3.connect('posts.db')
    cursor = conn.cursor()

    # Ensure the user hasn't already liked the post
    cursor.execute('''
    SELECT * FROM likes WHERE post_id = ? AND username = ?''', (post_id, username))
    if cursor.fetchone():
        print("User has already liked this post.")
    else:
        cursor.execute('''
        INSERT INTO likes (post_id, username)
        VALUES (?, ?)''', (post_id, username))
    
    conn.commit()
    conn.close()

# Get comments for a specific post
def get_comments_for_post(post_id):
    conn = sqlite3.connect('posts.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM comments WHERE post_id = ?''', (post_id,))
    comments = cursor.fetchall()
    
    conn.close()
    return comments

# Get the number of likes for a specific post
def get_likes_for_post(post_id):
    conn = sqlite3.connect('posts.db')
    cursor = conn.cursor()

    cursor.execute('''
    SELECT COUNT(*) FROM likes WHERE post_id = ?''', (post_id,))
    likes_count = cursor.fetchone()[0]

    conn.close()
    return likes_count

# Run the function to initialize the database
if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")
