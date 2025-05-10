# app.py
# --- START OF SQLITE PATCH ---
# This MUST be the very first thing in your app.py, before ANY other imports
import sys
try:
    print("--- Attempting to patch sqlite3 with pysqlite3-binary ---")
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    print("--- Successfully patched sqlite3 with pysqlite3-binary ---")
except ImportError:
    print("--- pysqlite3-binary not found or import error, using system sqlite3 ---")
except KeyError:
    print("--- 'pysqlite3' not found in sys.modules after import, patch might not have worked as expected. ---")
# --- END OF SQLITE PATCH ---

import streamlit as st
import os
import traceback
from core.pdf_processor import process_pdfs
from core.vector_store import get_vector_store, add_documents_to_store, get_retriever_with_filter, list_indexed_documents # get_vector_store now in-memory
from core.qa_engine import get_qa_chain, query_rag

# --- Configuration ---
UPLOAD_DIR = "uploads" 
# CHROMA_DB_PATH = "./chroma_db_v3" # No longer needed for in-memory
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- Helper Functions ---
def initialize_services(api_key): # Removed force_db_recreate
    """Initializes IN-MEMORY vector store and other services."""
    # For in-memory, we always create a new store when services are initialized for a session/run
    # No need to check current_api_key_for_store for in-memory, as it's always fresh
    print(f"--- Initializing IN-MEMORY services. ---")
    st.session_state.vector_store = get_vector_store(google_api_key=api_key)
    st.session_state.current_api_key_for_store = api_key # Still useful for general API key tracking
    st.info("In-memory vector store initialized with Google Gemini embeddings.")
    
def get_current_retriever(selected_docs=None):
    if "vector_store" not in st.session_state:
        st.error("Vector store not initialized. Please ensure API key is set and PDFs are processed.")
        return None
    return get_retriever_with_filter(st.session_state.vector_store, selected_docs)

# --- Streamlit UI ---
st.set_page_config(page_title="Chat with Your PDFs (Gemini - In-Memory)", layout="wide")
st.title("💬 Chat with Your PDFs (Powered by Gemini - In-Memory DB)")

# --- API Key Input & Service Initialization ---
st.sidebar.header("Configuration")
google_api_key_from_secret = os.environ.get("GOOGLE_API_KEY")

if google_api_key_from_secret:
    st.sidebar.success("Google API Key loaded from Secret!")
    google_api_key = google_api_key_from_secret
else:
    st.sidebar.warning("Google API Key not found in Secrets.")
    google_api_key = st.sidebar.text_input(
        "Enter your Google API Key (for Gemini):", 
        type="password", 
        key="google_api_key_manual_input"
    )

if not google_api_key:
    st.warning("Please provide your Google API Key to begin.")
    st.stop()

# Initialize services for the session
# In-memory store is created fresh each time services are initialized
# This happens on first load or if API key changes
if "services_initialized" not in st.session_state or \
   st.session_state.get("current_api_key") != google_api_key:
    with st.spinner("Initializing services (in-memory)..."):
        initialize_services(google_api_key) # No force_recreate needed
        st.session_state.services_initialized = True
        st.session_state.current_api_key = google_api_key
        if "messages" not in st.session_state:
            st.session_state.messages = []
        # indexed_documents will be populated after PDF processing
        st.session_state.indexed_documents = [] 
else:
    # Ensure these exist if services were already initialized but session state was lost (less common)
    if "messages" not in st.session_state: st.session_state.messages = []
    if "indexed_documents" not in st.session_state: st.session_state.indexed_documents = []


# --- PDF Upload and Processing ---
st.sidebar.header("Upload & Process PDFs")
st.sidebar.info("PDFs are processed for the current session only (in-memory database).")
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
                with st.spinner("Processing PDFs for this session..."):
                    try:
                        # Ensure vector store is initialized (it's in-memory, so should be fresh if not yet done)
                        if "vector_store" not in st.session_state or \
                           st.session_state.get("current_api_key_for_store") != google_api_key:
                             initialize_services(google_api_key)

                        chunks = process_pdfs(temp_file_paths)
                        if chunks:
                            print(f"--- Attempting to add {len(chunks)} chunks to IN-MEMORY vector store ---")
                            add_documents_to_store(st.session_state.vector_store, chunks)
                            st.success(f"Successfully processed and indexed {len(uploaded_files)} PDF(s) for this session.")
                            st.session_state.indexed_documents = list_indexed_documents(st.session_state.vector_store)
                            st.session_state.messages = [] 
                            st.info("Chat history cleared as new documents were processed for this session.")
                        else:
                            st.warning("No text could be extracted or chunked from the PDFs.")
                    except Exception as e:
                        st.error(f"An error occurred during PDF processing: {e}")
                        print(f"--- FULL TRACEBACK FOR PDF PROCESSING ERROR (IN-MEMORY) ---")
                        traceback.print_exc()
                    finally:
                        for path in temp_file_paths:
                            if os.path.exists(path):
                                os.remove(path)
            st.rerun()
    else:
        st.sidebar.warning("Please upload PDF files first.")

# --- Display and Select Indexed Documents ---
st.sidebar.header("Indexed Documents (Current Session)")
if "indexed_documents" not in st.session_state:
    st.session_state.indexed_documents = []

if st.session_state.indexed_documents:
    selected_documents_for_query = st.sidebar.multiselect(
        "Filter Q&A by specific document(s):",
        options=st.session_state.indexed_documents,
        default=[], 
        key="doc_selector_sidebar_mem"
    )
else:
    st.sidebar.info("No documents processed for this session yet.")
    selected_documents_for_query = []

# --- Chat Interface ---
st.header("Chat about your PDFs (Current Session)")

if "messages" not in st.session_state:
    st.session_state.messages = []

for i, message in enumerate(st.session_state.messages): # Use enumerate for unique keys
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "sources" in message and message["sources"]:
            with st.expander("Sources", expanded=False):
                st.text_area("", value=message["sources"], height=100, disabled=True, key=f"sources_{i}_{message['content'][:10]}")

if prompt := st.chat_input("Ask a question about the processed PDFs..."):
    if "vector_store" not in st.session_state:
        st.error("System not ready. Please ensure API key is set and PDFs are processed before asking questions.")
        st.stop()
    
    if not st.session_state.get("indexed_documents", []): 
        st.warning("No documents appear to be processed for this session. Please upload and process PDF documents first.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

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
                    with st.expander("Sources", expanded=True): # Expand for latest
                         st.text_area("", value=sources_text, height=100, disabled=True, key=f"sources_current_{len(st.session_state.messages)}")
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": full_response_content,
                    "sources": sources_text
                })
            else:
                err_msg = "Could not initialize retriever. No documents processed for this session?"
                message_placeholder.error(err_msg)
                st.session_state.messages.append({"role": "assistant", "content": err_msg, "sources": ""})
        except Exception as e:
            err_msg = f"An error occurred: {e}"
            message_placeholder.error(err_msg)
            print(f"--- FULL TRACEBACK FOR RAG QUERY ERROR (IN-MEMORY) ---")
            traceback.print_exc()
            st.session_state.messages.append({"role": "assistant", "content": err_msg, "sources": ""})

# --- Admin / DB Reset (Optional) ---
st.sidebar.markdown("---")
if st.sidebar.button("⚠️ Reset Session Data (Clears In-Memory DB & Chat)", key="reset_session_button"):
    if google_api_key: 
        with st.spinner("Resetting session data..."):
            # Re-initialize services, which creates a new in-memory DB
            initialize_services(google_api_key) 
            st.session_state.indexed_documents = [] 
            st.session_state.messages = [] 
        st.sidebar.success("Session data (in-memory DB, processed PDFs, chat) has been reset.")
        st.rerun()
    else:
        st.sidebar.error("Please provide Google API key before resetting.")
