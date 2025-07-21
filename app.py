import os
from flask import Flask, request, render_template
from calculations import generate_cashflow_plot, compute_break_funding_cost
from extract_from_pdf import extract_loan_terms

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

@app.route('/', methods=['GET', 'POST'])
def index():
    extracted = {}
    extracted_quotes = {}
    plot_generated = False
    break_funding_cost = None
    form_data = {}

    if request.method == 'POST':
        # If PDF uploaded, extract terms
        if 'pdf' in request.files and request.files['pdf'].filename.endswith('.pdf'):
            pdf_file = request.files['pdf']
            extracted, extracted_quotes = extract_loan_terms(pdf_file)

        # Combine user inputs with extracted values (user can override)
        def get_field(field, cast=str):
            return cast(request.form.get(field) or extracted.get(field) or "")

        form_data = {
            'effective_date': get_field('effective_date'),
            'maturity_date': get_field('maturity_date'),
            'frequency': get_field('frequency'),
            'amortization_type': get_field('amortization_type'),
            'loan_rate': get_field('loan_rate', float),
            'balance': get_field('balance', float),
            'prepayment_date': request.form.get('prepayment_date'),
            'prepayment_amount': float(request.form.get('prepayment_amount') or 0),
        }

        # Generate plot and compute break funding cost if all fields are filled
        if all(form_data.values()):
            generate_cashflow_plot(form_data)
            plot_generated = True

            break_funding_cost = compute_break_funding_cost(
                effective_date=form_data['effective_date'],
                maturity_date=form_data['maturity_date'],
                frequency=form_data['frequency'],
                balance=form_data['balance'],
                loan_rate=form_data['loan_rate'],
                amortization_type=form_data['amortization_type'],
                prepayment_date=form_data['prepayment_date'],
                prepayment_amount=form_data['prepayment_amount'],
            )

    return render_template(
        "index.html",
        extracted=extracted,
        extracted_quotes=extracted_quotes,
        plot_generated=plot_generated,
        break_funding_cost=break_funding_cost,
        **form_data
    )

# For deployment (e.g., Render.com)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)