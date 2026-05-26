import streamlit as st
import pdfplumber
import json
import time
import requests
import io
import datetime
from groq import Groq

def generate_pdf_report(doc_name, claims_data, verified_count, inaccurate_count, false_count, trust_score):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=18*mm, bottomMargin=18*mm)
    elements = []
    DARK_BG = colors.HexColor("#0d1117")
    ACCENT  = colors.HexColor("#00d4ff")
    GREEN   = colors.HexColor("#22c55e")
    YELLOW  = colors.HexColor("#f59e0b")
    RED     = colors.HexColor("#ef4444")
    LIGHT   = colors.HexColor("#e2e8f0")
    MUTED   = colors.HexColor("#64748b")
    CARD_BG = colors.HexColor("#161b22")
    title_s   = ParagraphStyle("t",  fontName="Helvetica-Bold", fontSize=26, textColor=ACCENT, alignment=TA_CENTER, spaceAfter=2)
    sub_s     = ParagraphStyle("s",  fontName="Helvetica", fontSize=10, textColor=MUTED, alignment=TA_CENTER, spaceAfter=14)
    h2_s      = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=13, textColor=LIGHT, spaceAfter=6, spaceBefore=10)
    small_s   = ParagraphStyle("sm", fontName="Helvetica", fontSize=8, textColor=MUTED, leading=12)
    claim_s   = ParagraphStyle("cl", fontName="Helvetica-Bold", fontSize=9, textColor=LIGHT, leading=13)
    correct_s = ParagraphStyle("co", fontName="Helvetica-Oblique", fontSize=8.5, textColor=ACCENT, leading=12)
    elements.append(Paragraph("FactLens", title_s))
    elements.append(Paragraph("AI-Powered Fact Verification Report", sub_s))
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=10))
    now = datetime.datetime.now().strftime("%B %d, %Y at %H:%M")
    mt = Table([["Document", doc_name], ["Generated", now], ["Total Claims", str(len(claims_data))]], colWidths=[45*mm, 130*mm])
    mt.setStyle(TableStyle([("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),("FONTNAME",(1,0),(1,-1),"Helvetica"),("FONTSIZE",(0,0),(-1,-1),9),("TEXTCOLOR",(0,0),(0,-1),MUTED),("TEXTCOLOR",(1,0),(1,-1),LIGHT),("ROWBACKGROUNDS",(0,0),(-1,-1),[CARD_BG,DARK_BG]),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),("LEFTPADDING",(0,0),(-1,-1),8),("GRID",(0,0),(-1,-1),0.3,MUTED)]))
    elements.append(mt); elements.append(Spacer(1,10))
    trust_color = GREEN if trust_score>=70 else YELLOW if trust_score>=40 else RED
    trust_label = "HIGH TRUST" if trust_score>=70 else "MODERATE TRUST" if trust_score>=40 else "LOW TRUST"
    elements.append(Paragraph("Summary", h2_s))
    st2 = Table([["TRUST SCORE","✓ VERIFIED","⚠ INACCURATE","✗ FALSE"],[f"{trust_score}% — {trust_label}",str(verified_count),str(inaccurate_count),str(false_count)]], colWidths=[60*mm,40*mm,40*mm,35*mm])
    st2.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),CARD_BG),("BACKGROUND",(0,1),(-1,1),DARK_BG),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTNAME",(0,1),(-1,1),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,0),8),("FONTSIZE",(0,1),(-1,1),13),("TEXTCOLOR",(0,0),(-1,0),MUTED),("TEXTCOLOR",(0,1),(0,1),trust_color),("TEXTCOLOR",(1,1),(1,1),GREEN),("TEXTCOLOR",(2,1),(2,1),YELLOW),("TEXTCOLOR",(3,1),(3,1),RED),("ALIGN",(0,0),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),8),("GRID",(0,0),(-1,-1),0.3,MUTED)]))
    elements.append(st2); elements.append(Spacer(1,14))
    elements.append(Paragraph("Detailed Findings", h2_s))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=MUTED, spaceAfter=8))
    for i, r in enumerate(claims_data):
        claim=r["claim"]; verif=r["verification"]
        verdict=verif.get("verdict","False"); conf=verif.get("confidence",0)
        explain=verif.get("explanation",""); correct=verif.get("correct_fact","")
        sources=verif.get("sources",[]); category=claim.get("category","other").upper()
        v_color={"Verified":GREEN,"Inaccurate":YELLOW,"False":RED}.get(verdict,RED)
        v_icon={"Verified":"✓","Inaccurate":"⚠","False":"✗"}.get(verdict,"?")
        ht=Table([[Paragraph(f"#{i+1}  {category}",small_s),Paragraph(f"{v_icon} {verdict.upper()}    Confidence: {conf}%",ParagraphStyle("vh",fontName="Helvetica-Bold",fontSize=9,textColor=v_color,alignment=TA_RIGHT))]],colWidths=[80*mm,95*mm])
        ht.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),CARD_BG),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),("LEFTPADDING",(0,0),(0,-1),8),("RIGHTPADDING",(-1,0),(-1,-1),8),("LINEBELOW",(0,0),(-1,-1),1,v_color)]))
        elements.append(ht)
        rows=[[Paragraph(claim.get("claim",""),claim_s)],[Paragraph(explain,small_s)]]
        if correct and correct!="Claim is accurate.": rows.append([Paragraph(f"Correct fact: {correct}",correct_s)])
        if sources:
            st3="  •  ".join([s.get("title","")[:55] for s in sources if s.get("title")])
            if st3: rows.append([Paragraph(f"Sources: {st3}",small_s)])
        bt=Table([[row[0]] for row in rows],colWidths=[175*mm])
        bt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),DARK_BG),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),("LEFTPADDING",(0,0),(-1,-1),10),("RIGHTPADDING",(0,0),(-1,-1),10)]))
        elements.append(bt); elements.append(Spacer(1,7))
    elements.append(Spacer(1,8))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=MUTED))
    elements.append(Paragraph("Generated by FactLens — AI-powered fact verification | Built for CogCulture Assessment", ParagraphStyle("f",fontName="Helvetica",fontSize=7.5,textColor=MUTED,alignment=TA_CENTER,spaceBefore=6)))
    doc.build(elements); buf.seek(0)
    return buf.getvalue()


st.set_page_config(page_title="FactLens – AI Claim Verifier", page_icon="🔍", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; background: #0d1117; }
section[data-testid="stSidebar"] { background: #010409 !important; border-right: 1px solid #21262d; }
section[data-testid="stSidebar"] * { color: #c9d1d9 !important; }
.block-container { padding-top: 1.5rem !important; }
.hero { background: linear-gradient(135deg,#010409 0%,#0d1117 40%,#0c1929 100%); border: 1px solid #21262d; border-radius: 20px; padding: 3rem 2.5rem 2.5rem; margin-bottom: 2rem; position: relative; overflow: hidden; }
.hero::before { content:''; position:absolute; top:-60px; right:-60px; width:240px; height:240px; background:radial-gradient(circle,rgba(0,212,255,0.08) 0%,transparent 70%); border-radius:50%; }
.hero-eyebrow { font-family:'Syne',sans-serif; font-size:0.7rem; letter-spacing:4px; text-transform:uppercase; color:#00d4ff; margin-bottom:0.8rem; }
.hero-title { font-family:'Syne',sans-serif; font-size:3.2rem; font-weight:800; color:#f0f6fc; line-height:1.05; margin:0 0 0.7rem 0; }
.hero-title span { color:#00d4ff; }
.hero-sub { font-size:1rem; color:#8b949e; max-width:540px; line-height:1.65; }
.hero-pipeline { display:flex; align-items:center; gap:0.5rem; margin-top:1.5rem; flex-wrap:wrap; }
.pipe-step { background:#161b22; border:1px solid #30363d; border-radius:8px; padding:5px 12px; font-size:0.78rem; color:#8b949e; font-weight:500; }
.pipe-arrow { color:#30363d; font-size:1rem; }
div[data-testid="stFileUploadDropzone"] { background:#161b22 !important; border:2px dashed #30363d !important; border-radius:14px !important; }
div[data-testid="stFileUploadDropzone"]:hover { border-color:#00d4ff !important; }
.claim-card { background:#161b22; border-radius:14px; padding:1.4rem 1.6rem 1.2rem; margin-bottom:1rem; border:1px solid #21262d; border-left:4px solid; }
.claim-card.verified   { border-left-color:#22c55e; }
.claim-card.inaccurate { border-left-color:#f59e0b; }
.claim-card.false      { border-left-color:#ef4444; }
.verdict-badge { display:inline-flex; align-items:center; gap:5px; padding:3px 10px; border-radius:6px; font-size:0.72rem; font-weight:700; letter-spacing:1px; text-transform:uppercase; font-family:'Syne',sans-serif; }
.badge-verified   { background:rgba(34,197,94,0.12);  color:#4ade80; border:1px solid rgba(34,197,94,0.25); }
.badge-inaccurate { background:rgba(245,158,11,0.12); color:#fbbf24; border:1px solid rgba(245,158,11,0.25); }
.badge-false      { background:rgba(239,68,68,0.12);  color:#f87171; border:1px solid rgba(239,68,68,0.25); }
.cat-tag { display:inline-block; padding:2px 9px; border-radius:4px; font-size:0.68rem; font-weight:600; text-transform:uppercase; letter-spacing:0.8px; background:#21262d; color:#8b949e; margin-left:8px; }
.conf-badge { float:right; font-size:0.75rem; color:#8b949e; margin-top:1px; }
.claim-text { color:#e6edf3; font-size:0.95rem; font-weight:500; margin:0.7rem 0 0.5rem; line-height:1.5; }
.explain-text { color:#8b949e; font-size:0.85rem; line-height:1.65; }
.correct-box { margin-top:0.8rem; padding:0.7rem 1rem; background:rgba(0,212,255,0.06); border:1px solid rgba(0,212,255,0.18); border-radius:8px; color:#7dd3fc; font-size:0.83rem; line-height:1.5; }
.source-row { margin-top:0.8rem; display:flex; flex-wrap:wrap; gap:0.5rem; }
.source-chip { display:inline-flex; align-items:center; gap:5px; background:#0d1117; border:1px solid #30363d; border-radius:6px; padding:3px 10px; font-size:0.75rem; color:#58a6ff; text-decoration:none; }
.stat-box { background:#161b22; border:1px solid #21262d; border-radius:14px; padding:1.3rem; text-align:center; }
.stat-num { font-family:'Syne',sans-serif; font-size:2.2rem; font-weight:800; line-height:1; }
.stat-lbl { font-size:0.78rem; color:#8b949e; margin-top:0.3rem; }
.trust-banner { border-radius:16px; padding:2rem; text-align:center; margin:1.5rem 0; }
.trust-num { font-family:'Syne',sans-serif; font-size:4rem; font-weight:800; line-height:1; }
.trust-label { font-size:0.85rem; margin-top:0.4rem; letter-spacing:2px; text-transform:uppercase; font-weight:600; }
.stButton > button { font-family:'Syne',sans-serif !important; font-weight:700 !important; letter-spacing:1px !important; border-radius:10px !important; }
.stButton > button[kind="primary"] { background:linear-gradient(135deg,#0ea5e9 0%,#00d4ff 100%) !important; border:none !important; color:#0d1117 !important; }
.stDownloadButton > button { background:#161b22 !important; border:1px solid #30363d !important; color:#c9d1d9 !important; font-family:'Syne',sans-serif !important; font-weight:600 !important; border-radius:10px !important; }
.stDownloadButton > button:hover { border-color:#00d4ff !important; color:#00d4ff !important; }
.stProgress > div > div { background:linear-gradient(90deg,#0ea5e9,#00d4ff) !important; }
.section-title { font-family:'Syne',sans-serif; font-size:1.1rem; font-weight:700; color:#f0f6fc; margin-bottom:1rem; }
.info-grid { display:grid; grid-template-columns:1fr 1fr; gap:0.7rem; margin-top:0.5rem; }
.info-item { background:#161b22; border:1px solid #21262d; border-radius:10px; padding:0.8rem 1rem; font-size:0.82rem; color:#8b949e; }
.info-item b { color:#c9d1d9; display:block; margin-bottom:2px; }
.empty-state { text-align:center; padding:4rem 2rem; background:#161b22; border:2px dashed #21262d; border-radius:20px; }
.empty-icon { font-size:3.5rem; margin-bottom:1rem; }
.empty-title { font-family:'Syne',sans-serif; font-size:1.2rem; color:#c9d1d9; }
.empty-sub { font-size:0.88rem; color:#8b949e; margin-top:0.4rem; line-height:1.6; }
#MainMenu { visibility:hidden; } footer { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

# ── HARDCODED KEYS — no secrets needed ──────────────────────────────────────────
GROQ_API_KEY   = "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"
TAVILY_API_KEY = "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"

# ── SIDEBAR ──────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:1.2rem 0 0.5rem;">
        <div style="font-family:'Syne',sans-serif;font-size:1.6rem;font-weight:800;color:#f0f6fc;">
            Fact<span style="color:#00d4ff;">Lens</span>
        </div>
        <div style="font-size:0.7rem;color:#8b949e;letter-spacing:2px;text-transform:uppercase;margin-top:2px;">
            AI Fact Verifier
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown('<div style="font-family:Syne,sans-serif;font-size:0.7rem;letter-spacing:2px;text-transform:uppercase;color:#8b949e;margin-bottom:0.6rem;">Navigation</div>', unsafe_allow_html=True)
    page = st.radio("", ["🏠  Home", "✨  Features", "⬇️  Download Report"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown('<div style="font-family:Syne,sans-serif;font-size:0.7rem;letter-spacing:2px;text-transform:uppercase;color:#8b949e;margin-bottom:0.6rem;">Settings</div>', unsafe_allow_html=True)
    # Auto-detect all claims — no limit
    model_choice = st.selectbox("LLM Model", ["llama-3.3-70b-versatile", "llama3-70b-8192", "mixtral-8x7b-32768"])
    report_fmt   = st.radio("Report format", ["PDF Report", "JSON Data"], index=0)
    st.markdown("---")
    st.markdown('<div style="font-size:0.75rem;color:#8b949e;line-height:1.7;">Built for <b style="color:#c9d1d9;">CogCulture</b><br>PM Trainee Assessment</div>', unsafe_allow_html=True)


# ── FEATURES PAGE ────────────────────────────────────────────────────────────────
if page == "✨  Features":
    st.markdown("""
    <div class="hero">
        <div class="hero-eyebrow">What FactLens Can Do</div>
        <h1 class="hero-title">Key <span>Features</span></h1>
        <p class="hero-sub">Everything built into FactLens to make fact-checking fast, accurate, and professional.</p>
    </div>
    """, unsafe_allow_html=True)
    f1, f2 = st.columns(2, gap="large")
    feats = [
        ("🤖","Smart Claim Extraction","Uses LLaMA 3.3 70B to identify only real verifiable claims — statistics, dates, revenue figures, technical specs — and ignores opinions or fluff."),
        ("🌐","Live Web Verification","Each claim is cross-referenced against the live web using Tavily search in real time. No static database — always current."),
        ("🏷️","Three-Tier Verdict System","Every claim gets labelled Verified ✓, Inaccurate ⚠, or False ✗ — with a confidence score and explanation for each verdict."),
        ("💡","Correct Fact Suggestions","When a claim is wrong or outdated, FactLens provides the correct current fact along with the source URL."),
        ("📊","Document Trust Score","An overall credibility % based on the ratio of verified claims — instantly tells you how trustworthy a document is."),
        ("📄","Professional PDF Report","Download a fully formatted PDF report with all verdicts, explanations, sources, and trust score — ready to share."),
    ]
    for i,(icon,title,desc) in enumerate(feats):
        with (f1 if i%2==0 else f2):
            st.markdown(f'<div class="claim-card verified" style="border-left-color:#00d4ff;margin-bottom:1rem;"><div style="font-size:1.8rem;margin-bottom:0.5rem;">{icon}</div><div style="font-family:Syne,sans-serif;font-size:1rem;font-weight:700;color:#f0f6fc;margin-bottom:0.4rem;">{title}</div><div style="font-size:0.85rem;color:#8b949e;line-height:1.6;">{desc}</div></div>', unsafe_allow_html=True)
    st.stop()

# ── DOWNLOAD REPORT PAGE ─────────────────────────────────────────────────────────
elif page == "⬇️  Download Report":
    st.markdown("""
    <div class="hero">
        <div class="hero-eyebrow">Export Your Results</div>
        <h1 class="hero-title">Download <span>Report</span></h1>
        <p class="hero-sub">Run a fact-check from Home first, then download your report here.</p>
    </div>
    """, unsafe_allow_html=True)
    if "last_results" in st.session_state:
        r = st.session_state["last_results"]
        st.success(f"✅ Last analysis: **{r['doc_name']}** — {r['total']} claims checked")
        c1, c2 = st.columns(2, gap="large")
        with c1:
            st.download_button("⬇️ Download PDF Report", data=r["pdf_bytes"], file_name=f"FactLens_Report_{r['doc_name'].replace('.pdf','')}.pdf", mime="application/pdf", use_container_width=True)
        with c2:
            st.download_button("⬇️ Download JSON Data", data=r["json_str"], file_name=f"FactLens_{r['doc_name']}.json", mime="application/json", use_container_width=True)
    else:
        st.markdown('<div class="empty-state"><div class="empty-icon">📄</div><div class="empty-title">No analysis yet</div><div class="empty-sub">Go to <b>Home</b>, upload a PDF and run the analysis first.</div></div>', unsafe_allow_html=True)
    st.stop()

# ── HOME PAGE ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-eyebrow">AI · Fact Verification · Live Web Search</div>
    <h1 class="hero-title">Fact<span>Lens</span></h1>
    <p class="hero-sub">Upload any PDF — marketing report, whitepaper, press release — and get an instant truth audit powered by live web data.</p>
    <div class="hero-pipeline">
        <span class="pipe-step">📄 Upload PDF</span><span class="pipe-arrow">→</span>
        <span class="pipe-step">🤖 Extract Claims</span><span class="pipe-arrow">→</span>
        <span class="pipe-step">🌐 Live Web Verify</span><span class="pipe-arrow">→</span>
        <span class="pipe-step">📊 Truth Report</span>
    </div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1.35, 1], gap="large")
with col1:
    st.markdown('<div class="section-title">📄 Upload Document</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Drop PDF here", type=["pdf"], label_visibility="collapsed")
with col2:
    st.markdown('<div class="section-title">ℹ️ What gets checked?</div>', unsafe_allow_html=True)
    st.markdown('<div class="info-grid"><div class="info-item"><b>📊 Statistics</b>Percentages, numbers, rates</div><div class="info-item"><b>📅 Dates</b>Event years, launch dates</div><div class="info-item"><b>💰 Financial</b>Revenue, market cap, growth</div><div class="info-item"><b>⚙️ Technical</b>Versions, specs, rankings</div></div>', unsafe_allow_html=True)


def extract_text(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t: text += t + "\n"
    return text.strip()

def extract_claims(text, client, model, n=20):
    prompt = f"""You are a fact-checking specialist. Extract EVERY specific, verifiable factual claim from the text below.

Focus ONLY on:
- Statistics and percentages (e.g., "67% of users prefer X")
- Specific numbers, revenue, market cap, financial figures
- Named dates and years of events
- Technical specifications or version numbers
- Named rankings or comparisons ("X is the largest...")
- Any specific numeric claim, salary figure, valuation, user count

Do NOT skip any verifiable claim — extract ALL of them.
Skip only pure opinions, marketing fluff, or vague statements with zero numbers or dates.

Return a JSON array with ALL found claims. Each object:
  - "claim": the exact claim text, 1-2 sentences max
  - "category": one of [statistic, date, financial, technical, ranking, other]
  - "search_query": 6-8 word focused search query to verify this

Return ONLY valid JSON. No markdown, no explanation.

TEXT:
{text[:8000]}"""

    r = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=4000,
    )
    raw = r.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    claims = json.loads(raw)
    return claims if isinstance(claims, list) else []

def search_web(query, api_key):
    # Try with original query first (advanced depth)
    try:
        resp = requests.post("https://api.tavily.com/search", json={
            "api_key": api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": 5,
            "include_answer": True,
        }, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("results"):
            return data
    except Exception:
        pass

    # Fallback: broader query (first 6 words)
    try:
        short_query = " ".join(query.split()[:6])
        resp = requests.post("https://api.tavily.com/search", json={
            "api_key": api_key,
            "query": short_query,
            "search_depth": "basic",
            "max_results": 5,
            "include_answer": True,
        }, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e), "results": [], "answer": ""}

def verify_claim(claim, search_data, client, model):
    results_text = ""
    sources = []

    if search_data.get("answer"):
        results_text += f"Web Summary: {search_data['answer']}\n\n"
    for r in search_data.get("results", []):
        results_text += f"Source: {r.get('title','')}\nURL: {r.get('url','')}\nContent: {r.get('content','')[:500]}\n\n"
        sources.append({"title": r.get("title",""), "url": r.get("url","")})

    has_web_evidence = bool(results_text.strip())

    prompt = f"""You are a rigorous fact-checker with deep knowledge. Evaluate this claim.

CLAIM: "{claim}"

WEB EVIDENCE:
{results_text if has_web_evidence else "No web results — use your own training knowledge to evaluate this claim."}

IMPORTANT RULES:
- If web evidence is available, use it as primary source
- If NO web evidence, use your own knowledge to fact-check
- NEVER write "Unknown" or "No information available" as correct_fact — always give the real correct fact
- For CGPA claims: Indian universities use 10-point scale, US universities use 4-point scale
- For date/year claims: use your knowledge of when events actually occurred
- For statistics: cite the actual correct figure you know

Verdict:
- "Verified"   → claim is accurate
- "Inaccurate" → wrong/outdated figure — provide the REAL correct figure
- "False"      → demonstrably wrong — provide the REAL correct fact

Return JSON:
  - "verdict": "Verified" | "Inaccurate" | "False"
  - "confidence": integer 1-100
  - "explanation": 2-3 sentences explaining WHY with specific facts
  - "correct_fact": ALWAYS the actual correct fact. Never write Unknown or No information available.

Return ONLY valid JSON. No markdown."""

    r = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=700,
    )
    raw = r.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    result = json.loads(raw)
    result["sources"] = sources[:2]
    return result

def render_card(idx, claim, verification):
    verdict=verification.get("verdict","False"); confidence=verification.get("confidence",0)
    explanation=verification.get("explanation",""); correct=verification.get("correct_fact","")
    sources=verification.get("sources",[]); category=claim.get("category","other"); verdict_l=verdict.lower()
    icons={"verified":"✓","inaccurate":"⚠","false":"✗"}
    cat_icons={"statistic":"📊","date":"📅","financial":"💰","technical":"⚙️","ranking":"🏆","other":"📌"}
    sources_html="".join([f'<a href="{s["url"]}" target="_blank" class="source-chip">🔗 {s.get("title","")[:50]}</a>' for s in sources if s.get("url")])
    correct_html=f'<div class="correct-box">💡 <b>Correct fact:</b> {correct}</div>' if correct and correct!="Claim is accurate." else ""
    st.markdown(f'<div class="claim-card {verdict_l}"><span class="verdict-badge badge-{verdict_l}">{icons.get(verdict_l,"?")} {verdict}</span><span class="cat-tag">{cat_icons.get(category,"📌")} {category}</span><span class="conf-badge">Confidence: {confidence}%</span><div class="claim-text">#{idx+1} — {claim["claim"]}</div><div class="explain-text">{explanation}</div>{correct_html}<div class="source-row">{sources_html}</div></div>', unsafe_allow_html=True)


if uploaded_file:
    groq_client = Groq(api_key=GROQ_API_KEY)
    st.markdown("---")
    if st.button("🚀 Start Fact-Check Analysis", use_container_width=True, type="primary"):
        with st.spinner("📖 Reading PDF..."):
            pdf_text = extract_text(uploaded_file)
        if not pdf_text or len(pdf_text) < 100:
            st.error("❌ Could not extract text. Try a different PDF."); st.stop()
        st.success(f"✅ Extracted {len(pdf_text):,} characters from PDF")
        with st.spinner("🤖 Identifying verifiable claims..."):
            try: claims = extract_claims(pdf_text, groq_client, model_choice)
            except Exception as e: st.error(f"❌ Claim extraction failed: {e}"); st.stop()
        if not claims: st.warning("⚠️ No verifiable claims found."); st.stop()
        st.info(f"🎯 Found **{len(claims)}** claims to verify")
        st.markdown("---")
        st.markdown('<div class="section-title">📋 Verification Results</div>', unsafe_allow_html=True)
        progress_bar = st.progress(0); status_text = st.empty()
        results = []; verified_count = inaccurate_count = false_count = 0
        for i, claim in enumerate(claims):
            status_text.markdown(f"🔍 Checking claim {i+1}/{len(claims)}: *{claim['claim'][:65]}...*")
            search_data = search_web(claim.get("search_query", claim["claim"]), TAVILY_API_KEY)
            try: verification = verify_claim(claim["claim"], search_data, groq_client, model_choice)
            except Exception as e: verification = {"verdict":"False","confidence":0,"explanation":f"Error: {e}","correct_fact":"Could not verify.","sources":[]}
            results.append({"claim":claim,"verification":verification})
            v = verification.get("verdict","False")
            if v=="Verified": verified_count+=1
            elif v=="Inaccurate": inaccurate_count+=1
            else: false_count+=1
            render_card(i, claim, verification)
            progress_bar.progress((i+1)/len(claims)); time.sleep(0.3)
        status_text.empty(); progress_bar.empty()

        st.markdown("---")
        st.markdown('<div class="section-title">📊 Analysis Summary</div>', unsafe_allow_html=True)
        trust_score = int((verified_count/len(claims))*100) if claims else 0
        t_color = "#22c55e" if trust_score>=70 else "#f59e0b" if trust_score>=40 else "#ef4444"
        t_bg = "rgba(34,197,94,0.07)" if trust_score>=70 else "rgba(245,158,11,0.07)" if trust_score>=40 else "rgba(239,68,68,0.07)"
        t_label = "HIGH TRUST" if trust_score>=70 else "MODERATE TRUST" if trust_score>=40 else "LOW TRUST"
        c1,c2,c3,c4 = st.columns(4)
        for col,num,color,label in [(c1,len(claims),"#58a6ff","Claims Analyzed"),(c2,verified_count,"#22c55e","✓ Verified"),(c3,inaccurate_count,"#f59e0b","⚠ Inaccurate"),(c4,false_count,"#ef4444","✗ False")]:
            with col: st.markdown(f'<div class="stat-box"><div class="stat-num" style="color:{color}">{num}</div><div class="stat-lbl">{label}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="trust-banner" style="background:{t_bg};border:1px solid {t_color}33;"><div class="trust-num" style="color:{t_color}">{trust_score}%</div><div class="trust-label" style="color:{t_color}">Document Trust Score — {t_label}</div></div>', unsafe_allow_html=True)

        st.markdown("---")
        export_data = {"document":uploaded_file.name,"generated_at":datetime.datetime.now().isoformat(),"total_claims":len(claims),"verified":verified_count,"inaccurate":inaccurate_count,"false":false_count,"trust_score":trust_score,
            "results":[{"claim":r["claim"]["claim"],"category":r["claim"]["category"],"verdict":r["verification"]["verdict"],"confidence":r["verification"]["confidence"],"explanation":r["verification"]["explanation"],"correct_fact":r["verification"]["correct_fact"]} for r in results]}
        try: pdf_bytes = generate_pdf_report(uploaded_file.name, results, verified_count, inaccurate_count, false_count, trust_score)
        except: pdf_bytes = None
        json_str = json.dumps(export_data, indent=2)
        st.session_state["last_results"] = {"doc_name":uploaded_file.name,"total":len(claims),"pdf_bytes":pdf_bytes,"json_str":json_str}
        dc1, dc2 = st.columns(2, gap="medium")
        with dc1:
            if pdf_bytes: st.download_button("⬇️ Download PDF Report", data=pdf_bytes, file_name=f"FactLens_Report_{uploaded_file.name.replace('.pdf','')}.pdf", mime="application/pdf", use_container_width=True)
        with dc2:
            st.download_button("⬇️ Download JSON Data", data=json_str, file_name=f"FactLens_{uploaded_file.name}.json", mime="application/json", use_container_width=True)
else:
    st.markdown('<div class="empty-state"><div class="empty-icon">🔍</div><div class="empty-title">No document uploaded yet</div><div class="empty-sub">Upload any PDF — marketing reports, research papers, press releases.<br>FactLens will extract every verifiable claim and cross-check it against live web data.</div></div>', unsafe_allow_html=True) 