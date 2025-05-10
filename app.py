# app.py
# --- START OF SQLITE PATCH ---
# This MUST be the very first thing in your app.py
import sys
try:
    print("--- Attempting to patch sqlite3 with pysqlite3-binary ---")
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    print("--- Successfully patched sqlite3 with pysqlite3-binary for Streamlit Cloud ---")
except ImportError:
    print("--- pysqlite3-binary not found or import error, using system sqlite3 ---")
except KeyError:
    print("--- 'pysqlite3' not found in sys.modules after import, patch might not have worked as expected. ---")
# --- END OF SQLITE PATCH ---


import streamlit as st
import os
from core.pdf_processor import process_pdfs
from core.vector_store import get_vector_store, add_documents_to_store, get_retriever_with_filter, list_indexed_documents
from core.qa_engine import get_qa_chain, query_rag

# --- Configuration ---
UPLOAD_DIR = "uploads" 
CHROMA_DB_PATH = "./chroma_db" # Relative to the project root
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHROMA_DB_PATH, exist_ok=True)


# --- Helper Functions ---
def initialize_services(api_key, force_db_recreate=False):
    """Initializes vector store, storing it in session state."""
    if "vector_store" not in st.session_state or \
       force_db_recreate or \
       st.session_state.get("current_api_key_for_store") != api_key:
        
        st.session_state.vector_store = get_vector_store(
            google_api_key=api_key, 
            db_path=CHROMA_DB_PATH,
            force_recreate=force_db_recreate
        )
        st.session_state.current_api_key_for_store = api_key
        st.info("Vector store initialized with Google Gemini embeddings." if not force_db_recreate else "Vector store re-created.")
    
def get_current_retriever(selected_docs=None):
    if "vector_store" not in st.session_state:
        # This case should ideally be handled before calling, but good as a safeguard
        st.error("Vector store not initialized. Please ensure API key is set and PDFs are processed.")
        return None
    return get_retriever_with_filter(st.session_state.vector_store, selected_docs)


# --- Streamlit UI ---
st.set_page_config(page_title="Chat with Your PDFs (Gemini)", layout="wide")
st.title("💬 Chat with Your PDFs (Powered by Gemini)")

# --- API Key Input & Service Initialization ---
st.sidebar.header("Configuration")
google_api_key_from_secret = os.environ.get("GOOGLE_API_KEY")

if google_api_key_from_secret:
    st.sidebar.success("Google API Key loaded from Codespaces Secret!")
    google_api_key = google_api_key_from_secret
else:
    st.sidebar.warning("Google API Key not found in Codespaces Secrets.")
    google_api_key = st.sidebar.text_input(
        "Enter your Google API Key (for Gemini):", 
        type="password", 
        key="google_api_key_manual_input"
    )

if not google_api_key:
    st.warning("Please provide your Google API Key to begin.")
    st.stop()

# Initialize services
if "services_initialized" not in st.session_state or \
   st.session_state.get("current_api_key") != google_api_key:
    with st.spinner("Initializing services with Google API Key..."):
        initialize_services(google_api_key, force_db_recreate=st.session_state.get("force_db_recreate_flag", False))
        st.session_state.services_initialized = True
        st.session_state.current_api_key = google_api_key
        st.session_state.force_db_recreate_flag = False 
        # Initialize chat history if not already present
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "indexed_documents" not in st.session_state: # Initialize if services were just re-initialized
            st.session_state.indexed_documents = list_indexed_documents(st.session_state.vector_store)


# --- PDF Upload and Processing ---
st.sidebar.header("Upload & Process PDFs")
uploaded_files = st.sidebar.file_uploader(
    "Upload one or more PDF files", type="pdf", accept_multiple_files=True, key="pdf_uploader"
)

if st.sidebar.button("Process Uploaded PDFs", key="process_button"):
    if uploaded_files:
        if not google_api_key:
            st.error("Please ensure your Google API Key is set.")
        else:
            temp_file_paths = []
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            for uploaded_file in uploaded_files:
                try:
                    temp_file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
                    with open(temp_file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    temp_file_paths.append(temp_file_path)
                except Exception as e:
                    st.error(f"Error saving {uploaded_file.name}: {e}")

            if temp_file_paths:
                with st.spinner("Processing PDFs... This may take a moment."):
                    try:
                        if "vector_store" not in st.session_state or \
                           st.session_state.get("current_api_key_for_store") != google_api_key:
                             initialize_services(google_api_key)

                        chunks = process_pdfs(temp_file_paths)
                        if chunks:
                            add_documents_to_store(st.session_state.vector_store, chunks)
                            st.success(f"Successfully processed and indexed {len(uploaded_files)} PDF(s).")
                            st.session_state.indexed_documents = list_indexed_documents(st.session_state.vector_store)
                            st.session_state.messages = [] # Clear chat history on new PDF processing
                            st.info("Chat history cleared as new documents were processed.")
                        else:
                            st.warning("No text could be extracted or chunked from the PDFs.")
                    except Exception as e:
                        st.error(f"An error occurred during PDF processing: {e}")
                    finally:
                        for path in temp_file_paths:
                            if os.path.exists(path):
                                os.remove(path)
            st.rerun()
    else:
        st.sidebar.warning("Please upload PDF files first.")

# --- Display and Select Indexed Documents ---
st.sidebar.header("Indexed Documents")
if "indexed_documents" not in st.session_state: # Ensure it's initialized
    st.session_state.indexed_documents = []

# Ensure vector_store is available before trying to list documents, especially after a reset
if "vector_store" in st.session_state and not st.session_state.indexed_documents:
     st.session_state.indexed_documents = list_indexed_documents(st.session_state.vector_store)


if st.session_state.indexed_documents:
    selected_documents_for_query = st.sidebar.multiselect(
        "Filter Q&A by specific document(s):",
        options=st.session_state.indexed_documents,
        default=[], 
        key="doc_selector_sidebar" # Changed key to avoid conflict if any old one existed
    )
else:
    st.sidebar.info("No documents have been indexed yet. Upload and process PDFs.")
    selected_documents_for_query = []

# --- Chat Interface ---
st.header("Chat about your PDFs")

# Initialize chat history if it was missed during initial service setup
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display prior chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "sources" in message and message["sources"]:
            with st.expander("Sources", expanded=False): # Keep sources collapsed by default
                st.text_area("", value=message["sources"], height=100, disabled=True, key=f"sources_{len(st.session_state.messages)}_{message['content'][:10]}")


# Get user input
if prompt := st.chat_input("Ask a question about the content of your uploaded PDFs..."):
    if "vector_store" not in st.session_state:
        st.error("System not ready. Please ensure API key is set and PDFs are processed before asking questions.")
        st.stop()
    if not st.session_state.indexed_documents and not uploaded_files: # Check if docs are processed
        st.warning("Please upload and process PDF documents before asking questions.")
        st.stop()


    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        try:
            current_retriever = get_current_retriever(selected_documents_for_query)
            if current_retriever:
                qa_chain_instance = get_qa_chain(google_api_key, current_retriever)
                answer, sources_text = query_rag(qa_chain_instance, prompt)
                
                full_response_content = answer
                message_placeholder.markdown(full_response_content)

                if sources_text:
                    with st.expander("Sources", expanded=True): # Expand sources for the latest answer
                         st.text_area("", value=sources_text, height=100, disabled=True, key=f"sources_current_{len(st.session_state.messages)}")
                
                # Add assistant response to chat history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": full_response_content,
                    "sources": sources_text
                })
            else:
                err_msg = "Could not initialize retriever. This might happen if no PDFs are processed or there's an issue with the vector store."
                message_placeholder.error(err_msg)
                st.session_state.messages.append({"role": "assistant", "content": err_msg, "sources": ""})

        except Exception as e:
            err_msg = f"An error occurred: {e}"
            message_placeholder.error(err_msg)
            st.session_state.messages.append({"role": "assistant", "content": err_msg, "sources": ""})

# --- Admin / DB Reset (Optional) ---
st.sidebar.markdown("---")
if st.sidebar.button("⚠️ Reset Document Index (Deletes DB)", key="reset_db_button"):
    if google_api_key: 
        with st.spinner("Resetting document index..."):
            st.session_state.force_db_recreate_flag = True
            initialize_services(google_api_key, force_db_recreate=True)
            st.session_state.indexed_documents = [] # Clear display list
            st.session_state.messages = [] # Clear chat history on DB reset
        st.sidebar.success("Document index and chat history have been reset.")
        st.rerun()
    else:
        st.sidebar.error("Please provide Google API key before resetting.")
