import os
from flask import Flask, request, render_template
from calculations import generate_cashflow_plot
from extract_from_pdf import extract_loan_terms

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

@app.route('/', methods=['GET', 'POST'])
def index():
    extracted = {}
    extracted_quotes = {}
    plot_generated = False

    if request.method == 'POST':
        # If PDF uploaded, extract terms
        if 'pdf' in request.files and request.files['pdf'].filename.endswith('.pdf'):
            pdf_file = request.files['pdf']
            extracted, extracted_quotes = extract_loan_terms(pdf_file)

        # Combine user inputs with extracted values (user can override)
        def get_field(field, cast=str):
            return cast(request.form.get(field) or extracted.get(field) or "")

        data = {
            'effective_date': get_field('effective_date'),
            'maturity_date': get_field('maturity_date'),
            'frequency': get_field('frequency'),
            'amortization_type': get_field('amortization_type'),
            'loan_rate': get_field('loan_rate', float),
            'balance': get_field('balance', float),
            'prepayment_date': request.form.get('prepayment_date'),       # user only
            'prepayment_amount': float(request.form.get('prepayment_amount') or 0),  # user only
        }

        # Generate plot only if everything is filled
        if all(data.values()):
            generate_cashflow_plot(data)
            plot_generated = True

    return render_template("index.html", extracted=extracted, extracted_quotes=extracted_quotes, plot_generated=plot_generated)

# For deployment (e.g., Render.com)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)