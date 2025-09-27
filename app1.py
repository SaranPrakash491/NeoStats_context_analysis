import streamlit as st
from langchain_openai import AzureChatOpenAI
import os
import json
import pandas as pd
from datetime import datetime
import tempfile
import PyPDF2
import docx

# Page configuration - MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="NeoStats Contract Analysis",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for green and black theme
st.markdown("""
<style>
    /* Main background - Dark theme with green accents */
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #0a0a0a 100%);
        min-height: 100vh;
        color: #ffffff;
    }

    /* Sidebar styling - Dark with green accents */
    section[data-testid="stSidebar"] {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%) !important;
        backdrop-filter: blur(10px);
        border-right: 2px solid #00ff88;
    }

    /* Risk level badges */
    .risk-high {
        background: linear-gradient(135deg, #ff4444 0%, #cc0000 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: bold;
        font-size: 0.8em;
    }

    .risk-medium {
        background: linear-gradient(135deg, #ffaa00 0%, #ff8800 100%);
        color: black;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: bold;
        font-size: 0.8em;
    }

    .risk-low {
        background: linear-gradient(135deg, #00ff88 0%, #00cc66 100%);
        color: black;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: bold;
        font-size: 0.8em;
    }

    .contract-score {
        font-size: 2.5em;
        font-weight: bold;
        text-align: center;
        margin: 10px 0;
    }

    .score-excellent { color: #00ff88; }
    .score-good { color: #aaff00; }
    .score-fair { color: #ffaa00; }
    .score-poor { color: #ff4444; }

    /* Card styling */
    .analysis-card {
        background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%);
        padding: 20px;
        border-radius: 12px;
        margin: 10px 0;
        box-shadow: 0 4px 15px rgba(0, 255, 136, 0.2);
        border: 1px solid #00ff88;
        color: #ffffff;
    }

    /* Clause card styling */
    .clause-card {
        background: rgba(26, 26, 26, 0.8);
        padding: 15px;
        border-radius: 8px;
        margin: 8px 0;
        border-left: 4px solid #00ff88;
    }

    /* Add the rest of your existing CSS styles here... */
    .stSidebar .stButton>button {
        background: linear-gradient(135deg, #00ff88 0%, #00cc66 100%);
        color: #000000;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
        font-weight: bold;
    }

    .stChatMessage {
        padding: 16px;
        border-radius: 16px;
        margin: 8px 0;
        box-shadow: 0 4px 15px rgba(0, 255, 136, 0.2);
    }

    div[data-testid="stChatMessage"] > div:first-child {
        background: linear-gradient(135deg, #00ff88 0%, #00cc66 100%) !important;
        color: #000000 !important;
        border-radius: 16px !important;
        border: 1px solid #00ff88;
        font-weight: bold;
    }

    div[data-testid="stChatMessage"] > div:first-child:not([style*="background-color: rgb(240, 242, 246)"]) {
        background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%) !important;
        color: #ffffff !important;
        border: 1px solid #00ff88 !important;
        border-radius: 16px !important;
    }

    .stButton button {
        background: linear-gradient(135deg, #00ff88 0%, #00cc66 100%);
        color: #000000;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: bold;
        transition: all 0.3s ease;
    }

    .main-header {
        color: #00ff88;
        text-align: center;
        font-size: 3em;
        font-weight: bold;
        margin-bottom: 20px;
        text-shadow: 0 0 10px #00ff88, 0 0 20px #00ff88;
        background: linear-gradient(135deg, #00ff88 0%, #00cc66 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .subheader {
        color: #00ff88;
        text-align: center;
        font-size: 1.2em;
        margin-bottom: 30px;
        opacity: 0.9;
        text-shadow: 0 0 5px #00ff88;
    }
</style>
""", unsafe_allow_html=True)


class ContractAnalyzer:
    def __init__(self, llm):
        self.llm = llm

    def extract_text_from_file(self, uploaded_file):
        """Extract text from uploaded file (PDF or DOCX)"""
        text = ""

        # Reset file pointer to beginning
        uploaded_file.seek(0)

        if uploaded_file.type == "application/pdf":
            # PDF processing
            try:
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            except Exception as e:
                st.error(f"Error reading PDF: {str(e)}")
                return ""

        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            # DOCX processing
            try:
                doc = docx.Document(uploaded_file)
                for para in doc.paragraphs:
                    if para.text.strip():
                        text += para.text + "\n"
            except Exception as e:
                st.error(f"Error reading DOCX: {str(e)}")
                return ""

        else:
            # Assume text file
            try:
                text = uploaded_file.getvalue().decode("utf-8")
            except UnicodeDecodeError:
                # Try alternative encoding if UTF-8 fails
                try:
                    text = uploaded_file.getvalue().decode("latin-1")
                except Exception as e:
                    st.error(f"Error reading text file: {str(e)}")
                    return ""

        return text

    def analyze_contract(self, contract_text):
        """Comprehensive contract analysis using LLM"""

        analysis_prompt = f"""
        Analyze the following contract and provide a comprehensive analysis in JSON format. Structure your response as follows:

        {{
            "overall_score": 0-100,
            "summary": "Brief overall summary",
            "clauses": [
                {{
                    "clause_number": "1",
                    "clause_title": "Clause Title",
                    "original_text": "Extracted clause text",
                    "risk_level": "High/Medium/Low",
                    "risk_explanation": "Explanation of risks",
                    "ambiguities": "List any ambiguous terms",
                    "compliance_status": "Compliant/Non-compliant/Partial",
                    "recommended_alternative": "Suggested alternative wording",
                    "best_practice": "Industry best practice for this clause"
                }}
            ],
            "key_risks": ["List of top 3 key risks"],
            "recommendations": ["List of top 3 recommendations"]
        }}

        Contract Text:
        {contract_text[:8000]}  # Limit text length to avoid token limits

        Provide only the JSON response, no additional text.
        """

        try:
            response = self.llm.invoke(analysis_prompt)
            return json.loads(response.content)
        except Exception as e:
            st.error(f"Error analyzing contract: {str(e)}")
            return None

    def query_clause(self, query, contract_data):
        """Answer questions about specific clauses"""

        query_prompt = f"""
        Based on the following contract analysis, answer the user's question about specific clauses.

        Contract Analysis: {json.dumps(contract_data)}

        User Question: {query}

        Provide a concise, helpful answer focusing on the specific clauses mentioned.
        """

        try:
            response = self.llm.invoke(query_prompt)
            return response.content
        except Exception as e:
            return f"Error processing query: {str(e)}"


# Initialize session state
if "contract_data" not in st.session_state:
    st.session_state.contract_data = None
if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# Title and description
st.markdown('<div class="main-header">NEOSTATS CONTRACT ANALYSIS</div>', unsafe_allow_html=True)
st.markdown('<div class="subheader">AI-Powered Contract Risk Assessment & Compliance Analysis</div>',
            unsafe_allow_html=True)

# Sidebar for configuration
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; margin-bottom: 30px;'>
        <h1 style='color: #00ff88; margin-bottom: 5px; text-shadow: 0 0 10px #00ff88;'>🔧</h1>
        <h2 style='color: #00ff88; margin: 0; text-shadow: 0 0 5px #00ff88;'>Configuration</h2>
    </div>
    """, unsafe_allow_html=True)

    # API configuration
    with st.container():
        st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
        st.subheader("🔐 Azure OpenAI Settings")

        deployment_name = st.text_input(
            "Deployment Name",
            value=st.session_state.get("deployment_name", "gpt-4.1"),
            help="Your Azure OpenAI deployment name"
        )

        # API key handling
        if 'api_key' not in st.session_state:
            env_api_key = os.getenv("AZURE_OPENAI_API_KEY", "4nkzcRZmen99IDRUgnaPx20FloouZy5Hff1U8gO7jE0glW80c03mJQQJ99BIACYeBjFXJ3w3AAAAACOGFDyO")
            if env_api_key:
                st.session_state.api_key = env_api_key
                st.success("🔑 API key loaded from environment")
            else:
                api_key = st.text_input("API Key", type="password")
                if api_key:
                    st.session_state.api_key = api_key
        else:
            st.success("🔑 API key configured")
            if st.button("Change API Key"):
                del st.session_state.api_key

        azure_endpoint = st.text_input(
            "Azure Endpoint",
            value=st.session_state.get("azure_endpoint", "https://neoaihackathon.cognitiveservices.azure.com/openai/deployments/gpt-4.1/chat/completions?api-version=2025-01-01-preview"),
            help="Your Azure OpenAI endpoint URL"
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # Model settings
    with st.container():
        st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
        st.subheader("⚙ Model Settings")
        temperature = st.slider("Temperature", 0.0, 1.0, 0.1)
        api_version = st.text_input("API Version", value="2024-05-01-preview")
        st.markdown('</div>', unsafe_allow_html=True)

# Store configuration
st.session_state.deployment_name = deployment_name
st.session_state.azure_endpoint = azure_endpoint

# Main content area
tab1, tab2, tab3 = st.tabs(["📄 Contract Upload & Analysis", "🔍 Analysis Results", "💬 Chat with Contract"])

with tab1:
    st.markdown("### Upload Contract Document")

    uploaded_file = st.file_uploader(
        "Choose a contract file",
        type=['pdf', 'docx', 'txt'],
        help="Supported formats: PDF, DOCX, TXT"
    )

    if uploaded_file is not None:
        st.success(f"✅ File uploaded: {uploaded_file.name}")

        # Display file preview
        with st.expander("📋 File Preview", expanded=False):
            if uploaded_file.type == "application/pdf":
                # For PDF files, show a sample of extracted text instead
                try:
                    # Reset file pointer to beginning
                    uploaded_file.seek(0)

                    # Extract a small sample for preview
                    pdf_reader = PyPDF2.PdfReader(uploaded_file)
                    preview_text = ""
                    for i, page in enumerate(pdf_reader.pages):
                        if i < 2:  # Only show first 2 pages for preview
                            page_text = page.extract_text()
                            if page_text:
                                preview_text += f"--- Page {i + 1} ---\n{page_text}\n\n"
                        if len(preview_text) > 1500:  # Limit preview size
                            break

                    if preview_text:
                        st.text_area("PDF Text Preview", preview_text, height=200)
                    else:
                        st.info("No extractable text found in PDF. The analysis may still work with OCR-based PDFs.")

                except Exception as e:
                    st.error(f"Error previewing PDF: {str(e)}")

            else:
                # For text and DOCX files
                try:
                    uploaded_file.seek(0)  # Reset file pointer

                    if uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                        # DOCX file
                        doc = docx.Document(uploaded_file)
                        text_content = ""
                        for para in doc.paragraphs:
                            if para.text.strip():
                                text_content += para.text + "\n"
                    else:
                        # Text file
                        text_content = uploaded_file.getvalue().decode("utf-8")

                    st.text_area("File Content", text_content[:2000], height=200)

                except Exception as e:
                    st.error(f"Error previewing file: {str(e)}")

        # Analyze contract button
        if st.button("🚀 Analyze Contract", use_container_width=True):
            if 'api_key' not in st.session_state:
                st.error("Please configure your API key in the sidebar")
            elif not st.session_state.api_key:
                st.error("Please enter your API key in the sidebar")
            elif not azure_endpoint:
                st.error("Please enter your Azure endpoint in the sidebar")
            elif not deployment_name:
                st.error("Please enter your deployment name in the sidebar")
            else:
                with st.spinner("Analyzing contract... This may take a few moments."):
                    try:
                        # Initialize LLM
                        llm = AzureChatOpenAI(
                            deployment_name=deployment_name,
                            model="gpt-4",  # Changed from "gpt-oss-120b" to a more common model name
                            temperature=temperature,
                            api_version=api_version,
                            api_key=st.session_state.api_key,
                            azure_endpoint=azure_endpoint
                        )

                        # Initialize analyzer
                        analyzer = ContractAnalyzer(llm)

                        # Extract text
                        contract_text = analyzer.extract_text_from_file(uploaded_file)

                        if not contract_text.strip():
                            st.error("No text could be extracted from the file. Please try a different file.")
                        else:
                            # Analyze contract
                            analysis_result = analyzer.analyze_contract(contract_text)

                            if analysis_result:
                                st.session_state.contract_data = analysis_result
                                st.session_state.analysis_complete = True
                                st.session_state.analyzer = analyzer
                                st.success("✅ Contract analysis complete!")
                                st.rerun()

                    except Exception as e:
                        st.error(f"Error during analysis: {str(e)}")
                        st.info("Please check your API configuration and try again.")

with tab2:
    if st.session_state.analysis_complete and st.session_state.contract_data:
        data = st.session_state.contract_data

        # Overall score display
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            score = data['overall_score']
            if score >= 80:
                score_class = "score-excellent"
            elif score >= 60:
                score_class = "score-good"
            elif score >= 40:
                score_class = "score-fair"
            else:
                score_class = "score-poor"

            st.markdown(f'<div class="contract-score {score_class}">{score}/100</div>', unsafe_allow_html=True)
            st.markdown(f"**Summary:** {data['summary']}")

        # Key risks and recommendations
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### ⚠️ Key Risks")
            for i, risk in enumerate(data['key_risks'], 1):
                st.markdown(f'<div class="clause-card">**{i}.** {risk}</div>', unsafe_allow_html=True)

        with col2:
            st.markdown("### 💡 Recommendations")
            for i, rec in enumerate(data['recommendations'], 1):
                st.markdown(f'<div class="clause-card">**{i}.** {rec}</div>', unsafe_allow_html=True)

        # Detailed clause analysis
        st.markdown("### 📑 Clause-by-Clause Analysis")

        for clause in data['clauses']:
            with st.expander(f"Clause {clause['clause_number']}: {clause['clause_title']}", expanded=False):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Original Text**")
                    st.text_area("", clause['original_text'][:500] + "...", height=100,
                                 key=f"text_{clause['clause_number']}")

                    st.markdown("**Risk Level**")
                    risk_class = f"risk-{clause['risk_level'].lower()}"
                    st.markdown(f'<div class="{risk_class}">{clause["risk_level"]}</div>', unsafe_allow_html=True)

                    st.markdown("**Compliance Status**")
                    st.info(clause['compliance_status'])

                with col2:
                    st.markdown("**Risk Explanation**")
                    st.warning(clause['risk_explanation'])

                    st.markdown("**Ambiguities**")
                    if clause['ambiguities']:
                        st.error(clause['ambiguities'])
                    else:
                        st.success("No ambiguities detected")

                    st.markdown("**Recommended Alternative**")
                    st.info(clause['recommended_alternative'])

        # Export options
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col2:
            if st.button("📊 Export Analysis Report", use_container_width=True):
                # Create downloadable JSON
                json_str = json.dumps(data, indent=2)
                st.download_button(
                    label="Download JSON Report",
                    data=json_str,
                    file_name=f"contract_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
    else:
        st.info("👆 Upload a contract and run analysis to see results here.")

with tab3:
    if st.session_state.analysis_complete and st.session_state.contract_data:
        st.markdown("### 💬 Chat with Your Contract Analysis")

        # Display chat messages
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input("Ask about specific clauses, risks, or recommendations..."):
            # Add user message
            st.session_state.chat_messages.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.markdown(prompt)

            # Get AI response
            with st.chat_message("assistant"):
                with st.spinner("Analyzing your question..."):
                    response = st.session_state.analyzer.query_clause(
                        prompt,
                        st.session_state.contract_data
                    )
                st.markdown(response)
                st.session_state.chat_messages.append({"role": "assistant", "content": response})

        # Clear chat button
        if st.button("Clear Chat History", use_container_width=True):
            st.session_state.chat_messages = []
            st.rerun()
    else:
        st.info("👆 Complete contract analysis first to enable chat functionality.")

# Footerstreamlit
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #00ff88; padding: 20px;'>
    <p style='margin: 0; font-size: 0.9em; opacity: 0.8;'>
        Powered by Azure OpenAI | Built with Streamlit | NeoStats Contract Analysis
    </p>
</div>
""", unsafe_allow_html=True)