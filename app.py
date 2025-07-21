from flask import Flask, render_template, request
from calculations import generate_cashflow_plot

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    plot_generated = False
    if request.method == 'POST':
        # Extract form data
        data = {
            'effective_date': request.form['effective_date'],
            'maturity_date': request.form['maturity_date'],
            'frequency': request.form['frequency'],
            'amortization_type': request.form['amortization_type'],
            'loan_rate': float(request.form['loan_rate']),
            'prepayment_date': request.form['prepayment_date'],
            'prepayment_amount': float(request.form['prepayment_amount'])
        }
        generate_cashflow_plot(data)
        plot_generated = True
    return render_template('index.html', plot_generated=plot_generated)

if __name__ == '__main__':
    app.run(debug=True)
