 Logic Flow
User fills form and clicks Calculate

Form data is POSTed to Flask endpoint

Backend calculates cash flows, generates matplotlib plot (plot.png)

HTML reloads with the plot embedded via <img src="/static/plot.png">
gunicorn app:app