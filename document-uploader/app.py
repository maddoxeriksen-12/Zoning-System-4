"""
Document Upload Web Application with Zoning Processing
Uploads documents locally and sends them to zoning backend for Grok LLM processing.
"""

import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, jsonify
from werkzeug.utils import secure_filename
import json
import requests

print("MODULE LOADING - app.py is being imported")

# Test if file is being executed during route calls
print("FILE_EXECUTION_TEST")

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'

# Add a before_request handler to debug
def debug_request():
    if request.path in ['/upload', '/test-post'] and request.method == 'POST':
        with open('/app/global_debug.log', 'a') as f:
            f.write(f"BEFORE_REQUEST: {request.method} {request.path}\n")
            f.flush()
        print(f"BEFORE_REQUEST: {request.method} {request.path}", flush=True)

app.before_request(debug_request)

# Configuration
UPLOAD_FOLDER = '/app/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'tiff', 'zip'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Zoning Backend Configuration
ZONING_BACKEND_URL = os.getenv('ZONING_BACKEND_URL', 'http://host.docker.internal:8000')
ZONING_API_UPLOAD_ENDPOINT = 'http://backend:8000/api/documents/upload'  # Fixed endpoint path

print(f"DEBUG: ZONING_BACKEND_URL = {ZONING_BACKEND_URL}")
print(f"DEBUG: ZONING_API_UPLOAD_ENDPOINT = {ZONING_API_UPLOAD_ENDPOINT}")
# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def send_to_zoning_backend(filepath, original_filename, municipality=None, county=None, state="NJ"):
    """Send uploaded file to zoning backend for Grok LLM processing"""
    print(f"SEND_TO_ZONING_BACKEND_STARTED: {original_filename}")
    try:
        print(f"DEBUG: Attempting to send {original_filename} to {ZONING_API_UPLOAD_ENDPOINT}")

        with open(filepath, 'rb') as f:
            files = {'file': (original_filename, f, 'application/pdf')}

            # Prepare form data
            data = {}
            if municipality:
                data['municipality'] = municipality
            if county:
                data['county'] = county
            data['state'] = state

            print(f"DEBUG: Sending file with data: {data}")

            # Send to zoning backend
            response = requests.post(
                ZONING_API_UPLOAD_ENDPOINT,
                files=files,
                data=data,
                timeout=30
            )

            print(f"DEBUG: Response status: {response.status_code}")
            print(f"DEBUG: Response text: {response.text[:200]}...")

            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"DEBUG: Success response: {result}")
                    return True, result, None
                except:
                    print("DEBUG: Could not parse JSON response")
                    return True, {"message": "File uploaded successfully"}, None
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                print(f"DEBUG: Error response: {error_msg}")
                return False, None, error_msg

    except requests.exceptions.RequestException as e:
        error_msg = f"Connection error: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return False, None, error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"DEBUG: {error_msg}")
        import traceback
        traceback.print_exc()
        return False, None, error_msg

def get_file_info():
    """Get information about all uploaded files"""
    files = []
    if os.path.exists(UPLOAD_FOLDER):
        for filename in os.listdir(UPLOAD_FOLDER):
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(filepath):
                stat = os.stat(filepath)
                files.append({
                    'name': filename,
                    'size': stat.st_size,
                    'size_human': f"{stat.st_size / (1024*1024):.1f} MB" if stat.st_size > 1024*1024 else f"{stat.st_size / 1024:.1f} KB",
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'type': filename.rsplit('.', 1)[1].lower() if '.' in filename else 'unknown'
                })
    return sorted(files, key=lambda x: x['modified'], reverse=True)

@app.route('/')
def index():
    """Main page with file upload and list"""
    files = get_file_info()
    return render_template('index.html', files=files)

@app.route('/test-backend')
def test_backend():
    """Test endpoint to check if backend connection works"""
    print("TEST_BACKEND_CALLED")
    import sys
    sys.stdout.flush()
    try:
        response = requests.get("http://host.docker.internal:8000/health", timeout=5)
        return f"Backend response: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Backend error: {str(e)}"

@app.route('/test-route')
def test_route():
    """Simple test route"""
    print("TEST_ROUTE_CALLED")
    return "Flask is working! Route called successfully."

@app.route('/test-post', methods=['POST'])
def test_post():
    """Test POST route"""
    with open('/app/test_debug.log', 'a') as f:
        f.write("TEST_POST_CALLED\n")
        f.flush()
    print("TEST_POST_CALLED", flush=True)
    return f"POST request received: {request.method}"

print("REGISTERING UPLOAD ROUTE")
@app.route('/upload-test', methods=['POST'])
def upload_test():
    """Test upload function"""
    with open('/tmp/upload_test.txt', 'w') as f:
        f.write("UPLOAD_TEST_CALLED\n")
        f.flush()
    return "Upload test successful"

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and send to zoning backend for processing"""
    with open('/tmp/function_start.txt', 'w') as f:
        f.write("FUNCTION_STARTED\n")
        f.flush()

    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            flash('❌ No file selected', 'error')
            return redirect(url_for('index'))

        file = request.files['file']
        if file.filename == '':
            flash('❌ No file selected', 'error')
            return redirect(url_for('index'))

        # Get form data
        municipality = request.form.get('municipality', '').strip()
        county = request.form.get('county', '').strip()
        state = request.form.get('state', 'NJ').strip() or 'NJ'

        # Validate file type
        allowed = allowed_file(file.filename)
        with open('/tmp/validation_debug.txt', 'w') as f:
            f.write(f"file.filename: {file.filename}\n")
            f.write(f"allowed_file result: {allowed}\n")
            f.write(f"ALLOWED_EXTENSIONS: {ALLOWED_EXTENSIONS}\n")
            f.flush()

        if not allowed:
            flash('❌ Invalid file type. Allowed: PDF, DOC, DOCX, TXT, JPG, PNG, TIFF, ZIP', 'error')
            return redirect(url_for('index'))

        # Save file locally first
        import uuid
        from werkzeug.utils import secure_filename

        original_name = secure_filename(file.filename)

        # Debug: check filename processing
        with open('/tmp/filename_debug.txt', 'w') as f:
            f.write(f"file.filename: {file.filename}\n")
            f.write(f"original_name: {original_name}\n")
            f.flush()

        name_parts = original_name.rsplit('.', 1)
        unique_name = f"{name_parts[0]}_{uuid.uuid4().hex[:8]}.{name_parts[1]}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_name)

        # Debug: log the filepath before saving
        with open('/tmp/filepath_debug.txt', 'w') as f:
            f.write(f"UPLOAD_FOLDER: {UPLOAD_FOLDER}\n")
            f.write(f"unique_name: {unique_name}\n")
            f.write(f"filepath: {filepath}\n")
            f.flush()

        file.save(filepath)

        # Debug: check if file was saved
        with open('/tmp/save_debug.txt', 'a') as f:
            f.write(f"Saved file to: {filepath}\n")
            f.write(f"File exists: {os.path.exists(filepath)}\n")
            f.flush()

        # Send to backend for processing
        success, result, error_msg = send_to_zoning_backend(filepath, original_name, municipality, county, state)

        if success:
            flash(f'✅ File "{original_name}" uploaded successfully! It will be processed for zoning analysis shortly.', 'success')
        else:
            flash(f'✅ File "{original_name}" saved locally, but backend processing failed: {error_msg}', 'warning')

        return redirect(url_for('index'))

    except Exception as e:
        flash(f'❌ Unexpected error: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    """Download a file"""
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    """Delete a file"""
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        flash(f'File "{filename}" deleted successfully', 'success')
    else:
        flash('File not found', 'error')
    return redirect(url_for('index'))

@app.route('/api/files')
def api_files():
    """JSON API for file listing"""
    files = get_file_info()
    return jsonify(files)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

print("APP.PY LOADED COMPLETELY")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
