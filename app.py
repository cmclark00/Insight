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

# AUTOMATICALLY EXTRACT CHARACTERS FROM EXISTING MANUSCRIPTS ON STARTUP
if 'auto_extracted_characters' not in st.session_state:
    st.session_state.auto_extracted_characters = []
    
    # Check for existing manuscripts and extract characters
    try:
        manuscripts = st.session_state.doc_processor.list_processed_manuscripts()
        if manuscripts:
            # Use the first available manuscript for character extraction
            manuscript = manuscripts[0]
            manuscript_id = manuscript.get('manuscript_id', 'startup_extraction')
            
            # Try to get the text from the example manuscript
            example_file = Path("example_manuscript.txt")
            if example_file.exists():
                with open(example_file, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                # Extract characters using the character extractor
                if hasattr(st.session_state.doc_processor, 'character_extractor') and st.session_state.doc_processor.character_extractor:
                    extracted_chars = st.session_state.doc_processor.character_extractor.extract_characters_from_text(text, manuscript_id)
                    st.session_state.auto_extracted_characters = extracted_chars
                    print(f"✅ Stored {len(extracted_chars)} auto-extracted characters in session state")
    except Exception as e:
        print(f"⚠️ Auto-extraction during startup failed: {e}")
        st.session_state.auto_extracted_characters = []

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
            st.info("📖 Please use the sidebar to navigate to 'Manuscript Manager'")
    
    with col2:
        manuscripts = st.session_state.doc_processor.list_processed_manuscripts()
        if manuscripts and st.button("👤 Create Character", use_container_width=True):
            st.info("👤 Please use the sidebar to navigate to 'Character Manager'")
        elif not manuscripts:
            st.button("👤 Create Character", disabled=True, help="Import a manuscript first", use_container_width=True)
    
    with col3:
        characters = st.session_state.char_manager.list_all_characters()
        if characters and st.button("💬 Start Chatting", use_container_width=True):
            st.info("💬 Please use the sidebar to navigate to 'Character Chat'")
        elif not characters:
            st.button("💬 Start Chatting", disabled=True, help="Create a character first", use_container_width=True)

def show_manuscript_manager():
    """Show manuscript management interface with character extraction testing"""
    st.header("📚 Manuscript Manager")
    
    # BASIC BUTTON TEST - Add this at the very top
    st.error("🧪 BASIC BUTTON TEST")
    if st.button("🔥 CLICK ME TO TEST BUTTONS", key="basic_button_test"):
        st.balloons()
        st.success("✅ BASIC BUTTONS WORK!")
        st.session_state["basic_test_clicked"] = True
    
    if st.session_state.get("basic_test_clicked", False):
        st.success("🎉 Basic test button was clicked before!")
    
    st.write("---")  # Separator
    
    # Debug session state
    with st.expander("🔍 Debug: Session State Contents", expanded=False):
        st.write(f"**auto_extracted_characters length**: {len(st.session_state.get('auto_extracted_characters', []))}")
        st.write(f"**auto_extracted_characters type**: {type(st.session_state.get('auto_extracted_characters', []))}")
        if st.session_state.get('auto_extracted_characters'):
            st.write("**First character sample**:")
            st.json(st.session_state.auto_extracted_characters[0])
    
    # Show automatically extracted characters from startup
    if st.session_state.auto_extracted_characters:
        st.subheader("🤖 Automatically Extracted Characters")
        st.info(f"Found {len(st.session_state.auto_extracted_characters)} characters from your manuscript:")
        
        for char_data in st.session_state.auto_extracted_characters:
            with st.expander(f"👤 {char_data['name']} (Confidence: {char_data.get('extraction_confidence', 0.5):.1%})"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Role**: {char_data.get('role', 'Not specified')}")
                    st.write(f"**Traits**: {char_data.get('traits', 'Not specified')}")
                    if char_data.get('description'):
                        st.write(f"**Description**: {char_data['description']}")
                
                with col2:
                    # Check if already imported
                    char_imported = st.session_state.get(f"imported_{char_data['name']}", False)
                    
                    if char_imported:
                        st.success("✅ Imported!")
                        if st.button(f"🔄 Re-import", key=f"reimport_{char_data['name']}"):
                            del st.session_state[f"imported_{char_data['name']}"]
                            st.rerun()
                    else:
                        if st.button(f"📥 Import {char_data['name']}", key=f"import_{char_data['name']}_auto"):
                            try:
                                # Create character using character manager - pass individual parameters
                                character = st.session_state.char_manager.create_character(
                                    name=char_data['name'],
                                    role=char_data.get('role', 'Character from manuscript'),
                                    traits=char_data.get('traits', 'Extracted character'),
                                    manuscript_id=char_data.get('manuscript_id', 'auto_extracted')
                                )
                                
                                # Character creation returns the character object
                                result = character
                                
                                if result:
                                    # Mark as imported
                                    st.session_state[f"imported_{char_data['name']}"] = True
                                    st.success(f"✅ Successfully imported {char_data['name']}!")
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to import {char_data['name']}")
                                
                            except Exception as e:
                                st.error(f"❌ Failed to import {char_data['name']}: {str(e)}")
        
        st.write("---")
    
    elif not st.session_state.auto_extracted_characters:
        st.info("No characters have been automatically extracted yet.")
        
        # Fallback: Button to load demo characters for testing
        if st.button("🧪 Load Demo Characters for Testing", key="load_demo_chars"):
            demo_chars = [
                {"name": "Justin", "role": "Information Security guy", "traits": "Cautious, detail-oriented", "extraction_confidence": 0.9, "manuscript_id": "demo"},
                {"name": "Wilson", "role": "Director of Operations", "traits": "Leadership, concerned", "extraction_confidence": 0.9, "manuscript_id": "demo"},
                {"name": "Alex", "role": "Informant", "traits": "Secretive, helpful", "extraction_confidence": 0.8, "manuscript_id": "demo"}
            ]
            st.session_state.auto_extracted_characters = demo_chars
            st.success("✅ Demo characters loaded!")
            st.rerun()
    
    # File upload section
    st.subheader("📤 Upload New Manuscript")
    uploaded_file = st.file_uploader(
        "Choose a text file",
        type=['txt', 'pdf', 'docx'],
        help="Upload your manuscript file for character extraction"
    )
    
    if uploaded_file is not None:
        manuscript_title = st.text_input(
            "Manuscript Title",
            value=Path(uploaded_file.name).stem
        )
        
        if st.button("📥 Process Manuscript", type="primary"):
            process_manuscript(uploaded_file, manuscript_title)
    
    # Processing info section
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
    
    # Debug: Show what manuscripts exist and if they have characters
    st.write("**Debug - Existing Manuscripts:**")
    for manuscript in manuscripts:
        st.write(f"- {manuscript.get('source_file', 'Unknown')}: ID {manuscript.get('manuscript_id', 'No ID')}")
        # Check if this manuscript has any extracted characters stored
        manuscript_id = manuscript.get('manuscript_id')
        if manuscript_id:
            # Check if characters were created for this manuscript
            chars_for_manuscript = st.session_state.char_manager.get_characters_by_manuscript(manuscript_id)
            st.write(f"  Characters created: {len(chars_for_manuscript)}")
            if chars_for_manuscript:
                for char in chars_for_manuscript:
                    st.write(f"    - {char.name}")
            
            if st.button(f"🔄 Re-process {manuscript.get('source_file', 'Unknown')}", key=f"reprocess_{manuscript.get('manuscript_id')}"):
                st.info("Re-processing manuscript to show character extraction...")
                
                # Create demo characters for testing the import workflow
                fake_characters = [
                    {"name": "Justin", "role": "Information Security guy", "traits": "Cautious, detail-oriented", "extraction_confidence": 0.9},
                    {"name": "Wilson", "role": "Director of Operations", "traits": "Leadership, concerned", "extraction_confidence": 0.9},
                    {"name": "Alex", "role": "Informant", "traits": "Secretive, helpful", "extraction_confidence": 0.8}
                ]
                
                st.write(f"**Debug - Simulated Extraction Result:**")
                st.write(f"- Extracted characters count: {len(fake_characters)}")
                
                # Debug: Check if this section is reached
                st.error("🔥 DEBUG: Re-process button was clicked! This should show demo characters below.")
                
                # Show import buttons
                st.subheader("🤖 Automatically Detected Characters")
                for char_data in fake_characters:
                    with st.expander(f"👤 {char_data['name']} (Confidence: {char_data.get('extraction_confidence', 0.5):.1%})"):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(f"**Role**: {char_data.get('role', 'Not specified')}")
                            st.write(f"**Traits**: {char_data.get('traits', 'Not specified')}")
                        
                        with col2:
                            # Debug: Check if this section is reached
                            st.error(f"🔥 DEBUG: Showing import button for {char_data['name']}")
                            
                            # Use a completely unique key approach
                            button_key = f"test_import_btn_{char_data['name']}_demo_unique"
                            
                            # Show current state before button
                            current_state = st.session_state.get(f"test_clicked_{char_data['name']}", "Not clicked yet")
                            st.write(f"**Button state**: {current_state}")
                            
                            # Try a different button approach
                            if st.button(f"🧪 Test Import {char_data['name']}", key=button_key):
                                st.session_state[f"test_clicked_{char_data['name']}"] = "CLICKED!"
                                st.balloons()
                                st.success(f"✅ SUCCESS! Button click registered for {char_data['name']}")
                                
                            # Show if the button was ever clicked
                            if st.session_state.get(f"test_clicked_{char_data['name']}") == "CLICKED!":
                                st.success(f"🎉 {char_data['name']} button WAS clicked before!")
                                
                            # Reset button for testing
                            if st.button(f"🔄 Reset {char_data['name']}", key=f"reset_{char_data['name']}_demo"):
                                if f"test_clicked_{char_data['name']}" in st.session_state:
                                    del st.session_state[f"test_clicked_{char_data['name']}"]
                                st.rerun()
            
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
            
            # Display automatically extracted characters
            extracted_characters = result.get('extracted_characters', [])
            
            # IMPORTANT: Store extracted characters in session state for later access
            if extracted_characters:
                st.session_state.auto_extracted_characters = extracted_characters
                print(f"✅ Stored {len(extracted_characters)} extracted characters in session state")
            
            # Debug: Show what we got from the processor
            st.write("**Debug - Extraction Result:**")
            st.write(f"- Result keys: {list(result.keys())}")
            st.write(f"- Extracted characters count: {len(extracted_characters)}")
            st.write(f"- Extracted characters type: {type(extracted_characters)}")
            if extracted_characters:
                st.write("- First character:", extracted_characters[0] if extracted_characters else "None")
            
            if extracted_characters:
                st.subheader("🤖 Automatically Detected Characters")
                st.info(f"Found {len(extracted_characters)} characters in your manuscript. Review and import the ones you'd like to chat with:")
                
                for char_data in extracted_characters:
                    with st.expander(f"👤 {char_data['name']} (Confidence: {char_data.get('extraction_confidence', 0.5):.1%})"):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(f"**Role**: {char_data.get('role', 'Not specified')}")
                            st.write(f"**Traits**: {char_data.get('traits', 'Not specified')}")
                            if char_data.get('description'):
                                st.write(f"**Description**: {char_data['description']}")
                            if char_data.get('relationships'):
                                st.write(f"**Relationships**: {', '.join(char_data['relationships'])}")
                            if char_data.get('key_quotes'):
                                st.write("**Key Quotes**:")
                                for quote in char_data['key_quotes'][:3]:  # Show first 3 quotes
                                    st.write(f"• \"{quote}\"")
                        
                        with col2:
                            if st.button(f"✅ Import {char_data['name']}", key=f"import_{char_data['name']}"):
                                try:
                                    st.info(f"🔄 Creating character {char_data['name']}...")
                                    
                                    # Debug: Show what we're trying to create
                                    st.write(f"**Debug - Creating character with:**")
                                    st.write(f"- Name: {char_data['name']}")
                                    st.write(f"- Role: {char_data.get('role', '')}")
                                    st.write(f"- Traits: {char_data.get('traits', '')}")
                                    st.write(f"- Manuscript ID: {manuscript_id}")
                                    
                                    # Create character in the system
                                    character = st.session_state.char_manager.create_character(
                                        name=char_data['name'],
                                        role=char_data.get('role', ''),
                                        traits=char_data.get('traits', ''),
                                        manuscript_id=manuscript_id
                                    )
                                    
                                    st.write(f"**Debug - Character object created:**")
                                    st.write(f"- Character ID: {character.character_id}")
                                    st.write(f"- Name: {character.name}")
                                    
                                    # Check if file was actually created
                                    from config import CHARACTERS_DIR
                                    char_file = CHARACTERS_DIR / f"{character.character_id}.json"
                                    st.write(f"**Debug - File creation:**")
                                    st.write(f"- Expected file: {char_file}")
                                    st.write(f"- File exists: {char_file.exists()}")
                                    
                                    if char_file.exists():
                                        st.write(f"- File size: {char_file.stat().st_size} bytes")
                                    
                                    # Force reload all characters to ensure UI is updated
                                    st.session_state.char_manager.load_all_characters()
                                    
                                    # Check characters in manager
                                    all_chars = st.session_state.char_manager.list_all_characters()
                                    st.write(f"**Debug - Characters in manager after creation: {len(all_chars)}**")
                                    for char in all_chars:
                                        st.write(f"  - {char.name}")
                                    
                                    st.success(f"✅ Imported {char_data['name']}! Character ID: {character.character_id}")
                                    time.sleep(3)  # Give more time to read debug info
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Failed to import {char_data['name']}: {str(e)}")
                                    st.write(f"**Full error details:**")
                                    import traceback
                                    st.code(traceback.format_exc())
                                    print(f"Character import error: {e}")  # Debug logging
                
                # Filter out low-quality characters for bulk import
                quality_characters = [char for char in extracted_characters 
                                    if char.get('extraction_confidence', 0) > 0.5 and 
                                       char.get('role') and char.get('traits')]
                
                # Bulk import option
                col1_bulk, col2_bulk = st.columns(2)
                with col1_bulk:
                    if st.button("📥 Import All High-Quality Characters", type="secondary"):
                        imported_count = 0
                        failed_count = 0
                        for char_data in quality_characters:
                            try:
                                character = st.session_state.char_manager.create_character(
                                    name=char_data['name'],
                                    role=char_data.get('role', ''),
                                    traits=char_data.get('traits', ''),
                                    manuscript_id=manuscript_id
                                )
                                imported_count += 1
                            except Exception as e:
                                print(f"Error importing {char_data['name']}: {e}")
                                failed_count += 1
                        
                        # Force reload all characters to ensure UI is updated
                        st.session_state.char_manager.load_all_characters()
                        
                        if imported_count > 0:
                            st.success(f"✅ Imported {imported_count} characters!")
                        if failed_count > 0:
                            st.warning(f"⚠️ Failed to import {failed_count} characters")
                        time.sleep(2)
                        st.rerun()
                
                with col2_bulk:
                    if len(quality_characters) != len(extracted_characters):
                        st.info(f"💡 Bulk import will include {len(quality_characters)} of {len(extracted_characters)} characters (high-quality only)")
            else:
                if hasattr(st.session_state.doc_processor, 'character_extractor') and st.session_state.doc_processor.character_extractor:
                    st.info("🔍 No characters were automatically detected in this manuscript. You can still create characters manually in the Character Manager.")
            
            time.sleep(3)
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

def show_auto_extracted_characters(manuscripts):
    """Show characters that were automatically extracted from manuscripts"""
    # Check if we have auto-extracted characters in session state
    auto_extracted = st.session_state.get('auto_extracted_characters', [])
    
    if auto_extracted:
        st.success(f"🎯 Found {len(auto_extracted)} automatically extracted characters from your manuscript!")
        
        # Create import section
        with st.expander("📋 Review and Import Auto-Extracted Characters", expanded=True):
            st.write("Review the characters that were automatically detected from your manuscript and import the ones you want to use:")
            
            # Show each extracted character
            import_selections = {}
            for i, char_data in enumerate(auto_extracted):
                col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
                
                with col1:
                    # Import checkbox
                    import_key = f"import_char_{i}"
                    import_selections[i] = st.checkbox("Import", key=import_key, value=True)
                
                with col2:
                    st.write(f"**{char_data.get('name', 'Unknown')}**")
                    role_text = char_data.get('role', 'Not specified')
                    gender_text = char_data.get('gender', 'unknown')
                    if gender_text != 'unknown':
                        st.write(f"Role: {role_text} ({gender_text})")
                    else:
                        st.write(f"Role: {role_text}")
                
                with col3:
                    confidence = char_data.get('confidence', 0)
                    st.write(f"Confidence: {confidence:.1%}")
                    traits = char_data.get('traits', 'No traits specified')
                    if len(traits) > 80:
                        traits = traits[:80] + "..."
                    st.write(f"Traits: {traits}")
                
                with col4:
                    # Show preview button
                    if st.button("👁️", key=f"preview_{i}", help="Preview character details"):
                        st.session_state[f"show_preview_{i}"] = not st.session_state.get(f"show_preview_{i}", False)
                
                # Show detailed preview if requested
                if st.session_state.get(f"show_preview_{i}", False):
                    with st.container():
                        st.markdown("**Full Character Details:**")
                        st.write(f"**Name:** {char_data.get('name', 'Unknown')}")
                        st.write(f"**Role:** {char_data.get('role', 'Not specified')}")
                        st.write(f"**Gender:** {char_data.get('gender', 'unknown')}")
                        st.write(f"**Traits:** {char_data.get('traits', 'No traits specified')}")
                        st.write(f"**Confidence:** {char_data.get('confidence', 0):.1%}")
                        st.write(f"**Manuscript ID:** {char_data.get('manuscript_id', 'Unknown')}")
                
                st.divider()
            
            # Import selected characters button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("✅ Import Selected Characters", type="primary", use_container_width=True):
                    imported_count = 0
                    for i, char_data in enumerate(auto_extracted):
                        if import_selections.get(i, False):
                            try:
                                # Create character using character manager
                                character = st.session_state.char_manager.create_character(
                                    name=char_data.get('name', 'Unknown'),
                                    role=char_data.get('role', ''),
                                    traits=char_data.get('traits', ''),
                                    manuscript_id=char_data.get('manuscript_id', manuscripts[0]['manuscript_id'] if manuscripts else None)
                                )
                                
                                # Add extraction metadata
                                if hasattr(character, 'extraction_confidence'):
                                    character.extraction_confidence = char_data.get('confidence', 0)
                                
                                imported_count += 1
                            except Exception as e:
                                st.error(f"Failed to import {char_data.get('name', 'Unknown')}: {str(e)}")
                    
                    if imported_count > 0:
                        st.success(f"✅ Successfully imported {imported_count} characters!")
                        # Clear the auto-extracted characters since they've been imported
                        st.session_state.auto_extracted_characters = []
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.warning("No characters were selected for import.")
    else:
        st.info("🔍 Upload a new manuscript to see automatically extracted characters here. Existing characters are shown below.")

def show_character_manager():
    """Display character management interface"""
    st.header("👤 Character Manager")
    
    # Debug info - remove this later
    with st.expander("🔍 Debug Info", expanded=False):
        st.write(f"**Session State Character Manager**: {type(st.session_state.char_manager)}")
        st.write(f"**Characters in memory**: {len(st.session_state.char_manager.characters)}")
        st.write(f"**Characters loaded**: {len(st.session_state.char_manager.list_all_characters())}")
        
        from config import CHARACTERS_DIR
        char_files = list(CHARACTERS_DIR.glob("*.json"))
        st.write(f"**Character files on disk**: {len(char_files)}")
        for char_file in char_files:
            st.write(f"   - {char_file.name}")
        
        if st.button("🔄 Force Reload Characters"):
            st.session_state.char_manager.load_all_characters()
            st.rerun()
    
    # Get available manuscripts
    manuscripts = st.session_state.doc_processor.list_processed_manuscripts()
    
    if not manuscripts:
        st.warning("⚠️ No manuscripts available. Please import a manuscript first.")
        return
    
    # Show tip about automatic character extraction
    st.info("💡 **Tip**: Characters are automatically extracted when you upload a manuscript! Check the 'Automatically Extracted Characters' section below.")
    
    # Create new character section
    with st.expander("➕ Create New Character Manually", expanded=False):
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
    
    # Show automatically extracted characters for review
    st.subheader("🤖 Automatically Extracted Characters")
    show_auto_extracted_characters(manuscripts)
    
    # Force reload characters to make sure we have the latest
    st.session_state.char_manager.load_all_characters()
    
    # List existing characters
    st.subheader("📚 Your Characters")
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
                    # Show if character was auto-extracted (check for extraction_confidence attribute)
                    if hasattr(character, 'extraction_confidence'):
                        st.write(f"**Auto-extracted**: ✅ ({character.extraction_confidence:.1%} confidence)")
                
                with col3:
                    if st.button(f"💬 Chat", key=f"chat_{character.character_id}"):
                        st.session_state.current_character_id = character.character_id
                        st.session_state.current_manuscript_id = character.manuscript_id
                        st.info("💬 Please use the sidebar to navigate to 'Character Chat'")
                    
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