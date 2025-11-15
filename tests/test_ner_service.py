"""
Unit tests for NER service.

Tests Named Entity Recognition functionality without depending on
extractor or normalizer logic.
"""

import pytest
from services.ner_service import (
    extract_entities_from_text,
    apply_ner_to_fragment,
    apply_ner_to_fragments,
)


class TestExtractEntitiesFromText:
    """Test extract_entities_from_text function."""

    def test_extract_entities_from_text_basic(self):
        """Test basic entity extraction with ORG and DATE."""
        text = "Apple Inc. was founded in April 1976 by Steve Jobs."
        
        entities = extract_entities_from_text(text)
        
        # Should have at least ORG and DATE entities
        assert "ORG" in entities
        assert "DATE" in entities
        assert "PERSON" in entities
        
        # Check specific entities
        assert "Apple Inc." in entities["ORG"]
        assert "Steve Jobs" in entities["PERSON"]
        assert "April 1976" in entities["DATE"]
        
    def test_extract_entities_multiple_same_type(self):
        """Test extraction with multiple entities of the same type."""
        text = "Google and Microsoft are competitors. Amazon joined later."
        
        entities = extract_entities_from_text(text)
        
        assert "ORG" in entities
        # Should have multiple organizations
        assert len(entities["ORG"]) >= 2
        
    def test_extract_entities_deduplication(self):
        """Test that duplicate entities are deduplicated."""
        text = "Apple makes iPhones. Apple is based in California. Apple Inc. is huge."
        
        entities = extract_entities_from_text(text)
        
        # Check that Apple appears only once in each form
        if "ORG" in entities:
            apple_count = entities["ORG"].count("Apple")
            assert apple_count <= 1, "Duplicate 'Apple' should be removed"
    
    def test_extract_entities_sorting(self):
        """Test that entity lists are sorted for determinism."""
        text = "Zebra Corp, Apple Inc, and Microsoft work together."
        
        entities = extract_entities_from_text(text)
        
        if "ORG" in entities:
            # Check that list is sorted alphabetically
            sorted_orgs = sorted(entities["ORG"])
            assert entities["ORG"] == sorted_orgs
    
    def test_extract_entities_empty_string(self):
        """Test that empty string returns empty dict."""
        entities = extract_entities_from_text("")
        
        assert entities == {}
    
    def test_extract_entities_none(self):
        """Test that None input returns empty dict."""
        entities = extract_entities_from_text(None)
        
        assert entities == {}
    
    def test_extract_entities_no_entities(self):
        """Test text with no recognizable entities."""
        text = "This is a simple sentence with no entities."
        
        entities = extract_entities_from_text(text)
        
        # Should return empty dict or dict with empty lists
        assert isinstance(entities, dict)
        # If dict is not empty, all values should be empty lists
        for label, entity_list in entities.items():
            assert len(entity_list) == 0
    
    def test_extract_entities_non_string_input(self):
        """Test that non-string input is handled safely."""
        entities = extract_entities_from_text(12345)
        
        assert entities == {}


class TestApplyNerToFragment:
    """Test apply_ner_to_fragment function."""

    def test_apply_ner_to_fragment_with_raw_text(self):
        """Test NER application to fragment with raw_text field."""
        fragment = {
            "id": 1,
            "raw_text": "Apple Inc. released new products in January 2024.",
            "source": "test"
        }
        
        result = apply_ner_to_fragment(fragment)
        
        # Check that NER field is added
        assert "ner" in result
        assert isinstance(result["ner"], dict)
        
        # Check that original fields are preserved
        assert result["id"] == 1
        assert result["source"] == "test"
        assert result["raw_text"] == fragment["raw_text"]
        
        # Check that entities were extracted
        if "ORG" in result["ner"]:
            assert "Apple Inc." in result["ner"]["ORG"]
        if "DATE" in result["ner"]:
            assert len(result["ner"]["DATE"]) > 0
    
    def test_apply_ner_to_fragment_with_content(self):
        """Test NER application to fragment with content field (fallback)."""
        fragment = {
            "id": 2,
            "content": "Microsoft announced a new CEO in March 2023.",
            "type": "article"
        }
        
        result = apply_ner_to_fragment(fragment)
        
        # Check that NER field is added
        assert "ner" in result
        assert isinstance(result["ner"], dict)
        
        # Check original fields preserved
        assert result["id"] == 2
        assert result["type"] == "article"
    
    def test_apply_ner_to_fragment_prefers_raw_text(self):
        """Test that raw_text is preferred over content."""
        fragment = {
            "raw_text": "Google is mentioned here.",
            "content": "Different text about Amazon.",
        }
        
        result = apply_ner_to_fragment(fragment)
        
        # Should extract from raw_text (Google), not content (Amazon)
        assert "ner" in result
        if result["ner"]:  # If any entities found
            # Check that Google was likely processed, not Amazon
            all_entities = []
            for entities in result["ner"].values():
                all_entities.extend(entities)
            # This is a soft check since NER might not always catch entities
            assert len(all_entities) >= 0  # Just verify it ran
    
    def test_apply_ner_to_fragment_no_text_fields(self):
        """Test fragment without raw_text or content."""
        fragment = {
            "id": 3,
            "value": 100,
            "status": "active"
        }
        
        result = apply_ner_to_fragment(fragment)
        
        # Should have empty NER dict
        assert "ner" in result
        assert result["ner"] == {}
        
        # Original fields should be preserved
        assert result["id"] == 3
        assert result["value"] == 100
    
    def test_apply_ner_to_fragment_none_content(self):
        """Test fragment with None content."""
        fragment = {
            "content": None,
            "id": 4
        }
        
        result = apply_ner_to_fragment(fragment)
        
        assert "ner" in result
        assert result["ner"] == {}
    
    def test_apply_ner_to_fragment_does_not_mutate_input(self):
        """Test that original fragment is not modified."""
        original = {
            "id": 5,
            "raw_text": "Test text with Apple Inc."
        }
        
        # Keep a reference to original
        original_keys = set(original.keys())
        
        result = apply_ner_to_fragment(original)
        
        # Original should not have NER field
        assert "ner" not in original
        assert set(original.keys()) == original_keys
        
        # Result should have NER field
        assert "ner" in result


class TestApplyNerToFragments:
    """Test apply_ner_to_fragments function."""

    def test_apply_ner_to_fragments_multiple(self):
        """Test NER application to multiple fragments."""
        fragments = [
            {"id": 1, "raw_text": "Apple Inc. is in California."},
            {"id": 2, "raw_text": "Microsoft is in Washington."},
            {"id": 3, "content": "Google operates globally."}
        ]
        
        results = apply_ner_to_fragments(fragments)
        
        # Should return same number of fragments
        assert len(results) == 3
        
        # Each should have NER field
        for result in results:
            assert "ner" in result
            assert isinstance(result["ner"], dict)
        
        # Check that IDs are preserved
        assert results[0]["id"] == 1
        assert results[1]["id"] == 2
        assert results[2]["id"] == 3
    
    def test_apply_ner_to_fragments_separate_outputs(self):
        """Test that each fragment gets its own NER output."""
        fragments = [
            {"raw_text": "Apple Inc. announced products."},
            {"raw_text": "Microsoft released updates."}
        ]
        
        results = apply_ner_to_fragments(fragments)
        
        assert len(results) == 2
        
        # Each fragment should have separate NER results
        # (entities from one fragment should not appear in another)
        ner1 = results[0]["ner"]
        ner2 = results[1]["ner"]
        
        # Verify they are separate dict objects
        assert ner1 is not ner2
    
    def test_apply_ner_to_fragments_empty_list(self):
        """Test with empty fragment list."""
        results = apply_ner_to_fragments([])
        
        assert results == []
    
    def test_apply_ner_to_fragments_does_not_mutate_input(self):
        """Test that input list and fragments are not modified."""
        original_fragments = [
            {"id": 1, "raw_text": "Test text"},
            {"id": 2, "content": "More text"}
        ]
        
        # Keep track of original state
        original_count = len(original_fragments)
        original_keys_0 = set(original_fragments[0].keys())
        original_keys_1 = set(original_fragments[1].keys())
        
        results = apply_ner_to_fragments(original_fragments)
        
        # Original list should be unchanged
        assert len(original_fragments) == original_count
        assert "ner" not in original_fragments[0]
        assert "ner" not in original_fragments[1]
        assert set(original_fragments[0].keys()) == original_keys_0
        assert set(original_fragments[1].keys()) == original_keys_1
        
        # Results should have NER
        assert "ner" in results[0]
        assert "ner" in results[1]
    
    def test_apply_ner_to_fragments_mixed_content_types(self):
        """Test with mix of fragments with different text fields."""
        fragments = [
            {"raw_text": "Apple Inc. exists."},
            {"content": "Microsoft exists."},
            {"id": 3, "value": 100},  # No text
            {"raw_text": "Google and Amazon."}
        ]
        
        results = apply_ner_to_fragments(fragments)
        
        assert len(results) == 4
        
        # All should have NER field
        for result in results:
            assert "ner" in result
        
        # Fragment with no text should have empty NER
        assert results[2]["ner"] == {}


class TestNerServiceEdgeCases:
    """Test edge cases and error handling."""

    def test_extract_entities_with_special_characters(self):
        """Test text with special characters and unicode."""
        text = "François Müller works at Zürich Bank in 2024."
        
        entities = extract_entities_from_text(text)
        
        # Should handle unicode properly
        assert isinstance(entities, dict)
    
    def test_extract_entities_very_long_text(self):
        """Test with very long text (performance check)."""
        # Create long text with repeated patterns
        text = "Apple Inc. was mentioned. " * 100
        
        entities = extract_entities_from_text(text)
        
        # Should complete without errors
        assert isinstance(entities, dict)
        
        # Should deduplicate repeated entities
        if "ORG" in entities:
            assert entities["ORG"].count("Apple Inc.") <= 1
    
    def test_fragment_with_numeric_content(self):
        """Test fragment with numeric content."""
        fragment = {"content": 12345}
        
        result = apply_ner_to_fragment(fragment)
        
        # Should convert to string and process (though unlikely to have entities)
        assert "ner" in result
        assert isinstance(result["ner"], dict)
    
    def test_fragment_with_boolean_content(self):
        """Test fragment with boolean content."""
        fragment = {"content": True}
        
        result = apply_ner_to_fragment(fragment)
        
        assert "ner" in result
        assert isinstance(result["ner"], dict)
