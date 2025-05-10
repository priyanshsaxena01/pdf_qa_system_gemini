import os
import shutil
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Default path if not overridden (Codespaces usually puts project at /workspaces/repo_name)
# CHROMA_DB_PATH_DEFAULT = "./chroma_db" # Relative to where app.py is run
COLLECTION_NAME = "pdf_gemini_codespaces_collection"

def get_vector_store(google_api_key, db_path, force_recreate=False): # Added db_path parameter
    """
    Initializes and returns a Chroma vector store using Google Generative AI Embeddings.
    If force_recreate is True, it deletes any existing database.
    """
    if force_recreate and os.path.exists(db_path):
        print(f"Deleting existing Chroma DB at {db_path}")
        try:
            shutil.rmtree(db_path)
        except OSError as e:
            print(f"Error removing directory {db_path}: {e.strerror}")
    
    os.makedirs(db_path, exist_ok=True)
    
    try:
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=google_api_key,
        )
    except Exception as e:
        print(f"Error initializing GoogleGenerativeAIEmbeddings: {e}")
        raise

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=db_path # Use the passed db_path
    )
    return vector_store

def add_documents_to_store(vector_store, documents):
    if not documents:
        print("No documents to add to vector store.")
        return
    try:
        vector_store.add_documents(documents)
        vector_store.persist() 
        print(f"Added {len(documents)} document chunks to the vector store and persisted.")
    except Exception as e:
        print(f"Error adding documents to vector store: {e}")
        raise

def get_retriever(vector_store, k_results=5):
    return vector_store.as_retriever(search_kwargs={"k": k_results})

def get_retriever_with_filter(vector_store, document_sources, k_results=5):
    if not document_sources:
        return get_retriever(vector_store, k_results)
    filter_dict = {"source": {"$in": document_sources}}
    return vector_store.as_retriever(search_kwargs={"k": k_results, "filter": filter_dict})

def list_indexed_documents(vector_store):
    try:
        all_docs_result = vector_store.get(include=["metadatas"]) 
        if all_docs_result and all_docs_result['metadatas']:
            sources = set(meta['source'] for meta in all_docs_result['metadatas'] if 'source' in meta)
            return sorted(list(sources))
        return []
    except Exception as e:
        print(f"Error listing indexed documents (collection might be empty or not yet created): {e}")
        return []