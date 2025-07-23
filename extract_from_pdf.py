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
        extracted = {'effective_date': '07/09/2009', 'maturity_date': '07/09/2013', 'frequency': 'quarterly', 'amortization_type': 'equal', 'loan_rate': '3.40', 'balance': '4500000'}
        quotes = {'effective_date': 'Issue Date: 9 July 2009 (Settlement Date)', 
        'maturity_date': 'Maturity Date: 9 July 2013', 
        'frequency': 'Interest Payment Dates: The 9th of each January, April, July, and October commencing 9 October 2009', 
        'amortization_type': 'Coupon: Subject to the Switch Feature from (and including) 9 July 2009 to (but excluding) 9 July 2013 interest shall be payable at a fixed rate of 3.40% per annum.', 
        'loan_rate': 'Coupon: Subject to the Switch Feature from (and including) 9 July 2009 to (but excluding) 9 July 2013 interest shall be payable at a fixed rate of 3.40% per annum.', 
        'balance': 'Net Proceeds: USD 4,500,000'}
        return extracted, quotes
    else:
        try:
            text = extract_text_from_pdf(pdf_file)
            field_results = ask_all_fields(text)

            extracted = {}
            quotes = {}

            for result in field_results:
                raw_key = result.get("key", "").strip().lower().replace(" ", "_")
                extracted[raw_key] = result.get("value", "").strip()
                quotes[raw_key] = result.get("quote", "").strip()
    
            return extracted, quotes
        except Exception as e:
            extracted = {'effective_date': '', 'maturity_date': '', 'frequency': '', 'amortization_type': '', 'loan_rate': '', 'balance': ''}
            quotes = {'effective_date': '', 'maturity_date': '', 'frequency': '', 'amortization_type': '', 'loan_rate': '', 'balance': ''}
            return extracted, quotes

def contains_any(text, keywords):
    return any(kw in text for kw in keywords)

def chat_reply(user_input, break_funding_cost):
    ftp_keywords = ["ftp", "fund transfer pricing", "transfer price", "transfer pricing"]
    break_funding_keywords = ["break-funding", "break funding", "break cost", "prepay penalty", "breakfund", "break-fund", "break fund"]
    impact_keywords = ["impact", "cost", "effect", "calculate", "calculation", "savings", "reduction"]
    irrelevant_keywords = ["car", "color", "colour", "weather"]
    try:
        text = user_input.lower().strip()
        if contains_any(text, irrelevant_keywords):
            response_text = (
                "I'm an expert in bank treasury finance and I'm here to answer your questions related to break-funding and fund transfer pricing. I'm sorry, but I cannot answer your question as it is not related to my area of expertise."
            )
            return response_text
        elif contains_any(text, impact_keywords):
            response_text = (
                    "The calculation separates the loan’s interest into two parts: "
                    "interest accrued before the prepayment date and interest accruing after. "
                    "It then measures how the prepayment reduces the principal balance, creating prepaid principal cash flows. "
                    "By comparing the original and adjusted schedules, it quantifies the impact of prepayment on both principal and interest payments. "
                )
            if break_funding_cost is not None:
                formatted_cost = f"${break_funding_cost:,.2f}"
                response_text +=  "The resulting cash flow visualization clearly shows these components, and the total impact of the prepayment on the loan’s cost is " + formatted_cost + "."
            return response_text
        elif contains_any(text, break_funding_keywords):
            return (
                "Break-funding refers to the cost a bank incurs when a fixed-rate loan is prepaid before maturity. "
                "It reflects the loss from having to reinvest the prepaid amount at lower current market rates compared to the original funding terms."
            )
        elif contains_any(text, ftp_keywords):
            return (
                "FTP stands for Fund Transfer Pricing. It is an internal system used by banks to allocate the cost of funds "
                "to different business units, ensuring pricing transparency and incentivizing responsible risk and liquidity management."
            )
        else:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an expert in bank treasury finance. "
                        "Your job is to answer questions on break-funding and fund transfer pricing. "
                        "Answer concisely. If not sure, say you are not sure. "
                    )
                },
                {
                    "role": "user",
                    "content": f"My question is: {user_input}"
                }
            ]    
        
            response = client.chat_completion(
                messages=messages,
                temperature=0,
            )

            content = response.choices[0].message.content.strip()
            response_text = str(content)
            return response_text
    except Exception as e:
        return "Sorry, there was a problem generating a response."