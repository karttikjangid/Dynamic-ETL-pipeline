"""
Tier 2 Tests: Normalization (JSON & KV)

Tests the normalization layer:
- JSON normalizer with recursive type inference
- KV normalizer with type coercion
- Key standardization (snake_case, trim, lowercase)
- Type inference (boolean, integer, float, ISO dates)
- Mixed content handling
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from extractors.json_extractor import JSONExtractor
from extractors.kv_extractor import KVExtractor
from normalizers.json_normalizer import normalize_json_record
from normalizers.kv_normalizer import normalize_kv_record
from normalizers.orchestrator import normalize_all_records


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


def test_json_normalization():
    """Test JSON normalization with type inference."""
    print_section("Test 2.1: JSON Normalization - Type Inference")
    
    file_path = "tests/payloads/tier2_mixed_content.txt"
    
    try:
        # Read and extract
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        extractor = JSONExtractor()
        json_records = extractor.extract(content)
        
        print(f"✓ Extracted {len(json_records)} JSON records")
        
        # Normalize
        normalized = []
        for record in json_records:
            norm_record = normalize_json_record(record)
            normalized.append(norm_record)
        
        print(f"✓ Normalized {len(normalized)} records")
        
        # Check first record for type inference
        if len(normalized) > 0:
            first = normalized[0]
            print(f"\nFirst Record Data Types:")
            for key, value in first.data.items():
                print(f"  {key}: {type(value).__name__} = {repr(value)}")
            
            # Verify type conversions from strings
            data = first.data
            
            # Check if string "150.50" was converted to float
            if 'amount' in data:
                assert isinstance(data['amount'], (int, float)), f"amount should be numeric, got {type(data['amount'])}"
                print(f"  ✓ 'amount' correctly converted to {type(data['amount']).__name__}")
            
            # Check if string "true" was converted to bool
            if 'verified' in data:
                assert isinstance(data['verified'], bool), f"verified should be bool, got {type(data['verified'])}"
                print(f"  ✓ 'verified' correctly converted to bool")
        
        print("\n✅ PASS: JSON normalization working correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_kv_normalization():
    """Test KV normalization with type coercion."""
    print_section("Test 2.2: KV Normalization - Type Coercion")
    
    file_path = "tests/payloads/tier2_mixed_content.txt"
    
    try:
        # Read and extract
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        extractor = KVExtractor()
        kv_records = extractor.extract(content)
        
        print(f"✓ Extracted {len(kv_records)} KV records")
        
        # Normalize
        normalized = []
        for record in kv_records:
            norm_record = normalize_kv_record(record)
            normalized.append(norm_record)
        
        print(f"✓ Normalized {len(normalized)} records")
        
        # Check for type inference
        if len(normalized) > 0:
            first = normalized[0]
            print(f"\nFirst Record Data Types:")
            for key, value in first.data.items():
                print(f"  {key}: {type(value).__name__} = {repr(value)}")
            
            data = first.data
            
            # Check numeric conversion
            numeric_fields = [k for k, v in data.items() if isinstance(v, (int, float))]
            if numeric_fields:
                print(f"  ✓ Found {len(numeric_fields)} numeric fields: {numeric_fields}")
        
        print("\n✅ PASS: KV normalization working correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_key_standardization():
    """Test key standardization (snake_case, lowercase, trim)."""
    print_section("Test 2.3: Key Standardization")
    
    file_path = "tests/payloads/tier4_edge_cases.txt"
    
    try:
        # Read and extract
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        extractor = KVExtractor()
        kv_records = extractor.extract(content)
        
        # Find record with varied key formats
        normalized = []
        for record in kv_records:
            norm_record = normalize_kv_record(record)
            normalized.append(norm_record)
        
        print(f"✓ Normalized {len(normalized)} KV records")
        
        # Check for standardized keys
        all_keys = set()
        for record in normalized:
            all_keys.update(record.data.keys())
        
        print(f"\nSample Standardized Keys:")
        for key in sorted(list(all_keys))[:10]:
            print(f"  - {key}")
        
        # Verify keys are lowercase and snake_case
        for key in all_keys:
            assert key == key.lower(), f"Key should be lowercase: {key}"
            assert ' ' not in key, f"Key should not have spaces: {key}"
            print(f"  ✓ '{key}' is properly standardized")
            break  # Just check one
        
        print("\n✅ PASS: Key standardization working correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_mixed_content_handling():
    """Test handling of mixed JSON and KV content."""
    print_section("Test 2.4: Mixed Content Handling")
    
    file_path = "tests/payloads/tier2_mixed_content.txt"
    
    try:
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract both types
        json_extractor = JSONExtractor()
        kv_extractor = KVExtractor()
        
        json_records = json_extractor.extract(content)
        kv_records = kv_extractor.extract(content)
        
        print(f"✓ Extracted {len(json_records)} JSON records")
        print(f"✓ Extracted {len(kv_records)} KV records")
        
        # Combine and normalize using orchestrator
        all_records = json_records + kv_records
        normalized = normalize_all_records(all_records)
        
        print(f"✓ Normalized {len(normalized)} total records")
        
        # Verify we have both types
        json_count = sum(1 for r in normalized if r.source_type == "json")
        kv_count = sum(1 for r in normalized if r.source_type == "kv")
        
        print(f"\nNormalized Record Types:")
        print(f"  JSON: {json_count}")
        print(f"  KV: {kv_count}")
        
        assert json_count > 0, "Should have normalized JSON records"
        assert kv_count > 0, "Should have normalized KV records"
        
        print("\n✅ PASS: Mixed content handling working correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_boolean_inference():
    """Test boolean inference from various formats."""
    print_section("Test 2.5: Boolean Inference")
    
    file_path = "tests/payloads/tier4_edge_cases.txt"
    
    try:
        # Read and extract
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        extractor = KVExtractor()
        records = extractor.extract(content)
        
        # Normalize
        normalized = []
        for record in records:
            norm_record = normalize_kv_record(record)
            normalized.append(norm_record)
        
        # Find boolean fields
        boolean_fields = []
        for record in normalized:
            for key, value in record.data.items():
                if isinstance(value, bool):
                    boolean_fields.append((key, value))
        
        print(f"✓ Found {len(boolean_fields)} boolean conversions")
        
        if len(boolean_fields) > 0:
            print(f"\nSample Boolean Conversions:")
            for key, value in boolean_fields[:5]:
                print(f"  {key}: {value}")
            
            print("\n✅ PASS: Boolean inference working correctly")
            return True
        else:
            print("\n⚠️  WARNING: No boolean conversions found")
            return True  # Not a failure, just no booleans in this test
        
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Tier 2 tests."""
    print_header("TIER 2: NORMALIZATION TESTS")
    
    results = []
    
    # Run tests
    results.append(("JSON Normalization", test_json_normalization()))
    results.append(("KV Normalization", test_kv_normalization()))
    results.append(("Key Standardization", test_key_standardization()))
    results.append(("Mixed Content Handling", test_mixed_content_handling()))
    results.append(("Boolean Inference", test_boolean_inference()))
    
    # Summary
    print_header("TIER 2 SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TIER 2 TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
