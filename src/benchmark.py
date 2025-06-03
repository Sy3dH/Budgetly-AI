import os
import time
import json
import csv
from dotenv import load_dotenv
from input.image_handler import load_image
from extraction.easyocr_extractor import extract_text_easyocr
from structure.structure_llm import (
    parse_receipt_with_gemini,
    parse_receipt_image_with_gemini
)

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

BASE_DIR = "./POC/src/sample_data"
EXCLUDED_LANGUAGES = {"English"}
OUTPUT_JSON = "./multi_lang_benchmark_results.json"
OUTPUT_CSV = "./multi_lang_benchmark_summary.csv"

results = []
csv_rows = []


def summarize_receipt(receipts):
    if not receipts or len(receipts) == 0:
        return {"vendor": "", "total": "", "num_items": 0, "items": ""}

    r = receipts[0]  # Assume single receipt per image
    items = r.get("items", [])
    item_names = ", ".join([item["name"] for item in items[:3]])  # limit to 3 for brevity
    return {
        "vendor": r.get("vendor", ""),
        "total": r.get("total", ""),
        "num_items": len(items),
        "items": item_names + ("..." if len(items) > 3 else "")
    }


for language_folder in sorted(os.listdir(BASE_DIR)):
    if language_folder in EXCLUDED_LANGUAGES:
        continue

    language_path = os.path.join(BASE_DIR, language_folder)
    if not os.path.isdir(language_path):
        continue

    for filename in sorted(os.listdir(language_path)):
        if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        full_path = os.path.join(language_path, filename)
        print(f"Processing [{language_folder}] {filename}...")

        result_entry = {
            "language": language_folder,
            "filename": filename,
            "e2e_latency_sec": None,
            "ocr_latency_sec": None,
            "e2e_result": None,
            "ocr_result": None,
            "e2e_error": None,
            "ocr_error": None
        }

        # E2E parse
        try:
            start = time.perf_counter()
            receipts = parse_receipt_image_with_gemini(full_path, API_KEY)
            end = time.perf_counter()
            result_entry["e2e_latency_sec"] = round(end - start, 3)
            result_entry["e2e_result"] = [r.model_dump() for r in receipts]
        except Exception as e:
            result_entry["e2e_error"] = str(e)

        # OCR + Gemini parse
        try:
            image = load_image(full_path)
            start = time.perf_counter()
            ocr_results = extract_text_easyocr(image)
            text = "\n".join([t for t, _ in ocr_results])
            receipts = parse_receipt_with_gemini(text, API_KEY)
            end = time.perf_counter()
            result_entry["ocr_latency_sec"] = round(end - start, 3)
            result_entry["ocr_result"] = [r.model_dump() for r in receipts]
        except Exception as e:
            result_entry["ocr_error"] = str(e)

        results.append(result_entry)

        # Summarize for CSV
        e2e_summary = summarize_receipt(result_entry["e2e_result"])
        ocr_summary = summarize_receipt(result_entry["ocr_result"])

        csv_rows.append({
            "Language": language_folder,
            "Filename": filename,
            "E2E Latency (s)": result_entry["e2e_latency_sec"],
            "OCR Latency (s)": result_entry["ocr_latency_sec"],
            "E2E Error": result_entry["e2e_error"] or "",
            "OCR Error": result_entry["ocr_error"] or "",
            "E2E Success": int(result_entry["e2e_result"] is not None),
            "OCR Success": int(result_entry["ocr_result"] is not None),
            "E2E Vendor": e2e_summary["vendor"],
            "E2E Total": e2e_summary["total"],
            "E2E #Items": e2e_summary["num_items"],
            "E2E Items": e2e_summary["items"],
            "OCR Vendor": ocr_summary["vendor"],
            "OCR Total": ocr_summary["total"],
            "OCR #Items": ocr_summary["num_items"],
            "OCR Items": ocr_summary["items"],
        })

# Save full JSON
with open(OUTPUT_JSON, "w") as f:
    json.dump(results, f, indent=2)

# Save summary CSV
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=csv_rows[0].keys())
    writer.writeheader()
    writer.writerows(csv_rows)

print(f"\n✅ Benchmark complete.")
print(f"📝 Full results saved to: {OUTPUT_JSON}")
print(f"📊 Summary CSV saved to: {OUTPUT_CSV}")
