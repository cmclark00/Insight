"""
Configuration settings for the Character Conversation Application
"""

import os
from pathlib import Path

# Application Settings
APP_NAME = "Character Conversation Studio"
APP_VERSION = "1.0.0"

# Directories
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MANUSCRIPTS_DIR = DATA_DIR / "manuscripts"
CHARACTERS_DIR = DATA_DIR / "characters"
VECTOR_DB_DIR = DATA_DIR / "vector_db"

# Create directories if they don't exist
for directory in [DATA_DIR, MANUSCRIPTS_DIR, CHARACTERS_DIR, VECTOR_DB_DIR]:
    directory.mkdir(exist_ok=True)

# LLM Settings
DEFAULT_LLM_MODEL = "llama3.1:8b"  # Ollama model name
OLLAMA_BASE_URL = "http://localhost:11434"
MAX_TOKENS = 2048
TEMPERATURE = 0.7

# Embedding Settings
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# RAG Settings
MAX_RETRIEVED_CHUNKS = 5
SIMILARITY_THRESHOLD = 0.7

# Supported file formats
SUPPORTED_FORMATS = [".txt", ".docx", ".pdf"]

# Character Prompt Template
CHARACTER_PROMPT_TEMPLATE = """### SYSTEM INSTRUCTION
You are not an AI assistant. You are a fictional character from a novel. You must answer completely from the perspective of this character, using their voice, personality, and knowledge. Never break character.

### CHARACTER BIOGRAPHY
Name: {character_name}
Role: {character_role}
Personality Traits: {character_traits}

### RELEVANT MANUSCRIPT CONTEXT
Here are some relevant excerpts from the manuscript that might help you answer the user's question. You should treat these as your memories and experiences:
---
{retrieved_context}
---

### CONVERSATION HISTORY
{chat_history}

### AUTHOR'S QUESTION
{user_question}

### YOUR RESPONSE (as {character_name}):
"""

# UI Settings
STREAMLIT_CONFIG = {
    "page_title": APP_NAME,
    "page_icon": "📚",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}