"""
Character Conversation Studio - Main Streamlit Application
A tool for authors to have conversations with their fictional characters using local LLMs
"""

import streamlit as st
import os
import time
import uuid
from pathlib import Path
from typing import Optional

# Import our custom modules
from config import APP_NAME, APP_VERSION, STREAMLIT_CONFIG, SUPPORTED_FORMATS
from document_processor import DocumentProcessor
from character_manager import CharacterManager, Character
from rag_engine import RAGEngine

# Configure Streamlit page
st.set_page_config(**STREAMLIT_CONFIG)

# Initialize session state
if 'doc_processor' not in st.session_state:
    st.session_state.doc_processor = DocumentProcessor()

if 'char_manager' not in st.session_state:
    st.session_state.char_manager = CharacterManager()

if 'rag_engine' not in st.session_state:
    try:
        st.session_state.rag_engine = RAGEngine()
        st.session_state.rag_initialized = True
    except Exception as e:
        st.session_state.rag_initialized = False
        st.session_state.rag_error = str(e)

if 'current_manuscript_id' not in st.session_state:
    st.session_state.current_manuscript_id = None

if 'current_character_id' not in st.session_state:
    st.session_state.current_character_id = None

def main():
    """Main application interface"""
    
    # Header
    st.title(f"📚 {APP_NAME}")
    st.markdown(f"*Version {APP_VERSION}* - Have conversations with your fictional characters")
    
    # Check system status
    check_system_status()
    
    # Sidebar
    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Choose a page:",
            ["🏠 Home", "📖 Manuscript Manager", "👤 Character Manager", "💬 Character Chat", "⚙️ Settings"]
        )
    
    # Route to appropriate page
    if page == "🏠 Home":
        show_home_page()
    elif page == "📖 Manuscript Manager":
        show_manuscript_manager()
    elif page == "👤 Character Manager":
        show_character_manager()
    elif page == "💬 Character Chat":
        show_character_chat()
    elif page == "⚙️ Settings":
        show_settings_page()

def check_system_status():
    """Check and display system status"""
    with st.expander("🔍 System Status", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**RAG Engine**")
            if st.session_state.get('rag_initialized', False):
                st.success("✅ Initialized")
            else:
                st.error("❌ Failed to initialize")
                if 'rag_error' in st.session_state:
                    st.error(f"Error: {st.session_state.rag_error}")
        
        with col2:
            st.write("**Ollama Connection**")
            if st.session_state.get('rag_initialized', False):
                if st.session_state.rag_engine.check_ollama_connection():
                    st.success("✅ Connected")
                else:
                    st.error("❌ Disconnected")
                    st.info("Make sure Ollama is running: `ollama serve`")
            else:
                st.warning("⚠️ RAG engine not initialized")
        
        with col3:
            st.write("**Available Models**")
            if st.session_state.get('rag_initialized', False):
                models = st.session_state.rag_engine.list_available_models()
                if models:
                    st.success(f"✅ {len(models)} models")
                    with st.expander("View models"):
                        for model in models:
                            st.write(f"• {model}")
                else:
                    st.warning("⚠️ No models found")
                    st.info("Install a model: `ollama pull llama3.1:8b`")
            else:
                st.warning("⚠️ Cannot check models")

def show_home_page():
    """Display home page with instructions"""
    st.header("Welcome to Character Conversation Studio!")
    
    st.markdown("""
    This application allows you to have immersive conversations with characters from your manuscripts using local AI models.
    
    ### 🚀 Getting Started
    
    1. **📖 Import Your Manuscript** - Upload your manuscript file (TXT, DOCX, or PDF)
    2. **👤 Create Characters** - Define the characters you want to chat with
    3. **💬 Start Conversations** - Begin brainstorming sessions with your characters
    
    ### ✨ Features
    
    - **Privacy First**: Everything runs locally on your machine
    - **RAG-Powered**: Characters remember context from your manuscript
    - **Conversation History**: Persistent chat sessions with each character
    - **Multiple Formats**: Support for TXT, DOCX, and PDF files
    - **Character Profiles**: Define personality traits and roles
    
    ### 🛠️ Requirements
    
    - **Ollama**: Make sure Ollama is installed and running (`ollama serve`)
    - **Models**: Download at least one model (recommended: `ollama pull llama3.1:8b`)
    
    """)
    
    # Quick actions
    st.subheader("Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📖 Import Manuscript", use_container_width=True):
            st.switch_page("📖 Manuscript Manager")
    
    with col2:
        manuscripts = st.session_state.doc_processor.list_processed_manuscripts()
        if manuscripts and st.button("👤 Create Character", use_container_width=True):
            st.switch_page("👤 Character Manager")
        elif not manuscripts:
            st.button("👤 Create Character", disabled=True, help="Import a manuscript first", use_container_width=True)
    
    with col3:
        characters = st.session_state.char_manager.list_all_characters()
        if characters and st.button("💬 Start Chatting", use_container_width=True):
            st.switch_page("💬 Character Chat")
        elif not characters:
            st.button("💬 Start Chatting", disabled=True, help="Create a character first", use_container_width=True)

def show_manuscript_manager():
    """Display manuscript management interface"""
    st.header("📖 Manuscript Manager")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Import New Manuscript")
        
        uploaded_file = st.file_uploader(
            "Choose a manuscript file",
            type=[ext[1:] for ext in SUPPORTED_FORMATS],
            help="Supported formats: TXT, DOCX, PDF"
        )
        
        if uploaded_file is not None:
            manuscript_title = st.text_input(
                "Manuscript Title",
                value=Path(uploaded_file.name).stem
            )
            
            if st.button("📥 Process Manuscript", type="primary"):
                process_manuscript(uploaded_file, manuscript_title)
    
    with col2:
        st.subheader("Processing Info")
        st.info("""
        **What happens during processing:**
        
        1. Text extraction from your file
        2. Document chunking for RAG
        3. Embedding generation
        4. Vector database storage
        
        This may take a few minutes for large manuscripts.
        """)
    
    # List existing manuscripts
    st.subheader("Existing Manuscripts")
    manuscripts = st.session_state.doc_processor.list_processed_manuscripts()
    
    if manuscripts:
        for manuscript in manuscripts:
            with st.expander(f"📚 {manuscript.get('source_file', 'Unknown')}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Chunks**: {manuscript.get('total_chunks', 0)}")
                    st.write(f"**Words**: {manuscript.get('word_count', 0):,}")
                
                with col2:
                    st.write(f"**Characters**: {manuscript.get('total_characters', 0):,}")
                    
                    # Show associated characters
                    chars = st.session_state.char_manager.get_characters_by_manuscript(
                        manuscript['manuscript_id']
                    )
                    st.write(f"**Characters Created**: {len(chars)}")
                
                with col3:
                    if st.button(f"🗑️ Delete", key=f"del_{manuscript['manuscript_id']}"):
                        delete_manuscript(manuscript['manuscript_id'])
                        st.rerun()
    else:
        st.info("No manuscripts imported yet. Upload your first manuscript above!")

def process_manuscript(uploaded_file, title):
    """Process an uploaded manuscript"""
    try:
        with st.spinner("Processing manuscript..."):
            # Save uploaded file temporarily
            manuscript_id = str(uuid.uuid4())
            temp_file_path = f"/tmp/{manuscript_id}_{uploaded_file.name}"
            
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Process the manuscript
            result = st.session_state.doc_processor.process_manuscript(
                temp_file_path, manuscript_id
            )
            
            # Create vector database collection
            if st.session_state.rag_initialized:
                st.session_state.rag_engine.create_manuscript_collection(manuscript_id)
                st.session_state.rag_engine.add_documents_to_collection(
                    manuscript_id, result['documents']
                )
            
            # Clean up temp file
            os.unlink(temp_file_path)
            
            st.success(f"✅ Manuscript '{title}' processed successfully!")
            st.info(f"Created {result['info']['total_chunks']} chunks from {result['info']['word_count']} words")
            
            time.sleep(2)
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ Error processing manuscript: {str(e)}")

def delete_manuscript(manuscript_id):
    """Delete a manuscript and its associated data"""
    try:
        # Delete vector collection
        if st.session_state.rag_initialized:
            st.session_state.rag_engine.delete_manuscript_collection(manuscript_id)
        
        # Delete associated characters
        characters = st.session_state.char_manager.get_characters_by_manuscript(manuscript_id)
        for char in characters:
            st.session_state.char_manager.delete_character(char.character_id)
        
        # Delete manuscript info file
        from config import MANUSCRIPTS_DIR
        info_file = MANUSCRIPTS_DIR / f"{manuscript_id}_info.json"
        if info_file.exists():
            info_file.unlink()
        
        st.success("Manuscript deleted successfully!")
        
    except Exception as e:
        st.error(f"Error deleting manuscript: {str(e)}")

def show_character_manager():
    """Display character management interface"""
    st.header("👤 Character Manager")
    
    # Get available manuscripts
    manuscripts = st.session_state.doc_processor.list_processed_manuscripts()
    
    if not manuscripts:
        st.warning("⚠️ No manuscripts available. Please import a manuscript first.")
        return
    
    # Create new character section
    with st.expander("➕ Create New Character", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            manuscript_options = {m['manuscript_id']: m['source_file'] for m in manuscripts}
            selected_manuscript = st.selectbox(
                "Select Manuscript",
                options=list(manuscript_options.keys()),
                format_func=lambda x: manuscript_options[x]
            )
            
            character_name = st.text_input("Character Name", placeholder="e.g., Arion")
            character_role = st.text_input("Character Role", placeholder="e.g., Brooding knight from Eldoria")
        
        with col2:
            character_traits = st.text_area(
                "Personality Traits",
                placeholder="e.g., Proud but secretly lonely, haunted by past failures, speaks in a formal manner",
                height=100
            )
        
        if st.button("✨ Create Character", type="primary"):
            if character_name and selected_manuscript:
                character = st.session_state.char_manager.create_character(
                    name=character_name,
                    role=character_role,
                    traits=character_traits,
                    manuscript_id=selected_manuscript
                )
                st.success(f"✅ Character '{character_name}' created successfully!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Please provide at least a character name and select a manuscript.")
    
    # List existing characters
    st.subheader("Existing Characters")
    characters = st.session_state.char_manager.list_all_characters()
    
    if characters:
        for character in characters:
            manuscript_name = "Unknown Manuscript"
            for m in manuscripts:
                if m['manuscript_id'] == character.manuscript_id:
                    manuscript_name = m['source_file']
                    break
            
            with st.expander(f"👤 {character.name} - {manuscript_name}"):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**Role**: {character.role or 'Not specified'}")
                    st.write(f"**Manuscript**: {manuscript_name}")
                    
                with col2:
                    st.write(f"**Traits**: {character.traits or 'Not specified'}")
                    st.write(f"**Conversations**: {len(character.conversation_history)}")
                
                with col3:
                    if st.button(f"💬 Chat", key=f"chat_{character.character_id}"):
                        st.session_state.current_character_id = character.character_id
                        st.session_state.current_manuscript_id = character.manuscript_id
                        st.switch_page("💬 Character Chat")
                    
                    if st.button(f"🗑️ Delete", key=f"del_{character.character_id}"):
                        st.session_state.char_manager.delete_character(character.character_id)
                        st.rerun()
    else:
        st.info("No characters created yet. Create your first character above!")

def show_character_chat():
    """Display character conversation interface"""
    st.header("💬 Character Chat")
    
    # Character selection
    characters = st.session_state.char_manager.list_all_characters()
    
    if not characters:
        st.warning("⚠️ No characters available. Please create a character first.")
        return
    
    if not st.session_state.rag_initialized:
        st.error("❌ RAG engine not initialized. Check system status.")
        return
    
    # Character selector
    character_options = {char.character_id: f"{char.name}" for char in characters}
    
    selected_char_id = st.selectbox(
        "Select Character to Chat With",
        options=list(character_options.keys()),
        format_func=lambda x: character_options[x],
        index=0 if not st.session_state.current_character_id else 
              list(character_options.keys()).index(st.session_state.current_character_id) 
              if st.session_state.current_character_id in character_options else 0
    )
    
    character = st.session_state.char_manager.get_character(selected_char_id)
    if not character:
        st.error("Character not found!")
        return
    
    # Character info
    with st.expander(f"ℹ️ About {character.name}", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Role**: {character.role or 'Not specified'}")
        with col2:
            st.write(f"**Traits**: {character.traits or 'Not specified'}")
    
    # Chat interface
    st.subheader(f"Conversation with {character.name}")
    
    # Display conversation history
    if character.conversation_history:
        for turn in character.conversation_history[-10:]:  # Show last 10 turns
            with st.chat_message("user"):
                st.write(turn['user_message'])
            with st.chat_message("assistant"):
                st.write(turn['character_response'])
    
    # Chat input
    user_message = st.chat_input(f"Ask {character.name} something...")
    
    if user_message:
        # Display user message
        with st.chat_message("user"):
            st.write(user_message)
        
        # Generate character response
        with st.chat_message("assistant"):
            with st.spinner(f"{character.name} is thinking..."):
                response, context_chunks = st.session_state.rag_engine.process_character_query(
                    manuscript_id=character.manuscript_id,
                    character_name=character.name,
                    character_role=character.role,
                    character_traits=character.traits,
                    user_question=user_message,
                    conversation_history=character.get_conversation_context()
                )
            
            st.write(response)
            
            # Show retrieved context (optional)
            if context_chunks:
                with st.expander("📚 Retrieved Context", expanded=False):
                    for i, chunk in enumerate(context_chunks):
                        st.write(f"**Chunk {i+1}**: {chunk[:200]}...")
        
        # Save conversation turn
        st.session_state.char_manager.add_conversation_turn(
            character.character_id, user_message, response
        )
    
    # Chat controls
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Conversation History"):
            st.session_state.char_manager.clear_conversation_history(character.character_id)
            st.rerun()
    
    with col2:
        if st.button("🔄 Refresh Character"):
            st.rerun()

def show_settings_page():
    """Display settings and configuration"""
    st.header("⚙️ Settings")
    
    st.subheader("System Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**App Version**: {APP_VERSION}")
        st.write(f"**RAG Engine**: {'✅ Initialized' if st.session_state.rag_initialized else '❌ Failed'}")
        
    with col2:
        if st.session_state.rag_initialized:
            models = st.session_state.rag_engine.list_available_models()
            st.write(f"**Available Models**: {len(models)}")
            for model in models:
                st.write(f"• {model}")
    
    st.subheader("Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        manuscripts = st.session_state.doc_processor.list_processed_manuscripts()
        st.write(f"**Manuscripts**: {len(manuscripts)}")
        
    with col2:
        characters = st.session_state.char_manager.list_all_characters()
        st.write(f"**Characters**: {len(characters)}")
    
    if st.button("🧹 Clear All Data", type="secondary"):
        if st.confirm("This will delete all manuscripts and characters. Are you sure?"):
            clear_all_data()

def clear_all_data():
    """Clear all application data"""
    try:
        # Clear characters
        for char in st.session_state.char_manager.list_all_characters():
            st.session_state.char_manager.delete_character(char.character_id)
        
        # Clear manuscripts
        for manuscript in st.session_state.doc_processor.list_processed_manuscripts():
            delete_manuscript(manuscript['manuscript_id'])
        
        st.success("All data cleared successfully!")
        time.sleep(2)
        st.rerun()
        
    except Exception as e:
        st.error(f"Error clearing data: {str(e)}")

if __name__ == "__main__":
    main()