# app.py - WattSense AI with Streamlit + Groq (Clean UI + PDF Export)

import streamlit as st
import requests
import os
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
    layout="centered",
    initial_sidebar_state="expanded"
)

# ===================================================
# 3. INITIALIZE SESSION STATE & CALLBACKS
# ===================================================
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""
if 'ai_response' not in st.session_state:
    st.session_state.ai_response = None

def set_example(text):
    st.session_state.user_input = text
    st.session_state.ai_response = None

# ===================================================
# 4. PDF GENERATION HELPER FUNCTION
# ===================================================

def export_to_pdf(input_text, response_text):
    """Generates a structured, clean PDF using ReportLab"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # Custom Clean Styles
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'],
        fontSize=24, leading=28, textColor=colors.HexColor("#d97706"), spaceAfter=15
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
    
    # AI Breakdown Section
    story.append(Paragraph("🎯 Energy Consumption Analysis & Tips:", section_style))
    
    lines = response_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Format distinct types of output lines beautifully inside tables/paragraphs
        if 'Total' in line or 'Monthly' in line or 'Savings' in line or '💰' in line:
            # Highlight Savings Box
            p = Paragraph(f"<b>{line}</b>", body_style)
            t = Table([[p]], colWidths=[530])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#dcfce7")),
                ('PADDING', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ]))
            story.append(t)
            story.append(Spacer(1, 6))
        elif '₹' in line or 'units' in line or 'kWh' in line or '📊' in line:
            story.append(Paragraph(f"• {line}", body_style))
            story.append(Spacer(1, 3))
        elif '💡' in line or 'Tip' in line or 'Save' in line or line.startswith(('1.', '2.', '3.')):
            # Tip box look
            p = Paragraph(line, body_style)
            t = Table([[p]], colWidths=[530])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fffbeb")),
                ('PADDING', (0,0), (-1,-1), 6),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ]))
            story.append(t)
            story.append(Spacer(1, 6))
        else:
            story.append(Paragraph(line, body_style))
            story.append(Spacer(1, 4))
            
    doc.build(story)
    buffer.seek(0)
    return buffer

# ===================================================
# 5. SYSTEM PROMPT (English Only)
# ===================================================

SYSTEM_PROMPT = """You are WattSense AI ⚡ - India's friendly energy saving advisor.

IMPORTANT: Respond ONLY in English. DO NOT use Bengali or any other regional language script.

When users describe their appliances, you MUST:
1. Calculate monthly electricity consumption (kWh)
2. Calculate monthly cost (₹8 per unit)
3. Give 3 personalized, actionable energy-saving tips
4. Show potential monthly savings in ₹

Use this appliance guide (monthly per appliance):
- 1.5 Ton AC: 360 units (₹2,880)
- Refrigerator: 144 units (₹1,152)
- LED TV: 12 units (₹96)
- Ceiling Fan: 22.5 units (₹180)
- LED Bulb: 1.5 units (₹12)
- Water Heater: 120 units (₹960)
- Laptop: 6 units (₹48)
- Washing Machine: 15 units (₹120)
- Microwave: 12 units (₹96)

Response Format:
1. Show calculation breakdown
2. Show total monthly cost
3. Give 3 numbered tips
4. Show total potential savings

Be encouraging and practical! Use simple English. Always show money saved!"""

# ===================================================
# 6. GROQ API FUNCTION
# ===================================================

def call_groq_api(user_input):
    """Call Groq API and return AI response"""
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
        "temperature": 0.7,
        "max_tokens": 600
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.Timeout:
        return "⏰ Request timed out. Please try again."
    except requests.exceptions.HTTPError as e:
        try:
            error_detail = response.json()
            if "error" in error_detail:
                return f"❌ API Error: {error_detail['error'].get('message', str(e))}"
        except:
            return f"❌ API Error: {str(e)}"
    except requests.exceptions.RequestException as e:
        return f"❌ Network Error: {str(e)}"

# ===================================================
# 7. FORMAT RESPONSE FUNCTION
# ===================================================

def display_native_response(response_text):
    """Parses response and assigns them to Streamlit's native UI cards"""
    lines = response_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if 'Total' in line or 'Monthly' in line or 'Savings' in line or '💰' in line:
            st.success(line)
        elif '₹' in line or 'units' in line or 'kWh' in line or '📊' in line:
            st.info(line)
        elif '💡' in line or 'Tip' in line or 'Save' in line or line.startswith(('1.', '2.', '3.')):
            st.warning(line)
        else:
            st.write(line)

# ===================================================
# 8. SIDEBAR
# ===================================================

with st.sidebar:
    st.title("⚡ WattSense AI")
    st.write("---")
    st.subheader("🎯 About")
    st.markdown("""
    AI-powered energy advisor that helps you:
    * Calculate monthly consumption  
    * Estimate electricity bill  
    * Get personalized saving tips  
    * Reduce carbon footprint  
    """)
    st.write("---")
    
    st.subheader("📊 Quick Stats")
    st.metric(label="Avg Monthly Savings", value="₹500+")
    
    st.write("---")
    st.subheader("🔑 API Status")
    if GROQ_API_KEY:
        st.success("API Key Loaded")
    else:
        st.error("No API Key")
        
    st.write("---")
    st.caption("🏷️ SDG 7: Affordable & Clean Energy")

# ===================================================
# 9. MAIN APP INTERFACE
# ===================================================

st.title("⚡ WattSense AI")
st.subheader("AI-Powered Energy Saving Advisor for Indian Households")
st.write("---")

st.markdown("### 📝 Describe Your Appliances")
st.caption("Example: 'I have 2 ACs, 1 fridge, 4 lights, and 1 TV'")

user_input = st.text_area(
    "What appliances do you have?",
    key="user_input",
    placeholder="E.g., 2 ACs, 1 fridge, 4 lights, 1 TV, 2 fans",
    height=120,
    label_visibility="collapsed"
)

submit = st.button("Get Energy Tips", type="primary", use_container_width=True)

# ===================================================
# 10. PROCESS INPUT AND DISPLAY STATE
# ===================================================

if submit:
    if not user_input.strip():
        st.warning("⚠️ Please describe your appliances first!")
    else:
        with st.spinner("WattSense AI is analyzing your energy usage..."):
            time.sleep(0.5)
            st.session_state.ai_response = call_groq_api(user_input)

if st.session_state.ai_response:
    st.write("---")
    st.header("🎯 WattSense AI Analysis")
    
    if st.session_state.ai_response.startswith("❌"):
        st.error(st.session_state.ai_response)
    else:
        display_native_response(st.session_state.ai_response)
        
        # New Feature: Generate PDF in binary memory 
        pdf_data = export_to_pdf(user_input, st.session_state.ai_response)
        
        st.write("") # Margin buffer
        st.download_button(
            label="📥 Download Analysis as PDF",
            data=pdf_data,
            file_name="WattSense_Energy_Report.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    
    st.write("---")
    if st.button("🔄 Clear and Start New Query", use_container_width=True):
        st.session_state.user_input = ""
        st.session_state.ai_response = None
        st.rerun()

# ===================================================
# 11. QUICK EXAMPLES SECTION
# ===================================================

st.write("---")
st.subheader("🔍 Try These Quick Examples")

col1, col2, col3 = st.columns(3)

col1.button(
    "🏠 Home Layout 1", 
    key="ex1", 
    use_container_width=True, 
    on_click=set_example, 
    args=("2 ACs, 1 fridge, 4 lights, 1 TV",)
)

col2.button(
    "🏠 Home Layout 2", 
    key="ex2", 
    use_container_width=True, 
    on_click=set_example, 
    args=("1 AC, 2 fans, 1 fridge, 1 water heater",)
)

col3.button(
    "🏠 Home Layout 3", 
    key="ex3", 
    use_container_width=True, 
    on_click=set_example, 
    args=("1 AC, 1 fridge, 1 TV, 3 fans, 6 lights",)
)

# ===================================================
# 12. FOOTER
# ===================================================

st.write("---")
st.caption("⚡ WattSense AI • Made for SDG 7: Affordable & Clean Energy • Built with Streamlit + Groq Llama 3")
