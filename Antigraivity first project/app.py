from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='public', static_url_path='')

DATA_FILE = os.path.join('data', 'content.json')
UPLOAD_FOLDER = os.path.join('public', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def read_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    content = read_data()
    return render_template('index.html', content=content)

@app.route('/admin')
def admin():
    content = read_data()
    return render_template('admin.html', content=content)

@app.route('/api/update', methods=['POST'])
def update_content():
    new_content = request.form.to_dict(flat=False)
    
    # Process nested keys (e.g., hero[title] -> hero: { title: ... })
    processed_content = {}
    for key, value in new_content.items():
        # value is a list because of flat=False
        val = value[0]
        
        if '[' in key and ']' in key:
            section, field = key.replace(']', '').split('[')
            if section not in processed_content:
                processed_content[section] = {}
            processed_content[section][field] = val
        else:
            processed_content[key] = val
            
    # Merge with existing data
    current_content = read_data()
    
    # Deep merge manually for the sections we know
    for section, fields in processed_content.items():
        if section in current_content and isinstance(current_content[section], dict):
            current_content[section].update(fields)
        else:
            current_content[section] = fields
            
    write_data(current_content)
    return redirect(url_for('admin'))

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'image' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({'filePath': f'/uploads/{filename}'})
    return jsonify({'error': 'File type not allowed'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=3000)
