"""
Document processing utilities for manuscript ingestion and text extraction
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any
import docx
import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from config import CHUNK_SIZE, CHUNK_OVERLAP, MANUSCRIPTS_DIR, SUPPORTED_FORMATS

# Import character extraction functionality
try:
    from character_extractor import CharacterExtractor
    CHARACTER_EXTRACTION_AVAILABLE = True
except ImportError:
    CHARACTER_EXTRACTION_AVAILABLE = False
    print("⚠️ Character extraction dependencies not available. Please install: pip install spacy textblob nltk")

class DocumentProcessor:
    """Handles manuscript ingestion and processing for RAG"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        # Initialize character extractor if available
        self.character_extractor = CharacterExtractor() if CHARACTER_EXTRACTION_AVAILABLE else None
    
    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from various file formats"""
        path_obj = Path(file_path)
        extension = path_obj.suffix.lower()
        
        if extension == '.txt':
            return self._extract_from_txt(path_obj)
        elif extension == '.docx':
            return self._extract_from_docx(path_obj)
        elif extension == '.pdf':
            return self._extract_from_pdf(path_obj)
        else:
            raise ValueError(f"Unsupported file format: {extension}")
    
    def _extract_from_txt(self, file_path: Path) -> str:
        """Extract text from .txt file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try different encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            raise ValueError(f"Could not decode file: {file_path}")
    
    def _extract_from_docx(self, file_path: Path) -> str:
        """Extract text from .docx file"""
        doc = docx.Document(str(file_path))
        text = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text.append(paragraph.text)
        return '\n\n'.join(text)
    
    def _extract_from_pdf(self, file_path: Path) -> str:
        """Extract text from .pdf file"""
        text = []
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text.strip():
                    text.append(page_text)
        return '\n\n'.join(text)
    
    def process_manuscript(self, file_path: str, manuscript_id: str) -> Dict[str, Any]:
        """Process a manuscript file and prepare it for RAG"""
        try:
            # Extract text
            text = self.extract_text_from_file(file_path)
            
            # Split into chunks
            documents = self.text_splitter.create_documents([text])
            
            # Add metadata to chunks
            for i, doc in enumerate(documents):
                doc.metadata = {
                    'manuscript_id': manuscript_id,
                    'chunk_id': i,
                    'source_file': Path(file_path).name
                }
            
            # Save processed manuscript info
            manuscript_info = {
                'manuscript_id': manuscript_id,
                'source_file': Path(file_path).name,
                'total_chunks': len(documents),
                'total_characters': len(text),
                'word_count': len(text.split())
            }
            
            self._save_manuscript_info(manuscript_id, manuscript_info)
            
            # Extract characters automatically if character extraction is available
            extracted_characters = []
            if self.character_extractor:
                try:
                    print("🤖 Extracting characters automatically...")
                    extracted_characters = self.character_extractor.extract_characters_from_text(text, manuscript_id)
                    print(f"✅ Extracted {len(extracted_characters)} characters")
                    # Show what was extracted
                    for char in extracted_characters:
                        print(f"   - {char['name']}: {char.get('role', 'No role')} (confidence: {char.get('extraction_confidence', 0.5):.1%})")
                except Exception as e:
                    print(f"⚠️ Character extraction failed: {e}")
                    # If extraction fails completely, ensure we still return empty list
                    extracted_characters = []
            
            return {
                'documents': documents,
                'info': manuscript_info,
                'text': text,
                'extracted_characters': extracted_characters
            }
            
        except Exception as e:
            raise Exception(f"Error processing manuscript: {str(e)}")
    
    def _save_manuscript_info(self, manuscript_id: str, info: Dict[str, Any]):
        """Save manuscript information to file"""
        info_path = MANUSCRIPTS_DIR / f"{manuscript_id}_info.json"
        with open(info_path, 'w') as f:
            json.dump(info, f, indent=2)
    
    def get_manuscript_info(self, manuscript_id: str) -> Dict[str, Any]:
        """Get saved manuscript information"""
        info_path = MANUSCRIPTS_DIR / f"{manuscript_id}_info.json"
        if info_path.exists():
            with open(info_path, 'r') as f:
                return json.load(f)
        return {}
    
    def list_processed_manuscripts(self) -> List[Dict[str, Any]]:
        """List all processed manuscripts"""
        manuscripts = []
        for info_file in MANUSCRIPTS_DIR.glob("*_info.json"):
            try:
                with open(info_file, 'r') as f:
                    manuscripts.append(json.load(f))
            except Exception:
                continue
        return manuscripts
    
    def extract_character_mentions(self, text: str, character_names: List[str]) -> Dict[str, List[str]]:
        """Extract passages mentioning specific characters"""
        mentions = {name: [] for name in character_names}
        
        # Split text into sentences for better context
        sentences = text.split('.')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            for name in character_names:
                if name.lower() in sentence.lower():
                    # Get some context around the mention
                    mentions[name].append(sentence)
        
        return mentions
    
    def create_character_summary(self, text: str, character_name: str) -> str:
        """Create a summary of character information from the text"""
        # This is a simple implementation - could be enhanced with NLP
        sentences = text.split('.')
        character_sentences = []
        
        for sentence in sentences:
            if character_name.lower() in sentence.lower():
                character_sentences.append(sentence.strip())
        
        return '. '.join(character_sentences[:10])  # First 10 mentions