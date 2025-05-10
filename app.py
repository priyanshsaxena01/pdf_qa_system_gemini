# app.py
# --- START OF SQLITE PATCH ---
# (Keep your SQLite patch here as the absolute first thing)
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
from core.vector_store import get_vector_store, add_documents_to_store, get_retriever_with_filter, list_indexed_documents
from core.qa_engine import get_qa_chain, query_rag

# --- Configuration ---
UPLOAD_DIR = "uploads" 
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- Helper Functions ---
def initialize_services(api_key, clear_existing_data=False):
    """
    Initializes IN-MEMORY vector store and other services.
    If clear_existing_data is True, it also clears session state related to docs and chat.
    """
    print(f"--- Initializing IN-MEMORY services. Clear existing data: {clear_existing_data} ---")
    
    # Always create a new in-memory vector store instance
    st.session_state.vector_store = get_vector_store(google_api_key=api_key)
    st.session_state.current_api_key_for_store = api_key
    
    if clear_existing_data:
        print("--- Clearing existing session data: indexed_documents and messages ---")
        st.session_state.indexed_documents = []
        st.session_state.messages = []
        st.info("In-memory vector store re-initialized. Processed PDFs and chat history for the session cleared.")
    else:
        st.info("In-memory vector store initialized for the session.")
    
    # Ensure these lists exist if they were cleared or never created
    if "indexed_documents" not in st.session_state:
        st.session_state.indexed_documents = []
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
def get_current_retriever(selected_docs=None):
    if "vector_store" not in st.session_state:
        st.error("Vector store not initialized. Please ensure API key is set.")
        return None
    return get_retriever_with_filter(st.session_state.vector_store, selected_docs)

# --- Streamlit UI ---
st.set_page_config(page_title="Chat with Your PDFs by Priyansh Saxena", layout="wide")

st.title("💬 Chat with Your PDFs")
st.markdown("### _A Project by Priyansh Saxena_") 
st.markdown("_(Powered by Google Gemini - In-Memory DB)_")

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
if "services_initialized" not in st.session_state or \
   st.session_state.get("current_api_key") != google_api_key:
    print("--- First time service initialization or API key change ---")
    with st.spinner("Initializing services (in-memory)..."):
        initialize_services(google_api_key, clear_existing_data=True) # Clear data on first init or key change
        st.session_state.services_initialized = True
        st.session_state.current_api_key = google_api_key
else:
    # This block runs on subsequent reruns if services are already initialized
    # We should NOT re-initialize the vector store here unless explicitly asked (e.g., by reset button)
    # Just ensure session state lists exist
    if "messages" not in st.session_state: st.session_state.messages = []
    if "indexed_documents" not in st.session_state: st.session_state.indexed_documents = []
    print(f"--- Services already initialized. Indexed docs count: {len(st.session_state.get('indexed_documents', []))} ---")


# --- PDF Upload and Processing ---
st.sidebar.header("Upload & Process PDFs")
st.sidebar.info("PDFs are processed for the current session only (in-memory database).")
uploaded_files = st.sidebar.file_uploader(
    "Upload one or more PDF files", type="pdf", accept_multiple_files=True, key="pdf_uploader"
)

if st.sidebar.button("Process Uploaded PDFs", key="process_button"):
    if uploaded_files:
        if not google_api_key: # Should be caught by now
            st.error("Please ensure your Google API Key is set.")
        else:
            temp_file_paths = []
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            for uploaded_file in uploaded_files:
                # Use a more unique temp name to avoid clashes if same filename uploaded in different sessions (though UPLOAD_DIR should be session-specific on cloud)
                # For local or less isolated envs, this helps.
                # unique_name = f"{uuid.uuid4()}_{uploaded_file.name}" 
                # temp_file_path = os.path.join(UPLOAD_DIR, unique_name)
                temp_file_path = os.path.join(UPLOAD_DIR, uploaded_file.name) # Keeping it simple for now
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                temp_file_paths.append(temp_file_path)

            if temp_file_paths:
                with st.spinner("Processing PDFs for this session..."):
                    try:
                        # With in-memory, vector_store should always be present after initial service init.
                        # If we want to *replace* existing processed docs, we need to re-init the store.
                        print("--- Processing PDFs: Re-initializing in-memory vector store for new batch ---")
                        initialize_services(google_api_key, clear_existing_data=True) # This will create a new empty vector_store and clear indexed_docs

                        chunks = process_pdfs(temp_file_paths)
                        if chunks:
                            print(f"--- Attempting to add {len(chunks)} chunks to IN-MEMORY vector store ---")
                            add_documents_to_store(st.session_state.vector_store, chunks)
                            st.success(f"Successfully processed and indexed {len(uploaded_files)} PDF(s) for this session.")
                            # list_indexed_documents should now reflect only the newly processed docs
                            st.session_state.indexed_documents = list_indexed_documents(st.session_state.vector_store)
                            # Messages were already cleared by initialize_services if clear_existing_data=True
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
            st.rerun() # Rerun to update UI, especially the indexed documents list
    else:
        st.sidebar.warning("Please upload PDF files first.")

# --- Display and Select Indexed Documents ---
st.sidebar.header("Indexed Documents (Current Session)")
# Ensure indexed_documents list is available in session_state
current_indexed_docs = st.session_state.get("indexed_documents", [])
print(f"--- Displaying Indexed Documents. Current list from session_state: {current_indexed_docs} ---")


if current_indexed_docs:
    selected_documents_for_query = st.sidebar.multiselect(
        "Filter Q&A by specific document(s):",
        options=current_indexed_docs, # Use the variable from session_state
        default=[], 
        key="doc_selector_sidebar_mem"
    )
else:
    st.sidebar.info("No documents processed for this session yet.")
    selected_documents_for_query = []

# --- Chat Interface ---
st.header("Chat about your PDFs (Current Session)")
st.header("Made by Priyansh Saxena")
current_messages = st.session_state.get("messages", [])
for i, message in enumerate(current_messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "sources" in message and message["sources"]:
            with st.expander("Sources", expanded=False):
                st.text_area("", value=message["sources"], height=100, disabled=True, key=f"sources_{i}_{message['content'][:10]}")

if prompt := st.chat_input("Ask a question about the processed PDFs..."):
    if "vector_store" not in st.session_state:
        st.error("System not ready. Please ensure API key is set and initialize the session by processing PDFs.")
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
                    with st.expander("Sources", expanded=True):
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
        print("--- Reset Session Data button clicked ---")
        with st.spinner("Resetting session data..."):
            initialize_services(google_api_key, clear_existing_data=True) 
            # indexed_documents and messages are cleared within initialize_services now
        st.sidebar.success("Session data (in-memory DB, processed PDFs, chat) has been reset.")
        st.rerun() # Rerun to reflect the cleared state in the UI immediately
    else:
        st.sidebar.error("Please provide Google API key before resetting.")
