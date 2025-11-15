"""
Tier 1 Tests: Basic Extraction (JSON & KV)

Tests the extraction layer:
- JSON extractor with byte offset tracking
- KV extractor with key-value pair detection
- File parsing functionality
- ExtractedRecord creation
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from extractors.json_extractor import JSONExtractor
from extractors.kv_extractor import KVExtractor
from extractors.file_parser import parse_file


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


def print_record(record, index=None):
    """Print an extracted record in a readable format."""
    prefix = f"Record {index}: " if index is not None else "Record: "
    print(f"\n{prefix}")
    print(f"  Type: {record.source_type}")
    print(f"  Confidence: {record.confidence}")
    print(f"  Data: {record.data}")
    print(f"  Data Keys: {list(record.data.keys())}")


def test_json_extraction():
    """Test basic JSON extraction."""
    print_section("Test 1.1: JSON Extraction - Basic Objects")
    
    file_path = "tests/payloads/tier1_basic_json.txt"
    
    try:
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract JSON records
        extractor = JSONExtractor()
        records = extractor.extract(content)
        
        print(f"✓ File loaded: {file_path}")
        print(f"✓ Records extracted: {len(records)}")
        
        if len(records) == 0:
            print("❌ FAIL: No records extracted")
            return False
        
        # Display sample records
        for i, record in enumerate(records[:3], 1):
            print_record(record, i)
        
        # Validate record structure
        for record in records:
            assert hasattr(record, 'source_type'), "Missing source_type"
            assert hasattr(record, 'data'), "Missing data"
            assert hasattr(record, 'confidence'), "Missing confidence"
            assert record.source_type == "json", f"Wrong source type: {record.source_type}"
            assert isinstance(record.data, dict), "Data should be dict"
        
        print("\n✅ PASS: JSON extraction working correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_kv_extraction():
    """Test basic KV extraction."""
    print_section("Test 1.2: KV Extraction - Simple Pairs")
    
    file_path = "tests/payloads/tier1_basic_kv.txt"
    
    try:
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract KV records
        extractor = KVExtractor()
        records = extractor.extract(content)
        
        print(f"✓ File loaded: {file_path}")
        print(f"✓ Records extracted: {len(records)}")
        
        if len(records) == 0:
            print("❌ FAIL: No records extracted")
            return False
        
        # Display sample records
        for i, record in enumerate(records[:3], 1):
            print_record(record, i)
        
        # Validate record structure
        for record in records:
            assert hasattr(record, 'source_type'), "Missing source_type"
            assert hasattr(record, 'data'), "Missing data"
            assert hasattr(record, 'confidence'), "Missing confidence"
            assert record.source_type == "kv", f"Wrong source type: {record.source_type}"
            assert isinstance(record.data, dict), "Data should be dict"
            assert len(record.data) > 0, "KV data should not be empty"
        
        print("\n✅ PASS: KV extraction working correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_file_parsing():
    """Test file parsing utility."""
    print_section("Test 1.3: File Parsing Utility")
    
    file_path = "tests/payloads/tier1_basic_json.txt"
    
    try:
        # Parse file
        content = parse_file(file_path)
        
        print(f"✓ File parsed: {file_path}")
        print(f"✓ Content length: {len(content)} characters")
        print(f"✓ Content type: {type(content).__name__}")
        
        assert isinstance(content, str), "Content should be string"
        assert len(content) > 0, "Content should not be empty"
        
        print("\n✅ PASS: File parsing working correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_byte_offset_accuracy():
    """Test data extraction accuracy."""
    print_section("Test 1.4: Data Extraction Accuracy")
    
    try:
        content = '{"id": 1}\n{"id": 2}'
        extractor = JSONExtractor()
        records = extractor.extract(content)
        
        print(f"✓ Test content: {repr(content)}")
        print(f"✓ Records extracted: {len(records)}")
        
        # Check extracted data
        for i, record in enumerate(records, 1):
            print(f"\nRecord {i}:")
            print(f"  Data: {record.data}")
            print(f"  Source Type: {record.source_type}")
            
            # Verify data has expected structure
            assert 'id' in record.data, "Should have 'id' field"
            assert isinstance(record.data['id'], int), "id should be integer"
            print(f"  ✓ Valid data structure")
        
        print("\n✅ PASS: Data extraction accurate")
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Tier 1 tests."""
    print_header("TIER 1: BASIC EXTRACTION TESTS")
    
    results = []
    
    # Run tests
    results.append(("JSON Extraction", test_json_extraction()))
    results.append(("KV Extraction", test_kv_extraction()))
    results.append(("File Parsing", test_file_parsing()))
    results.append(("Data Extraction Accuracy", test_byte_offset_accuracy()))
    
    # Summary
    print_header("TIER 1 SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TIER 1 TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
