#!/usr/bin/env python3
"""
Script to process uploaded files and send them to the zoning backend.
This runs as a background process to work around Flask routing issues.
"""

print("Starting process_uploads.py script...")

import os
import time
import requests
import shutil
from pathlib import Path

UPLOAD_DIR = '/app/uploads'
PROCESSED_DIR = '/app/processed'
ZONING_API_URL = 'http://host.docker.internal:8000/api/documents/upload'

def ensure_dirs():
    """Ensure required directories exist"""
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)

def process_file(filepath):
    """Process a single file and send to backend"""
    try:
        filename = os.path.basename(filepath)

        # Extract municipality from filename if possible (format: original_name_uuid.pdf)
        # For now, use a default municipality
        municipality = "Unknown"
        state = "NJ"

        print(f"Processing file: {filename}")

        # Send to backend
        try:
            with open(filepath, 'rb') as f:
                files = {'file': (filename, f, 'application/pdf')}
                data = {
                    'municipality': municipality,
                    'state': state
                }

                response = requests.post(ZONING_API_URL, files=files, data=data, timeout=60)

                print(f"Response status: {response.status_code}")
                print(f"Response headers: {response.headers}")
                print(f"Response content: {response.text}")

                if response.status_code == 200:
                    print(f"✅ Successfully sent {filename} to backend")
                    return True
                else:
                    print(f"❌ Failed to send {filename}: HTTP {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
        except Exception as e:
            print(f"❌ Error sending {filename} to backend: {e}")
            return False

    except Exception as e:
        print(f"❌ Error processing {filename}: {e}")
        return False

def main():
    """Main processing loop"""
    ensure_dirs()
    print("Starting upload processor...")

    processed_files = set()

    while True:
        try:
            # Find new files in upload directory
            upload_path = Path(UPLOAD_DIR)
            files_found = list(upload_path.glob('*'))
            print(f"Checking for files... Found {len([f for f in files_found if f.is_file()])} files")

            for file_path in files_found:
                if file_path.is_file():
                    file_str = str(file_path)
                    print(f"Checking file: {file_path.name}, in processed: {file_str in processed_files}")

                    if file_str not in processed_files:
                        print(f"Found new file: {file_path}")

                        result = process_file(file_str)
                        print(f"process_file returned: {result}")

                        if result:
                            # Move to processed directory on success
                            try:
                                processed_path = Path(PROCESSED_DIR) / file_path.name
                                print(f"About to move {file_path} to {processed_path}")
                                shutil.move(str(file_path), str(processed_path))
                                processed_files.add(file_str)
                                print(f"Moved {file_path.name} to processed directory")
                            except Exception as e:
                                print(f"Error moving file: {e}")
                        else:
                            # Keep in uploads for retry
                            print(f"Keeping {file_path.name} for retry")

            time.sleep(5)  # Check every 5 seconds

        except KeyboardInterrupt:
            print("Stopping upload processor...")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
