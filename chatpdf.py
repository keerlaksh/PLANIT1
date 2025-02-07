import streamlit as st
import PyPDF2
import pytesseract
from pdf2image import convert_from_path
import requests

# Set up the Streamlit UI with custom styling
st.set_page_config(page_title="Chat With PDF", layout="wide")

# Apply custom CSS for background color and font color
st.markdown(
    """
    <style>
    body {
        background-color: #060108 !important; /* Dark Purple */
        color: white !important;
    }
    .stApp {
        background-color: #060108 !important; /* Dark Purple */
    }
    h1 {
        color: white !important; /* Ensures title is white */
        text-shadow: 0 0 10px #ff00ff, 0 0 20px #ff00ff, 0 0 30px #ff00ff; /* Glow effect */
    }
    .stTextInput input {
        background-color: #793499 !important; /* Indigo input box */
        color: white !important;
    }
    .stButton>button {
        background-color: #640c86 !important; /* Lighter Purple buttons */
        color: white !important;
        border-radius: 10px;
    }
    /* Custom styling for the sidebar */
    .css-1d391kg {
        background-color: #3c0a45 !important; /* Darkish purple for sidebar */
    }
    /* Ensures chat messages and warnings appear in white */
    .stMarkdown, .stChatMessage, .stText, .stWarning {
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📄 Chat With Your PDF")

# Initialize session state for chat
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! Upload a PDF and ask me anything about it. 😊"}]
if "last_response" not in st.session_state:
    st.session_state.last_response = None  # To track the last assistant response

# Sidebar for uploading the PDF
with st.sidebar:
    st.header("Upload PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

# Function to extract text using PyPDF2
def extract_text_with_pypdf2(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    return text

# Function to extract text using OCR
def extract_text_with_ocr(pdf_file):
    images = convert_from_path(pdf_file)
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img)
    return text

# Function to extract text from the uploaded PDF using a hybrid approach
def extract_pdf_text(pdf_file):
    try:
        text = extract_text_with_pypdf2(pdf_file)
        if text.strip():
            return text
    except Exception:
        pass
    return extract_text_with_ocr(pdf_file)

# Function to send a message to the AI API
def get_groq_chat_completion(message, pdf_content):
    api_endpoint = "https://api.groq.com/openai/v1/chat/completions"
    api_key = "key"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    data = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system",
             "content": "You are a helpful assistant for students. Use the provided PDF content to answer queries."},
            {"role": "user", "content": f"The PDF content is: {pdf_content}. {message}"}
        ]
    }
    response = requests.post(api_endpoint, headers=headers, json=data)
    response_data = response.json()
    return response_data.get("choices", [{}])[0].get("message", {}).get("content", "Sorry, I couldn't generate a response.")

# Display chat messages
for message in st.session_state.messages:
    if message["role"] == "assistant":
        st.markdown(f"<p style='color: white;'>🟢 Assistant: {message['content']}</p>", unsafe_allow_html=True)
    else:
        st.markdown(f"<p style='color: white;'>🔵 You: {message['content']}</p>", unsafe_allow_html=True)

# Input box for user query
if uploaded_file:
    pdf_content = extract_pdf_text(uploaded_file)
    user_input = st.text_input("Ask a question about your PDF:", key="user_input")

    # Function to handle button queries
    def handle_query(query):
        st.session_state.messages.append({"role": "user", "content": query})
        with st.spinner("Thinking..."):
            response = get_groq_chat_completion(query, pdf_content)
        st.session_state.messages.append({"role": "assistant", "content": response})

    # Buttons for predefined queries
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        if st.button("Summarize"):
            handle_query("Summarize the content of the PDF.")
    with col2:
        if st.button("Give in Points"):
            handle_query("List the main points from the PDF.")
    with col3:
        if st.button("Mnemonics to Remember"):
            handle_query("Create mnemonics to remember the key content of the PDF.")
    with col4:
        if st.button("Make it Understandable"):
            handle_query("Explain the PDF content in simple terms.")
    with col5:
        if st.button("Generate Questions, MCQs"):
            handle_query("Generate questions and multiple-choice questions based on the PDF content.")

    if user_input and user_input.strip():
        st.session_state.messages.append({"role": "user", "content": user_input})
        if user_input != st.session_state.last_response:
            with st.spinner("Thinking..."):
                response = get_groq_chat_completion(user_input, pdf_content)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.last_response = user_input
        else:
            st.warning("Please ask a new question.")
else:
    # Custom warning message in white
    st.markdown("<p style='color: white; background-color: #620574; padding: 10px; border-radius: 5px;'>⚠️ Please upload a PDF to start chatting!</p>", unsafe_allow_html=True)