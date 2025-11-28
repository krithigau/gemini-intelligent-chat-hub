# Gemini Intelligent Knowledge Hub (RAG-Powered)

## Project Overview

The Gemini Intelligent Knowledge Hub is a full-stack application designed to solve the **"write-only" memory problem** inherent to large language models (LLMs). It transforms a flat, chronological chat history into a persistent, organized, and semantically searchable knowledge base.

This system demonstrates the implementation of a **Retrieval-Augmented Generation (RAG)** pipeline in a production-style, multi-service architecture.

##  Technical Architecture

The project is split into two primary services:

### I. Frontend (Chrome Extension)
* **Technology:** Vanilla JavaScript (ES6+), HTML/CSS, Chrome Extension API.
* **Function:** Injects a "Save" button into the Gemini UI, orchestrates asynchronous saving/query requests, and handles dynamic multi-view rendering (Collections/Search).

### II. Backend (Service Layer)
* **Technology:** Python, FastAPI, Uvicorn (ASGI Server).
* **Data Persistence (Hybrid):**
    * **SQL Metadata:** PostgreSQL/SQLite managed by SQLAlchemy for collections and basic chat metadata.
    * **Vector Store:** ChromaDB (local persistence) for storing high-dimensional vector embeddings.
* **Intelligence:** Google Gemini API (`gemini-pro` / `gemini-1.5-flash`).

##  Key Features & Achieved Milestones

| Feature | Description | Achievement Demonstrated |
| :--- | :--- | :--- |
| **RAG Semantic Search** | Users can ask natural language questions (e.g., "Summarize key SQL concepts") and receive a synthesized answer based *only* on the content saved across all their chats. | Implementation of **vector embedding** (using `sentence-transformers`) and complex vector database querying. |
| **Full-Stack Data Pipeline** | Seamless communication between the `content.js` script (on Google's domain) and the local FastAPI server using **CORS middleware** and the `fetch` API. | Mastery of cross-origin communication and service integration. |
| **Robust DOM Observation** | The extension successfully injects persistent buttons and scrapes data from Gemini's complex interface using a **Debounced MutationObserver**. | Expertise in real-world **DOM manipulation** and mitigating Single Page Application (SPA) re-rendering/hydration issues. |
| **Data Integrity** | Implements a **duplicate checking** mechanism in the backend (`/save_chat`) based on URL before processing, ensuring data hygiene in the database. | Practical application of database query optimization and integrity checks. |
| **Multi-View UI** | Developed a clear, organized popup with **Collections** (folders) functionality, allowing users to browse saved chats and scope their AI searches. | Proficiency in modular frontend design and event handling. |

##  Development Hurdles & Problem Solving

This project involved overcoming several significant real-world development challenges:

1.  **Dependency Resolution:** Faced and resolved multiple `pip` dependency conflicts (e.g., between `kubernetes`, `urllib3`, and new AI libraries) by performing a **minimal environment rebuild**, ensuring clean operation.
2.  **External API Management:** Diagnosed and fixed the recurrent **`404 models/gemini-pro is not found`** error by correctly identifying that the local library version was outdated and forcing an upgrade, demonstrating robust **API version management**.
3.  **Network/Testing Isolation:** Debugged issues where the PowerShell `POST` request was blocked by a local proxy/firewall while `GET` requests were working, requiring a pivot to a **browser-based `fetch` test** to isolate the error from the local shell environment.
4.  **Fragile Selectors:** Successfully debugged and corrected outdated CSS selectors (`a.chat-history-item` -> `div.conversation`) by using the browser's **Inspect Element** tool, demonstrating adaptability to target website changes.

## ⚙️ Developer Guide (Installation)

### Prerequisites
* Python 3.10+
* A Gemini API Key (set as a `GOOGLE_API_KEY` in a local `.env` file)

### 1. Backend Service Setup (API)

```bash
# Clone and navigate to the backend folder
git clone https://github.com/krithigau/gemini-intelligent-chat-hub.git
cd gemini-intelligent-chat-hub/gemini-hub-backend

# 1. Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1  # (Use 'source venv/bin/activate' on Mac/Linux)

# 2. Install all core dependencies
pip install fastapi uvicorn sqlalchemy sentence-transformers chromadb google-generativeai python-dotenv pydantic

# 3. Start the server
uvicorn main:app --reload
