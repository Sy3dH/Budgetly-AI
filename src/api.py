# api.py
import os
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from tempfile import NamedTemporaryFile
from pathlib import Path
from mimetypes import guess_type
import shutil

from input.image_handler import load_image
from extraction.easyocr_extractor import extract_text_easyocr
from speech.whisper_transcriber import transcribe_audio
from structure.structure_llm import (
    parse_receipt_with_gemini,
    parse_receipt_image_with_gemini
)
from chat.chat import (
    natural_language_to_sql,
    extract_sql,
    execute_safe_query,
    generate_natural_language_response,
    format_query_results
)

load_dotenv()
app = FastAPI(title="Receipt Processor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for NL2SQL
class NLQueryRequest(BaseModel):
    question: str


class NLQueryResponse(BaseModel):
    original_question: str
    generated_sql: str
    natural_language_response: str
    raw_results: list = None
    error: str = None


def detect_file_type(file_path: str) -> str:
    mime, _ = guess_type(file_path)
    if mime:
        if mime.startswith("image"):
            return "image"
        elif mime.startswith("audio"):
            return "audio"
    ext = Path(file_path).suffix.lower()
    if ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
        return "image"
    elif ext in [".mp3", ".wav", ".m4a", ".ogg"]:
        return "audio"
    return "unknown"


@app.post("/process")
async def process_receipt(
        file: UploadFile = File(...),
        e2e: bool = Form(False)
):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not set.")

    # Save uploaded file to temp path
    suffix = Path(file.filename).suffix
    with NamedTemporaryFile(delete=False, suffix=suffix) as temp:
        shutil.copyfileobj(file.file, temp)
        temp_path = temp.name

    file_type = detect_file_type(temp_path)

    try:
        if file_type == "image":
            if e2e:
                receipts = parse_receipt_image_with_gemini(temp_path, api_key)
            else:
                image = load_image(temp_path)
                ocr_results = extract_text_easyocr(image)
                text = "\n".join([t for t, _ in ocr_results])
                receipts = parse_receipt_with_gemini(text, api_key)

        elif file_type == "audio":
            text = transcribe_audio(temp_path)
            receipts = parse_receipt_with_gemini(text, api_key)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type.")

        # Return structured receipt(s) as JSON
        return JSONResponse([r.model_dump() for r in receipts])

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {e}")

    finally:
        os.remove(temp_path)


@app.post("/query", response_model=NLQueryResponse)
async def query_database(request: NLQueryRequest):
    """
    Endpoint to query the database using natural language.
    Converts natural language to SQL, executes it safely, and returns a natural language response.
    """
    try:
        # Generate SQL from natural language
        sql = natural_language_to_sql(request.question)
        cleaned_sql = extract_sql(sql)

        if not cleaned_sql:
            raise HTTPException(status_code=400, detail="Unable to generate valid SQL from the question.")

        # Execute the query safely
        try:
            results, nl_response = execute_safe_query(cleaned_sql, request.question)

            if results is None:
                return NLQueryResponse(
                    original_question=request.question,
                    generated_sql=cleaned_sql,
                    natural_language_response="Sorry, I couldn't execute the query due to a database error.",
                    error="Database execution failed"
                )

            return NLQueryResponse(
                original_question=request.question,
                generated_sql=cleaned_sql,
                natural_language_response=nl_response,
                raw_results=results
            )

        except ValueError as ve:
            # This handles the "Only read-only queries are allowed" error
            return NLQueryResponse(
                original_question=request.question,
                generated_sql=cleaned_sql,
                natural_language_response="I can only execute read-only queries for security reasons. Please ask questions that don't require data modification.",
                error=str(ve)
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing error: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Receipt Processor API with NL2SQL"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)