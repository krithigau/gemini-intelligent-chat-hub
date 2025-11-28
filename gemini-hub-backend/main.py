from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# --- SQLAlchemy Imports  ---
from sqlalchemy import create_engine, Column, Integer, String, Text, JSON, distinct
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
# ----------------------------------------

# Import AI Libraries
import chromadb
from sentence_transformers import SentenceTransformer
# --------------------------------

#===== Database Setup ===
DATABASE_URL = "sqlite:///./chats.db"
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
# ---------------------------

# --- Pydantic "Contracts"  ---
class Message(BaseModel):
    role: str
    content: str

class Conversation(BaseModel):
    title: str
    url: str
    messages: List[Message]
    sidebarTitle: Optional[str] = None
    collection: Optional[str] = "Uncategorized"
# ---------------------------------------
class QueryRequest(BaseModel):
    query: str
    collection_filter: Optional[str] = None
# --- SQLAlchemy "Model" (Keep this) ---
class Chat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    url = Column(String, unique=True)
    messages = Column(JSON)
    collection = Column(String, index=True, default="Uncategorized")
# ----------------------------------------------------

# --- Create SQL tables ---
Base.metadata.create_all(bind=engine)
# ---------------------------------------

# ---Initializing AI Components ---
# 1. Load the embedding model (this might download the model the first time)
#    'all-MiniLM-L6-v2' is a good, small, fast model.
print("Loading embedding model...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
print("Embedding model loaded.")

# 2. Initialize the ChromaDB client
#    'persistent' means it will save the vectors to disk in the 'chroma_db' folder.
print("Initializing vector database...")
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# 3. Get or create a "collection" (like a table for vectors)
#    We need to tell Chroma how large our vectors are (384 for this model).
#    The 'cosine' distance is good for semantic similarity.
vector_collection = chroma_client.get_or_create_collection(
    name="gemini_chats",
    metadata={"hnsw:space": "cosine"} # Use cosine distance
)
print("Vector database initialized.")
# -----------------------------------

app = FastAPI()

# Add CORS middleware (Keep this)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Session Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# ------------------------------------------

@app.get("/")
async def read_root():
    return {"Hello": "World"}


# ---  Save Chat Endpoint with AI! ---
@app.post("/api/save_chat")
async def save_chat(conversation: Conversation, db: Session = Depends(get_db)):
    print("--- SERVER RECEIVED A CHAT! ---")
    existing_chat = db.query(Chat).filter(Chat.url == conversation.url).first()
    
    if existing_chat:
        print(f"Chat with URL {conversation.url} already exists (ID: {existing_chat.id}). Skipping save.")
        print("---------------------------------")
        # Send a message back indicating it's already saved
        return {
            "status": "info",
            "message": f"Chat '{existing_chat.title}' was already saved.",
            "database_id": existing_chat.id 
        }
    # --- Part 1: Save to SQL Database (Keep this) ---
    messages_as_dicts = [message.model_dump() for message in conversation.messages]
    db_chat = Chat(
        title=conversation.sidebarTitle,
        url=conversation.url,
        messages=messages_as_dicts,
        collection=conversation.collection
    )
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    sql_db_id = db_chat.id # Get the ID from the SQL database
    print(f"Saved chat metadata to SQL DB with ID {sql_db_id}")
    # -----------------------------------------------

    # --- Chunk, Embed, and Save to Vector DB ---
    try:
        chunks = []
        chunk_ids = []
        metadatas = []
        current_chunk = ""
        chunk_counter = 0

        # Simple chunking: Combine messages until a certain length
        for i, msg in enumerate(conversation.messages):
            current_chunk += f"{msg.role}: {msg.content}\n"
            if len(current_chunk) > 500 or i == len(conversation.messages) - 1: # Chunk by length or at the end
                chunks.append(current_chunk)
                # Create a unique ID for each chunk: sql_id_chunk_number
                chunk_id = f"{sql_db_id}_{chunk_counter}"
                chunk_ids.append(chunk_id)
                # Store metadata linking back to the original chat
                metadatas.append({
                    "sql_chat_id": sql_db_id,
                    "title": conversation.sidebarTitle,
                    "url": conversation.url,
                    "chunk_index": chunk_counter,
                    "collection": conversation.collection
                })
                current_chunk = ""
                chunk_counter += 1

        if chunks:
            print(f"Generated {len(chunks)} chunks. Creating embeddings...")
            # Create embeddings for all chunks at once (more efficient)
            embeddings = embedding_model.encode(chunks).tolist()
            print("Embeddings created. Adding to vector database...")

            # Add to ChromaDB
            vector_collection.add(
                embeddings=embeddings,
                documents=chunks, # Store the text chunk itself
                metadatas=metadatas,
                ids=chunk_ids # Unique ID for each chunk
            )
            print(f"Successfully added {len(chunks)} chunks to vector DB.")
        else:
            print("No chunks generated for vector DB.")
            
    except Exception as e:
        print(f"Error during embedding/vector DB storage: {e}")
        # We don't fail the whole request, just log the error
    # -----------------------------------------------------
    
    print("---------------------------------")
    
    return {
        "status": "success",
        "message": f"Saved chat '{db_chat.title}'",
        "database_id": sql_db_id
    }

# --- Keeping the old search endpoint for now, we'll replace it later ---
@app.get("/api/search")
async def search_chats(q: str, db: Session = Depends(get_db)):
    print(f"--- SERVER RECEIVED A (Basic) SEARCH! Query: {q} ---")
    search_term = f"%{q}%"
    results = db.query(Chat).filter(Chat.title.ilike(search_term)).limit(10).all()
    print(f"Found {len(results)} results.")
    return results


@app.get("/api/chat_status")
async def get_chat_status(url: str, db: Session = Depends(get_db)):
    """
    Checks if a chat with the given URL exists in the database.
    """
    print(f"--- SERVER CHECKING STATUS for URL: {url} ---")
    existing_chat = db.query(Chat).filter(Chat.url == url).first()
    
    if existing_chat:
        print("Status: Found")
        return {"exists": True, "id": existing_chat.id, "title": existing_chat.title}
    else:
        print("Status: Not Found")
        return {"exists": False}
        
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv() # Load variables from .env file
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    print("Warning: GOOGLE_API_KEY not found in .env file.")
    # Handle the case where the key is missing - maybe raise an error or disable AI features
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print("Gemini API configured.")
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")

@app.post("/api/ai_search")
async def ai_search_chats(query_request: QueryRequest):
    """
    Performs semantic search on vector DB and generates a synthesized answer using Gemini.
    Expects a JSON body like: {"query": "user's question", "collection_filter": "SQL"}
    """
    query = query_request.query
    if not query:
        raise HTTPException(status_code=400, detail="Missing 'query' in request body")

    print(f"--- SERVER RECEIVED AI SEARCH! Query: {query} ---")

    try:
        # 1. Embed the user's query
        print("Embedding query...")
        query_embedding = embedding_model.encode([query]).tolist()[0]

        # --- NEW FILTER LOGIC GOES HERE (Inside the function!) ---
        where_filter = None
        if query_request.collection_filter:
            print(f"Filtering search by collection: {query_request.collection_filter}")
            where_filter = {"collection": query_request.collection_filter}
        # ---------------------------------------------------------

        # 2. Query ChromaDB for relevant chunks
        print("Querying vector database...")
        results = vector_collection.query(
            query_embeddings=[query_embedding],
            n_results=20, 
            include=['documents', 'metadatas'],
            where=where_filter # <-- Use the filter here!
        )

        if not results or not results.get('documents') or not results['documents'][0]:
             print("No relevant documents found in vector DB.")
             return {"answer": "I couldn't find any relevant information in your saved chats to answer that.", "sources": []}

        # 3. Prepare context for Gemini
        print("Preparing context for LLM...")
        context = "\n---\n".join(results['documents'][0])
        source_metadatas = results['metadatas'][0] if results.get('metadatas') else []

        unique_sources = []
        seen_urls = set()
        for meta in source_metadatas:
            if meta and meta.get('url') not in seen_urls:
                unique_sources.append({
                    "title": meta.get('title', 'Unknown Title'),
                    "url": meta.get('url')
                })
                seen_urls.add(meta.get('url'))

        # 4. Generate Answer using Gemini API (RAG)
        if not GEMINI_API_KEY:
             print("Gemini API Key not configured. Returning raw context.")
             return {"answer": "Gemini API key not configured. Raw context:\n" + context, "sources": unique_sources}

        print("Calling Gemini API...")
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            prompt = f"""Based *only* on the following context from my saved chat history, please answer my question. Be concise and synthesize the information. If the context doesn't contain the answer, say so.

            Context:
            {context}

            Question: {query}

            Answer:"""

            response = model.generate_content(prompt)

            if response.parts:
                generated_answer = "".join(part.text for part in response.parts)
                print("Gemini response received.")
            else:
                print("Gemini response was empty or blocked.")
                generated_answer = "The AI model returned an empty response. This might be due to safety settings or the query itself."

        except Exception as genai_error:
             print(f"Error calling Gemini API: {genai_error}")
             generated_answer = f"Error generating answer with Gemini: {genai_error}. Raw context:\n{context}"

        return {"answer": generated_answer, "sources": unique_sources}

    except Exception as e:
        print(f"Error during AI search: {e}")
        raise HTTPException(status_code=500, detail=f"An internal error occurred during search: {e}")

@app.get("/api/collections", response_model=List[str])
async def get_collections(db: Session = Depends(get_db)):
    """
    Get a list of all unique collection names.
    """
    print("--- SERVER RECEIVED REQUEST for collections ---")
    
    # Query the Chat table for all unique, non-null collection names
    collection_tuples = db.query(Chat.collection).distinct().filter(Chat.collection.isnot(None)).all()
    
    # The query returns a list of tuples, like [('SQL'), ('Python')].
    # We need to flatten it into a simple list: ['SQL', 'Python']
    collections = [c[0] for c in collection_tuples if c[0]]
    
    print(f"Found collections: {collections}")
    return collections


@app.get("/api/chats")
async def get_chats_by_collection(collection: str, db: Session = Depends(get_db)):
    """
    Get all chats belonging to a specific collection.
    """
    print(f"--- SERVER RECEIVED REQUEST for chats in collection: {collection} ---")
    
    # Query the Chat table and filter by the collection name
    # We'll order by ID descending to get the newest ones first
    chats = db.query(Chat).filter(Chat.collection == collection).order_by(Chat.id.desc()).all()
    
    print(f"Found {len(chats)} chats in this collection.")
    # FastAPI will automatically convert this list of Chat objects into JSON
    return chats
