# 🔍 FactLens – AI-Powered PDF Fact Verifier

> Upload a PDF → Extract Claims → Cross-Reference Live Web Data → Get Instant Truth Audit

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app.streamlit.app)

---

## 🎯 What It Does

FactLens reads any PDF, automatically extracts verifiable claims (statistics, dates, financial figures, technical specs), and cross-references each one against **live web data** in real time. No API key entry needed — just upload and click Analyze.

| Verdict | Meaning |
|---|---|
| ✅ Verified | Claim matches current web evidence |
| ⚠️ Inaccurate | Claim has outdated or wrong figures |
| ❌ False | Claim is demonstrably wrong / no evidence found |

---

## 🏗️ Architecture

```
PDF Upload → pdfplumber text extraction
           → Groq LLM extracts verifiable claims (JSON)
           → Tavily live web search per claim
           → Groq LLM judges claim vs. web evidence
           → PDF Report (ReportLab) or JSON download
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| LLM | Groq API — LLaMA 3.3 70B |
| Live Web Search | Tavily API |
| PDF Parsing | pdfplumber |
| PDF Report Generation | ReportLab |
| Deployment | Streamlit Cloud |

---

## ⚙️ Local Setup

### 1. Clone & install
```bash
git clone https://github.com/YOUR_USERNAME/factlens.git
cd factlens
pip install -r requirements.txt
```

### 2. Add API keys to `.streamlit/secrets.toml`
```toml
GROQ_API_KEY   = "gsk_your_key_here"
TAVILY_API_KEY = "tvly_your_key_here"
```
- **Groq** (free): https://console.groq.com
- **Tavily** (free): https://app.tavily.com

### 3. Run
```bash
streamlit run app.py
```

---

## ☁️ Deploy on Streamlit Cloud

1. Push repo to GitHub
2. Go to https://share.streamlit.io → New app → select repo → `app.py`
3. **Settings → Secrets** → paste:
```toml
GROQ_API_KEY   = "gsk_your_key_here"
TAVILY_API_KEY = "tvly_your_key_here"
```
4. Click Deploy — done in ~2 minutes

> Users never see or enter API keys. They just upload a PDF and click Analyze.

---

## 📁 Project Structure

```
factlens/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── README.md                 # This file
└── .streamlit/
    └── secrets.toml          # API keys (local only, git-ignored)
```

---

*Built for the CogCulture Product Management Trainee Assessment*
