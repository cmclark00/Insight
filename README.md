# 📚 Character Conversation Studio

A powerful local application that allows authors and writers to have immersive conversations with characters from their manuscripts using state-of-the-art local Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG).

## ✨ Features

- **💬 Character Conversations**: Chat with your fictional characters as if they were real people
- **🧠 RAG-Powered Memory**: Characters remember context from your entire manuscript
- **🔒 Privacy First**: Everything runs locally - your manuscripts never leave your machine
- **📖 Multi-Format Support**: Import TXT, DOCX, and PDF manuscripts
- **👤 Character Profiles**: Define detailed personality traits and roles
- **💾 Persistent Conversations**: Chat history is saved and maintained
- **🎯 Context-Aware Responses**: Characters respond based on relevant manuscript content
- **🔄 Real-Time Processing**: Fast embedding generation and similarity search

## 🏗️ Architecture

This application implements a sophisticated RAG (Retrieval-Augmented Generation) pipeline:

1. **Document Ingestion**: Manuscripts are processed and chunked into manageable pieces
2. **Embedding Generation**: Text chunks are converted to vector embeddings using sentence transformers
3. **Vector Storage**: Embeddings are stored in ChromaDB for fast similarity search
4. **Context Retrieval**: When you ask a character a question, relevant manuscript chunks are retrieved
5. **Response Generation**: Local LLM generates character responses using retrieved context and character profiles

## 🛠️ Prerequisites

### 1. Install Ollama

**macOS/Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
Download from [ollama.ai](https://ollama.ai/download/windows)

### 2. Start Ollama Server
```bash
ollama serve
```

### 3. Install a Language Model
```bash
# Recommended model for character conversations
ollama pull llama3.1:8b

# Alternative models you can try:
ollama pull mistral:7b
ollama pull gemma2:9b
```

## 🚀 Installation

### Quick Installation (Recommended)

1. **Clone or download this repository**
```bash
git clone <repository-url>
cd character-conversation-studio
```

2. **Run the installation script**
```bash
./install.sh
```

3. **Run the application**
```bash
./run_venv.sh
```

### Manual Installation

1. **Clone or download this repository**
```bash
git clone <repository-url>
cd character-conversation-studio
```

2. **Create a virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the application**
```bash
streamlit run app.py
```

5. **Open your browser** to `http://localhost:8501`

## 📋 Usage Guide

### Step 1: Import Your Manuscript
1. Navigate to "📖 Manuscript Manager"
2. Upload your manuscript file (TXT, DOCX, or PDF)
3. Give it a title and click "📥 Process Manuscript"
4. Wait for processing to complete (this creates embeddings and stores them in the vector database)

### Step 2: Create Characters
1. Go to "👤 Character Manager"
2. Click "➕ Create New Character"
3. Fill in character details:
   - **Name**: Your character's name
   - **Role**: Their role in the story (e.g., "Brooding knight from Eldoria")
   - **Traits**: Personality traits (e.g., "Proud but secretly lonely, speaks formally")
4. Click "✨ Create Character"

### Step 3: Start Conversations
1. Navigate to "💬 Character Chat"
2. Select your character from the dropdown
3. Start typing questions or prompts
4. Enjoy natural conversations with your character!

## 💡 Example Interactions

**You**: "Arion, how did you feel when you discovered the truth about your father?"

**Arion**: "The revelation struck me like a blade to the heart, dear author. For years, I had carried the weight of believing him a coward who fled from battle. To learn that he died protecting our village... it changed everything. The anger I harbored turned to shame, and the shame to a fierce determination to honor his memory."

**You**: "What drives you to continue your quest despite the dangers?"

**Arion**: "The faces of those who depend on me, the memory of my father's sacrifice, and perhaps... perhaps the hope that I might finally prove myself worthy of the name I bear. Each step forward is both burden and blessing."

## 🔧 Configuration

### Model Settings
You can modify the LLM settings in `config.py`:
- `DEFAULT_LLM_MODEL`: Change the Ollama model used
- `TEMPERATURE`: Adjust response creativity (0.0-1.0)
- `MAX_TOKENS`: Maximum response length

### RAG Settings
- `CHUNK_SIZE`: Size of text chunks for processing
- `MAX_RETRIEVED_CHUNKS`: Number of relevant chunks to retrieve
- `SIMILARITY_THRESHOLD`: Minimum similarity for chunk relevance

## 📁 Project Structure

```
character-conversation-studio/
├── app.py                 # Main Streamlit application
├── config.py             # Configuration settings
├── document_processor.py # Manuscript processing and text extraction
├── character_manager.py  # Character profiles and conversation management
├── rag_engine.py         # Core RAG implementation
├── requirements.txt      # Python dependencies
├── README.md            # This file
└── data/                # Created automatically
    ├── manuscripts/     # Processed manuscript info
    ├── characters/      # Character profiles and chat history
    └── vector_db/       # ChromaDB vector storage
```

## 🔍 Troubleshooting

### "RAG engine not initialized"
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check that Ollama is running: `ollama serve`

### "No models found"
- Install at least one model: `ollama pull llama3.1:8b`
- Verify installation: `ollama list`

### "Ollama connection failed"
- Make sure Ollama server is running on port 11434
- Check firewall settings if necessary

### Slow responses
- Try a smaller model like `mistral:7b`
- Reduce `MAX_RETRIEVED_CHUNKS` in config.py
- Ensure you have adequate RAM/VRAM

## 🎨 Customization

### Custom Prompt Templates
Modify the `CHARACTER_PROMPT_TEMPLATE` in `config.py` to change how characters respond:

```python
CHARACTER_PROMPT_TEMPLATE = """
Your custom prompt here...
Character: {character_name}
Context: {retrieved_context}
Question: {user_question}
"""
```

### Adding New File Formats
Extend `document_processor.py` to support additional file formats by adding new extraction methods.

## 🚧 Known Limitations

- Character responses depend on the quality of the local LLM
- Very large manuscripts (>100MB) may take significant time to process
- Character consistency may vary based on the model used
- Requires substantial RAM for larger models (8GB+ recommended)

## 🔮 Future Enhancements

- **Character Voice Training**: Fine-tune models on specific character dialogue
- **Multi-Character Conversations**: Support group conversations between characters
- **Export Options**: Export conversations as scripts or dialogue files
- **Advanced Character Analysis**: Automatic character trait extraction from manuscripts
- **Cloud Sync**: Optional cloud backup for character profiles

## 🤝 Contributing

This is an open-source project. Contributions are welcome! Please feel free to:
- Report bugs and issues
- Suggest new features
- Submit pull requests
- Improve documentation

## 📄 License

This project is released under the MIT License. See LICENSE file for details.

## 🙏 Acknowledgments

- **Ollama** - For making local LLM deployment accessible
- **LangChain** - For RAG framework and document processing
- **ChromaDB** - For efficient vector storage
- **Streamlit** - For the beautiful web interface
- **Sentence Transformers** - For high-quality embeddings

---

**Happy writing! May your characters come alive through conversation.** 📚✨