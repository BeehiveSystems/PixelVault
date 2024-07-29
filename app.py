from flask import Flask, request, jsonify, send_from_directory, render_template
from werkzeug.utils import secure_filename
from PIL import Image
import os
import sqlite3
import time

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['THUMBNAIL_FOLDER'] = 'thumbnails'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['THUMBNAIL_FOLDER'], exist_ok=True)

DATABASE_PATH = os.getenv('DATABASE_URL', 'database/database.db')
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)


def init_db():
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

init_db()

@app.route('/')
def index():
    images = []
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT filename FROM images ORDER BY timestamp DESC')
        for row in cursor.fetchall():
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], row[0])
            try:
                file_size = os.path.getsize(file_path)
                size_mb = round(file_size / (1024 * 1024), 2)
                images.append({'filename': row[0], 'size': size_mb})
            except FileNotFoundError:
                # If the file does not exist, skip adding it to the list
                continue
    return render_template('index.html', images=images)


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'image' not in request.files:
        return jsonify(success=False, error="No file part")
    file = request.files['image']
    if file.filename == '':
        return jsonify(success=False, error="No selected file")
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Generate and save thumbnail
    create_thumbnail(filepath, filename)

    # Store image data in the database
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO images (filename) VALUES (?)', (filename,))
        conn.commit()

    return jsonify(success=True, url=f'/uploads/{filename}')

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


@app.route('/thumbnails/<filename>')
def get_thumbnail(filename):
    return send_from_directory(app.config['THUMBNAIL_FOLDER'], filename)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/delete/<filename>', methods=['DELETE'])
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
        return jsonify(success=False, error=str(e))


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['THUMBNAIL_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=5000)
