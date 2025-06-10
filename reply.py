import streamlit as st
import os
from fpdf import FPDF
from google.generativeai import GenerativeModel, configure

# Configure Gemini API key (ensure it's set in your environment or directly here)
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
configure(api_key=GEMINI_API_KEY)
model = GenerativeModel("gemini-pro")

# Helper to generate email
@st.cache_data(show_spinner=False)
def generate_email(applicant_text, tone, format_type, name, role, company):
    prompt = f"""
    You are an HR manager. Write an email response to a job applicant.
    Applicant Name: {name}
    Role Applied For: {role}
    Company: {company}
    Email Format: {format_type}
    Tone: {tone}
    Applicant Message: {applicant_text}
    Please generate a professional email response.
    """
    response = model.generate_content(prompt)
    return response.text.strip()

# Helper to download email as PDF
def create_pdf(content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in content.split('\n'):
        pdf.multi_cell(0, 10, line)
    pdf_path = "/tmp/generated_email.pdf"
    pdf.output(pdf_path)
    return pdf_path

# Streamlit UI
st.set_page_config(page_title="HR Email Generator", layout="centered")
st.title("📩 HR Email Reply Generator")

with st.form("email_form"):
    st.write("### Applicant Details")
    name = st.text_input("Applicant's Name", "John Doe")
    role = st.text_input("Role Applied For", "Software Engineer")
    company = st.text_input("Company Name", "Acme Corp")
    applicant_text = st.text_area("Paste Applicant's Message", height=200)

    st.write("### Email Preferences")
    format_type = st.selectbox("Select Email Format", ["Acknowledgement", "Rejection", "Interview Invitation", "Further Information Request"])
    tone = st.radio("Select Tone", ["Formal", "Friendly", "Encouraging"])

    submitted = st.form_submit_button("Generate Email")

# Session state to store email
if 'email_content' not in st.session_state:
    st.session_state.email_content = ""

# Generate email
if submitted:
    if applicant_text.strip() == "":
        st.error("Please paste the applicant's message.")
    else:
        with st.spinner("Generating email..."):
            email_content = generate_email(applicant_text, tone, format_type, name, role, company)
            st.session_state.email_content = email_content

# Display generated email
if st.session_state.email_content:
    st.write("---")
    st.subheader("📧 Generated Email")
    st.text_area("Email Response", value=st.session_state.email_content, height=300)

    # PDF download
    pdf_file_path = create_pdf(st.session_state.email_content)
    with open(pdf_file_path, "rb") as f:
        st.download_button(
            label="📥 Download Email as PDF",
            data=f,
            file_name="HR_Email_Response.pdf",
            mime="application/pdf"
        )

    # Regenerate option
    if st.button("🔁 Regenerate Email with New Format/Tone"):
        st.session_state.email_content = "Thank you for your application."

