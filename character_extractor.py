"""
Automatic Character Extraction and Analysis Module
Extracts characters and their personality traits from manuscripts using NLP and LLM analysis
"""

import re
import spacy
import json
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict, Counter
from textblob import TextBlob
import requests
from config import OLLAMA_BASE_URL, DEFAULT_LLM_MODEL

class CharacterExtractor:
    """Extracts characters and their traits from manuscript text"""
    
    def __init__(self):
        self.nlp = None
        self.character_patterns = [
            # Common dialogue patterns - more comprehensive
            r'"[^"]*"[,\s]*(?:said|asked|replied|whispered|shouted|muttered|exclaimed|declared|announced|called|cried|yelled)\s+([A-Z][a-zA-Z]+)',
            r'([A-Z][a-zA-Z]+)\s+(?:said|asked|replied|whispered|shouted|muttered|exclaimed|declared|announced|called|cried|yelled)[,\s]*"[^"]*"',
            # Character action patterns - expanded
            r'([A-Z][a-zA-Z]+)(?:\s+[A-Z][a-z]+)?\s+(?:walked|ran|looked|turned|smiled|frowned|nodded|shook|stood|sat|moved|stepped|climbed|jumped|fell|rose|laughed|cried|sighed)',
            # Possessive patterns - expanded
            r"([A-Z][a-zA-Z]+)'s\s+(?:eyes|face|voice|hand|heart|mind|head|body|hair|arms|legs|smile|frown|expression|thoughts)",
            # Direct address patterns
            r'"[^"]*,\s*([A-Z][a-zA-Z]+)[,\.]',
            r'([A-Z][a-zA-Z]+)[,\s]+(?:the|a|an)\s+(?:young|old|tall|short|brave|wise|skilled|beautiful|handsome|mysterious)',
            # Descriptive patterns
            r'([A-Z][a-zA-Z]+)\s+was\s+(?:a|an|the)',
            r'([A-Z][a-zA-Z]+),?\s+(?:who|whom)\s+(?:was|had|could|would)',
        ]
        self._load_nlp_model()
    
    def _load_nlp_model(self):
        """Load spaCy model for NER"""
        try:
            # Try to load the English model
            self.nlp = spacy.load("en_core_web_sm")
        except IOError:
            print("⚠️ SpaCy English model not found. Installing...")
            # Note: In production, this should be handled during setup
            try:
                import subprocess
                subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
                self.nlp = spacy.load("en_core_web_sm")
                print("✅ SpaCy model installed successfully")
            except Exception as e:
                print(f"❌ Failed to install spaCy model: {e}")
                print("Please run: python -m spacy download en_core_web_sm")
                self.nlp = None
    
    def extract_characters_from_text(self, text: str, manuscript_id: str) -> List[Dict[str, Any]]:
        """Main method to extract characters and their information from text"""
        print("🔍 Analyzing manuscript for characters...")
        
        # Step 1: Extract potential character names
        potential_names = self._extract_character_names(text)
        print(f"Found {len(potential_names)} potential character names")
        
        # Step 2: Filter and validate character names
        validated_characters = self._validate_character_names(text, potential_names)
        print(f"Validated {len(validated_characters)} main characters")
        
        # Step 3: Extract character information for each validated character
        character_profiles = []
        for character_name in validated_characters:
            print(f"📝 Analyzing character: {character_name}")
            profile = self._extract_character_profile(text, character_name, manuscript_id)
            if profile:
                character_profiles.append(profile)
        
        return character_profiles
    
    def _extract_character_names(self, text: str) -> List[str]:
        """Extract potential character names using multiple techniques"""
        names = set()
        
        # Method 1: Named Entity Recognition with spaCy (most reliable)
        if self.nlp:
            doc = self.nlp(text[:50000])  # Analyze first 50k chars for performance
            for ent in doc.ents:
                if ent.label_ == "PERSON" and len(ent.text.split()) <= 3:
                    # Clean the name
                    clean_name = self._clean_character_name(ent.text)
                    if clean_name and len(clean_name) > 2 and self._is_valid_name(clean_name):
                        names.add(clean_name)
        
        # Method 2: Dialogue pattern extraction
        for pattern in self.character_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                for group in match.groups():
                    if group and self._is_valid_name(group):
                        clean_name = self._clean_character_name(group)
                        if clean_name:
                            names.add(clean_name)
        
        # Method 3: Common name patterns - be much more selective
        # Look for capitalized words that appear frequently in name-like contexts
        name_context_patterns = [
            r'\b([A-Z][a-z]{2,15})\s+(?:said|asked|replied|whispered|shouted|muttered|exclaimed|declared|announced)',
            r'"[^"]*,?\s*([A-Z][a-z]{2,15})[,\.]',
            r'\b([A-Z][a-z]{2,15})\s+(?:was|is|had|could|would|might|should|walked|ran|looked|turned|smiled|frowned)',
            r'\b([A-Z][a-z]{2,15}),?\s+(?:the|a|an)\s+(?:young|old|tall|short|brave|wise|skilled|beautiful|handsome|mysterious)',
        ]
        
        for pattern in name_context_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if self._is_valid_name(match):
                    names.add(match)
        
        return list(names)
    
    def _clean_character_name(self, name: str) -> str:
        """Clean and normalize character names"""
        if not name:
            return ""
        
        # Remove extra whitespace and capitalize properly
        clean_name = ' '.join(name.split())
        
        # Handle basic title case
        clean_name = clean_name.title()
        
        # Remove quotes and other unwanted characters
        clean_name = re.sub(r'["""''""\'`]', '', clean_name)
        
        return clean_name.strip()
    
    def _is_valid_name(self, name: str) -> bool:
        """Check if a string looks like a valid character name"""
        if not name or len(name) < 2:
            return False
        
        # Comprehensive exclude list - common words that aren't names
        exclude_words = {
            # Basic words
            'The', 'And', 'But', 'When', 'Where', 'What', 'Who', 'How', 'Why',
            'This', 'That', 'These', 'Those', 'Here', 'There', 'Now', 'Then',
            'Yes', 'No', 'Maybe', 'Perhaps', 'Indeed', 'However', 'Therefore',
            'Chapter', 'Page', 'Book', 'Story', 'Tale', 'End', 'Beginning',
            'Morning', 'Evening', 'Night', 'Day', 'Yesterday', 'Tomorrow',
            
            # Calendar
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December',
            'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',
            
            # Pronouns and common words
            'For', 'You', 'We', 'He', 'She', 'It', 'They', 'I', 'Me', 'My', 'Mine',
            'Your', 'His', 'Her', 'Its', 'Their', 'Our', 'Us', 'Him', 'Them',
            'All', 'Some', 'Many', 'Few', 'One', 'Two', 'Three', 'First', 'Last',
            'Once', 'Only', 'Even', 'Still', 'Just', 'More', 'Most', 'Much',
            'Very', 'Too', 'So', 'Such', 'Well', 'Good', 'Bad', 'Best', 'Worst',
            'Old', 'New', 'Young', 'Long', 'Short', 'Big', 'Small', 'Great',
            'Little', 'Right', 'Left', 'Up', 'Down', 'In', 'Out', 'On', 'Off',
            'Before', 'After', 'During', 'While', 'Until', 'Since', 'From',
            'To', 'At', 'By', 'With', 'Without', 'About', 'Over', 'Under',
            'Through', 'Around', 'Near', 'Far', 'Back', 'Forward', 'Away',
            'Again', 'Always', 'Never', 'Sometimes', 'Often', 'Usually',
            'Finally', 'Suddenly', 'Quickly', 'Slowly', 'Carefully',
            
            # Common false positives from user's output
            'Was', 'Were', 'Been', 'Being', 'Have', 'Has', 'Had', 'Do', 'Does', 'Did',
            'Will', 'Would', 'Could', 'Should', 'Can', 'May', 'Might', 'Must',
            'Are', 'Is', 'Am', 'Not', 'Any', 'Every', 'Each', 'Both', 'Either',
            'Neither', 'None', 'Nothing', 'Something', 'Anything', 'Everything',
            'Someone', 'Anyone', 'Everyone', 'No', 'Nobody', 'Somebody', 'Everybody',
            'Somewhere', 'Anywhere', 'Everywhere', 'Nowhere',
            
            # Question words and conjunctions
            'If', 'Unless', 'Although', 'Though', 'Because', 'Since', 'As',
            'Whether', 'While', 'Whereas', 'Until', 'Before', 'After',
            
            # Misc common words
            'Other', 'Another', 'Same', 'Different', 'Next', 'Previous', 'Following',
            'Above', 'Below', 'Inside', 'Outside', 'Between', 'Among', 'Against',
            
            # Time and date words
            'Today', 'Tomorrow', 'Yesterday', 'Tonight', 'Morning', 'Afternoon', 'Evening',
            'Week', 'Month', 'Year', 'Time', 'Hour', 'Minute', 'Second', 'Moment',
            
            # Place names and businesses (common false positives)
            'Walmart', 'Target', 'Home', 'Office', 'Store', 'Shop', 'Mall', 'Center',
            'Street', 'Road', 'Avenue', 'Drive', 'Lane', 'Place', 'Square', 'Park',
            'City', 'Town', 'State', 'Country', 'World', 'Earth', 'North', 'South',
            'East', 'West', 'Central', 'Grand', 'Main', 'First', 'Second', 'Third',
            
            # Technology and objects
            'Phone', 'Computer', 'Internet', 'Email', 'Website', 'App', 'Software',
            'Program', 'System', 'Network', 'Database', 'Server', 'File', 'Document',
            
            # Actions and states
            'Stop', 'Start', 'Begin', 'End', 'Finish', 'Complete', 'Continue', 'Pause',
            'Wait', 'Hold', 'Keep', 'Stay', 'Leave', 'Go', 'Come', 'Move', 'Turn',
            'Open', 'Close', 'Lock', 'Unlock', 'Push', 'Pull', 'Press', 'Click'
        }
        
        # Case-insensitive check against exclude words
        if name.lower() in {word.lower() for word in exclude_words}:
            return False
        
        # Must start with capital letter and contain only letters, spaces, apostrophes
        if not re.match(r"^[A-Z][a-zA-Z\s']+$", name):
            return False
        
        # Exclude very common English words and verbs
        common_verbs = {'said', 'asked', 'replied', 'looked', 'went', 'came', 'made', 'took', 
                       'walked', 'ran', 'turned', 'smiled', 'frowned', 'nodded', 'shook',
                       'stood', 'sat', 'lay', 'fell', 'rose', 'jumped', 'climbed',
                       'opened', 'closed', 'held', 'dropped', 'picked', 'threw', 'caught'}
        
        if name.lower() in common_verbs:
            return False
        
        # Must be a reasonable length for a name (2-20 characters)
        if len(name) < 2 or len(name) > 20:
            return False
        
        # Names shouldn't be all uppercase (likely not a name)
        if name.isupper() and len(name) > 3:
            return False
        
        # Additional validation: must look like a proper name
        # Should start with uppercase and contain mostly lowercase letters
        if not re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$', name):
            return False
        
        # Must not be a common English word (additional check)
        # Common words that might slip through
        additional_excludes = {
            'said', 'asked', 'replied', 'told', 'called', 'named', 'known',
            'seen', 'heard', 'found', 'made', 'took', 'gave', 'came', 'went',
            'thought', 'felt', 'seemed', 'appeared', 'became', 'remained',
            'continued', 'started', 'stopped', 'finished', 'decided',
            # Business/place names that commonly appear
            'walmart', 'target', 'amazon', 'google', 'facebook', 'twitter',
            'microsoft', 'apple', 'samsung', 'toyota', 'ford', 'honda',
            # Time/calendar terms
            'today', 'tomorrow', 'yesterday', 'morning', 'evening', 'afternoon',
            # Common false positive patterns
            'grand', 'central', 'main', 'first', 'second', 'third', 'last',
            'north', 'south', 'east', 'west', 'center', 'middle', 'upper', 'lower',
            # Generic terms
            'office', 'home', 'work', 'school', 'hospital', 'hotel', 'restaurant',
            'store', 'shop', 'mall', 'park', 'street', 'road', 'building',
            
            # Countries and geographical entities (major issue from user feedback)
            'Russia', 'China', 'America', 'England', 'France', 'Germany', 'Italy', 
            'Spain', 'Japan', 'India', 'Brazil', 'Canada', 'Mexico', 'Australia',
            'Egypt', 'Greece', 'Turkey', 'Poland', 'Sweden', 'Norway', 'Denmark',
            'Finland', 'Ireland', 'Scotland', 'Wales', 'Belgium', 'Netherlands',
            'Switzerland', 'Austria', 'Portugal', 'Romania', 'Hungary', 'Czech',
            'Slovakia', 'Bulgaria', 'Croatia', 'Serbia', 'Ukraine', 'Belarus',
            'Lithuania', 'Latvia', 'Estonia', 'Israel', 'Jordan', 'Syria', 'Iraq',
            'Iran', 'Saudi', 'Yemen', 'Kuwait', 'Qatar', 'Emirates', 'Oman',
            'Pakistan', 'Afghanistan', 'Bangladesh', 'Myanmar', 'Thailand',
            'Vietnam', 'Cambodia', 'Laos', 'Malaysia', 'Indonesia', 'Philippines',
            'Singapore', 'Korea', 'Mongolia', 'Nepal', 'Tibet', 'Sri', 'Maldives',
            'Africa', 'Asia', 'Europe', 'Antarctica', 'Arctic', 'Pacific', 'Atlantic',
            'Indian', 'Mediterranean', 'Caribbean', 'Baltic', 'North', 'South',
            'East', 'West', 'Central', 'Western', 'Eastern', 'Northern', 'Southern',
            
            # US States (common false positives)
            'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado',
            'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho',
            'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana',
            'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota',
            'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada',
            'Hampshire', 'Jersey', 'Mexico', 'York', 'Carolina', 'Dakota',
            'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode', 'Tennessee',
            'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington', 'Wisconsin',
            'Wyoming',
            
            # Major cities (common false positives)
            'London', 'Paris', 'Berlin', 'Rome', 'Madrid', 'Moscow', 'Tokyo',
            'Beijing', 'Shanghai', 'Mumbai', 'Delhi', 'Bangkok', 'Singapore',
            'Sydney', 'Melbourne', 'Toronto', 'Vancouver', 'Montreal', 'York',
            'Angeles', 'Francisco', 'Chicago', 'Houston', 'Philadelphia', 'Phoenix',
            'Antonio', 'Diego', 'Dallas', 'Jose', 'Austin', 'Jacksonville',
            'Columbus', 'Charlotte', 'Francisco', 'Indianapolis', 'Seattle',
            'Denver', 'Boston', 'Nashville', 'Baltimore', 'Louisville', 'Portland',
            'Oklahoma', 'Milwaukee', 'Vegas', 'Albuquerque', 'Tucson', 'Fresno',
            'Sacramento', 'Mesa', 'Atlanta', 'Omaha', 'Colorado', 'Raleigh',
            'Miami', 'Oakland', 'Minneapolis', 'Tulsa', 'Cleveland', 'Wichita',
            'Arlington', 'Bakersfield', 'Tampa', 'Aurora', 'Anaheim', 'Santa',
            'Riverside', 'Corpus', 'Lexington', 'Pittsburgh', 'Anchorage',
            'Stockton', 'Cincinnati', 'Paul', 'Toledo', 'Newark', 'Greensboro',
            'Plano', 'Henderson', 'Lincoln', 'Buffalo', 'Jersey', 'Chula',
            'Orleans', 'Chandler', 'Laredo', 'Norfolk', 'Madison', 'Durham',
            'Lubbock', 'Winston', 'Garland', 'Glendale', 'Hialeah', 'Reno',
            'Baton', 'Irving', 'Chesapeake', 'Scottsdale', 'Fremont', 'Gilbert',
            'Birmingham', 'Rochester', 'Modesto', 'Spokane', 'Montgomery',
            'Yonkers', 'Shreveport', 'Des', 'Moines', 'Tacoma', 'Fontana',
            'San', 'Bernardino', 'Fayetteville', 'Sioux', 'Falls', 'Springfield',
            'Huntsville', 'Glendale', 'Salt', 'Lake', 'Tallahassee', 'Grand',
            'Rapids', 'Huntington', 'Beach', 'Overland', 'Knoxville', 'Worcester',
            'Brownsville', 'Newport', 'News', 'Fort', 'Lauderdale', 'Providence',
            'Salt', 'Lake', 'Huntsville', 'Amarillo', 'Grand', 'Prairie',
            'Peoria', 'Mobile', 'Columbia', 'Shreveport', 'Little', 'Rock',
            'Augusta', 'Akron', 'Dayton', 'Eugene', 'Cedar', 'Rapids',
            
            # Organizations, companies, brands (common false positives)
            'Google', 'Apple', 'Microsoft', 'Amazon', 'Facebook', 'Twitter',
            'Instagram', 'YouTube', 'Netflix', 'Disney', 'Sony', 'Samsung',
            'Toyota', 'Ford', 'Honda', 'Bmw', 'Mercedes', 'Audi', 'Volkswagen',
            'Nike', 'Adidas', 'Coca', 'Cola', 'Pepsi', 'Starbucks', 'Mcdonalds',
            'Walmart', 'Target', 'Costco', 'Fedex', 'Ups', 'Dhl', 'Usps',
            'Bank', 'America', 'Wells', 'Fargo', 'Chase', 'Citibank',
            
            # Institutions and government
            'Government', 'Congress', 'Senate', 'House', 'Court', 'Supreme',
            'Department', 'Agency', 'Bureau', 'Office', 'Ministry', 'Parliament',
            'Council', 'Committee', 'Commission', 'Board', 'Authority',
            'University', 'College', 'School', 'Institute', 'Academy',
            'Hospital', 'Clinic', 'Center', 'Foundation', 'Organization',
            'Association', 'Society', 'Union', 'Federation', 'League',
            'Corporation', 'Company', 'Enterprise', 'Business', 'Industry',
            'Group', 'Team', 'Club', 'Party', 'Alliance'
        }
        
        if name.lower() in additional_excludes:
            return False
        
        # Additional check: avoid single common words that are capitalized in sentences
        # These are often sentence beginnings, not names
        sentence_starters = {
            'meanwhile', 'however', 'therefore', 'furthermore', 'moreover',
            'nonetheless', 'nevertheless', 'consequently', 'subsequently',
            'finally', 'initially', 'eventually', 'immediately', 'suddenly',
            'quickly', 'slowly', 'carefully', 'quietly', 'loudly'
        }
        
        if name.lower() in sentence_starters:
            return False
        
        return True
    
    def _validate_character_names(self, text: str, potential_names: List[str]) -> List[str]:
        """Validate and filter character names based on context and frequency"""
        validated = []
        
        # Additional geographical/organizational filter as backup
        geo_entities = {
            'russia', 'china', 'america', 'england', 'france', 'germany', 'italy', 
            'spain', 'japan', 'india', 'brazil', 'canada', 'mexico', 'australia',
            'africa', 'asia', 'europe', 'usa', 'uk', 'soviet', 'ussr',
            'government', 'congress', 'senate', 'parliament', 'ministry',
            'department', 'agency', 'bureau', 'office', 'court', 'supreme'
        }
        
        for name in potential_names:
            # Skip obvious geographical/organizational entities
            if name.lower() in geo_entities:
                continue
            # Count mentions in different contexts
            total_mentions = len(re.findall(r'\b' + re.escape(name) + r'\b', text, re.IGNORECASE))
            dialogue_mentions = len(re.findall(
                r'["""''""\'`].*?' + re.escape(name) + r'.*?["""''""\'`]|' +
                re.escape(name) + r'\s+(?:said|asked|replied|whispered|shouted|muttered|exclaimed)',
                text, re.IGNORECASE
            ))
            action_mentions = len(re.findall(
                re.escape(name) + r'\s+(?:walked|ran|looked|turned|smiled|frowned|nodded|shook|stood|sat)',
                text, re.IGNORECASE
            ))
            
            # Character validation criteria - be less strict to catch more characters
            is_main_character = (
                total_mentions >= 3 and  # Mentioned at least 3 times (reduced from 5)
                (dialogue_mentions >= 1 or action_mentions >= 1 or total_mentions >= 5)  # Has dialogue, actions, or frequent mentions
            )
            
            if is_main_character:
                validated.append(name)
        
        # Sort by frequency (most mentioned first)
        validated.sort(key=lambda x: len(re.findall(r'\b' + re.escape(x) + r'\b', text, re.IGNORECASE)), reverse=True)
        
        # Deduplicate similar names (e.g., "Alex" and "Alex Johnson")
        deduplicated = self._deduplicate_character_names(validated, text)
        
        # Limit to top 10 most prominent characters
        return deduplicated[:10]
    
    def _deduplicate_character_names(self, character_names: List[str], text: str) -> List[str]:
        """Remove duplicate character names where one name is contained in another"""
        if not character_names:
            return character_names
        
        # Create a list to track which names to keep
        final_names = []
        
        # Sort by length (longest first) so we prioritize full names
        sorted_names = sorted(character_names, key=len, reverse=True)
        
        for i, name1 in enumerate(sorted_names):
            is_duplicate = False
            
            # Check if this name is a subset of any longer name we've already accepted
            for kept_name in final_names:
                if self._is_name_subset(name1, kept_name, text):
                    is_duplicate = True
                    break
            
            # Also check if any remaining shorter names are subsets of this name
            if not is_duplicate:
                # Remove any previously added names that are subsets of this name
                final_names = [name for name in final_names if not self._is_name_subset(name, name1, text)]
                final_names.append(name1)
        
        # Sort the final list by original frequency order
        name_frequencies = {name: len(re.findall(r'\b' + re.escape(name) + r'\b', text, re.IGNORECASE)) 
                           for name in final_names}
        final_names.sort(key=lambda x: name_frequencies[x], reverse=True)
        
        return final_names
    
    def _is_name_subset(self, shorter_name: str, longer_name: str, text: str) -> bool:
        """Check if shorter_name is likely the same character as longer_name"""
        if shorter_name == longer_name:
            return False
        
        # Check if the shorter name is contained in the longer name
        shorter_words = shorter_name.lower().split()
        longer_words = longer_name.lower().split()
        
        # If shorter name is just one word, check if it's the first name of the longer name
        if len(shorter_words) == 1 and len(longer_words) >= 2:
            # "Alex" should match "Alex Johnson" but not "Alexander"
            return shorter_words[0] == longer_words[0]
        
        # If both have multiple words, check if all words of shorter name are in longer name
        if len(shorter_words) > 1:
            return all(word in longer_words for word in shorter_words)
        
        return False
    
    def _extract_character_profile(self, text: str, character_name: str, manuscript_id: str) -> Optional[Dict[str, Any]]:
        """Extract detailed character profile using LLM analysis"""
        # Extract relevant passages about the character
        character_passages = self._extract_character_passages(text, character_name)
        
        if not character_passages:
            return None
        
        # Use LLM to analyze character
        character_analysis = self._analyze_character_with_llm(character_name, character_passages)
        
        # If LLM analysis fails, create a basic profile
        if not character_analysis:
            print(f"⚠️ LLM analysis failed for {character_name}, creating basic profile")
            character_analysis = self._create_basic_character_profile(character_name, character_passages)
        
        return {
            'name': character_name,
            'role': character_analysis.get('role', ''),
            'traits': character_analysis.get('traits', ''),
            'description': character_analysis.get('description', ''),
            'gender': character_analysis.get('gender', 'unknown'),
            'relationships': character_analysis.get('relationships', []),
            'key_quotes': character_analysis.get('key_quotes', []),
            'manuscript_id': manuscript_id,
            'extraction_confidence': character_analysis.get('confidence', 0.5)
        }
    
    def _extract_character_passages(self, text: str, character_name: str) -> List[str]:
        """Extract text passages that mention or involve the character"""
        passages = []
        
        # Split text into sentences
        sentences = re.split(r'[.!?]+', text)
        
        # Find sentences mentioning the character
        character_sentences = []
        for sentence in sentences:
            if re.search(r'\b' + re.escape(character_name) + r'\b', sentence, re.IGNORECASE):
                character_sentences.append(sentence.strip())
        
        # Group sentences into meaningful passages (3-5 sentences each)
        for i in range(0, len(character_sentences), 3):
            passage = ' '.join(character_sentences[i:i+5])
            if len(passage) > 50:  # Meaningful length
                passages.append(passage)
        
        # Limit to most relevant passages
        return passages[:10]
    
    def _analyze_character_with_llm(self, character_name: str, passages: List[str]) -> Optional[Dict[str, Any]]:
        """Use LLM to analyze character traits and information"""
        if not passages:
            return None
        
        # Prepare the analysis prompt
        passages_text = '\n\n'.join(passages[:5])  # Use top 5 passages
        
        # Calculate better confidence based on text analysis
        total_mentions = len(re.findall(r'\b' + re.escape(character_name) + r'\b', '\n'.join(passages), re.IGNORECASE))
        dialogue_mentions = len(re.findall(
            r'["""''""\'`].*?' + re.escape(character_name) + r'.*?["""''""\'`]|' +
            re.escape(character_name) + r'\s+(?:said|asked|replied|whispered|shouted|muttered|exclaimed)',
            '\n'.join(passages), re.IGNORECASE
        ))
        action_mentions = len(re.findall(
            re.escape(character_name) + r'\s+(?:walked|ran|looked|turned|smiled|frowned|nodded|shook|stood|sat|went|came|moved|jumped|climbed)',
            '\n'.join(passages), re.IGNORECASE
        ))
        
        # Base confidence calculation
        base_confidence = min(0.9, 0.4 + (total_mentions * 0.1) + (dialogue_mentions * 0.15) + (action_mentions * 0.1))
        
        prompt = f"""Analyze the character "{character_name}" based on the following passages from a manuscript. This character appears {total_mentions} times in these passages, has {dialogue_mentions} dialogue mentions, and {action_mentions} action mentions.

PASSAGES:
{passages_text}

Please provide a JSON response with the following structure. Pay special attention to gender indicators (pronouns like he/him, she/her, they/them, titles like Mr./Ms./Dr., gendered descriptions):

{{
    "role": "Brief description of character's role/occupation/position (e.g., 'village blacksmith', 'young wizard', 'kingdom's general')",
    "traits": "Key personality traits, behavioral patterns, and characteristics (e.g., 'brave but impulsive, loyal to friends, struggles with self-doubt')",
    "description": "Physical or notable descriptive details if mentioned",
    "gender": "male/female/non-binary/unknown - based on pronouns, titles, or descriptions in the text",
    "relationships": ["list", "of", "other", "characters", "mentioned", "in", "relation", "to", "this", "character"],
    "key_quotes": ["Notable quotes or dialogue from this character"],
    "confidence": {base_confidence:.2f}
}}

Important guidelines:
- For gender: Look for pronouns (he/him=male, she/her=female, they/them=non-binary), titles (Mr./Sir=male, Ms./Mrs./Lady=female), or physical descriptions
- For confidence: Consider how much concrete information is available about this character
- Main characters with lots of dialogue and actions should have higher confidence (0.8-0.9)
- Background characters with minimal mentions should have lower confidence (0.3-0.6)
- If this character has substantial dialogue, detailed descriptions, or multiple relationships, increase confidence

JSON Response:"""

        try:
            # Make request to Ollama [[memory:2545521]]
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": DEFAULT_LLM_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '').strip()
                
                # Try to parse JSON response
                try:
                    analysis = json.loads(response_text)
                    return analysis
                except json.JSONDecodeError:
                    # Fallback: extract information from text response
                    print(f"⚠️ Could not parse JSON for {character_name}, using fallback")
                    return self._parse_text_analysis(response_text, character_name)
            
        except Exception as e:
            print(f"❌ Error analyzing character {character_name}: {e}")
        
        return None
    
    def _parse_text_analysis(self, text: str, character_name: str) -> Dict[str, Any]:
        """Fallback method to parse character analysis from text"""
        # Try basic gender detection from text
        gender = 'unknown'
        if re.search(r'\b(he|him|his)\b', text.lower()):
            gender = 'male'
        elif re.search(r'\b(she|her|hers)\b', text.lower()):
            gender = 'female'
        elif re.search(r'\b(they|them|their)\b', text.lower()):
            gender = 'non-binary'
        
        return {
            'role': 'Character from the manuscript',
            'traits': 'Character with unique personality traits',
            'description': '',
            'gender': gender,
            'relationships': [],
            'key_quotes': [],
            'confidence': 0.3
        }
    
    def extract_character_relationships(self, text: str, characters: List[str]) -> Dict[str, List[str]]:
        """Extract relationships between characters"""
        relationships = defaultdict(list)
        
        # Look for characters mentioned together in sentences
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            mentioned_chars = [char for char in characters 
                             if re.search(r'\b' + re.escape(char) + r'\b', sentence, re.IGNORECASE)]
            
            # If multiple characters in same sentence, they likely have a relationship
            if len(mentioned_chars) >= 2:
                for i, char1 in enumerate(mentioned_chars):
                    for char2 in mentioned_chars[i+1:]:
                        if char2 not in relationships[char1]:
                            relationships[char1].append(char2)
                        if char1 not in relationships[char2]:
                            relationships[char2].append(char1)
        
        return dict(relationships)
    
    def _create_basic_character_profile(self, character_name: str, character_passages: List[str]) -> Dict[str, Any]:
        """Create a basic character profile when LLM analysis is unavailable"""
        # Extract basic information from passages
        all_text = ' '.join(character_passages)
        
        # Try to determine role from common patterns
        role = "Character from the manuscript"
        role_patterns = [
            (r'(?:king|queen|prince|princess|lord|lady)', 'Noble/Royalty'),
            (r'(?:knight|warrior|soldier|guard)', 'Warrior/Fighter'), 
            (r'(?:wizard|mage|sorcerer|witch)', 'Magic User'),
            (r'(?:blacksmith|smith)', 'Blacksmith'),
            (r'(?:archer|bowman)', 'Archer'),
            (r'(?:merchant|trader)', 'Merchant'),
            (r'(?:priest|cleric|monk)', 'Religious Figure'),
            (r'(?:thief|rogue|assassin)', 'Rogue'),
            (r'(?:bard|musician)', 'Bard/Musician'),
            (r'(?:healer|doctor)', 'Healer'),
        ]
        
        for pattern, role_desc in role_patterns:
            if re.search(pattern, all_text, re.IGNORECASE):
                role = role_desc
                break
        
        # Extract basic traits from common descriptive words
        traits = []
        trait_patterns = [
            (r'(?:brave|courageous|bold)', 'brave'),
            (r'(?:wise|intelligent|smart)', 'wise'),
            (r'(?:kind|gentle|caring)', 'kind'),
            (r'(?:strong|powerful|mighty)', 'strong'), 
            (r'(?:mysterious|enigmatic)', 'mysterious'),
            (r'(?:young|youthful)', 'young'),
            (r'(?:old|elderly|aged)', 'old'),
            (r'(?:beautiful|handsome|attractive)', 'attractive'),
            (r'(?:skilled|talented)', 'skilled'),
        ]
        
        for pattern, trait in trait_patterns:
            if re.search(pattern, all_text, re.IGNORECASE):
                traits.append(trait)
        
        traits_text = ', '.join(traits) if traits else 'Unique personality traits'
        
        # Basic gender detection
        gender = 'unknown'
        if re.search(r'\b(he|him|his)\b', all_text.lower()):
            gender = 'male'
        elif re.search(r'\b(she|her|hers)\b', all_text.lower()):
            gender = 'female'
        elif re.search(r'\b(they|them|their)\b', all_text.lower()):
            gender = 'non-binary'
        elif re.search(r'\b(mr|sir|lord|king|prince)\b', all_text.lower()):
            gender = 'male'
        elif re.search(r'\b(ms|mrs|miss|lady|queen|princess)\b', all_text.lower()):
            gender = 'female'
        
        return {
            'role': role,
            'traits': traits_text,
            'description': '',
            'gender': gender,
            'relationships': [],
            'key_quotes': [],
            'confidence': 0.3  # Lower confidence for basic profiles
        }
    
    def get_character_excerpts(self, text: str, character_name: str, max_excerpts: int = 5) -> List[str]:
        """Get key excerpts featuring the character for preview"""
        excerpts = []
        
        # Split into paragraphs
        paragraphs = text.split('\n\n')
        
        for para in paragraphs:
            if re.search(r'\b' + re.escape(character_name) + r'\b', para, re.IGNORECASE):
                # Clean and limit length
                clean_para = para.strip()
                if len(clean_para) > 200:
                    clean_para = clean_para[:200] + "..."
                excerpts.append(clean_para)
                
                if len(excerpts) >= max_excerpts:
                    break
        
        return excerpts 