# core/vector_store.py
import os
# import shutil # No longer needed for deleting directories
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
# import time # No longer needed for delays

# COLLECTION_NAME can still be used for in-memory, though less critical
# Using a versioned name is still good if you ever switch back to persistence.
COLLECTION_NAME = "pdf_gemini_in_memory_v1"

def get_vector_store(google_api_key): # Removed db_path and force_recreate
    """
    Initializes and returns an IN-MEMORY Chroma vector store.
    """
    print(f"--- Initializing IN-MEMORY Chroma with collection_name: {COLLECTION_NAME} ---")
    try:
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=google_api_key,
        )
        print("--- GoogleGenerativeAIEmbeddings initialized successfully (for in-memory store) ---")
    except Exception as e:
        print(f"--- CRITICAL: Error initializing GoogleGenerativeAIEmbeddings: {e} ---")
        raise

    try:
        # For an in-memory Chroma instance with LangChain,
        # you simply don't provide a persist_directory.
        # LangChain's Chroma wrapper will use chromadb.Client() which defaults to in-memory.
        vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings
            # No persist_directory here!
        )
        
        # Check if collection was created
        if vector_store._collection:
            print(f"--- IN-MEMORY Chroma vector store initialized. Collection: '{vector_store._collection.name}', ID: {vector_store._collection.id} ---")
            # You can do a quick test
            # vector_store.add_texts(["test_in_memory"], ids=["test_mem_id"])
            # print(f"--- In-memory test add done. Count: {vector_store._collection.count()} ---")
            # vector_store._collection.delete(ids=["test_mem_id"])
        else:
            print("--- WARNING: In-memory Chroma store initialized, but _collection is None. This is unexpected. ---")

        return vector_store
    except Exception as e:
        print(f"--- CRITICAL ERROR initializing IN-MEMORY Chroma instance: {e} ---")
        import traceback
        traceback.print_exc()
        raise

def add_documents_to_store(vector_store, documents):
    """Adds Langchain Document objects to the in-memory Chroma vector store."""
    if not documents:
        print("--- No documents to add to in-memory vector store. ---")
        return
    
    collection_name_debug = vector_store._collection.name if hasattr(vector_store, '_collection') and vector_store._collection else 'N/A'
    print(f"--- Attempting to add {len(documents)} chunks to IN-MEMORY vector store '{collection_name_debug}' ---")
    try:
        vector_store.add_documents(documents)
        # No vector_store.persist() needed for in-memory
        print(f"--- Successfully added {len(documents)} document chunks to the IN-MEMORY vector store. ---")
    except Exception as e:
        print(f"--- CRITICAL ERROR adding documents to IN-MEMORY vector store: {e} ---")
        raise

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
    """Lists unique 'source' (filename) documents in the in-memory vector store."""
    collection_name_debug = vector_store._collection.name if hasattr(vector_store, '_collection') and vector_store._collection else 'N/A'
    print(f"--- Listing indexed documents from IN-MEMORY vector store. Collection: {collection_name_debug} ---")
    try:
        # In-memory store still holds documents in the same way
        all_docs_result = vector_store.get(include=["metadatas"]) 
        if all_docs_result and all_docs_result['metadatas']:
            sources = set(meta['source'] for meta in all_docs_result['metadatas'] if 'source' in meta)
            sorted_sources = sorted(list(sources))
            print(f"--- Found indexed sources in IN-MEMORY store: {sorted_sources} ---")
            return sorted_sources
        print("--- No metadatas found or no 'source' key in metadatas (in-memory). Returning empty list. ---")
        return []
    except Exception as e:
        print(f"--- Error listing indexed documents from IN-MEMORY store: {e}. ---")
        return []
