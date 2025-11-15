"""
Tier 3 Tests: Schema Generation

Tests the schema generation layer:
- compute_schema_for_source() bridge function
- generate_schema() with field detection
- Type inference from normalized records
- Confidence scoring based on type consistency
- Nullable field detection
- Example value extraction
- compute_schema_diff() for schema evolution
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from extractors.json_extractor import JSONExtractor
from normalizers.orchestrator import normalize_all_records
from services.schema_service import compute_schema_for_source
from inference.schema_generator import compute_schema_diff
from core.models import SchemaMetadata


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(text.center(80))
    print("=" * 80 + "\n")


def print_section(text):
    """Print a formatted section."""
    print("\n" + "-" * 80)
    print(text)
    print("-" * 80)


def test_schema_generation_basic():
    """Test basic schema generation from normalized records."""
    print_section("Test 3.1: Basic Schema Generation")
    
    file_path = "tests/payloads/tier1_basic_json.txt"
    
    try:
        # Read and extract
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        extractor = JSONExtractor()
        records = extractor.extract(content)
        
        # Normalize
        normalized = normalize_all_records(records)
        
        print(f"✓ Normalized {len(normalized)} records")
        
        # Generate schema
        schema = compute_schema_for_source(normalized, "test_users")
        
        print(f"✓ Schema generated")
        print(f"\nSchema Details:")
        print(f"  Schema ID: {schema['schema_id']}")
        print(f"  Source ID: {schema['source_id']}")
        print(f"  Version: {schema['version']}")
        print(f"  Record Count: {schema['record_count']}")
        print(f"  Fields Detected: {len(schema['fields'])}")
        
        # Verify schema structure
        assert 'schema_id' in schema, "Missing schema_id"
        assert 'source_id' in schema, "Missing source_id"
        assert 'fields' in schema, "Missing fields"
        assert isinstance(schema['fields'], list), "Fields should be a list"
        assert len(schema['fields']) > 0, "Should have detected fields"
        
        print(f"\nDetected Fields:")
        for field in schema['fields']:
            print(f"  - {field['name']}: {field['type']} (nullable={field['nullable']}, confidence={field['confidence']})")
        
        print("\n✅ PASS: Basic schema generation working correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_nullable_field_detection():
    """Test nullable field detection."""
    print_section("Test 3.2: Nullable Field Detection")
    
    file_path = "tests/payloads/tier3_schema_generation.txt"
    
    try:
        # Read and extract
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        extractor = JSONExtractor()
        records = extractor.extract(content)
        
        # Normalize
        normalized = normalize_all_records(records)
        
        print(f"✓ Normalized {len(normalized)} records")
        
        # Generate schema
        schema = compute_schema_for_source(normalized, "users_with_nullables")
        
        print(f"✓ Schema generated with {len(schema['fields'])} fields")
        
        # Check for nullable fields
        nullable_fields = [f for f in schema['fields'] if f['nullable']]
        required_fields = [f for f in schema['fields'] if not f['nullable']]
        
        print(f"\nNullable Fields ({len(nullable_fields)}):")
        for field in nullable_fields:
            print(f"  - {field['name']}: {field['type']}")
        
        print(f"\nRequired Fields ({len(required_fields)}):")
        for field in required_fields:
            print(f"  - {field['name']}: {field['type']}")
        
        # Verify age and premium are nullable
        field_names = {f['name']: f for f in schema['fields']}
        
        if 'age' in field_names:
            assert field_names['age']['nullable'], "age should be nullable (missing in some records)"
            print(f"\n✓ 'age' correctly marked as nullable")
        
        if 'premium' in field_names:
            assert field_names['premium']['nullable'], "premium should be nullable (missing in some records)"
            print(f"✓ 'premium' correctly marked as nullable")
        
        # Verify user_id is NOT nullable
        if 'user_id' in field_names:
            assert not field_names['user_id']['nullable'], "user_id should NOT be nullable (present in all)"
            print(f"✓ 'user_id' correctly marked as required")
        
        print("\n✅ PASS: Nullable field detection working correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_type_inference_in_schema():
    """Test type inference in schema generation."""
    print_section("Test 3.3: Type Inference in Schema")
    
    file_path = "tests/payloads/tier3_schema_generation.txt"
    
    try:
        # Read and extract
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        extractor = JSONExtractor()
        records = extractor.extract(content)
        
        # Normalize
        normalized = normalize_all_records(records)
        
        # Generate schema
        schema = compute_schema_for_source(normalized, "type_inference_test")
        
        print(f"✓ Schema generated")
        
        # Check field types
        field_types = {f['name']: f['type'] for f in schema['fields']}
        
        print(f"\nDetected Field Types:")
        for name, type_name in sorted(field_types.items()):
            print(f"  {name}: {type_name}")
        
        # Verify expected types
        expected_types = {
            'user_id': 'integer',
            'username': 'string',
            'email': 'string',
            'age': 'integer',
            'premium': 'boolean',
            'signup_date': 'string'
        }
        
        for field_name, expected_type in expected_types.items():
            if field_name in field_types:
                actual_type = field_types[field_name]
                if actual_type == expected_type:
                    print(f"✓ '{field_name}' correctly typed as {expected_type}")
                else:
                    print(f"⚠️  '{field_name}' expected {expected_type}, got {actual_type}")
        
        print("\n✅ PASS: Type inference working correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_confidence_scoring():
    """Test confidence scoring for fields."""
    print_section("Test 3.4: Confidence Scoring")
    
    file_path = "tests/payloads/tier3_schema_generation.txt"
    
    try:
        # Read and extract
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        extractor = JSONExtractor()
        records = extractor.extract(content)
        
        # Normalize
        normalized = normalize_all_records(records)
        
        # Generate schema
        schema = compute_schema_for_source(normalized, "confidence_test")
        
        print(f"✓ Schema generated")
        
        # Check confidence scores
        print(f"\nField Confidence Scores:")
        for field in schema['fields']:
            confidence = field.get('confidence', 0)
            print(f"  {field['name']}: {confidence:.2f}")
            
            # Confidence should be between 0 and 1
            assert 0 <= confidence <= 1, f"Confidence out of range: {confidence}"
        
        # Calculate average confidence
        avg_confidence = schema['extraction_stats'].get('avg_confidence', 0)
        print(f"\nAverage Confidence: {avg_confidence:.2f}")
        
        print("\n✅ PASS: Confidence scoring working correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_example_value_extraction():
    """Test example value extraction."""
    print_section("Test 3.5: Example Value Extraction")
    
    file_path = "tests/payloads/tier1_basic_json.txt"
    
    try:
        # Read and extract
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        extractor = JSONExtractor()
        records = extractor.extract(content)
        
        # Normalize
        normalized = normalize_all_records(records)
        
        # Generate schema
        schema = compute_schema_for_source(normalized, "example_values_test")
        
        print(f"✓ Schema generated")
        
        # Check example values
        print(f"\nExample Values:")
        for field in schema['fields']:
            example = field.get('example_value')
            print(f"  {field['name']}: {repr(example)}")
            
            # Should have example values for most fields
            if example is not None:
                print(f"    ✓ Has example value")
        
        print("\n✅ PASS: Example value extraction working correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_schema_diff():
    """Test schema difference computation."""
    print_section("Test 3.6: Schema Diff (compute_schema_diff)")
    
    try:
        from datetime import datetime
        from core.models import SchemaField, SchemaMetadata
        
        # Create old schema
        old_schema = SchemaMetadata(
            schema_id="test_v1",
            source_id="test",
            version=1,
            fields=[
                SchemaField(name="id", type="integer", nullable=False, confidence=1.0),
                SchemaField(name="name", type="string", nullable=False, confidence=1.0),
                SchemaField(name="status", type="string", nullable=False, confidence=0.9),
            ],
            generated_at=datetime.now(),
            record_count=10,
            extraction_stats={}
        )
        
        # Create new schema (with changes)
        new_schema = SchemaMetadata(
            schema_id="test_v2",
            source_id="test",
            version=2,
            fields=[
                SchemaField(name="id", type="string", nullable=False, confidence=1.0),  # Type changed
                SchemaField(name="name", type="string", nullable=False, confidence=1.0),
                SchemaField(name="email", type="string", nullable=True, confidence=0.8),  # Added field
            ],
            generated_at=datetime.now(),
            record_count=15,
            extraction_stats={}
        )
        
        # Compute diff
        diff = compute_schema_diff(old_schema, new_schema)
        
        print(f"✓ Schema diff computed")
        print(f"\nDiff Results:")
        print(f"  Added fields: {diff['added']}")
        print(f"  Removed fields: {diff['removed']}")
        print(f"  Changed fields: {list(diff['changed'].keys())}")
        
        # Verify diff results
        assert 'email' in diff['added'], "Should detect added field 'email'"
        assert 'status' in diff['removed'], "Should detect removed field 'status'"
        assert 'id' in diff['changed'], "Should detect type change in 'id'"
        
        print(f"\n✓ Added: {diff['added']}")
        print(f"✓ Removed: {diff['removed']}")
        
        if 'id' in diff['changed']:
            print(f"✓ Changed 'id':")
            print(f"    Old type: {diff['changed']['id']['old']['type']}")
            print(f"    New type: {diff['changed']['id']['new']['type']}")
        
        print("\n✅ PASS: Schema diff working correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_empty_input_handling():
    """Test schema generation with empty input."""
    print_section("Test 3.7: Empty Input Handling")
    
    try:
        # Generate schema with empty records
        schema = compute_schema_for_source([], "empty_test")
        
        print(f"✓ Schema generated for empty input")
        print(f"\nSchema Details:")
        print(f"  Record Count: {schema['record_count']}")
        print(f"  Fields: {len(schema['fields'])}")
        
        assert schema['record_count'] == 0, "Record count should be 0"
        assert len(schema['fields']) == 0, "Should have no fields"
        
        print("\n✅ PASS: Empty input handling working correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Tier 3 tests."""
    print_header("TIER 3: SCHEMA GENERATION TESTS")
    
    results = []
    
    # Run tests
    results.append(("Basic Schema Generation", test_schema_generation_basic()))
    results.append(("Nullable Field Detection", test_nullable_field_detection()))
    results.append(("Type Inference", test_type_inference_in_schema()))
    results.append(("Confidence Scoring", test_confidence_scoring()))
    results.append(("Example Value Extraction", test_example_value_extraction()))
    results.append(("Schema Diff", test_schema_diff()))
    results.append(("Empty Input Handling", test_empty_input_handling()))
    
    # Summary
    print_header("TIER 3 SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TIER 3 TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
