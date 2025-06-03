from google import genai
from pydantic import BaseModel
from typing import List, Literal


class ReceiptItem(BaseModel):
    name: str
    quantity: int
    price_per_item: float
    category: Literal["Food & Dining", "Groceries", "Transportation", "Fuel", "Lodging", "Travel",
    "Utilities", "Healthcare", "Pharmacy", "Clothing", "Electronics",
    "Entertainment", "Office Supplies", "Hardware & Tools", "Services",
    "Education", "Subscriptions", "Telecom", "Insurance", "Taxes & Fees",
    "Gifts & Donations", "Household", "Childcare", "Pet Care", "Miscellaneous"
]

class Receipt(BaseModel):
    vendor: str
    date: str
    total: float
    items: List[ReceiptItem]

def parse_receipt_with_gemini(text: str, api_key: str) -> List[Receipt]:
    client = genai.Client(api_key=api_key)

    prompt = f"""Extract the structured information from this receipt OCR text:
    ---
    {text}
    ---
    Return the result as a JSON object with keys: vendor (string), date (string), total (float), and items (list of strings).
    Keep the same language.
"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config={"response_mime_type": "application/json", "response_schema": list[Receipt],}
    )

    return response.parsed

def parse_receipt_image_with_gemini(image_path: str, api_key: str) -> List[Receipt]:
    client = genai.Client(api_key=api_key)

    # Upload the image
    uploaded_file = client.files.upload(file=image_path)

    # Prompt for structured extraction
    prompt = """Extract the structured information from this receipt image.
 Return the result as a JSON object with keys: vendor (string), date (string), total (float), and items (list of strings)."""

    # Send image + prompt to Gemini
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[uploaded_file, prompt],
        config={"response_mime_type": "application/json", "response_schema": list[Receipt], }
    )

    return response.parsed