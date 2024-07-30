from flask import Flask, request, jsonify, send_from_directory, render_template, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
import os
import re
import sqlite3
from werkzeug.utils import secure_filename
from PIL import Image
# Debug
import traceback

# More debug

#print(f"UPLOAD_FOLDER path: {app.config['UPLOAD_FOLDER']}")
#print(f"THUMBNAIL_FOLDER path: {app.config['THUMBNAIL_FOLDER']}")
#print(f"UPLOAD_FOLDER exists: {os.path.exists(app.config['UPLOAD_FOLDER'])}")
#print(f"THUMBNAIL_FOLDER exists: {os.path.exists(app.config['THUMBNAIL_FOLDER'])}")
#print(f"UPLOAD_FOLDER writable: {os.access(app.config['UPLOAD_FOLDER'], os.W_OK)}")
#print(f"THUMBNAIL_FOLDER writable: {os.access(app.config['THUMBNAIL_FOLDER'], os.W_OK)}")

# NOTE: BE SURE TO REMOVE THE DROP TABLE

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with your secret key
csrf = CSRFProtect(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')

DATABASE_PATH = os.getenv('DATABASE_URL')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['THUMBNAIL_FOLDER'] = 'thumbnails'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['THUMBNAIL_FOLDER'], exist_ok=True)
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

# Initialize Flask-Login and Flask-Bcrypt
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
bcrypt = Bcrypt(app)

# User class
class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email
# Load user
@login_manager.user_loader
def load_user(user_id):
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        if user:
            return User(id=user[0], username=user[1], email=user[2])
    return None


def init_db():
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('DROP TABLE IF EXISTS users')  # Only for development
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        conn.commit()

init_db()

def validate_password(password):
    # Define the regular expressions for each character type
    lower = re.search(r'[a-z]', password)
    upper = re.search(r'[A-Z]', password)
    digit = re.search(r'\d', password)
    special = re.search(r'[@$!%*?&]', password)

    # Count the number of character types present
    character_types = sum(bool(x) for x in [lower, upper, digit, special])

    # Check if the password meets the requirements
    if len(password) < 8 or character_types < 3:
        return jsonify(success=False, message='Password must be at least 8 characters long and include at least three of the following: uppercase letter, lowercase letter, number, special character.')

    return True  # If the password is valid

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm-password']

        # Validate password
        if not validate_password(password):
            return validate_password(password)

        if password != confirm_password:
            return jsonify(success=False, message='Passwords do not match.')

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', (username, email, hashed_password))
                conn.commit()
            return jsonify(success=True, message='Signup successful.', redirect='/login')
        except sqlite3.IntegrityError:
            return jsonify(success=False, message='Username or email already exists.')
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        print(f"Login attempt for email: {email}")  # Debug print

        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, email, password FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            if user and bcrypt.check_password_hash(user[3], password):
                user_obj = User(id=user[0], username=user[1], email=user[2])
                login_user(user_obj)
                print(f"User {user[1]} logged in successfully")  # Debug print

                next_page = request.args.get('next')
                redirect_url = next_page or url_for('index')
                print(f"Redirecting to: {redirect_url}") # Debug print
                return redirect(redirect_url)
            else:
                print("Invalid email or password")  # Debug print
                flash('Invalid email or password.')
                return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    print(f"User {current_user.username} accessed the index page")  # Debug print
    images = []
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT filename FROM images WHERE user_id = ? ORDER BY timestamp DESC', (current_user.id,))
        rows = cursor.fetchall()
    print(f"Found {len(rows)} images for user")  # Debug print
    for row in rows:
        filename = row[0]
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            file_size = os.path.getsize(file_path)
            size_mb = round(file_size / (1024 * 1024), 2)
            images.append({'filename': filename, 'size': size_mb})
        except FileNotFoundError:
            print(f"File not found: {file_path}")  # Debug print
            continue
    print(f"Rendering index.html with {len(images)} images")  # Debug print
    return render_template('index.html', images=images)


@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    print("Upload function called")  # Debug print
    try:
        if 'image' not in request.files:
            print("No file part in request")  # Debug print
            return jsonify(success=False, message="No file part"), 400

        file = request.files['image']
        print(f"File received: {file.filename}")  # Debug print

        if file.filename == '':
            print("No selected file")  # Debug print
            return jsonify(success=False, message="No selected file"), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        print(f"Saving file to: {filepath}")  # Debug print

        file.save(filepath)
        print("File saved successfully")  # Debug print

        # Generate and save thumbnail
        create_thumbnail(filepath, filename)
        print("Thumbnail created")  # Debug print

        # Store image data in the database
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO images (filename, user_id) VALUES (?, ?)', (filename, current_user.id))
            conn.commit()
        print("Database entry created")  # Debug print

        # Use BASE_URL to construct the full URL
        BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')
        file_url = f"{BASE_URL}/uploads/{filename}"

        return jsonify(success=True, url=file_url)
    except Exception as e:
        print(f"Error during file upload: {str(e)}")  # Log the error
        return jsonify(success=False, message=str(e)), 500




def create_thumbnail(filepath, filename):
    try:
        img = Image.open(filepath)
        img.thumbnail((200, 200))

        # Convert image mode to 'RGB' to ensure compatibility with JPEG format
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Save thumbnail in JPEG format
        base, _ = os.path.splitext(filename)
        thumbnail_filename = f"{base}.jpg"
        thumbnail_path = os.path.join(app.config['THUMBNAIL_FOLDER'], thumbnail_filename)
        img.save(thumbnail_path, "JPEG")
    except Exception as e:
        print(f"Error creating thumbnail for {filename}: {e}")

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/thumbnails/<filename>')
def get_thumbnail(filename):
    return send_from_directory(app.config['THUMBNAIL_FOLDER'], filename)



@app.route('/delete/<filename>', methods=['DELETE'])
@login_required
# @csrf.exempt # Only if I want to exempt this from CSRF
def delete_file(filename):
    try:
        # Delete the original file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            os.remove(filepath)

        # Delete the thumbnail
        thumbnail_path = os.path.join(app.config['THUMBNAIL_FOLDER'], filename.rsplit('.', 1)[0] + '.jpg')
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)

        # Remove the record from the database
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM images WHERE filename = ?', (filename,))
            conn.commit()

        return jsonify(success=True)
    except Exception as e:
        print(f"Error deleting file: {str(e)}") # Log the error
        return jsonify(success=False, error=str(e))

@app.errorhandler(404)
def page_not_found(e):
    print(f"404 error: {request.url}")  # Debug print
    return "404 Not Found", 404

@app.errorhandler(Exception)
def handle_exception(e):
    print(f"Unhandled exception: {str(e)}")  # Debug print
    print(traceback.format_exc()) # Debug, get rid of this
    return "An error occurred", 500

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['THUMBNAIL_FOLDER'], exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
