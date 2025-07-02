"""
RAG (Retrieval-Augmented Generation) engine for character conversations
Handles embeddings, vector storage, and context retrieval
"""

import os
import pickle
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import requests
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from langchain.schema import Document
from langchain_ollama import OllamaLLM

from config import (
    EMBEDDING_MODEL, VECTOR_DB_DIR, MAX_RETRIEVED_CHUNKS, 
    SIMILARITY_THRESHOLD, DEFAULT_LLM_MODEL, OLLAMA_BASE_URL,
    MAX_TOKENS, TEMPERATURE, CHARACTER_PROMPT_TEMPLATE
)

class RAGEngine:
    """Core RAG engine for character conversations"""
    
    def __init__(self):
        self.embedding_model = None
        self.chroma_client = None
        self.llm = None
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize embedding model, vector DB, and LLM"""
        try:
            # Initialize embedding model
            print("Loading embedding model...")
            self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
            
            # Initialize ChromaDB
            print("Initializing vector database...")
            self.chroma_client = chromadb.PersistentClient(
                path=str(VECTOR_DB_DIR),
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Initialize LLM
            print("Connecting to Ollama...")
            self.llm = OllamaLLM(
                model=DEFAULT_LLM_MODEL,
                base_url=OLLAMA_BASE_URL,
                temperature=TEMPERATURE
            )
            
            print("RAG engine initialized successfully!")
            
        except Exception as e:
            print(f"Error initializing RAG engine: {e}")
            raise
    
    def check_ollama_connection(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def check_model_availability(self, model_name: str) -> bool:
        """Check if a specific model is available in Ollama"""
        try:
            response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return any(model['name'].startswith(model_name.split(':')[0]) for model in models)
        except:
            pass
        return False
    
    def create_manuscript_collection(self, manuscript_id: str) -> bool:
        """Create a new collection for a manuscript"""
        try:
            collection_name = f"manuscript_{manuscript_id}"
            
            # Delete existing collection if it exists
            try:
                self.chroma_client.delete_collection(collection_name)
            except:
                pass
            
            # Create new collection
            self.chroma_client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            return True
        except Exception as e:
            print(f"Error creating collection: {e}")
            return False
    
    def add_documents_to_collection(self, manuscript_id: str, documents: List[Document]) -> bool:
        """Add processed documents to the vector database"""
        try:
            collection_name = f"manuscript_{manuscript_id}"
            collection = self.chroma_client.get_collection(collection_name)
            
            # Extract texts and create embeddings
            texts = [doc.page_content for doc in documents]
            embeddings = self.embedding_model.encode(texts).tolist()
            
            # Prepare metadata
            metadatas = []
            ids = []
            for i, doc in enumerate(documents):
                metadata = doc.metadata.copy()
                metadata['text_preview'] = doc.page_content[:100] + "..."
                metadatas.append(metadata)
                ids.append(f"{manuscript_id}_chunk_{i}")
            
            # Add to collection
            collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            return True
            
        except Exception as e:
            print(f"Error adding documents to collection: {e}")
            return False
    
    def retrieve_relevant_context(self, manuscript_id: str, query: str, 
                                 character_name: str = "") -> List[str]:
        """Retrieve relevant context for a query"""
        try:
            collection_name = f"manuscript_{manuscript_id}"
            collection = self.chroma_client.get_collection(collection_name)
            
            # Enhance query with character name for better retrieval
            enhanced_query = f"{query} {character_name}" if character_name else query
            
            # Create query embedding
            query_embedding = self.embedding_model.encode([enhanced_query]).tolist()
            
            # Search for similar documents
            results = collection.query(
                query_embeddings=query_embedding,
                n_results=MAX_RETRIEVED_CHUNKS,
                include=['documents', 'metadatas', 'distances']
            )
            
            relevant_chunks = []
            
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0], 
                    results['metadatas'][0], 
                    results['distances'][0]
                )):
                    # Only include chunks that meet similarity threshold
                    similarity = 1 - distance  # Convert distance to similarity
                    if similarity >= SIMILARITY_THRESHOLD:
                        relevant_chunks.append(doc)
            
            return relevant_chunks
            
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return []
    
    def generate_character_response(self, character_name: str, character_role: str,
                                   character_traits: str, user_question: str,
                                   retrieved_context: List[str], 
                                   conversation_history: str = "") -> str:
        """Generate character response using LLM"""
        try:
            # Prepare context
            context_text = "\n\n".join(retrieved_context) if retrieved_context else "No specific context available."
            
            # Format the prompt
            prompt = CHARACTER_PROMPT_TEMPLATE.format(
                character_name=character_name,
                character_role=character_role,
                character_traits=character_traits,
                retrieved_context=context_text,
                chat_history=conversation_history,
                user_question=user_question
            )
            
            # Generate response
            response = self.llm.invoke(prompt)
            
            return response.strip()
            
        except Exception as e:
            print(f"Error generating character response: {e}")
            return f"I'm sorry, I'm having trouble responding right now. Please try again. (Error: {str(e)})"
    
    def process_character_query(self, manuscript_id: str, character_name: str,
                               character_role: str, character_traits: str,
                               user_question: str, conversation_history: str = "") -> Tuple[str, List[str]]:
        """Complete pipeline: retrieve context and generate response"""
        try:
            # Retrieve relevant context
            context_chunks = self.retrieve_relevant_context(
                manuscript_id, user_question, character_name
            )
            
            # Generate character response
            response = self.generate_character_response(
                character_name, character_role, character_traits,
                user_question, context_chunks, conversation_history
            )
            
            return response, context_chunks
            
        except Exception as e:
            print(f"Error processing character query: {e}")
            return f"I apologize, but I'm having trouble right now. Please try again. (Error: {str(e)})", []
    
    def get_collection_info(self, manuscript_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a manuscript's vector collection"""
        try:
            collection_name = f"manuscript_{manuscript_id}"
            collection = self.chroma_client.get_collection(collection_name)
            count = collection.count()
            
            return {
                'collection_name': collection_name,
                'document_count': count,
                'embedding_model': EMBEDDING_MODEL
            }
        except Exception as e:
            print(f"Error getting collection info: {e}")
            return None
    
    def delete_manuscript_collection(self, manuscript_id: str) -> bool:
        """Delete a manuscript's vector collection"""
        try:
            collection_name = f"manuscript_{manuscript_id}"
            self.chroma_client.delete_collection(collection_name)
            return True
        except Exception as e:
            print(f"Error deleting collection: {e}")
            return False
    
    def list_available_models(self) -> List[str]:
        """List available models in Ollama"""
        try:
            response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [model['name'] for model in models]
        except:
            pass
        return []
    
    def switch_model(self, model_name: str) -> bool:
        """Switch to a different LLM model"""
        try:
            self.llm = OllamaLLM(
                model=model_name,
                base_url=OLLAMA_BASE_URL,
                temperature=TEMPERATURE
            )
            return True
        except Exception as e:
            print(f"Error switching model: {e}")
            return False