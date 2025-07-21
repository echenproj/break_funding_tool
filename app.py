import os
from flask import Flask, render_template, request
from calculations import generate_cashflow_plot

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    plot_generated = False

    if request.method == 'POST':
        try:
            # Extract form values from request
            data = {
                'effective_date': request.form['effective_date'],
                'maturity_date': request.form['maturity_date'],
                'frequency': request.form['frequency'],
                'amortization_type': request.form['amortization_type'],
                'loan_rate': float(request.form['loan_rate']),
                'balance': float(request.form['balance']),
                'prepayment_date': request.form['prepayment_date'],
                'prepayment_amount': float(request.form['prepayment_amount'])
            }

            # Call plotting function
            generate_cashflow_plot(data)
            plot_generated = True

        except Exception as e:
            print(f"Error: {e}")
            plot_generated = False

    return render_template('index.html', plot_generated=plot_generated)

# For deployment (e.g., Render.com)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)