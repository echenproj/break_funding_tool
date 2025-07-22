import datetime
from dateutil.relativedelta import relativedelta
import math
import numpy as np


import matplotlib.pyplot as plt
import matplotlib.ticker as mtick


def compute_original_cashflow(data):
    start = datetime.datetime.strptime(data['effective_date'], "%Y-%m-%d")
    end = datetime.datetime.strptime(data['maturity_date'], "%Y-%m-%d")
    balance = data['balance']
    annual_rate = data['loan_rate'] / 100
    amortization = data['amortization_type'].lower()
    frequency = data['frequency'].lower()

    freq_map = {
        'monthly': 1,
        'quarterly': 3,
        'semiannual': 6,
        'annual': 12
    }

    if frequency not in freq_map:
        raise ValueError("Invalid frequency")

    months_per_period = freq_map[frequency]

    # Generate payment dates
    payment_dates = []
    dt = start
    while dt < end:
        payment_dates.append(dt)
        dt += relativedelta(months=+months_per_period)
    payment_dates.append(end)
    num_periods = len(payment_dates) - 1

    period_rate = annual_rate * months_per_period / 12

    principal_vector = []
    interest_vector = []

    if amortization == "interest only":
        for i in range(num_periods):
            interest_payment = balance * period_rate
            principal_payment = 0.0
            if i == num_periods - 1:
                principal_payment = balance
            interest_vector.append(round(interest_payment, 2))
            principal_vector.append(round(principal_payment, 2))

    elif amortization == "equal":
        if period_rate == 0:
            annuity_payment = balance / num_periods
        else:
            annuity_payment = balance * (period_rate / (1 - (1 + period_rate) ** -num_periods))
        for i in range(num_periods):
            interest_payment = balance * period_rate
            principal_payment = annuity_payment - interest_payment
            interest_vector.append(round(interest_payment, 2))
            principal_vector.append(round(principal_payment, 2))
            balance -= principal_payment

    elif amortization == "linear":
        principal_payment = balance / num_periods
        for i in range(num_periods):
            interest_payment = balance * period_rate
            interest_vector.append(round(interest_payment, 2))
            principal_vector.append(round(principal_payment, 2))
            balance -= principal_payment

    elif amortization == "custom":
        raise NotImplementedError("Custom amortization not yet supported")

    else:
        raise ValueError("Unknown amortization type")

    return principal_vector, interest_vector


def compute_prepayment_cashflow(data, principal_vector, interest_vector):
    effective_date = datetime.datetime.strptime(data['effective_date'], "%Y-%m-%d")
    prepayment_date = datetime.datetime.strptime(data['prepayment_date'], "%Y-%m-%d")
    prepayment_amount = data['prepayment_amount']
    frequency = data['frequency'].lower()

    freq_map = {
        'monthly': 1,
        'quarterly': 3,
        'semiannual': 6,
        'annual': 12
    }

    months_per_period = freq_map[frequency]
    num_periods = len(principal_vector)

    # Build period start dates
    period_dates = []
    dt = effective_date
    for _ in range(num_periods):
        period_dates.append(dt)
        dt += relativedelta(months=+months_per_period)

    # Find the first period on or after the prepayment date
    prepay_index = next((i for i, date in enumerate(period_dates) if date >= prepayment_date), None)
    if prepay_index is None:
        raise ValueError("Prepayment date is beyond loan maturity.")

    remaining_balance = sum(principal_vector[prepay_index:])
    if prepayment_amount > remaining_balance:
        raise ValueError("Prepayment amount exceeds remaining balance.")

    # Apply prepayment by backloading principal
    updated_principal_vector = principal_vector.copy()
    remaining_prepayment = prepayment_amount
    i = num_periods - 1
    while remaining_prepayment > 0 and i >= prepay_index:
        reduction = min(updated_principal_vector[i], remaining_prepayment)
        updated_principal_vector[i] -= reduction
        remaining_prepayment -= reduction
        i -= 1

    return updated_principal_vector, interest_vector  # Interest not recalculated here



def compute_break_funding_cost(
    effective_date,
    maturity_date,
    frequency,
    balance,
    loan_rate,
    amortization_type,
    prepayment_date,
    prepayment_amount
):
    import math

    # Step 1: Compute original cashflows
    data = {
        'effective_date': effective_date,
        'maturity_date': maturity_date,
        'frequency': frequency,
        'loan_rate': loan_rate,
        'balance': balance,
        'amortization_type': amortization_type,
        'prepayment_date': prepayment_date,
        'prepayment_amount': prepayment_amount,
    }
    original_principal, original_interest = compute_original_cashflow(data)

    # Step 2: Compute adjusted cashflows (after prepayment)
    adjusted_principal, adjusted_interest = compute_prepayment_cashflow(data, original_principal, original_interest)

    # Step 3: Generate a fake SOFR curve for discounting
    freq_map = {'monthly': 1, 'quarterly': 3, 'semiannual': 6, 'annual': 12}
    months_per_period = freq_map[frequency.lower()]
    num_periods = len(original_principal)

    dt = datetime.datetime.strptime(prepayment_date, "%Y-%m-%d")
    discount_factors = []
    for i in range(num_periods):
        future_date = dt + relativedelta(months=i * months_per_period)
        t = (future_date - dt).days / 365.0
        rate = 0.05 + 0.0005 * i  # Example fake SOFR curve
        df = 1 / ((1 + rate) ** t)
        discount_factors.append(df)

    # Step 4: Compute NPV of original and adjusted cashflows
    pv_original = sum(
        (p + i) * df for p, i, df in zip(original_principal, original_interest, discount_factors)
    )
    pv_adjusted = sum(
        (p + i) * df for p, i, df in zip(adjusted_principal, adjusted_interest, discount_factors)
    )

    # Step 5: Return break funding cost
    return round(pv_original - pv_adjusted, 2)

    

def generate_cashflow_plot(data):
    # Step 1: Compute original and adjusted schedules
    original_principal, original_interest = compute_original_cashflow(data)
    adjusted_principal, adjusted_interest = compute_prepayment_cashflow(data, original_principal, original_interest)

    # Step 2: Compute stacked components
    prepaid_principal = [orig - adj for orig, adj in zip(original_principal, adjusted_principal)]
    remaining_principal = adjusted_principal
    prepaid_interest = [0] * len(original_interest)
    remaining_interest = adjusted_interest

    # Step 3: Build date labels
    start = datetime.datetime.strptime(data['effective_date'], "%Y-%m-%d")
    end = datetime.datetime.strptime(data['maturity_date'], "%Y-%m-%d")
    freq_map = {'monthly': 1, 'quarterly': 3, 'semiannual': 6, 'annual': 12}
    months_per_period = freq_map[data['frequency'].lower()]

    dates = []
    dt = start
    while dt < end:
        dates.append(dt.strftime('%Y-%m-%d'))
        dt += relativedelta(months=+months_per_period)
    if len(dates) < len(original_principal):
        dates.append(end.strftime('%Y-%m-%d'))

    x = range(len(original_principal))
    labels = dates[:len(original_principal)]

    # Step 4: Plot
    plt.style.use('ggplot')
    fig, ax = plt.subplots(figsize=(18, 10))

    # Professional muted color palette
    colors = {
        'Prepaid Interest': '#c6d9ec',
        'Prepaid Principal': '#6baed6',
        'Remaining Interest': '#fdbf6f',
        'Remaining Principal': '#e6550d',
    }

    ax.bar(x, prepaid_interest, label='Prepaid Interest', color=colors['Prepaid Interest'])
    ax.bar(x, prepaid_principal, bottom=prepaid_interest, label='Prepaid Principal', color=colors['Prepaid Principal'])
    ax.bar(
        x, 
        remaining_interest, 
        bottom=[pi + pp for pi, pp in zip(prepaid_interest, prepaid_principal)],
        label='Remaining Interest', 
        color=colors['Remaining Interest']
    )
    ax.bar(
        x, 
        remaining_principal, 
        bottom=[pi + pp + ri for pi, pp, ri in zip(prepaid_interest, prepaid_principal, remaining_interest)],
        label='Remaining Principal', 
        color=colors['Remaining Principal']
    )

    # Larger, business-style fonts
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=-90, ha='right', fontsize=24)
    ax.set_xlabel("Payment Period", fontsize=26, weight='bold', labelpad=22)
    ax.set_ylabel("Amount ($)", fontsize=26, weight='bold', labelpad=22)
    ax.tick_params(axis='y', labelsize=24)

    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
    ax.legend(fontsize=14, loc='upper right', frameon=False)

    # Reduce grid clutter
    ax.grid(True, which='major', axis='y', linestyle='--', linewidth=0.5, alpha=0.6)
    ax.grid(False, axis='x')

    # Tight and clean layout
    plt.tight_layout(pad=2.0)
    plt.savefig("static/plot.png", dpi=300, bbox_inches='tight')
    plt.close()