"""
Character management system for storing and retrieving character profiles and conversations
"""

import json
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from config import CHARACTERS_DIR

class Character:
    """Represents a character from a manuscript"""
    
    def __init__(self, name: str, role: str = "", traits: str = "", 
                 manuscript_id: str = "", character_id: Optional[str] = None):
        self.character_id = character_id or str(uuid.uuid4())
        self.name = name
        self.role = role
        self.traits = traits
        self.manuscript_id = manuscript_id
        self.created_at = datetime.now().isoformat()
        self.conversation_history: List[Dict[str, Any]] = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert character to dictionary for storage"""
        return {
            'character_id': self.character_id,
            'name': self.name,
            'role': self.role,
            'traits': self.traits,
            'manuscript_id': self.manuscript_id,
            'created_at': self.created_at,
            'conversation_history': self.conversation_history
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Character':
        """Create character from dictionary"""
        character = cls(
            name=data['name'],
            role=data.get('role', ''),
            traits=data.get('traits', ''),
            manuscript_id=data.get('manuscript_id', ''),
            character_id=data['character_id']
        )
        character.created_at = data.get('created_at', datetime.now().isoformat())
        character.conversation_history = data.get('conversation_history', [])
        return character
    
    def add_conversation_turn(self, user_message: str, character_response: str):
        """Add a conversation turn to the history"""
        turn = {
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message,
            'character_response': character_response
        }
        self.conversation_history.append(turn)
        
        # Keep only last 20 turns to prevent memory issues
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    def get_conversation_context(self, last_n_turns: int = 5) -> str:
        """Get recent conversation history as formatted string"""
        if not self.conversation_history:
            return "No previous conversation."
        
        recent_turns = self.conversation_history[-last_n_turns:]
        context_lines = []
        
        for turn in recent_turns:
            context_lines.append(f"Author: {turn['user_message']}")
            context_lines.append(f"{self.name}: {turn['character_response']}")
        
        return "\n".join(context_lines)

class CharacterManager:
    """Manages character profiles and conversations"""
    
    def __init__(self):
        self.characters: Dict[str, Character] = {}
        self.load_all_characters()
    
    def create_character(self, name: str, role: str = "", traits: str = "", 
                        manuscript_id: str = "") -> Character:
        """Create a new character"""
        character = Character(name, role, traits, manuscript_id)
        self.characters[character.character_id] = character
        self.save_character(character)
        return character
    
    def save_character(self, character: Character):
        """Save character to file"""
        file_path = CHARACTERS_DIR / f"{character.character_id}.json"
        with open(file_path, 'w') as f:
            json.dump(character.to_dict(), f, indent=2)
    
    def load_character(self, character_id: str) -> Optional[Character]:
        """Load character from file"""
        file_path = CHARACTERS_DIR / f"{character_id}.json"
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                return Character.from_dict(data)
            except Exception as e:
                print(f"Error loading character {character_id}: {e}")
        return None
    
    def load_all_characters(self):
        """Load all characters from files"""
        self.characters = {}
        for char_file in CHARACTERS_DIR.glob("*.json"):
            try:
                with open(char_file, 'r') as f:
                    data = json.load(f)
                character = Character.from_dict(data)
                self.characters[character.character_id] = character
            except Exception as e:
                print(f"Error loading character from {char_file}: {e}")
    
    def get_character(self, character_id: str) -> Optional[Character]:
        """Get character by ID"""
        return self.characters.get(character_id)
    
    def get_characters_by_manuscript(self, manuscript_id: str) -> List[Character]:
        """Get all characters for a specific manuscript"""
        return [char for char in self.characters.values() 
                if char.manuscript_id == manuscript_id]
    
    def list_all_characters(self) -> List[Character]:
        """Get list of all characters"""
        return list(self.characters.values())
    
    def update_character(self, character_id: str, name: Optional[str] = None, 
                        role: Optional[str] = None, traits: Optional[str] = None) -> bool:
        """Update character information"""
        character = self.get_character(character_id)
        if not character:
            return False
        
        if name is not None:
            character.name = name
        if role is not None:
            character.role = role
        if traits is not None:
            character.traits = traits
        
        self.save_character(character)
        return True
    
    def delete_character(self, character_id: str) -> bool:
        """Delete a character"""
        if character_id in self.characters:
            del self.characters[character_id]
            file_path = CHARACTERS_DIR / f"{character_id}.json"
            if file_path.exists():
                file_path.unlink()
            return True
        return False
    
    def add_conversation_turn(self, character_id: str, user_message: str, 
                             character_response: str) -> bool:
        """Add a conversation turn for a character"""
        character = self.get_character(character_id)
        if character:
            character.add_conversation_turn(user_message, character_response)
            self.save_character(character)
            return True
        return False
    
    def clear_conversation_history(self, character_id: str) -> bool:
        """Clear conversation history for a character"""
        character = self.get_character(character_id)
        if character:
            character.conversation_history = []
            self.save_character(character)
            return True
        return False
    
    def export_character(self, character_id: str) -> Optional[Dict[str, Any]]:
        """Export character data for backup or sharing"""
        character = self.get_character(character_id)
        return character.to_dict() if character else None
    
    def import_character(self, character_data: Dict[str, Any]) -> Optional[Character]:
        """Import character from exported data"""
        try:
            # Generate new ID to avoid conflicts
            character_data['character_id'] = str(uuid.uuid4())
            character = Character.from_dict(character_data)
            self.characters[character.character_id] = character
            self.save_character(character)
            return character
        except Exception as e:
            print(f"Error importing character: {e}")
            return None