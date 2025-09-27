from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

def get_qa_chain(google_api_key, retriever):
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite", 
            google_api_key=google_api_key,
            temperature=0.5,
            convert_system_message_to_human=True
        )
    except Exception as e:
        print(f"Error initializing ChatGoogleGenerativeAI: {e}")
        raise

    prompt_template_str = """You are an AI assistant. Your task is to answer questions based ONLY on the provided context.
If the answer is not found in the context, explicitly state "The answer is not found in the provided documents."
Do not make up information or answer from your general knowledge.
When you use information from the context, you MUST cite the source.
A citation includes the source document filename and the page number. Format citations as: (Source: [filename], Page: [page_number]).
If multiple pieces of context are used, cite each one.

Context:
---
{context}
---

Question: {question}

Helpful Answer (Remember to cite sources from the context if information is used):"""
    
    PROMPT = PromptTemplate(
        template=prompt_template_str, input_variables=["context", "question"]
    )

    chain_type_kwargs = {"prompt": PROMPT}
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs=chain_type_kwargs
    )
    return qa_chain

def query_rag(qa_chain, question):
    try:
        result = qa_chain.invoke({"query": question})
        answer = result["result"]
        source_documents = result["source_documents"]
        
        sources_text_list = []
        if source_documents:
            unique_sources = {}
            for doc in source_documents:
                filename = doc.metadata.get('source', 'Unknown Document')
                page_num_0_indexed = doc.metadata.get('page', None)
                
                page_display = int(page_num_0_indexed) + 1 if page_num_0_indexed is not None else 'N/A'
                
                source_key = (filename, page_display)
                if source_key not in unique_sources:
                    sources_text_list.append(f"- {filename}, Page: {page_display}")
                    unique_sources[source_key] = True
        
        formatted_sources = "\n".join(sources_text_list) if sources_text_list else "No specific sources cited by the model for this answer, or sources not found in metadata."
        return answer, formatted_sources
    
    except Exception as e:
        error_message = f"An error occurred during RAG query: {e}"
        print(error_message)
        if "response was blocked" in str(e).lower() or "SAFETY" in str(e).upper():
            return "The response was blocked due to safety settings or other API restrictions. Try rephrasing your question or check the document content.", "No sources available due to API restriction."
        return error_message, "No sources available due to error."
