from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import json
import traceback

from .ml_processor import process_pdf_files

app = FastAPI(title="Veritas ML Backend")

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Since it's local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "service": "Veritas ML Backend"}

@app.post("/api/process-evidence")
async def process_evidence(files: List[UploadFile] = File(...)):
    print(f"Received {len(files)} files for processing.")
    
    # Process files
    try:
        # In a real app we would save these to a temp dir or process in memory
        # Here we process them in memory using PyPDF2
        graph_data = process_pdf_files(files)
        return graph_data
    except Exception as e:
        print(f"Error processing files: {e}")
        traceback.print_exc()
        return {"nodes": [], "links": []}
