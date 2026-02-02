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
    return {
        "provider": os.getenv("AI_PROVIDER", "openai"),
        "model": os.getenv("AI_MODEL", "gpt-4o-mini"),
        "openai": len(os.getenv("OPENAI_API_KEY", "") or os.getenv("AI_API_KEY", "")) > 5,
        "anthropic": len(os.getenv("ANTHROPIC_API_KEY", "")) > 5,
        "gemini": len(os.getenv("GEMINI_API_KEY", "")) > 5,
        "openrouter": len(os.getenv("OPENROUTER_API_KEY", "")) > 5
    }

from typing import Optional

@app.post("/settings/save")
def save_settings(
    provider: str = Form(...),
    model: str = Form("gpt-4o-mini"),
    openai_key: Optional[str] = Form(None),
    anthropic_key: Optional[str] = Form(None),
    gemini_key: Optional[str] = Form(None),
    openrouter_key: Optional[str] = Form(None)
):
    # Read existing env
    env_vars = {}
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if "=" in line:
                    key, val = line.strip().split("=", 1)
                    env_vars[key] = val

    # Update vars
    env_vars["AI_PROVIDER"] = provider
    env_vars["AI_MODEL"] = model
    if openai_key is not None: env_vars["OPENAI_API_KEY"] = openai_key
    if anthropic_key is not None: env_vars["ANTHROPIC_API_KEY"] = anthropic_key
    if gemini_key is not None: env_vars["GEMINI_API_KEY"] = gemini_key
    if openrouter_key is not None: env_vars["OPENROUTER_API_KEY"] = openrouter_key
    
    # Write back
    with open(".env", "w") as f:
        for k, v in env_vars.items():
            f.write(f"{k}={v}\n")
    
    # Update process env
    os.environ["AI_PROVIDER"] = provider
    os.environ["AI_MODEL"] = model
    if openai_key: os.environ["OPENAI_API_KEY"] = openai_key
    if anthropic_key: os.environ["ANTHROPIC_API_KEY"] = anthropic_key
    if gemini_key: os.environ["GEMINI_API_KEY"] = gemini_key
    if openrouter_key: os.environ["OPENROUTER_API_KEY"] = openrouter_key
    
    # Hot-reload analyzer
    bot.analyzer.reload_config()
    
    return {"status": "success", "message": f"Settings saved. Provider: {provider}, Model: {model}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
