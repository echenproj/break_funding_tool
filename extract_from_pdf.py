import fitz  # PyMuPDF
import json
import os
from huggingface_hub import InferenceClient

# Replace this with your Hugging Face token
HUGGINGFACE_API_TOKEN = os.getenv("HF_TOKEN")

# Set your hosted model (you can choose another one)
HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"
client = InferenceClient(model=HF_MODEL, token=HUGGINGFACE_API_TOKEN)

FIELDS = [
    "Effective Date", "Maturity Date", "Frequency", "Amortization Type",
    "Loan Rate", "Balance"
]

def extract_text_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    return "\n".join(page.get_text() for page in doc)

def ask_field_info(pdf_text, field):
    prompt = f"""
You are an assistant extracting loan terms from a term sheet.

Extract the **{field}**, and quote the sentence that supports it.

Respond in JSON:
{{"value": "...", "quote": "..."}}

PDF Text:
\"\"\"{pdf_text[:2000]}\"\"\"
"""
    try:
        response = client.text_generation(prompt, max_new_tokens=512, temperature=0)
        json_start = response.index('{')
        json_end = response.rindex('}') + 1
        return json.loads(response[json_start:json_end])
    except Exception:
        return {"value": "", "quote": "Could not extract quote"}

def extract_loan_terms(pdf_file):
    text = extract_text_from_pdf(pdf_file)
    extracted = {}
    quotes = {}
    for field in FIELDS:
        result = ask_field_info(text, field)
        key = field.lower().replace(" ", "_")
        extracted[key] = result["value"]
        quotes[key] = result["quote"]
    return extracted, quotes