import streamlit as st
import requests
import pandas as pd
import os

API_URL = os.getenv("API_URL", "http://server:8003/process")

st.set_page_config(page_title="Receipt Parser", layout="centered")
st.title("🧾 Receipt Processor")
st.caption("Upload a receipt image or audio to extract structured data using Gemini.")

uploaded_file = st.file_uploader("Upload image or audio file", type=["jpg", "jpeg", "png", "bmp", "tiff", "mp3", "wav", "m4a", "ogg"])
use_e2e = st.checkbox("Use Gemini E2E (direct image-to-structure)")

if uploaded_file and st.button("Process"):
    with st.spinner("Processing..."):
        try:
            files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
            data = {"e2e": str(use_e2e).lower()}
            response = requests.post(API_URL, files=files, data=data)
            response.raise_for_status()
            receipts = response.json()
        except Exception as e:
            st.error(f"Failed to process receipt: {e}")
        else:
            for idx, receipt in enumerate(receipts):
                st.subheader(f"Receipt {idx + 1}")
                st.write(f"**Vendor:** {receipt.get('vendor')}")
                st.write(f"**Date:** {receipt.get('date')}")
                st.write(f"**Total:** ${receipt.get('total'):.2f}")

                items = receipt.get("items", [])
                if items:
                    df = pd.DataFrame(items)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No items detected.")
