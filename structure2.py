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
st.write("Answer the questions below. Examples are provided to guide you.")

# --------------------------
# FORM WITH EXAMPLES
# --------------------------
with st.form("business_form"):
    name = st.text_input(
        "1. Your name",
        placeholder="e.g., Sarah Johnson"
    )

    email = st.text_input(
        "2. Your email",
        placeholder="e.g., sarah@gmail.com"
    )

    business_name = st.text_input(
        "3. Business name",
        placeholder="e.g., FitMeal Prep Co."
    )

    idea = st.text_area(
        "4. Business idea",
        placeholder="e.g., A meal prep service delivering healthy, ready-to-eat meals to busy professionals."
    )

    target_customer = st.text_area(
        "5. Target customers",
        placeholder="e.g., Busy professionals aged 25–45 who want healthy meals but lack time to cook."
    )

    problem = st.text_area(
        "6. Problem you're solving",
        placeholder="e.g., People want to eat healthy but don’t have time to plan, shop, and cook meals."
    )

    revenue = st.text_area(
        "7. Revenue model",
        placeholder="e.g., Weekly subscription plans ($80–$150/week) depending on number of meals."
    )

    competition = st.text_area(
        "8. Competitors",
        placeholder="e.g., HelloFresh, local meal prep companies, Uber Eats (indirect competition)."
    )

    marketing = st.text_area(
        "9. Marketing strategy",
        placeholder="e.g., Instagram ads, influencer partnerships, referral program, local gym partnerships."
    )

    budget = st.text_input(
        "10. Startup budget",
        placeholder="e.g., $5,000 for kitchen setup, marketing, and initial inventory."
    )

    submitted = st.form_submit_button("Generate Business Plan")

# --------------------------
# PROMPTS
# --------------------------
def build_prompt_en(data):
    return f"""
You are an expert business consultant.

Create a structured business plan including:
- Executive Summary
- Problem & Opportunity
- Target Market
- Revenue Model
- Marketing Strategy
- Competition Analysis
- Budget
- Action Plan

Be clear and practical.

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
Vous êtes un expert en création d'entreprise.

Créez un plan d'affaires structuré comprenant :
- Résumé exécutif
- Problème et opportunité
- Marché cible
- Modèle de revenus
- Stratégie marketing
- Analyse de la concurrence
- Budget
- Plan d'action

Soyez clair et pratique.

DONNÉES :
Nom : {data['name']}
Entreprise : {data['business_name']}
Idée : {data['idea']}
Clients : {data['target_customer']}
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
    response = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

# --------------------------
# PDF
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
# EMAIL
# --------------------------
def send_email(plan_en, plan_fr, pdf_en, pdf_fr, user_email):
    recipients = [
        "peter.sheceo+bizplan@gmail.com",
        user_email
    ]

    msg = EmailMessage()
    msg["Subject"] = "Your Business Plan (EN + FR)"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = ", ".join(recipients)

    msg.set_content("Your business plan is attached.")

    pdf_en.seek(0)
    pdf_fr.seek(0)

    msg.add_attachment(plan_en.encode("utf-8"),
                       maintype="text",
                       subtype="plain",
                       filename="business_plan_en.txt")

    msg.add_attachment(plan_fr.encode("utf-8"),
                       maintype="text",
                       subtype="plain",
                       filename="business_plan_fr.txt")

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

            try:
                send_email(plan_en, plan_fr, pdf_en, pdf_fr, email)
                st.success("Plans generated and emailed!")
            except Exception as e:
                st.warning(f"Email failed: {e}")

            # DISPLAY + DOWNLOAD
            st.subheader("English Plan")
            st.text_area("EN", plan_en, height=300)
            st.download_button("Download EN TXT", plan_en, "business_plan_en.txt")
            st.download_button("Download EN PDF", pdf_en, "business_plan_en.pdf")

            st.subheader("Plan Français")
            st.text_area("FR", plan_fr, height=300)
            st.download_button("Download FR TXT", plan_fr, "business_plan_fr.txt")
            st.download_button("Download FR PDF", pdf_fr, "business_plan_fr.pdf")

        except Exception as e:
            st.error(f"Error: {e}")
