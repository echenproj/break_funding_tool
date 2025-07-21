import os
from flask import Flask, request, render_template
from calculations import generate_cashflow_plot, compute_break_funding_cost
from extract_from_pdf import extract_loan_terms

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

FIELDS = [
    'effective_date', 'maturity_date', 'frequency', 'amortization_type',
    'loan_rate', 'balance'
]

def safe_field(field_name, extracted, form):
    user_val = form.get(field_name)
    extracted_val = extracted.get(field_name, "")
    if user_val is not None and user_val.strip() != "":
        return user_val.strip()
    elif extracted_val not in (None, "", "None"):
        return extracted_val
    else:
        return ""

@app.route('/', methods=['GET', 'POST'])
def index():
    extracted = {}
    extracted_quotes = {}
    plot_generated = False
    break_funding_cost = None
    error_message = None
    data = {}

    if request.method == 'POST':
        action = request.form.get("action")

        # If user clicked Upload
        if action == "upload":
            pdf_file = request.files.get('pdf')
            if pdf_file and pdf_file.filename.endswith('.pdf'):
                extracted, extracted_quotes = extract_loan_terms(pdf_file)

            # Fill form inputs using extracted data only
            for field in FIELDS:
                data[field] = extracted.get(field, "")

            # Prepayment fields left blank
            data['prepayment_date'] = ''
            data['prepayment_amount'] = ''

            return render_template("index.html", **data,
                                   extracted_quotes=extracted_quotes,
                                   plot_generated=False,
                                   error_message=None,
                                   break_funding_cost=None)

        # If user clicked Calculate
        elif action == "calculate":
            # Combine extracted and user input
            pdf_file = request.files.get('pdf')
            if pdf_file and pdf_file.filename.endswith('.pdf'):
                extracted, extracted_quotes = extract_loan_terms(pdf_file)
            else:
                extracted_quotes = {}

            for field in FIELDS:
                data[field] = safe_field(field, extracted, request.form)

            data['prepayment_date'] = request.form.get('prepayment_date', '').strip()
            data['prepayment_amount'] = request.form.get('prepayment_amount', '').strip()

            required_fields = FIELDS + ['prepayment_date', 'prepayment_amount']
            if all(data.get(f) not in (None, '', 'None') for f in required_fields):
                try:
                    data['loan_rate'] = float(data['loan_rate'])
                    data['balance'] = float(data['balance'])
                    data['prepayment_amount'] = float(data['prepayment_amount'])
                except ValueError:
                    error_message = "Please enter valid numeric values."
                    return render_template("index.html", **data, extracted_quotes=extracted_quotes,
                                           plot_generated=False, error_message=error_message,
                                           break_funding_cost=None)

                try:
                    generate_cashflow_plot(data)
                    break_funding_cost = compute_break_funding_cost(**data)
                    plot_generated = True
                except Exception as e:
                    error_message = f"Error generating plot: {e}"
            else:
                error_message = "Please fill in all required fields."

            return render_template("index.html", **data, extracted_quotes=extracted_quotes,
                                   plot_generated=plot_generated,
                                   error_message=error_message,
                                   break_funding_cost=break_funding_cost if plot_generated else None)

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
                           error_message=None
                           )
                           
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)