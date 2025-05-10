# 📄 ChatPDF-Gemini: Intelligent PDF Q&A with Conversational AI

**Engage in dynamic conversations with your PDF documents!** ChatPDF-Gemini leverages the power of Google's Gemini AI (specifically `gemini-1.5-flash-latest`) and advanced RAG (Retrieval Augmented Generation) techniques to provide accurate, context-aware answers from your uploaded PDFs.

**Live Demo:** [**https://pdf-system.streamlit.app/**](https://pdf-system.streamlit.app/)

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://pdf-system.streamlit.app/)

## ✨ Features

*   **Conversational Interface:** Ask multiple follow-up questions in a natural chat flow.
*   **Multi-PDF Support:** Upload and query one or more PDF documents simultaneously.
*   **Intelligent Document Processing:**
    *   Robust PDF parsing using PyMuPDF.
    *   Effective text chunking strategies for optimal context retrieval.
*   **State-of-the-Art AI:**
    *   Utilizes Google's `gemini-1.5-flash-latest` for insightful answer generation.
    *   Employs Google's `models/embedding-001` for high-quality semantic embeddings.
*   **Accurate Retrieval:**
    *   Embeddings stored and queried efficiently using ChromaDB.
    *   Semantic search retrieves the most relevant text chunks for your questions.
*   **Source Citations:** Answers are accompanied by clear citations, including the source document filename and page number.
*   **Document Filtering:** Optionally focus your Q&A on specific uploaded documents.
*   **Persistent Chat History:** Your conversation is maintained during your session.
*   **Secure API Key Handling:** Designed for secure API key management, especially when deployed (e.g., Streamlit Community Cloud secrets).
*   **Easy Deployment:** Ready for deployment on platforms like Streamlit Community Cloud.

## 🚀 How It Works (RAG Architecture)

1.  **PDF Ingestion & Processing:**
    *   User uploads PDF(s).
    *   Text is extracted and intelligently split into manageable, overlapping chunks.
    *   Metadata (filename, page number) is associated with each chunk.
2.  **Embedding & Vector Storage:**
    *   Each text chunk is converted into a numerical vector (embedding) using Google's embedding model.
    *   These embeddings and their metadata are stored in a ChromaDB vector database.
3.  **User Query & Retrieval:**
    *   User asks a question in the chat interface.
    *   The question is embedded using the same model.
    *   A similarity search is performed in ChromaDB to find the most relevant text chunks (context) from the indexed PDFs.
    *   Optional filtering by document source is applied.
4.  **Answer Generation with LLM:**
    *   The retrieved context chunks and the user's question are formulated into a prompt.
    *   This prompt is sent to the Gemini LLM (`gemini-1.5-flash-latest`).
    *   The LLM generates an answer based *solely* on the provided context, citing sources as instructed.
5.  **Display:**
    *   The answer and cited sources are displayed in the chat interface.

## 🛠️ Tech Stack

*   **Language:** Python 3.10+
*   **Web Framework:** Streamlit
*   **LLM & Embeddings:** Google Gemini API (`gemini-1.5-flash-latest`, `models/embedding-001`) via `langchain-google-genai`
*   **Core RAG Framework:** LangChain
*   **Vector Database:** ChromaDB
*   **PDF Parsing:** PyMuPDF (`fitz`)
*   **SQLite Handling (if needed):** `pysqlite3-binary` (includes a patch in `app.py` for compatibility in some deployment environments)

## ⚙️ Local Setup & Running (e.g., on Codespaces or Locally)

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git 
    # Replace with your actual repository URL
    cd YOUR_REPOSITORY_NAME
    ```

2.  **Create and Activate a Virtual Environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Linux/macOS
    # .venv\Scripts\activate   # On Windows
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` includes `pysqlite3-binary` for SQLite compatibility.*

4.  **Set Google API Key:**
    *   **Recommended for Codespaces/Deployment:** Set it as an environment variable or a secret named `GOOGLE_API_KEY`. The application will try to read this.
    *   **Local Testing:** If the environment variable isn't set, the Streamlit app will prompt you to enter it in the sidebar.
    *   Ensure your API key is enabled for the "Vertex AI API" or "Generative Language API" in Google Cloud Console and has quota for the Gemini models.

5.  **Run the Streamlit Application:**
    ```bash
    streamlit run app.py
    ```
    The application will typically open in your web browser at `http://localhost:8501`.

## ☁️ Deployment (Streamlit Community Cloud)

This application is optimized for deployment on [Streamlit Community Cloud](https://share.streamlit.io/).

1.  **Push your code to a GitHub repository.** Ensure `requirements.txt` is accurate and includes `pysqlite3-binary`.
2.  **The `app.py` includes a patch at the very beginning to use `pysqlite3-binary` for SQLite compatibility, which is crucial for ChromaDB on Streamlit Cloud.**
3.  **Sign up/Log in to Streamlit Community Cloud** using your GitHub account.
4.  Click **"New app"** and connect your GitHub repository.
5.  **Configuration:**
    *   **Repository:** Your GitHub repo.
    *   **Branch:** e.g., `main`.
    *   **Main file path:** `app.py`.
    *   **Advanced Settings > Secrets:** Add your `GOOGLE_API_KEY` with its value.
6.  Click **"Deploy!"**.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Please feel free to:
*   Open an issue to discuss a bug or a new feature.
*   Submit a pull request with your improvements.

## 📜 License

This project is licensed under the MIT License - see the `LICENSE` file for details (if you add one).

---

**Note on SQLite Version for ChromaDB:**
ChromaDB requires `sqlite3 >= 3.35.0`. Some environments (like default Codespaces or certain deployment platforms) might have an older system SQLite. This project includes `pysqlite3-binary` in `requirements.txt` and a patch at the beginning of `app.py` to instruct Python to use this newer, bundled SQLite version. This generally resolves compatibility issues.
