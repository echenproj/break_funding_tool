# Save this as create_readme.py and run it with Python
# 💼 BreakFunding.AI

**BreakFunding.AI** is a Flask web application that allows users to upload loan term sheets (PDF), automatically extract key terms using an LLM, and calculate break-funding costs with a visualized cashflow chart. Users can also export the results to a PowerPoint slide.

---

## 🚀 Features

- 📄 Upload a PDF term sheet
- 🤖 Auto-extract loan fields using a Hugging Face LLM
- 📊 Generate amortization and prepayment cashflow plots
- 💰 Calculate break-funding cost
- 🖼️ Download a PowerPoint summary slide
- 🧠 Smart defaults for missing fields
- 🔒 Disclaimer for data usage

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask
- **Frontend:** HTML (Jinja2 templates)
- **LLM:** [Mistral-7B-Instruct](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2) via Hugging Face Inference API
- **Visualization:** Matplotlib
- **PDF Parsing:** PyMuPDF (`fitz`)
- **Presentation:** `python-pptx`

---

## 📁 Project Structure
break_funding_tool/
├── app.py # Flask app
├── calculations.py # Cashflow and cost logic
├── extract_from_pdf.py # PDF parsing + LLM field extraction
├── requirements.txt # Dependencies
├── static/ # Images (plot, logos)
├── templates/ # HTML UI (Jinja2)
└── README.md

---

## 🌐 How to Use (Locally)

1. **Clone the Repo**

```bash
git clone https://github.com/yourusername/break_funding_tool.git
cd break_funding_tool
```
2. **Set up Environment**
```bash
python -m venv venv
source venv/bin/activate  # or venv\\Scripts\\activate on Windows
pip install -r requirements.txt
```

3. **Set Hugging Face Token**
Create a .env file or export the token in your shell:

```bash
export HF_TOKEN=your_huggingface_token
```

4. **Run the App**
```bash
python app.py
```
Visit http://localhost:5000 in your browser.

Local Command: gunicorn app:app