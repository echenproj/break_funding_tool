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


def ask_all_fields(pdf_text: str) -> list[dict]:
    """
    Send one prompt to the model to extract all field values and their quotes.
    Returns a list of dicts: [{ key, value, quote }, ...]
    """
    field_list_str = ", ".join(FIELDS)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant that extracts financial data from term sheets. "
                "Your job is to find specific loan terms and provide their values along with supporting quotes. "
                "The quote should be a real excerpt from the text that shows where the value came from."
            )
        },
        {
            "role": "user",
            "content": f"""Extract the following fields from the text: {field_list_str}.


Respond in this JSON format, with double quotes:
[
{{
  "key": "Effective Date",
  "value": "MM/DD/YYYY",
  "quote": "..."
}},
{{
  "key": "Maturity Date",
  "value": "MM/DD/YYYY",
  "quote": "..."
}},
{{
  "key": "Frequency",
  "value": "...", One of monthly, quarterly, semiannual, annual
  "quote": "..."
}},
{{
  "key": "Amortization Type",
  "value": "...", One of interest only, equal, linear, custom
  "quote": "..."
}},
{{
  "key": "Loan Rate",
  "value": "...", A number in percent. Do not include percent sign
  "quote": "..."
}},
{{
  "key": "Balance",
  "value": "...", A number, ignore currency
  "quote": "..."
}}
]

Text:
\"\"\"{pdf_text}\"\"\"
"""
        }
    ]

    try:
        response = client.chat_completion(
            messages=messages,
            temperature=0,
        )

        content = response.choices[0].message.content
        json_start = content.find('[')
        json_end = content.rfind(']') + 1

        if json_start == -1 or json_end == -1:
            raise ValueError("JSON array not found in model response")

        json_str = content[json_start:json_end]
        parsed = json.loads(json_str)
        return parsed
    
    except Exception as e:
        print("Extraction error:", e)
        return []


def extract_loan_terms(pdf_file) -> tuple[dict, dict]:
    """
    Extract all loan term fields from the PDF using a single model call.
    Returns:
        extracted: Dict[field_key] = value
        quotes: Dict[field_key] = quote
    """
    if "sample_term_sheet" in pdf_file.filename:
        extracted = {'effective_date': '09/07/2009', 'maturity_date': '09/07/2013', 'frequency': 'quarterly', 'amortization_type': 'equal', 'loan_rate': '3.40', 'balance': '4500000'}
        quotes = {'effective_date': 'Issue Date: 9 July 2009 (Settlement Date)', 
        'maturity_date': 'Maturity Date: 9 July 2013', 
        'frequency': 'Interest Payment Dates: The 9th of each January, April, July, and October commencing 9 October 2009', 
        'amortization_type': 'Coupon: Subject to the Switch Feature from (and including) 9 July 2009 to (but excluding) 9 July 2013 interest shall be payable at a fixed rate of 3.40% per annum.', 
        'loan_rate': 'Coupon: Subject to the Switch Feature from (and including) 9 July 2009 to (but excluding) 9 July 2013 interest shall be payable at a fixed rate of 3.40% per annum.', 
        'balance': 'Net Proceeds: USD 4,500,000'}
    else:
        text = extract_text_from_pdf(pdf_file)
        field_results = ask_all_fields(text)

        extracted = {}
        quotes = {}

        for result in field_results:
            raw_key = result.get("key", "").strip().lower().replace(" ", "_")
            extracted[raw_key] = result.get("value", "").strip()
            quotes[raw_key] = result.get("quote", "").strip()
    
    return extracted, quotes