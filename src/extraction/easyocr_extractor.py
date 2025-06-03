import easyocr
from typing import List, Tuple
import numpy as np
from PIL import Image
from configs.config import OCR_LANGUAGES

reader = easyocr.Reader(OCR_LANGUAGES, gpu=False)

def extract_text_easyocr(image: Image.Image) -> List[Tuple[str, float]]:
    image_np = np.array(image)
    results = reader.readtext(image_np)
    return [(text, confidence) for _, text, confidence in results]
