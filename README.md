# PDF Question Answering System (Powered by Gemini on GitHub Codespaces)

This system allows users to upload PDF documents and ask questions that are answered based on the content of those documents. It uses Retrieval Augmented Generation (RAG) with Google's Gemini API and ChromaDB as a vector store, designed to run smoothly in a GitHub Codespace.

## Features
(Same as before)

## Project Structure
(Same as before)

## Setup and Running in GitHub Codespaces

1.  **Open in Codespace:**
    *   Navigate to your GitHub repository containing this project.
    *   Click the "<> Code" button.
    *   Go to the "Codespaces" tab.
    *   Click "Create codespace on main" (or your desired branch). This will build and open your Codespace.

2.  **Set Google API Key as a Secret (Recommended):**
    *   Once the Codespace is open, find the GitHub Codespaces settings (often accessible via a command palette or a specific icon/menu related to Codespaces).
    *   Go to "Secrets" or "Repository secrets" (if you want it available for all Codespaces of this repo).
    *   Add a new secret:
        *   **Name:** `GOOGLE_API_KEY`
        *   **Value:** `your_actual_google_api_key`
    *   The `app.py` is configured to try and read this environment variable. If not found, it will ask you to input it in the Streamlit sidebar.
    *   *Note: After adding a secret, you might need to rebuild or restart the Codespace for the new environment variable to be picked up by already running terminals/processes. A fresh terminal should have it.*

3.  **Open a Terminal in Codespaces:**
    *   The Codespace interface includes an integrated terminal (usually at the bottom).

4.  **Install Dependencies (if not automatically handled by a devcontainer config):**
    *   Codespaces often uses a `devcontainer.json` to pre-configure the environment. If you don't have one that installs Python dependencies, or if you want to ensure they are up-to-date:
        ```bash
        python -m venv .venv  # Create a virtual environment (good practice)
        source .venv/bin/activate # Activate it
        pip install -r requirements.txt
        ```
    *   If you choose to use a virtual environment, make sure your Codespace terminal is using it. The Python extension in Codespaces should also pick it up.

5.  **Run the Streamlit Application:**
    *   In the Codespaces terminal (with the virtual environment activated if you created one):
        ```bash
        streamlit run app.py
        ```

6.  **Access the Application:**
    *   Codespaces will automatically detect that a service is running on a port (Streamlit defaults to 8501).
    *   A notification will usually pop up in the bottom-right corner saying "Your application running on port 8501 is available." with an "Open in Browser" button.
    *   You can also go to the "Ports" tab in the Codespaces interface (often next to the Terminal tab) and find the forwarded port for your application. Click the "Open in Browser" (globe) icon.

7.  **Using the App:**
    *   If you set the `GOOGLE_API_KEY` secret, it should be pre-filled or automatically used. Otherwise, enter it in the sidebar.
    *   Upload PDFs, process them, and ask questions as before.
    *   The `chroma_db` and `uploads` directories will be created within your Codespace's file system. These will persist as long as your Codespace exists (but are `.gitignored` so they won't be committed back to your repo).

## Troubleshooting in Codespaces

*   **Port Not Forwarding:** If the app runs but you don't see a notification, check the "Ports" tab manually. Ensure Streamlit is running and listening.
*   **API Key Issues:** Double-check the secret name (`GOOGLE_API_KEY`) and its value. Ensure your Google API key is valid and has the necessary permissions for Gemini and embedding models.
*   **"ModuleNotFoundError":** Make sure you've installed dependencies correctly (Step 4). If using a venv, ensure it's activated in the terminal where you run `streamlit run`.
*   **Performance:** Codespaces offers different machine types. If you find it slow (unlikely for this app unless PDFs are huge), you can change the machine type for your Codespace (this might involve costs if you exceed free tier limits).

(Keep other sections like "Features", "Project Structure" from the previous README if they are still accurate)