from fastapi import FastAPI, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import bot
import uvicorn
import os

app = FastAPI(title="Excel Analysis Bot", version="1.0")

# Ensure static directory exists
os.makedirs("static", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

from typing import List

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    results = []
    for file in files:
        if not file.filename:
            continue
        content = await file.read()
        hash_id = bot.save_file_content(content, file.filename, source="Web")
        results.append({"hash_id": hash_id, "filename": file.filename})
    return results

@app.get("/list")
def list_files():
    return bot.list_files()

@app.post("/query")
def query_file(hash_id: str = Form(...), query: str = Form(...)):
    response = bot.analyze_file(hash_id, query)
    return {"response": response}

@app.post("/edit")
def edit_file(hash_id: str = Form(...), instruction: str = Form(...)):
    new_hash, msg = bot.edit_file_dataset(hash_id, instruction)
    if new_hash:
        return {"status": "success", "new_hash": new_hash, "message": msg}
    else:
        return {"status": "error", "message": msg}

@app.get("/settings/status")
def get_settings_status():
    api_key = os.getenv("AI_API_KEY", "")
    return {"has_api_key": len(api_key) > 5}

@app.post("/settings/save")
def save_settings(api_key: str = Form(...)):
    # Simple .env writer
    env_lines = []
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            env_lines = f.readlines()
    
    new_lines = []
    key_found = False
    for line in env_lines:
        if line.startswith("AI_API_KEY="):
            new_lines.append(f"AI_API_KEY={api_key}\n")
            key_found = True
        else:
            new_lines.append(line)
    
    if not key_found:
        new_lines.append(f"\nAI_API_KEY={api_key}\n")
        
    with open(".env", "w") as f:
        f.writelines(new_lines)
    
    # Update local process env for immediate use
    os.environ["AI_API_KEY"] = api_key
    bot.analyzer.api_key = api_key # Update instance directly if possible or trigger reload
    bot.analyzer.client = bot.OpenAI(api_key=api_key) # Re-init client
    
    return {"status": "success", "message": "API Key saved. You can now use AI features."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
