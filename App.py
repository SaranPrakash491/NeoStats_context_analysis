import streamlit as st
from langchain_openai import AzureChatOpenAI
import os

# Page configuration
st.set_page_config(
    page_title="Azure OpenAI Chat",
    page_icon="🤖",
    layout="wide"
)

# Title and description
st.title("🤖 NeoStats - Context Solution")
st.markdown("Chat with Azure OpenAI's GPT-OSS-120B model")

# Sidebar for configuration
with st.sidebar:
    st.header("🔧 Configuration")

    # API configuration
    st.subheader("Azure OpenAI Settings")

    deployment_name = st.text_input(
        "Deployment Name",
        value=st.session_state.get("deployment_name", "gpt-4.1"),
        help="Your Azure OpenAI deployment name"
    )

    api_key = st.text_input(
        "API Key",
        type="password",
        value=st.session_state.get("api_key", "4nkzcRZmen99IDRUgnaPx20FloouZy5Hff1U8gO7jE0glW80c03mJQQJ99BIACYeBjFXJ3w3AAAAACOGFDyO"),
        help="Your Azure OpenAI API key"
    )

    azure_endpoint = st.text_input(
        "Azure Endpoint",
        value=st.session_state.get("azure_endpoint", "https://neoaihackathon.cognitiveservices.azure.com/openai/deployments/gpt-4.1/chat/completions?api-version=2025-01-01-preview"),
        help="Your Azure OpenAI endpoint URL"
    )

    # Model settings
    st.subheader("Model Settings")

    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.1,
        help="Controls randomness: 0 = deterministic, 1 = creative"
    )

    api_version = st.text_input(
        "API Version",
        value="2024-05-01-preview",
        help="Azure OpenAI API version"
    )

# Store configuration in session state
st.session_state.deployment_name = deployment_name
st.session_state.api_key = api_key
st.session_state.azure_endpoint = azure_endpoint

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Type your message here..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        # Check if all required fields are filled
        if not all([deployment_name, api_key, azure_endpoint]):
            error_msg = "⚠ Please fill in all required configuration fields in the sidebar."
            message_placeholder.markdown(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
        else:
            try:
                # Initialize Azure OpenAI LLM
                llm = AzureChatOpenAI(
                    deployment_name=deployment_name,
                    model="gpt-oss-120b",
                    temperature=temperature,
                    api_version=api_version,
                    api_key=api_key,
                    azure_endpoint=azure_endpoint
                )

                # Get response from Azure OpenAI
                with st.spinner("Thinking..."):
                    response = llm.invoke(prompt)

                # Display the response
                message_placeholder.markdown(response.content)

                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response.content})

            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                message_placeholder.markdown(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Clear chat history button
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Instructions section
with st.expander("ℹ Instructions"):
    st.markdown("""
    ### How to use this app:
    1. *Configure Azure OpenAI* in the sidebar:
       - Deployment Name: Your Azure OpenAI deployment name
       - API Key: Your Azure OpenAI API key
       - Azure Endpoint: Your Azure OpenAI endpoint URL

    2. *Adjust model settings* if needed:
       - Temperature: Controls response creativity (0 = more deterministic)
       - API Version: Azure OpenAI API version

    3. *Start chatting* by typing in the input box at the bottom

    ### Required Azure OpenAI setup:
    - You need an Azure OpenAI resource with GPT-OSS-120B model deployed
    - Get your API key and endpoint from the Azure Portal
    - Ensure your deployment has the correct model access
    """)

# Footer
st.markdown("---")
st.markdown("Powered by Azure OpenAI | Built with Streamlit")