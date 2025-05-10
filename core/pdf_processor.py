import os
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

def process_pdfs(pdf_files_paths):
    all_docs_for_db = []
    for pdf_path in pdf_files_paths:
        try:
            loader = PyMuPDFLoader(pdf_path)
            documents_from_pdf_pages = loader.load() 

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )
            
            for doc_page in documents_from_pdf_pages:
                doc_page.metadata["source"] = os.path.basename(pdf_path) # Consistent key for filtering

            split_chunks = text_splitter.split_documents(documents_from_pdf_pages)
            all_docs_for_db.extend(split_chunks)
            print(f"Processed and chunked {os.path.basename(pdf_path)}: {len(documents_from_pdf_pages)} pages -> {len(split_chunks)} chunks")
        except Exception as e:
            print(f"Error processing {os.path.basename(pdf_path)}: {e}")
            continue
            
    return all_docs_for_db
