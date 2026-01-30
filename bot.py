import hashlib
import os
import shutil
from datetime import datetime
from db import DBHandler
from ai_analyzer import AIAnalyzer
from dotenv import load_dotenv

load_dotenv()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./data/uploads")
DB_PATH = os.getenv("DB_PATH", "./data/bot.db")

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

db = DBHandler(DB_PATH)
analyzer = AIAnalyzer()

def generate_hash(file_bytes):
    # Spec: hash_id = hashlib.sha256(file_content + timestamp).hexdigest()[:16]
    timestamp = str(datetime.now().timestamp()).encode('utf-8')
    return hashlib.sha256(file_bytes + timestamp).hexdigest()[:16]

def save_file(file_path, source="CLI"):
    """Saves a file from a local path."""
    with open(file_path, "rb") as f:
        content = f.read()
    
    filename = os.path.basename(file_path)
    hash_id = generate_hash(content)
    
    # Store with extension
    _, ext = os.path.splitext(filename)
    dest_filename = f"{hash_id}{ext}"
    dest_path = os.path.join(UPLOAD_DIR, dest_filename)
    
    # Write content to dest
    with open(dest_path, "wb") as f_out:
        f_out.write(content)
        
    # Add to DB
    db.add_file(hash_id, filename, source, dest_path)
    return hash_id

def save_file_content(content, filename, source="Web"):
    """Saves file content directly (bytes)."""
    hash_id = generate_hash(content)
    
    _, ext = os.path.splitext(filename)
    dest_filename = f"{hash_id}{ext}"
    dest_path = os.path.join(UPLOAD_DIR, dest_filename)
    
    with open(dest_path, "wb") as f_out:
        f_out.write(content)
        
    db.add_file(hash_id, filename, source, dest_path)
    return hash_id

def list_files():
    return db.list_files()

def analyze_file(hash_id, query):
    file_record = db.get_file(hash_id)
    if not file_record:
        return "File not found."
    
    path = file_record['file_path']
    return analyzer.analyze(path, query)

def edit_file_dataset(hash_id, instruction):
    file_record = db.get_file(hash_id)
    if not file_record:
        return None, "File not found."
    
    src_path = file_record['file_path']
    filename = file_record['filename']
    
    # Create temp path
    temp_path = os.path.join(UPLOAD_DIR, "temp_edit.xlsx")
    
    success, msg = analyzer.edit(src_path, instruction, temp_path)
    if not success:
        return None, msg
        
    # Read back and save properly
    with open(temp_path, "rb") as f:
        content = f.read()
        
    # Create new filename "edited_<oldname>"
    new_filename = f"edited_{filename}"
    new_hash = save_file_content(content, new_filename, source="AI-Edit")
    
    # Clean up
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
    return new_hash, msg
