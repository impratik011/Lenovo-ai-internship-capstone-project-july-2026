# app.py - WattSense AI with Streamlit + Groq (Redesigned Green UI + PDF Export)

import streamlit as st
import requests
import os
import json
import time
from io import BytesIO
from dotenv import load_dotenv

# Import ReportLab modules for clean PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ===================================================
# 1. LOAD API KEY FROM .env FILE
# ===================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("⚠️ API Key not found! Please create a .env file with GROQ_API_KEY=your_key")
    st.stop()

# ===================================================
# 2. PAGE CONFIGURATION
# ===================================================

st.set_page_config(
    page_title="⚡ WattSense AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ===================================================
# 3. THEME (GREEN) - CUSTOM CSS
# ===================================================

PRIMARY_GREEN = "#16a34a"
DARK_GREEN = "#15803d"
LIGHT_GREEN_BG = "#eafaf0"
LIGHT_YELLOW_BG = "#fef9e7"
TEXT_DARK = "#1f2937"
TEXT_MUTED = "#6b7280"

st.markdown(f"""
<style>

    /* Page background */
    .stApp {{
        background-color: #f4f7f6;
    }}

    header[data-testid="stHeader"] {{
        background: transparent;
    }}

    /* Card containers (st.container(border=True)) */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: #ffffff;
        border-radius: 16px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        padding: 8px 6px;
    }}

    /* Primary buttons -> green */
    .stButton > button[kind="primary"] {{
        background-color: {PRIMARY_GREEN};
        border-color: {PRIMARY_GREEN};
        color: white;
        font-weight: 600;
        border-radius: 10px;
        padding: 0.6rem 1rem;
    }}
    .stButton > button[kind="primary"]:hover {{
        background-color: {DARK_GREEN};
        border-color: {DARK_GREEN};
    }}

    /* Secondary / pill buttons */
    .stButton > button[kind="secondary"] {{
        background-color: #ffffff;
        border: 1px solid #d1d5db;
        color: {TEXT_DARK};
        border-radius: 999px;
        font-weight: 500;
    }}
    .stButton > button[kind="secondary"]:hover {{
        border-color: {PRIMARY_GREEN};
        color: {PRIMARY_GREEN};
    }}

    .app-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 14px 4px;
    }}
    .app-header-left {{
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    .logo-box {{
        width: 52px;
        height: 52px;
        border-radius: 12px;
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.7rem;
        flex-shrink: 0;
    }}
    .app-header-title {{
        font-size: 1.65rem;
        font-weight: 700;
        color: {TEXT_DARK};
        margin: 0;
        line-height: 1.2;
    }}
    .app-header-sub {{
        font-size: 0.9rem;
        color: {TEXT_MUTED};
        margin: 0;
    }}
    .status-pill {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.9rem;
        color: {TEXT_DARK};
    }}
    .status-dot {{
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: {PRIMARY_GREEN};
        display: inline-block;
    }}

    .tip-box {{
        background-color: {LIGHT_GREEN_BG};
        border-radius: 12px;
        padding: 14px 16px;
        color: {TEXT_DARK};
        font-size: 0.92rem;
    }}
    .fact-box {{
        font-size: 0.88rem;
        color: {TEXT_MUTED};
    }}

    /* Result rows (matches target mockup) */
    .result-row {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-radius: 12px;
        padding: 16px 18px;
        margin-bottom: 10px;
    }}
    .result-row.green {{
        background-color: {LIGHT_GREEN_BG};
    }}
    .result-row.yellow {{
        background-color: {LIGHT_YELLOW_BG};
    }}
    .result-row-label {{
        display: flex;
        align-items: center;
        gap: 10px;
        font-weight: 600;
        font-size: 0.98rem;
    }}
    .result-row-label.green-text {{
        color: {DARK_GREEN};
    }}
    .result-row-label.yellow-text {{
        color: #b45309;
    }}
    .result-row-value {{
        font-weight: 700;
        font-size: 1.02rem;
        color: {TEXT_DARK};
    }}

    /* Fix expander (View your personalized tips / appliance breakdown) visibility */
    div[data-testid="stExpander"] {{
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        overflow: hidden;
    }}
    div[data-testid="stExpander"] summary {{
        background-color: #ffffff;
        color: {TEXT_DARK} !important;
        font-weight: 600;
        padding: 10px 14px;
    }}
    div[data-testid="stExpander"] summary:hover {{
        color: {PRIMARY_GREEN} !important;
    }}
    div[data-testid="stExpander"] summary svg {{
        fill: {TEXT_DARK};
    }}
    div[data-testid="stExpander"] summary p {{
        color: {TEXT_DARK} !important;
    }}
    div[data-testid="stExpanderDetails"] {{
        background-color: #ffffff;
        color: {TEXT_DARK} !important;
        padding: 10px 16px 16px 16px;
    }}
    div[data-testid="stExpanderDetails"] p,
    div[data-testid="stExpanderDetails"] li,
    div[data-testid="stExpanderDetails"] span,
    div[data-testid="stExpanderDetails"] div {{
        color: {TEXT_DARK} !important;
    }}

    .footer-bar {{
        background-color: {LIGHT_GREEN_BG};
        border-radius: 14px;
        padding: 18px 10px;
        text-align: center;
        margin-top: 20px;
    }}
    .footer-title {{
        color: {DARK_GREEN};
        font-weight: 600;
    }}
    .footer-sub {{
        color: {TEXT_MUTED};
        font-size: 0.85rem;
    }}
</style>
""", unsafe_allow_html=True)

# ===================================================
# 4. INITIALIZE SESSION STATE & CALLBACKS
# ===================================================
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""
if 'ai_response' not in st.session_state:
    st.session_state.ai_response = None   # will hold parsed dict, or a string on error

def set_example(text):
    st.session_state.user_input = text
    st.session_state.ai_response = None

# ===================================================
# 5. PDF GENERATION HELPER FUNCTION
# ===================================================

def export_to_pdf(input_text, data):
    """Generates a structured, clean PDF using ReportLab from the structured analysis data"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )

    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'],
        fontSize=24, leading=28, textColor=colors.HexColor(DARK_GREEN), spaceAfter=15
    )
    section_style = ParagraphStyle(
        'SectionHeading', parent=styles['Heading2'],
        fontSize=14, leading=18, textColor=colors.HexColor("#1f2937"), spaceBefore=15, spaceAfter=8
    )
    body_style = ParagraphStyle(
        'BodyDark', parent=styles['Normal'],
        fontSize=10, leading=14, textColor=colors.HexColor("#374151")
    )

    # Document Header
    story.append(Paragraph("⚡ WattSense AI - Energy Audit Report", title_style))
    story.append(Paragraph(f"<b>Generated on:</b> {time.strftime('%Y-%m-%d %H:%M:%S')}", body_style))
    story.append(Spacer(1, 15))

    # User Input Section
    story.append(Paragraph("📋 Input Configuration:", section_style))
    story.append(Paragraph(input_text, body_style))
    story.append(Spacer(1, 15))

    # Summary Section
    story.append(Paragraph("📊 Energy Consumption Summary:", section_style))

    summary_rows = [
        ("Monthly Electricity Consumption (kWh)", f"{data.get('monthly_units', 'N/A')} units"),
        ("Monthly Electricity Cost (₹8 per unit)", f"₹{data.get('monthly_cost', 'N/A')}"),
        ("Total Potential Savings", f"₹{data.get('total_savings', 'N/A')} per month"),
    ]
    for label, value in summary_rows:
        p = Paragraph(f"<b>{label}:</b> {value}", body_style)
        t = Table([[p]], colWidths=[500])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#dcfce7")),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        story.append(t)
        story.append(Spacer(1, 6))

    # Breakdown Section (if present)
    breakdown = data.get("breakdown") or []
    if breakdown:
        story.append(Spacer(1, 10))
        story.append(Paragraph("🔌 Appliance Breakdown:", section_style))
        for item in breakdown:
            line = f"{item.get('appliance', '')}: {item.get('units', '')} units (₹{item.get('cost', '')})"
            story.append(Paragraph(f"• {line}", body_style))
            story.append(Spacer(1, 3))

    # Tips Section
    tips = data.get("tips") or []
    if tips:
        story.append(Spacer(1, 15))
        story.append(Paragraph("💡 Personalized Energy Saving Tips:", section_style))
        for i, tip in enumerate(tips, start=1):
            p = Paragraph(f"{i}. {tip}", body_style)
            t = Table([[p]], colWidths=[500])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#fffbeb")),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ]))
            story.append(t)
            story.append(Spacer(1, 6))

    doc.build(story)
    buffer.seek(0)
    return buffer

# ===================================================
# 6. SYSTEM PROMPT (English Only, STRICT JSON OUTPUT)
# ===================================================

SYSTEM_PROMPT = """You are WattSense AI - India's friendly energy saving advisor.

IMPORTANT: Respond ONLY in English. DO NOT use Bengali or any other regional language script.

You MUST respond with ONLY a valid JSON object and nothing else - no preamble, no markdown
code fences, no explanation text before or after. The JSON object must have this exact shape:

{
  "monthly_units": <number, total monthly kWh across all appliances>,
  "monthly_cost": <number, total monthly cost in rupees at ₹8 per unit>,
  "total_savings": <number, realistic total potential monthly savings in rupees if the user follows the tips>,
  "breakdown": [
    {"appliance": "<name and quantity>", "units": <number>, "cost": <number>}
  ],
  "tips": [
    "<actionable, personalized energy-saving tip 1>",
    "<actionable, personalized energy-saving tip 2>",
    "<actionable, personalized energy-saving tip 3>"
  ]
}

Use this appliance guide (monthly per single appliance):
- 1.5 Ton AC: 360 units (₹2,880)
- Refrigerator: 144 units (₹1,152)
- LED TV: 12 units (₹96)
- Ceiling Fan: 22.5 units (₹180)
- LED Bulb: 1.5 units (₹12)
- Water Heater: 120 units (₹960)
- Laptop: 6 units (₹48)
- Washing Machine: 15 units (₹120)
- Microwave: 12 units (₹96)

Multiply per-appliance values by the quantity the user mentions. Be encouraging and practical
in the tips, and make sure total_savings is a believable number based on the tips given.
Respond with ONLY the JSON object."""

# ===================================================
# 7. GROQ API FUNCTION
# ===================================================

def call_groq_api(user_input):
    """Call Groq API and return a parsed dict, or a string starting with '❌' on error"""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ],
        "temperature": 0.5,
        "max_tokens": 800,
        "response_format": {"type": "json_object"}
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        raw_text = result["choices"][0]["message"]["content"]

        # Clean up in case the model wraps it in code fences anyway
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()

        parsed = json.loads(cleaned)
        return parsed
    except requests.exceptions.Timeout:
        return "❌ Request timed out. Please try again."
    except requests.exceptions.HTTPError as e:
        try:
            error_detail = response.json()
            if "error" in error_detail:
                return f"❌ API Error: {error_detail['error'].get('message', str(e))}"
        except Exception:
            return f"❌ API Error: {str(e)}"
    except json.JSONDecodeError:
        return "❌ Could not parse the AI response. Please try again."
    except requests.exceptions.RequestException as e:
        return f"❌ Network Error: {str(e)}"

# ===================================================
# 8. RESULT ROW RENDER HELPER
# ===================================================

def render_result_row(icon, label, value, color="green"):
    text_class = "green-text" if color == "green" else "yellow-text"
    st.markdown(
        f"""
        <div class="result-row {color}">
            <div class="result-row-label {text_class}">
                <span>{icon}</span> <span>{label}</span>
            </div>
            <div class="result-row-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ===================================================
# 9. HEADER BAR
# ===================================================

with st.container(border=True):
    h1, h2 = st.columns([3, 2])
    with h1:
        st.markdown(
            """
            <div class="app-header-left">
                <div class="logo-box">⚡</div>
                <div>
                    <p class="app-header-title">WattSense AI</p>
                    <p class="app-header-sub">AI-Powered Energy Saving Advisor</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with h2:
        s1, s2 = st.columns([1, 1])
        with s1:
            st.markdown(
                """
                <div class="status-pill" style="justify-content:flex-end; padding-top: 18px;">
                    <span class="status-dot"></span> API Connected
                </div>
                """,
                unsafe_allow_html=True
            )
        with s2:
            st.button("ℹ️ About WattSense AI", key="about_btn", use_container_width=True)

# ===================================================
# 10. QUICK EXAMPLES CARD
# ===================================================

with st.container(border=True):
    st.markdown(
        f"""<p style="font-weight:700; font-size:1.0rem; color:{TEXT_DARK}; margin-bottom:10px;">
            Try Quick Examples:
        </p>""",
        unsafe_allow_html=True
    )

    ex1, ex2, ex3 = st.columns(3)
    ex1.button(
        "🏠 Small Home",
        key="ex1",
        use_container_width=True,
        on_click=set_example,
        args=("1 AC, 1 fridge, 2 lights, 1 fan, 1 TV",)
    )
    ex2.button(
        "🏢 Large Home",
        key="ex2",
        use_container_width=True,
        on_click=set_example,
        args=("2 ACs, 1 fridge, 4 lights, 1 TV, 2 fans, 1 water heater",)
    )
    ex3.button(
        "💼 Office",
        key="ex3",
        use_container_width=True,
        on_click=set_example,
        args=("4 ACs, 10 laptops, 8 lights, 1 fridge, 1 microwave",)
    )

# ===================================================
# 11. MAIN BODY: INPUT CARD + TIPS CARDS
# ===================================================

body_left, body_right = st.columns([3, 2])

with body_left:
    with st.container(border=True):
        st.markdown(
            f"""
            <p style="font-weight:700; font-size:1.1rem; color:{TEXT_DARK}; margin-bottom:0;">
                📝 Describe Your Appliances
            </p>
            <p style="color:{TEXT_MUTED}; font-size:0.9rem; margin-top:2px;">
                Tell us what appliances you use and how many.
            </p>
            """,
            unsafe_allow_html=True
        )

        user_input = st.text_area(
            "What appliances do you have?",
            key="user_input",
            placeholder="E.g., 2 ACs, 1 fridge, 4 lights, 1 TV, 2 fans",
            height=120,
            label_visibility="collapsed"
        )

        submit = st.button("⚡ Get Energy Tips", type="primary", use_container_width=True)

with body_right:
    with st.container(border=True):
        st.markdown(
            f"""
            <p style="font-weight:700; font-size:1.1rem; color:{TEXT_DARK};">
                💡 Energy Tip of the Day
            </p>
            <div class="tip-box">
                🍃 Switching to LED bulbs can reduce lighting costs by up to 80%.<br><br>
                Small changes today, big savings tomorrow! 🌍
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<hr style='margin:16px 0;'>", unsafe_allow_html=True)

        st.markdown(
            f"""
            <p style="font-weight:700; font-size:1.0rem; color:{TEXT_DARK};">
                ℹ️ Did You Know?
            </p>
            <div class="fact-box">
                Setting your AC temperature to 24°C instead of 20°C can save up to
                10-15% on your electricity bill.
            </div>
            """,
            unsafe_allow_html=True
        )

# ===================================================
# 12. PROCESS INPUT
# ===================================================

if submit:
    if not user_input.strip():
        st.warning("⚠️ Please describe your appliances first!")
    else:
        with st.spinner("WattSense AI is analyzing your energy usage..."):
            time.sleep(0.5)
            st.session_state.ai_response = call_groq_api(user_input)

# ===================================================
# 13. ANALYSIS RESULT CARD
# ===================================================

with st.container(border=True):
    result_header_l, result_header_r = st.columns([3, 1])
    with result_header_l:
        st.markdown(
            f"""
            <p style="font-weight:700; font-size:1.1rem; color:{TEXT_DARK}; margin-bottom:0;">
                📊 Your Energy Analysis
            </p>
            """,
            unsafe_allow_html=True
        )

    response = st.session_state.ai_response

    if not response:
        st.markdown(
            f"""
            <p style="color:{TEXT_MUTED};">
                Submit your appliances to get a detailed analysis with saving tips and recommendations.
            </p>
            """,
            unsafe_allow_html=True
        )
        with result_header_r:
            st.button("📥 Download Report", disabled=True, use_container_width=True)

    elif isinstance(response, str):
        # Error case
        st.error(response)

    else:
        # Structured, successful response
        with result_header_r:
            pdf_data = export_to_pdf(user_input, response)
            st.download_button(
                label="📥 Download Report",
                data=pdf_data,
                file_name="WattSense_Energy_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        st.write("")

        render_result_row(
            "📈", "Monthly Electricity Consumption (kWh):",
            f"{response.get('monthly_units', 'N/A')} units", color="green"
        )
        render_result_row(
            "₹", "Monthly Electricity Cost (₹8 per unit):",
            f"₹{response.get('monthly_cost', 'N/A')}", color="green"
        )
        render_result_row(
            "🐷", "Total Potential Savings:",
            f"₹{response.get('total_savings', 'N/A')} per month", color="green"
        )

        tips = response.get("tips") or []
        render_result_row(
            "💡", "Personalized Energy Saving Tips:",
            f"{len(tips)} simple tips to save more!" if tips else "No tips available",
            color="yellow"
        )

        if tips:
            with st.expander("View your personalized tips"):
                for i, tip in enumerate(tips, start=1):
                    st.write(f"**{i}.** {tip}")

        breakdown = response.get("breakdown") or []
        if breakdown:
            with st.expander("View appliance breakdown"):
                for item in breakdown:
                    st.write(
                        f"- **{item.get('appliance', '')}**: "
                        f"{item.get('units', '')} units (₹{item.get('cost', '')})"
                    )

        st.write("")
        if st.button("🔄 Clear and Start New Query", use_container_width=True):
            st.session_state.user_input = ""
            st.session_state.ai_response = None
            st.rerun()

# ===================================================
# 14. FOOTER
# ===================================================

st.markdown(
    """
    <div class="footer-bar">
        <div class="footer-title">⚡ WattSense AI &nbsp;•&nbsp; Smart Energy for a Better Tomorrow</div>
        <div class="footer-sub">Made for SDG 7: Affordable &amp; Clean Energy &nbsp;•&nbsp; Built with Streamlit + Groq Llama 3</div>
    </div>
    """,
    unsafe_allow_html=True
)
