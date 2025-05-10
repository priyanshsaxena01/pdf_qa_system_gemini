
## Setup and Running in GitHub Codespaces

1.  **Open in Codespace:**
    *   Navigate to your GitHub repository containing this project.
    *   Click the green "<> Code" button.
    *   Go to the "Codespaces" tab.
    *   Click "Create codespace on main" (or your desired branch). This will build and open your Codespace.

2.  **Set Google API Key as a Secret (Highly Recommended):**
    *   Once the Codespace is open, on the left sidebar, click the "Remote Explorer" icon (looks like a computer monitor or a remote connection symbol).
    *   In the "REMOTE EXPLORER" pane that opens, find the "GitHub" section. Your Codespace should be listed.
    *   Alternatively, open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`) and type "Codespaces: Manage User Secrets" or "Codespaces: Manage Repository Secrets".
    *   Add a new secret:
        *   **Name:** `GOOGLE_API_KEY`
        *   **Value:** `your_actual_google_api_key_for_gemini`
    *   The `app.py` is configured to automatically try and read this environment variable. If not found, it will prompt you to input it in the Streamlit sidebar.
    *   *Note: After adding a secret, you might need to "Rebuild Container" or at least close and reopen any active terminals for the new environment variable to be picked up by all processes. A fresh terminal should have it.*

3.  **Open a Terminal in Codespaces:**
    *   The Codespace interface includes an integrated terminal (usually at the bottom). If not visible, go to "Terminal" > "New Terminal" from the top menu.

4.  **Create Virtual Environment & Install Dependencies:**
    *   It's good practice to use a virtual environment:
        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        ```
    *   Install the required packages:
        ```bash
        pip install -r requirements.txt
        ```

5.  **Handle SQLite Version for ChromaDB (If Necessary):**
    *   ChromaDB requires `sqlite3 >= 3.35.0`. Default Codespace images might have an older version.
    *   **After running `pip install -r requirements.txt`**, if you encounter a `RuntimeError` about an unsupported `sqlite3` version when you first run the app:
        1.  Ensure your virtual environment (`.venv`) is active.
        2.  Install the `pysqlite3-binary` package:
            ```bash
            pip install pysqlite3-binary
            ```
        3.  **Apply the patch:** Open the file `/workspaces/<YOUR_REPO_NAME>/.venv/lib/python3.X/site-packages/chromadb/__init__.py` (replace `<YOUR_REPO_NAME>` and `python3.X` with your actual repo name and Python version).
            At the **very top** of this file, add:
            ```python
            # START ChromaDB patch for SQLite
            try:
                __import__('pysqlite3')
                import sys
                sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
                # print("Successfully patched sqlite3 with pysqlite3-binary for ChromaDB.") # Optional: for confirmation
            except ImportError:
                pass # print("pysqlite3-binary not found, ChromaDB might use system's sqlite3.") # Optional
            # END ChromaDB patch for SQLite

            # ... (rest of the original chromadb/__init__.py file starts here) ...
            ```
        4.  Save the `chromadb/__init__.py` file. This patch makes Python use the newer SQLite version provided by `pysqlite3-binary`.

6.  **Run the Streamlit Application:**
    *   In the Codespaces terminal (with the virtual environment activated):
        ```bash
        streamlit run app.py
        ```

7.  **Access the Application:**
    *   Codespaces will automatically detect that a service is running on a port (Streamlit defaults to 8501).
    *   A notification will usually pop up in the bottom-right corner: "Your application running on port 8501 is available." Click the "Open in Browser" button.
    *   Alternatively, go to the "Ports" tab in the Codespaces interface (usually next to the Terminal tab or in the bottom panel). Find the forwarded port for your application (it will say "localhost:8501" or similar) and click the "Open in Browser" (globe) icon next to it.

## Using the Application

1.  **API Key:** If you didn't set the `GOOGLE_API_KEY` as a Codespace secret, enter it in the sidebar when prompted.
2.  **Upload PDFs:** Use the "Upload one or more PDF files" widget in the sidebar.
3.  **Process PDFs:** Click the "Process Uploaded PDFs" button. Wait for processing and indexing to complete. The chat history will be cleared.
4.  **Filter (Optional):** The "Indexed Documents" list in the sidebar will show processed PDF filenames. You can select specific documents to narrow down your Q&A scope for subsequent questions.
5.  **Chat:** Type your question about the PDF content in the chat input box at the bottom of the main area and press Enter.
6.  **View Responses:** The system will retrieve relevant context, generate an answer using Gemini, and display the answer along with cited sources (document filename and page number) in the chat interface. Your conversation history will be maintained.

## Committing Changes from Codespaces to GitHub

1.  **Source Control Panel:** Click the Source Control icon (branching diagram) on the left sidebar in Codespaces.
2.  **Stage Changes:** Click the `+` icon next to changed files or next to the "Changes" header to stage all.
3.  **Commit Message:** Type a descriptive message in the input box at the top of the Source Control panel.
4.  **Commit:** Click the checkmark icon (✓) or press `Ctrl+Enter` (`Cmd+Enter` on Mac).
5.  **Push/Sync:** Click the "Synchronize Changes" button in the status bar (bottom of the window) or use the `...` menu in the Source Control panel to "Push".

## Troubleshooting in Codespaces

*   **Port Not Forwarding:** If the app runs but you don't see a notification, check the "Ports" tab manually.
*   **API Key Issues:** Double-check the secret name (`GOOGLE_API_KEY`) and its value. Ensure your Google API key is valid and has the necessary permissions/quotas for Gemini (`gemini-1.5-flash-latest`) and embedding models (`models/embedding-001`).
*   **`ModuleNotFoundError`:** Ensure dependencies are installed in your active virtual environment (`pip install -r requirements.txt`).
*   **SQLite Error:** Follow Step 5 under "Setup and Running" if you see errors related to `sqlite3` version.
*   **Content Filtering/Safety Settings:** Gemini models have safety filters. If responses are blocked, the app will try to indicate this. Consider rephrasing questions or checking document content.

---

This README should be comprehensive and guide users effectively. Remember to replace placeholders like `<YOUR_REPO_NAME>` or `python3.X` if you're manually guiding someone through the SQLite fix.
