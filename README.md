# 🧠 Gemini Intelligent Chat Hub

A full-stack AI application that transforms Google Gemini into a persistent, organized, and searchable personal knowledge base.


*(Optional: Add a banner image or GIF of the extension in action here)*

## 🚀 The Problem
Gemini is a powerful tool, but its chat history is a "write-only" system. Valuable insights get buried in a linear, unorganized list.
* **No Memory:** You can't ask Gemini to reference a conversation you had last week.
* **No Organization:** There is no way to group chats by project or topic (e.g., "SQL Prep", "Python Learning").
* **Information Silos:** Knowledge is trapped in individual chats, forcing you to re-ask questions.

## 💡 The Solution
I built a **Retrieval-Augmented Generation (RAG)** system that acts as a "Second Brain" for your Gemini interactions.

1.  **Capture:** A Chrome Extension injects a "Save" button directly into the Gemini UI.
2.  **Organize:** Users can tag chats into custom **Collections**.
3.  **Recall:** An AI-powered "Eureka!" search lets you ask questions like *"What did I learn about subqueries?"*. The system searches your saved history and synthesizes a new answer based on your personal notes.

## 🛠️ Tech Stack

### Frontend (Chrome Extension)
* **JavaScript (Vanilla):** DOM manipulation, `MutationObserver` for dynamic content handling, and Fetch API.
* **HTML/CSS:** Custom popup UI with multi-view navigation.

### Backend (API)
* **Python & FastAPI:** High-performance REST API.
* **SQLAlchemy & SQLite:** Relational database for managing chat metadata and collections.
* **ChromaDB:** Vector database for storing semantic embeddings.
* **Sentence-Transformers:** Local/Cloud embedding models to convert text to vectors.
* **Google Gemini API:** Used for the final RAG generation step.

## ✨ Key Features

* **🕷️ Robust DOM Scraping:** Uses `MutationObserver` and debouncing to handle Gemini's complex Single Page Application (SPA) hydration events.
* **📂 Smart Collections:** Tag and organize chats into folders.
* **🔍 Semantic Search:** Uses vector embeddings to find relevant chats by *meaning*, not just keywords.
* **🧠 RAG Pipeline:** Retrieves relevant context chunks and uses an LLM to generate a specific answer grounded in your saved data.

## ⚙️ How to Run Locally

### 1. Clone the Repository
```bash
git clone https://github.com/krithigau/gemini-intelligent-chat-hub.git
cd gemini-intelligent-chat-hub