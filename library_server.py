from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
import os
import uuid
import json
from typing import Dict, List
import shutil

app = FastAPI(title="Cosmic Library Backend")

# Directory to store .cosmic files
STORAGE_DIR = "library_storage"
INDEX_FILE = "library_index.json"

# Ensure storage directory exists
os.makedirs(STORAGE_DIR, exist_ok=True)

# Initialize or load the library index
def load_index() -> Dict[str, Dict]:
    if os.path.exists(INDEX_FILE):
        try:
            with open(INDEX_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading index: {e}")
            return {}
    return {}

def save_index(index: Dict[str, Dict]):
    with open(INDEX_FILE, "w") as f:
        json.dump(index, f, indent=2)

@app.post("/upload")
async def upload_scratchpad(
    file: UploadFile = File(...),
    title: str = Form(...),
    author: str = Form(...),
    description: str = Form(...)
):
    """
    Upload a new scratchpad to the library.
    """
    try:
        # Generate a unique ID for the scratchpad
        scratchpad_id = str(uuid.uuid4())

        # Save the file content
        file_path = os.path.join(STORAGE_DIR, f"{scratchpad_id}.cosmic")
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Update the index with metadata
        index = load_index()
        index[scratchpad_id] = {
            "title": title,
            "author": author,
            "description": description,
            "filename": f"{scratchpad_id}.cosmic"
        }
        save_index(index)

        return JSONResponse(content={"uuid": scratchpad_id}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading scratchpad: {str(e)}")

@app.get("/list", response_model=List[Dict])
async def list_scratchpads():
    """
    List all available scratchpads with their metadata.
    """
    index = load_index()
    result = []
    for scratchpad_id, metadata in index.items():
        result.append({
            "uuid": scratchpad_id,
            "title": metadata["title"],
            "author": metadata["author"],
            "description": metadata["description"]
        })
    return result

@app.get("/scratchpad/{uuid}")
async def get_scratchpad(uuid: str):
    """
    Retrieve a specific scratchpad by its UUID.
    """
    index = load_index()
    if uuid not in index:
        raise HTTPException(status_code=404, detail="Scratchpad not found")

    file_path = os.path.join(STORAGE_DIR, f"{uuid}.cosmic")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Scratchpad file not found")

    try:
        with open(file_path, "r") as f:
            content = json.load(f)
        return JSONResponse(content=content, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading scratchpad: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
