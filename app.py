import os
import re
from flask import Flask, request, render_template
from dateutil import parser

from calculations import generate_cashflow_plot, compute_break_funding_cost
from extract_from_pdf import extract_loan_terms

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

FIELDS = [
    'effective_date', 'maturity_date', 'frequency', 'amortization_type',
    'loan_rate', 'balance'
]

def safe_field(field_name, extracted, form):
    """
    The safe_field() function is a helper that prioritizes user input, but falls back 
    to extracted values (like from a PDF), and if neither is available, returns a 
    blank string.
    """
    user_val = form.get(field_name)
    extracted_val = extracted.get(field_name, "")
    if user_val is not None and user_val.strip() != "":
        return user_val.strip()
    elif extracted_val not in (None, "", "None"):
        return extracted_val
    else:
        return ""

def normalize_date(date_str):
    try:
        dt = parser.parse(date_str)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return ""

def normalize_frequency(freq_str):
    freq_str = freq_str.strip().lower()
    mapping = {
        'monthly': 'monthly',
        'month': 'monthly',
        'quarterly': 'quarterly',
        'quarter': 'quarterly',
        '3m': 'quarterly',
        'semiannual': 'semiannual',
        'semi-annually': 'semiannual',
        '6m': 'semiannual',
        'annual': 'annual',
        'yearly': 'annual',
        '12m': 'annual'
    }
    return mapping.get(freq_str, '')

def normalize_amortization_type(amt_str):
    amt_str = amt_str.strip().lower()
    mapping = {
        'interest only': 'interest only',
        'io': 'interest only',
        'i/o': 'interest only',

        'equal': 'equal',
        'equal payment': 'equal',
        'annuity': 'equal',
        'level payment': 'equal',

        'linear': 'linear',
        'straight line': 'linear',
        'even principal': 'linear',
        'constant principal': 'linear',

        'custom': 'custom',
        'manual': 'custom',
        'user defined': 'custom',
    }
    return mapping.get(amt_str, '')


# Normalize/parse balance as float (handle commas, $ signs)
def parse_amount(s):
    if not s:
        return None
    s = re.sub(r'[^\d.]', '', s)
    try:
        return float(s)
    except ValueError:
        return None


@app.route('/', methods=['GET', 'POST'])
def index():
    extracted = {}
    extracted_quotes = {}
    data = {}
    plot_generated = False
    break_funding_cost = None
    error_message = None

    if request.method == 'POST':
        action = request.form.get('action')  # Check whether it's 'upload' or 'calculate'

        if action == 'upload':
            # Only handle PDF upload and pre-fill the form
            pdf_file = request.files.get('pdf')
            if pdf_file and pdf_file.filename.endswith('.pdf'):
                extracted, extracted_quotes = extract_loan_terms(pdf_file)

            # Pre-fill fields with extracted values (if found), else blank
            for field in FIELDS:
                data[field] = extracted.get(field, '')


            # Extracted values from the PDF or user input
            effective_date = normalize_date(extracted.get('effective_date', ''))
            balance = parse_amount(extracted.get('balance', ''))

            # Set Prepayment Date default to Effective Date if missing
            if effective_date != "":
                prepayment_date = effective_date

            # Set Prepayment Amount default to half Balance if missing and Balance is valid
            if balance != "":
                prepayment_amount = float(balance / 2)

            # Leave prepayment fields empty
            data['prepayment_date'] = prepayment_date or ''
            data['prepayment_amount'] = prepayment_amount or ''

            data['effective_date'] = effective_date
            data['maturity_date'] = normalize_date(extracted.get('maturity_date', ''))
            data['frequency'] = normalize_frequency(safe_field('frequency', extracted, request.form))
            data['amortization_type'] = normalize_amortization_type(safe_field('amortization_type', extracted, request.form))

            return render_template('index.html', **data,
                                extracted_quotes=extracted_quotes,
                                plot_generated=False,
                                error_message=None,
                                break_funding_cost=None,
                                loading=True)  # Pass this flag

        elif action == 'calculate':
            # # Continue to validate and compute results
            # pdf_file = request.files.get('pdf')
            # if pdf_file and pdf_file.filename.endswith('.pdf'):
            #     extracted, extracted_quotes = extract_loan_terms(pdf_file)

            # Use safe_field to prioritize user input
            for field in FIELDS:
                data[field] = safe_field(field, extracted, request.form)

            data['prepayment_date'] = request.form.get('prepayment_date', '').strip()
            data['prepayment_amount'] = request.form.get('prepayment_amount', '').strip()

            data['effective_date'] = normalize_date(safe_field('effective_date', extracted, request.form))
            data['maturity_date'] = normalize_date(safe_field('maturity_date', extracted, request.form))
            data['frequency'] = normalize_frequency(safe_field('frequency', extracted, request.form))
            data['amortization_type'] = normalize_amortization_type(safe_field('amortization_type', extracted, request.form))

            required_fields = FIELDS + ['prepayment_date', 'prepayment_amount']
            if all(data.get(f) not in (None, '', 'None') for f in required_fields):
                try:
                    data['loan_rate'] = float(data['loan_rate'])
                    data['balance'] = float(data['balance'])
                    data['prepayment_amount'] = float(data['prepayment_amount'])
                except ValueError:
                    error_message = "Please enter valid numeric values."
                    return render_template("index.html", **data,
                                           extracted_quotes=extracted_quotes,
                                           plot_generated=False,
                                           error_message=error_message,
                                           break_funding_cost=None,
                                           loading=False)
                try:
                    generate_cashflow_plot(data)
                    break_funding_cost = compute_break_funding_cost(**data)
                    plot_generated = True
                except Exception as e:
                    error_message = f"Error generating plot: {e}"

            else:
                error_message = "Please fill in all required fields."

            return render_template('index.html', **data,
                                   extracted_quotes=extracted_quotes,
                                   plot_generated=plot_generated,
                                   error_message=error_message,
                                   break_funding_cost=break_funding_cost,
                                   loading=False)

    # GET request
    return render_template("index.html",
                           effective_date='',
                           maturity_date='',
                           frequency='',
                           amortization_type='',
                           loan_rate='',
                           balance='',
                           prepayment_date='',
                           prepayment_amount='',
                           extracted_quotes={},
                           plot_generated=False,
                           break_funding_cost=None,
                           error_message=None,
                           loading=False)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)