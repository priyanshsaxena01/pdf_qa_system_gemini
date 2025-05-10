import os
import shutil
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import time # Import time for a small delay
import chromadb # Import chromadb for Settings if needed later (not used directly for client_settings now)

COLLECTION_NAME = "pdf_gemini_collection_v3" # Incremented version again

def get_vector_store(google_api_key, db_path, force_recreate=False):
    """
    Initializes and returns a Chroma vector store using Google Generative AI Embeddings.
    If force_recreate is True, it deletes any existing database.
    """
    print(f"--- get_vector_store called. db_path: {db_path}, force_recreate: {force_recreate} ---")
    if force_recreate and os.path.exists(db_path):
        print(f"--- Attempting to delete existing Chroma DB at {db_path} ---")
        try:
            shutil.rmtree(db_path)
            print(f"--- Successfully deleted directory: {db_path} ---")
            time.sleep(0.5) # Small delay
        except OSError as e:
            print(f"--- Error removing directory {db_path}: {e.strerror}. Will try to proceed. ---")
            # This could be problematic if files are locked.
    
    try:
        print(f"--- Ensuring directory exists: {db_path} (absolute: {os.path.abspath(db_path)}) ---")
        os.makedirs(db_path, exist_ok=True)
    except OSError as e:
        print(f"--- CRITICAL: Error creating directory {db_path}: {e.strerror}. Chroma will likely fail. ---")
        raise 

    print(f"--- Initializing Chroma with persist_directory: {db_path} and collection_name: {COLLECTION_NAME} ---")
    try:
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=google_api_key,
        )
        print("--- GoogleGenerativeAIEmbeddings initialized successfully ---")
    except Exception as e:
        print(f"--- CRITICAL: Error initializing GoogleGenerativeAIEmbeddings: {e} ---")
        raise

    try:
        vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=db_path # This is how LangChain's Chroma wrapper handles persistence
        )
        # Attempt a benign read operation to confirm writability or catch read-only issues early
        try:
            count = vector_store._collection.count()
            print(f"--- Chroma vector store initialized. Collection count: {count}. Name: {COLLECTION_NAME} ---")
        except Exception as e_read_check:
            print(f"--- WARNING: Post-initialization check failed for Chroma (e.g., count()): {e_read_check}. DB might be read-only or other issue. ---")
            # Depending on the error, you might want to raise it here if it indicates a fundamental problem
            # For "attempt to write a readonly database", this count() might still work if it's a read op,
            # but it's a good place to catch other init issues.

        return vector_store
    except Exception as e:
        print(f"--- CRITICAL ERROR initializing Chroma instance: {e} ---")
        print(f"--- This is often where 'attempt to write a readonly database' occurs. ---")
        print(f"--- Check permissions and if the path '{db_path}' is writable by the app process. ---")
        print(f"--- Also ensure the SQLite version is compatible (pysqlite3-binary patch). ---")
        raise

def add_documents_to_store(vector_store, documents):
    """Adds Langchain Document objects to the Chroma vector store."""
    if not documents:
        print("--- No documents to add to vector store. ---")
        return
    
    print(f"--- Attempting to add {len(documents)} chunks to vector store '{vector_store._collection.name if hasattr(vector_store, '_collection') and vector_store._collection else 'N/A'}' ---")
    try:
        vector_store.add_documents(documents)
        print(f"--- Successfully added {len(documents)} chunks. Attempting to persist... ---")
        vector_store.persist() 
        print(f"--- Successfully persisted {len(documents)} document chunks to the vector store. ---")
    except Exception as e:
        print(f"--- CRITICAL ERROR adding/persisting documents to vector store: {e} ---")
        print(f"--- This is often where 'attempt to write a readonly database' occurs if not caught during init. ---")
        raise # Re-raise to be caught by the Streamlit app's error handler

def get_retriever(vector_store, k_results=5):
    """Returns a general retriever from the vector store."""
    return vector_store.as_retriever(search_kwargs={"k": k_results})

def get_retriever_with_filter(vector_store, document_sources, k_results=5):
    """
    Returns a retriever that filters by specific document sources (filenames).
    """
    if not document_sources:
        return get_retriever(vector_store, k_results)
    filter_dict = {"source": {"$in": document_sources}}
    return vector_store.as_retriever(search_kwargs={"k": k_results, "filter": filter_dict})

def list_indexed_documents(vector_store):
    """Lists unique 'source' (filename) documents in the vector store."""
    print(f"--- Listing indexed documents from vector store. Collection: {vector_store._collection.name if hasattr(vector_store, '_collection') and vector_store._collection else 'N/A'} ---")
    try:
        all_docs_result = vector_store.get(include=["metadatas"]) 
        if all_docs_result and all_docs_result['metadatas']:
            sources = set(meta['source'] for meta in all_docs_result['metadatas'] if 'source' in meta)
            sorted_sources = sorted(list(sources))
            print(f"--- Found indexed sources: {sorted_sources} ---")
            return sorted_sources
        print("--- No metadatas found or no 'source' key in metadatas. Returning empty list for indexed documents. ---")
        return []
    except Exception as e:
        print(f"--- Error listing indexed documents: {e}. Collection might be empty or not yet created properly. ---")
        return []
