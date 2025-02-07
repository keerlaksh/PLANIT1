from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.utils import secure_filename, safe_join
import os
import sqlite3
from functools import wraps
import mimetypes

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configurations
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {
    'pdf', 'doc', 'docx', 'ppt', 'pptx', 
    'jpg', 'jpeg', 'png', 'gif',
    'txt', 'csv', 'xlsx', 'xls'
}

# Create uploads folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# File handling helper functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_file_icon(filename):
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    icons = {
        'pdf': '📄',
        'doc': '📝',
        'docx': '📝',
        'ppt': '📊',
        'pptx': '📊',
        'jpg': '🖼️',
        'jpeg': '🖼️',
        'png': '🖼️',
        'gif': '🖼️',
        'txt': '📝',
        'csv': '📊',
        'xlsx': '📊',
        'xls': '📊'
    }
    return icons.get(ext, '📎')

# Database helper functions
def get_db_connection(db_name):
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    return conn

# Login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# User management functions
def check_user_credentials(username, password):
    try:
        conn = get_db_connection('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        return user
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()

def register_user(username, password):
    try:
        conn = get_db_connection('users.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()

# Post management functions
def get_posts_for_subject(subject):
    try:
        conn = get_db_connection('posts.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*, COUNT(l.id) as likes_count 
            FROM posts p 
            LEFT JOIN likes l ON p.id = l.post_id 
            WHERE p.subject = ?
            GROUP BY p.id
            ORDER BY p.id DESC
        ''', (subject,))
        posts = cursor.fetchall()
        return posts
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        conn.close()

def add_post(subject, username, description, uploaded_file):
    try:
        conn = get_db_connection('posts.db')
        cursor = conn.cursor()
        
        file_path = None
        if uploaded_file and uploaded_file.filename:
            if allowed_file(uploaded_file.filename):
                filename = secure_filename(uploaded_file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                uploaded_file.save(file_path)
                # Store only the filename in the database
                file_path = filename
            else:
                raise ValueError("File type not allowed")
        
        cursor.execute(
            'INSERT INTO posts (subject, username, description, file_path) VALUES (?, ?, ?, ?)',
            (subject, username, description, file_path)
        )
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error adding post: {e}")
        return None
    finally:
        conn.close()

def delete_post(post_id, username):
    try:
        conn = get_db_connection('posts.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM posts WHERE id = ? AND username = ?', (post_id, username))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()

# Comment and like functions
def add_comment(post_id, username, comment):
    try:
        conn = get_db_connection('posts.db')
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO comments (post_id, username, comment) VALUES (?, ?, ?)',
            (post_id, username, comment)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()

def toggle_like(post_id, username):
    try:
        conn = get_db_connection('posts.db')
        cursor = conn.cursor()
        # Check if the user has already liked the post
        cursor.execute('SELECT id FROM likes WHERE post_id = ? AND username = ?', (post_id, username))
        like = cursor.fetchone()
        if like:
            # If a like exists, remove it (unlike)
            cursor.execute('DELETE FROM likes WHERE id = ?', (like['id'],))
            conn.commit()
            return "unliked"
        else:
            # If no like exists, add one
            cursor.execute('INSERT INTO likes (post_id, username) VALUES (?, ?)', (post_id, username))
            conn.commit()
            return "liked"
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()


def get_comments_for_post(post_id):
    try:
        conn = get_db_connection('posts.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM comments WHERE post_id = ? ORDER BY id DESC', (post_id,))
        comments = cursor.fetchall()
        return comments
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        conn.close()

def get_likes_for_post(post_id):
    try:
        conn = get_db_connection('posts.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM likes WHERE post_id = ?', (post_id,))
        return cursor.fetchone()[0]
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return 0
    finally:
        conn.close()

# Routes
@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        flash('Please provide both username and password')
        return redirect(url_for('home'))

    user = check_user_credentials(username, password)
    if user:
        session['username'] = username
        return redirect(url_for('domain_page'))
    flash('Invalid credentials, please try again.')
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not all([username, password, confirm_password]):
            flash('All fields are required')
            return redirect(url_for('register'))
            
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('register'))
        
        if register_user(username, password):
            flash('Registration successful! Please login.')
            return redirect(url_for('home'))
        flash('Registration failed')
        return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/domains')
@login_required
def domain_page():
    return render_template('domains.html')

@app.route('/subject/<subject>', methods=['GET', 'POST'])
@login_required
def subject_page(subject):
    if request.method == 'POST':
        description = request.form.get('description')
        file = request.files.get('file')
        
        if not description:
            flash('Description is required')
            return redirect(url_for('subject_page', subject=subject))
        
        try:
            post_id = add_post(subject, session['username'], description, file)
            if post_id:
                flash('Post created successfully')
            else:
                flash('Error creating post')
        except ValueError as e:
            flash(str(e))
        
        return redirect(url_for('subject_page', subject=subject))

    posts = get_posts_for_subject(subject)
    return render_template('subject.html',
                         subject=subject,
                         posts=posts,
                         get_comments_for_post=get_comments_for_post,
                         get_likes_for_post=get_likes_for_post,
                         get_file_icon=get_file_icon)

@app.route('/subject/<subject>/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post_route(subject, post_id):
    if delete_post(post_id, session['username']):
        flash('Post deleted successfully')
    else:
        flash('Error deleting post')
    return redirect(url_for('subject_page', subject=subject))

@app.route('/subject/<subject>/add_comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment_route(subject, post_id):
    comment = request.form.get('comment')
    if not comment:
        flash('Comment is required')
        return redirect(url_for('subject_page', subject=subject))
        
    if add_comment(post_id, session['username'], comment):
        flash('Comment added successfully')
    else:
        flash('Error adding comment')
    return redirect(url_for('subject_page', subject=subject))


@app.route('/subject/<subject>/toggle_like/<int:post_id>', methods=['POST'])
@login_required
def toggle_like_route(subject, post_id):
    result = toggle_like(post_id, session['username'])
    if result == "liked":
        flash("You liked this post!")
    elif result == "unliked":
        flash("You unliked this post!")
    else:
        flash("Error toggling like.")
    return redirect(url_for('subject_page', subject=subject))


@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    try:
        # Ensure the file exists
        file_path = safe_join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            flash('File not found')
            return redirect(request.referrer or url_for('domain_page'))
        
        # Get the correct MIME type
        mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        
        return send_from_directory(
            app.config['UPLOAD_FOLDER'],
            filename,
            mimetype=mime_type,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        print(f"Error downloading file: {e}")
        flash('Error downloading file')
        return redirect(request.referrer or url_for('domain_page'))

if __name__ == '__main__':
    app.run(debug=True)
