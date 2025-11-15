"""
NER (Named Entity Recognition) Service

Provides named entity extraction using spaCy for the ETL pipeline.
Extracts entities like PERSON, ORG, DATE, GPE, etc. from text fragments.
"""

from typing import Dict, List, Optional
import spacy

# Load spaCy model once at module level for efficiency
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    raise RuntimeError(
        "spaCy model 'en_core_web_sm' not found. "
        "Please run: python -m spacy download en_core_web_sm"
    )


def extract_entities_from_text(text: str) -> Dict[str, List[str]]:
    """
    Extract named entities from text using spaCy NER.
    
    Args:
        text: Input text to extract entities from
        
    Returns:
        Dictionary mapping entity labels to lists of entity texts.
        Example:
            {
                "ORG": ["Apple", "Google"],
                "PERSON": ["John Smith", "Jane Doe"],
                "DATE": ["2024-01-15", "November 2023"]
            }
        Returns empty dict if no entities found.
        
    Notes:
        - Entity lists are deduplicated and sorted for determinism
        - Handles empty or None text safely
        - Common entity types: PERSON, ORG, GPE, DATE, MONEY, etc.
    """
    # Handle empty or None text
    if not text or not isinstance(text, str):
        return {}
    
    # Process text with spaCy
    doc = nlp(text)
    
    # Group entities by label
    entities_by_label: Dict[str, List[str]] = {}
    
    for ent in doc.ents:
        label = ent.label_
        entity_text = ent.text
        
        if label not in entities_by_label:
            entities_by_label[label] = []
        
        entities_by_label[label].append(entity_text)
    
    # Deduplicate and sort each list for determinism
    for label in entities_by_label:
        # Convert to set for deduplication, then sort
        entities_by_label[label] = sorted(list(set(entities_by_label[label])))
    
    return entities_by_label


def apply_ner_to_fragment(fragment: Dict) -> Dict:
    """
    Apply NER to a single fragment and add entity information.
    
    Args:
        fragment: Dictionary containing fragment data.
                 Should have either "raw_text" or "content" field.
                 
    Returns:
        New dictionary with original fragment data plus "ner" field
        containing extracted entities.
        
    Notes:
        - Prefers "raw_text" field if it exists, otherwise uses "content"
        - Original fragment is not modified (returns new dict)
        - Adds empty dict for "ner" if no text is available
    """
    # Create a copy to avoid modifying input
    result = fragment.copy()
    
    # Extract text from fragment
    text = None
    if "raw_text" in fragment:
        text = fragment["raw_text"]
    elif "content" in fragment:
        # Convert content to string if it exists
        content = fragment["content"]
        if content is not None:
            text = str(content)
    
    # Extract entities
    entities = extract_entities_from_text(text) if text else {}
    
    # Add NER results to fragment
    result["ner"] = entities
    
    return result


def apply_ner_to_fragments(fragments: List[Dict]) -> List[Dict]:
    """
    Apply NER to multiple fragments.
    
    Args:
        fragments: List of fragment dictionaries
        
    Returns:
        New list of fragments with NER data added to each fragment.
        Original input list is not modified.
        
    Notes:
        - Returns a new list (does not modify input in-place)
        - Deterministic output (entity lists are sorted)
        - Safe for empty or malformed fragments
    """
    # Process each fragment and return new list
    return [apply_ner_to_fragment(fragment) for fragment in fragments]
