import fitz  # PyMuPDF
import json
import os
from huggingface_hub import InferenceClient

# Hugging Face API token from environment variable
HUGGINGFACE_API_TOKEN = os.getenv("HF_TOKEN")

# Use a chat model instead of a pure text-generation one
HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"  # or any chat-compatible model

# Initialize the client
client = InferenceClient(model=HF_MODEL, token=HUGGINGFACE_API_TOKEN)

FIELDS = [
    "Effective Date", "Maturity Date", "Frequency", "Amortization Type",
    "Loan Rate", "Balance"
]


def extract_text_from_pdf(pdf_file) -> str:
    """
    Extract all text from the PDF file stream using PyMuPDF.
    """
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    full_text = "\n".join(page.get_text() for page in doc)
    return full_text


def ask_field_info(pdf_text: str, field: str) -> dict:
    """
    Query a conversational model to extract a specific field's value and a supporting quote.

    Returns:
        dict: { "value": ..., "quote": ... }
    """
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that extracts financial data from term sheets. "
                       "Your job is to find specific loan terms and provide the value with a quote from the text."
        },
        {
            "role": "user",
            "content": f"""Extract the **{field}** from the following text and give a supporting quote.

Respond in this JSON format:
{{
  "value": "...",
  "quote": "..."
}}

Text:
\"\"\"{pdf_text[:2000]}\"\"\""""
        }
    ]

    try:
        response = client.chat_completion(
            messages=messages,
            temperature=0,
        )

        json_start = response.content.find('{')
        json_end = response.content.rfind('}') + 1

        if json_start == -1 or json_end == -1:
            raise ValueError("JSON output not found in model response")

        json_str = response.content[json_start:json_end]
        parsed = json.loads(json_str)

        return {
            "value": parsed.get("value", "").strip(),
            "quote": parsed.get("quote", "").strip() or "No supporting quote found"
        }

    except Exception as e:
        return {
            "value": "",
            "quote": f"Error during extraction: {str(e)}"
        }


def extract_loan_terms(pdf_file) -> tuple[dict, dict]:
    """
    Extract all loan term fields from the PDF using conversational model.

    Returns:
        extracted: Dict[field] = value
        quotes: Dict[field] = supporting quote
    """
    text = extract_text_from_pdf(pdf_file)
    # with open("raw_pdf_text.txt", "w") as f:
    #     f.write(text)

    extracted = {}
    quotes = {}

    for field in FIELDS:
        result = ask_field_info(text, field)

        key = field.lower().replace(" ", "_")
        extracted[key] = result["value"]
        quotes[key] = result["quote"]

    return extracted, quotes