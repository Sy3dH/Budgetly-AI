# main.py
import os
import sys
from pathlib import Path
from mimetypes import guess_type
from dotenv import load_dotenv
from argparse import ArgumentParser

from input.image_handler import load_image
from extraction.easyocr_extractor import extract_text_easyocr
from speech.whisper_transcriber import transcribe_audio
from structure.structure_llm import (
    parse_receipt_with_gemini,
    parse_receipt_image_with_gemini  # <-- new import
)

load_dotenv()

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

def main():
    parser = ArgumentParser(description="Process a receipt from an image or audio file.")
    parser.add_argument("input_file", help="Path to the input image or audio file.")
    parser.add_argument("--e2e", action="store_true", help="Use Gemini directly on the image for E2E extraction.")
    args = parser.parse_args()

    input_path = args.input_file
    use_e2e = args.e2e

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        sys.exit(1)

    file_type = detect_file_type(input_path)

    if file_type == "image":
        print(f"Processing image: {input_path}")
        if use_e2e:
            print("Using Gemini for E2E image parsing...")
            try:
                receipts = parse_receipt_image_with_gemini(input_path, api_key)
                print("\n== Structured Receipt Data ==")
                for receipt in receipts:
                    print(receipt.model_dump_json(indent=2))
            except Exception as e:
                print(f"Error while parsing image with Gemini: {e}")
        else:
            image = load_image(input_path)
            ocr_results = extract_text_easyocr(image)
            text = "\n".join([t for t, _ in ocr_results])
            print("\n== Raw Extracted Text ==")
            print(text)

            print("\n== Structured Receipt Data ==")
            try:
                receipts = parse_receipt_with_gemini(text, api_key)
                for receipt in receipts:
                    print(receipt.model_dump_json(indent=2))
            except Exception as e:
                print(f"Error while parsing text with Gemini: {e}")

    elif file_type == "audio":
        print(f"Processing audio: {input_path}")
        text = transcribe_audio(input_path)
        print("\n== Raw Transcribed Text ==")
        print(text)

        print("\n== Structured Receipt Data ==")
        try:
            receipts = parse_receipt_with_gemini(text, api_key)
            for receipt in receipts:
                print(receipt.model_dump_json(indent=2))
        except Exception as e:
            print(f"Error while parsing audio transcript with Gemini: {e}")

    else:
        print("Unsupported file type.")
        sys.exit(1)

if __name__ == "__main__":
    main()
