import streamlit as st
import requests
import smtplib
from email.message import EmailMessage
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from io import BytesIO

# --------------------------
# CONFIG
# --------------------------
API_KEY = st.secrets["DEEPSEEK_API_KEY"]
APP_PASSWORD = st.secrets["APP_PASSWORD"]

EMAIL_ADDRESS = st.secrets["EMAIL_ADDRESS"]
EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]

API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"

st.set_page_config(page_title="AI Business Plan Generator")

# --------------------------
# PASSWORD PROTECTION
# --------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("Protected Access")

    password_input = st.text_input("Enter access password", type="password")

    if st.button("Login"):
        if password_input == APP_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")

    st.stop()

# --------------------------
# HEADER
# --------------------------
st.title("AI Business Plan Generator")
st.write("Generate your business plan in English and French.")

# --------------------------
# FORM
# --------------------------
with st.form("business_form"):
    name = st.text_input("1. Your name")
    email = st.text_input("2. Email")
    business_name = st.text_input("3. Business name")
    idea = st.text_area("4. Business idea")
    target_customer = st.text_area("5. Target customers")
    problem = st.text_area("6. Problem you're solving")
    revenue = st.text_area("7. Revenue model")
    competition = st.text_area("8. Competitors")
    marketing = st.text_area("9. Marketing strategy")
    budget = st.text_input("10. Startup budget")

    submitted = st.form_submit_button("Generate Business Plan")

# --------------------------
# PROMPTS
# --------------------------
def build_prompt_en(data):
    return f"""
You are an expert business consultant.

Create a structured business plan including:

1. Executive Summary
2. Problem & Opportunity
3. Target Market
4. Revenue Model
5. Marketing Strategy
6. Competition Analysis
7. Startup Budget
8. Action Plan

Be concise and practical.

DATA:
Name: {data['name']}
Business: {data['business_name']}
Idea: {data['idea']}
Target: {data['target_customer']}
Problem: {data['problem']}
Revenue: {data['revenue']}
Competition: {data['competition']}
Marketing: {data['marketing']}
Budget: {data['budget']}
"""

def build_prompt_fr(data):
    return f"""
Vous êtes un consultant expert en création d'entreprise.

Créez un plan d'affaires structuré comprenant :

1. Résumé exécutif
2. Problème et opportunité
3. Marché cible
4. Modèle de revenus
5. Stratégie marketing
6. Analyse de la concurrence
7. Budget de démarrage
8. Plan d'action

Soyez concis et pratique.

DONNÉES :
Nom : {data['name']}
Entreprise : {data['business_name']}
Idée : {data['idea']}
Clients cibles : {data['target_customer']}
Problème : {data['problem']}
Revenus : {data['revenue']}
Concurrence : {data['competition']}
Marketing : {data['marketing']}
Budget : {data['budget']}
"""

# --------------------------
# API CALL
# --------------------------
def generate_plan(prompt):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(API_URL, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"]

# --------------------------
# PDF GENERATOR
# --------------------------
def create_pdf(text):
    buffer = BytesIO()

    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))

    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    story = []

    for line in text.split("\n"):
        story.append(Paragraph(line, styles["Normal"]))
        story.append(Spacer(1, 6))

    doc.build(story)
    buffer.seek(0)

    return buffer

# --------------------------
# EMAIL FUNCTION
# --------------------------
def send_email(plan_en, plan_fr, pdf_en, pdf_fr, user_email):
    msg = EmailMessage()
    msg["Subject"] = "New Business Plan Generated (EN + FR)"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = "peter.sheceo@gmail.com"

    msg.set_content(f"""
New business plan generated.

User email: {user_email}
""")

    # Reset buffers before reading
    pdf_en.seek(0)
    pdf_fr.seek(0)

    # Attach TXT
    msg.add_attachment(plan_en.encode("utf-8"),
                       maintype="text",
                       subtype="plain",
                       filename="business_plan_en.txt")

    msg.add_attachment(plan_fr.encode("utf-8"),
                       maintype="text",
                       subtype="plain",
                       filename="business_plan_fr.txt")

    # Attach PDFs
    msg.add_attachment(pdf_en.read(),
                       maintype="application",
                       subtype="pdf",
                       filename="business_plan_en.pdf")

    msg.add_attachment(pdf_fr.read(),
                       maintype="application",
                       subtype="pdf",
                       filename="business_plan_fr.pdf")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

# --------------------------
# RUN
# --------------------------
if submitted:
    data = {
        "name": name,
        "email": email,
        "business_name": business_name,
        "idea": idea,
        "target_customer": target_customer,
        "problem": problem,
        "revenue": revenue,
        "competition": competition,
        "marketing": marketing,
        "budget": budget
    }

    with st.spinner("Generating business plans..."):
        try:
            plan_en = generate_plan(build_prompt_en(data))
            plan_fr = generate_plan(build_prompt_fr(data))

            pdf_en = create_pdf(plan_en)
            pdf_fr = create_pdf(plan_fr)

            # SEND EMAIL (with visible error if fails)
            try:
                send_email(plan_en, plan_fr, pdf_en, pdf_fr, email)
                st.success("Business plans generated and email sent!")
            except Exception as e:
                st.warning(f"Plan generated, but email failed: {e}")

            # --------------------------
            # DISPLAY + DOWNLOAD
            # --------------------------

            st.subheader("Business Plan (English)")
            st.text_area("English Version", plan_en, height=300)

            st.download_button(
                "Download EN TXT",
                plan_en,
                file_name="business_plan_en.txt"
            )

            st.download_button(
                "Download EN PDF",
                pdf_en,
                file_name="business_plan_en.pdf"
            )

            st.subheader("Plan d'affaires (Français)")
            st.text_area("Version Française", plan_fr, height=300)

            st.download_button(
                "Télécharger TXT (FR)",
                plan_fr,
                file_name="business_plan_fr.txt"
            )

            st.download_button(
                "Télécharger PDF (FR)",
                pdf_fr,
                file_name="business_plan_fr.pdf"
            )

        except Exception as e:
            st.error(f"Error generating plan: {e}")
