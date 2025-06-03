from transformers import pipeline
import time
from typing import List, Dict

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

CANDIDATE_LABELS = [
    "Food & Dining", "Groceries", "Transportation", "Fuel", "Lodging", "Travel",
    "Utilities", "Healthcare", "Pharmacy", "Clothing", "Electronics",
    "Entertainment", "Office Supplies", "Hardware & Tools", "Services",
    "Education", "Subscriptions", "Telecom", "Insurance", "Taxes & Fees",
    "Gifts & Donations", "Household", "Childcare", "Pet Care", "Miscellaneous"
]

def classify_items(receipt: Dict) -> Dict:
    """Classifies each item in a receipt and adds 'category' field."""
    for item in receipt.get("items", []):
        sequence = item["name"]
        result = classifier(sequence, CANDIDATE_LABELS)

        item["category"] = result["labels"][0]
        item["classification_score"] = round(result["scores"][0], 3)
    return receipt