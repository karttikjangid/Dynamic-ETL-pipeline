"""Quick manual dev test for extractor functionality."""

from extractors.json_extractor import JSONExtractor
from extractors.kv_extractor import KVExtractor

# Sample text containing both JSON and key-value pairs
text = """
title: Widget A
price: 9.99

{ "id": "123", "name": "Sample Item", "details": {"color": "blue"} }
"""

print("=" * 60)
print("Testing JSON Extractor")
print("=" * 60)
json_extractor = JSONExtractor()
json_records = json_extractor.extract(text)
print(f"\nJSON Records Found: {len(json_records)}")
for i, record in enumerate(json_records, 1):
    print(f"\n{i}. {record.source_type.upper()} Record:")
    print(f"   Confidence: {record.confidence}")
    print(f"   Data: {record.data}")

print("\n" + "=" * 60)
print("Testing Key-Value Extractor")
print("=" * 60)
kv_extractor = KVExtractor()
kv_records = kv_extractor.extract(text)
print(f"\nKey-Value Records Found: {len(kv_records)}")
for i, record in enumerate(kv_records, 1):
    print(f"\n{i}. {record.source_type.upper()} Record:")
    print(f"   Confidence: {record.confidence}")
    print(f"   Data: {record.data}")

print("\n" + "=" * 60)
print("Combined Results")
print("=" * 60)
all_records = json_records + kv_records
print(f"\nTotal Records Extracted: {len(all_records)}")
print(f"  - JSON fragments: {len(json_records)}")
print(f"  - KV pairs: {len(kv_records)}")
