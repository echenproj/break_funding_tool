import matplotlib.pyplot as plt
import datetime
import matplotlib.dates as mdates

def generate_cashflow_plot(data):
    # Mock example: Generate simple time series cashflows
    start = datetime.datetime.strptime(data['effective_date'], "%Y-%m-%d")
    end = datetime.datetime.strptime(data['maturity_date'], "%Y-%m-%d")
    dates = [start + datetime.timedelta(days=30 * i) for i in range(12)]
    cashflows = [1000 - i * 50 for i in range(12)]  # Example declining cashflows

    # Plot
    plt.figure(figsize=(8, 4))
    plt.plot(dates, cashflows, marker='o', linestyle='-')
    plt.title("Cashflow Schedule")
    plt.xlabel("Date")
    plt.ylabel("Amount")
    plt.grid(True)
    plt.tight_layout()
    plt.gcf().autofmt_xdate()
    plt.savefig("static/plot.png")
    plt.close()
