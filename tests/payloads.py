"""
Complete Test Payload Dictionary - Real, Fully-Specified, Non-Hallucinated

All payloads are raw text strings that can be directly used for testing.
No fictional APIs, no magical fields, no hidden assumptions.
"""

TEST_PAYLOADS = {
    "test_case_1_simple_valid_json": """{
  "user_id": 1001,
  "username": "alice_wonder",
  "email": "alice@example.com",
  "active": true,
  "balance": 1250.50,
  "signup_date": "2024-01-15"
}

{
  "user_id": 1002,
  "username": "bob_smith",
  "email": "bob@example.com",
  "active": false,
  "balance": 0,
  "signup_date": "2024-02-20"
}""",

    "test_case_2_broken_json_missing_braces": """{
  "product_id": "PROD-001",
  "name": "Laptop",
  "price": 999.99
  "in_stock": true

{
  "product_id": "PROD-002",
  "name": "Mouse"
  "price": 29.99,
  "in_stock": false
}""",

    "test_case_3_nested_json_objects_and_arrays": """{
  "order_id": "ORD-5001",
  "customer": {
    "id": 123,
    "name": "Charlie Brown",
    "address": {
      "street": "123 Main St",
      "city": "New York",
      "zip": "10001",
      "coordinates": {
        "lat": 40.7128,
        "lng": -74.0060
      }
    }
  },
  "items": [
    {"sku": "ITEM-001", "qty": 2, "price": 50.00},
    {"sku": "ITEM-002", "qty": 1, "price": 150.00},
    {"sku": "ITEM-003", "qty": 5, "price": 10.00}
  ],
  "total": 300.00,
  "tags": ["express", "gift", "priority"]
}""",

    "test_case_4_simple_kv_pairs": """user_id: 12345
username: john_doe
email: john@example.com
role: administrator
last_login: 2024-11-15
active: true

server_name: prod-web-01
ip_address: 192.168.1.100
port: 8080
protocol: HTTPS
status: running""",

    "test_case_5_nested_like_kv_dotted_keys": """user.id: 9876
user.name: Jane Smith
user.email: jane@example.com
user.profile.age: 28
user.profile.city: San Francisco
user.settings.theme: dark
user.settings.notifications: enabled

product.sku: SKU-789
product.name: Wireless Headphones
product.price: 79.99
product.category.main: Electronics
product.category.sub: Audio""",

    "test_case_6_inconsistent_kv_formatting": """Name:Alice Johnson
Email :alice@test.com
Age: 28
City:New York
Status : active
Balance:1500.50
Member-Since: 2023-01-15
Premium:YES
Verified : true
Phone:+1-555-1234""",

    "test_case_7_mixed_json_and_kv_same_file": """{
  "transaction_id": "TXN-2024-5500",
  "amount": 150.50,
  "currency": "USD",
  "timestamp": "2024-11-15T10:30:00"
}

payment_method: credit_card
merchant_id: 98765
customer_id: 44556
processing_time: 1.5
retry_count: 0
status: completed

{
  "session_id": "SESS-ABC-123",
  "duration_seconds": 3600,
  "pages_viewed": 15
}

device_type: mobile
browser: Chrome
os: Android
country: US""",

    "test_case_8_markdown_lists_and_headers": """## User Profile Data

- Name: David Wilson
- Email: david@example.com
- Age: 35
- Premium: true

### Recent Orders

1. Order ID: ORD-001
2. Order ID: ORD-002
3. Order ID: ORD-003

## Configuration

* Server: prod-db-01
* Port: 5432
* Database: main_db
* SSL: enabled

Some random text here that should be ignored.
This is just noise in the document.

## Payment Info

- Card Type: Visa
- Last 4: 1234
- Expiry: 12/25""",

    "test_case_9_table_like_text": """| user_id | username | email | status |
|---------|----------|-------|--------|
| 1001 | alice | alice@test.com | active |
| 1002 | bob | bob@test.com | inactive |
| 1003 | charlie | charlie@test.com | active |

Some text between tables.

Product | Price | Stock
--------|-------|------
Laptop  | 999   | 50
Mouse   | 29    | 200
Keyboard| 79    | 150""",

    "test_case_10_random_noise_irrelevant_sentences": """This is a document with lots of random text.
Lorem ipsum dolor sit amet, consectetur adipiscing elit.

user_id: 7890
username: test_user
email: test@example.com

Here is some more random noise that should be ignored.
The quick brown fox jumps over the lazy dog.
1234567890 !@#$%^&*()

status: active
balance: 500.75

More irrelevant content here.
This should not be extracted as structured data.

last_login: 2024-11-15""",

    "test_case_11_html_snippet_inside_text": """<div class="user-profile">
  <h1>User Profile</h1>
  <p>Name: Emma Thompson</p>
  <p>Email: emma@example.com</p>
</div>

user_id: 5555
username: emma_t
status: active

<table>
  <tr>
    <td>Product</td>
    <td>Price</td>
  </tr>
  <tr>
    <td>Widget</td>
    <td>$49.99</td>
  </tr>
</table>

balance: 1200.00
verified: true""",

    "test_case_12_csv_snippet_inside_text": """id,name,email,age,city
1001,Alice,alice@test.com,28,NYC
1002,Bob,bob@test.com,35,LA
1003,Charlie,charlie@test.com,42,Chicago

Some text after CSV.

user_id: 2001
username: data_user
email: data@example.com

product_id,name,price,stock
PROD-001,Laptop,999.99,50
PROD-002,Mouse,29.99,200""",

    "test_case_13_duplicate_fields_different_formats": """user_id: 1111
userId: 2222
USER_ID: 3333
User-Id: 4444

name: John
Name: Jane
NAME: Jack

email: john@test.com
Email: jane@test.com
e-mail: jack@test.com

status: active
Status: inactive
STATUS: pending""",

    "test_case_14_number_like_strings": """{
  "id": "00045",
  "code": "12",
  "reference": "09",
  "amount": "12.00",
  "quantity": "12,000",
  "pi": "3.1415926535",
  "zero_padded": "00000123",
  "scientific": "1.23e10",
  "negative": "-999.99"
}

order_number: 00456
invoice_id: 12345
zip_code: 09876
price: 1,234.56
discount: 0.15""",

    "test_case_15_booleans_and_boolean_like_strings": """{
  "flag1": "true",
  "flag2": "TRUE",
  "flag3": "True",
  "flag4": "false",
  "flag5": "FALSE",
  "flag6": "False",
  "flag7": "yes",
  "flag8": "YES",
  "flag9": "no",
  "flag10": "NO"
}

active: yes
enabled: YES
verified: true
premium: TRUE
disabled: no
inactive: NO
blocked: false
suspended: FALSE""",

    "test_case_16_null_like_strings": """{
  "field1": "null",
  "field2": "NULL",
  "field3": "none",
  "field4": "None",
  "field5": "NONE",
  "field6": "N/A",
  "field7": "n/a",
  "field8": "-",
  "field9": "",
  "field10": null
}

status: null
value: NULL
description: none
comment: N/A
notes: -
data: n/a""",

    "test_case_17_date_formats_iso_and_near_date": """{
  "date1": "2024-01-05",
  "date2": "2024-01-05T08:30:00",
  "date3": "2024-01-05T08:30:45.123",
  "date4": "2024/01/05",
  "date5": "01/05/2024",
  "date6": "Jan 5, 2024",
  "date7": "January 5, 2024",
  "date8": "05-Jan-2024",
  "date9": "2024-W01-5",
  "date10": "20240105"
}

signup_date: 2024-11-15
birth_date: 1990/05/20
last_login: 2024-11-15T10:30:00
created_at: Jan 15, 2024
updated_at: 2024-01-05T08:30:45.123456""",

    "test_case_18_arrays_with_mixed_types": """{
  "mixed_array": [1, "2", true, null, 3.14, "text", false],
  "number_array": [1, 2, 3, 4, 5],
  "string_array": ["a", "b", "c"],
  "boolean_array": [true, false, true],
  "null_array": [null, null, null],
  "nested_array": [[1, 2], [3, 4], [5, 6]],
  "object_array": [
    {"id": 1, "name": "First"},
    {"id": 2, "name": "Second"},
    {"id": 3, "name": "Third"}
  ]
}""",

    "test_case_19_extremely_large_array_simulation": """{
  "user_id": 9999,
  "username": "bulk_user",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8", "tag9", "tag10", "tag11", "tag12", "tag13", "tag14", "tag15", "tag16", "tag17", "tag18", "tag19", "tag20"],
  "scores": [100, 95, 92, 88, 85, 82, 79, 76, 73, 70, 68, 65, 62, 59, 56, 53, 50, 47, 44, 41, 38, 35, 32, 29, 26, 23, 20],
  "note": "This simulates a large array without generating huge payload"
}""",

    "test_case_20_deeply_nested_structures": """{
  "level1": {
    "id": 1,
    "level2": {
      "id": 2,
      "level3": {
        "id": 3,
        "level4": {
          "id": 4,
          "data": "deepest level",
          "value": 42
        },
        "metadata": {
          "created": "2024-01-01",
          "modified": "2024-11-15"
        }
      },
      "tags": ["deep", "nested", "structure"]
    },
    "info": "second level info"
  },
  "root_field": "root value"
}""",

    "test_case_21_embedded_code_block_fences": """Here is some text before the code block.

```json
{
  "user_id": 8888,
  "username": "code_block_user",
  "email": "code@example.com"
}
```

Some text between code blocks.

```python
user_id = 9999
username = "python_user"
email = "python@example.com"
```

More text after code blocks.

actual_field: actual_value
real_data: this is real""",

    "test_case_22_html_tags_and_entities": """<div id="container">
  <h1>Product Catalog</h1>
  <ul>
    <li>Product 1: $99.99</li>
    <li>Product 2: $49.99</li>
  </ul>
</div>

product_id: HTML-001
name: Widget &amp; Gadget
price: 99.99
description: A &lt;great&gt; product

<script>
var userId = 12345;
var userName = "test_user";
</script>

status: active
verified: true""",

    "test_case_23_csv_with_commas_in_values": """id,name,description,price,status
1001,"Laptop Pro","High-end laptop, 16GB RAM",1299.99,active
1002,"Mouse","Wireless mouse, ergonomic",29.99,active
1003,"Keyboard","Mechanical, RGB, "gaming"",79.99,discontinued

user_id: CSV-001
product_count: 3
total_value: 1409.97""",

    "test_case_24_unicode_symbols_and_special_chars": """{
  "currency_symbol": "₹",
  "euro": "€",
  "pound": "£",
  "yen": "¥",
  "em_dash": "—",
  "trademark": "™",
  "copyright": "©",
  "registered": "®",
  "degree": "45°C",
  "bullet": "•",
  "name": "François Müller",
  "city": "São Paulo",
  "message": "Hello 👋 World 🌍",
  "language": "日本語"
}

price: ₹1,999
temperature: 25°C
company: Tech™ Solutions
address: São Paulo, Brazil""",

    "test_case_25_all_edge_cases_combined": """## Mixed Content Document

{
  "user_id": "00123",
  "username": "edge_case_user",
  "email": "edge@example.com",
  "balance": "1,234.56",
  "active": "yes",
  "verified": null,
  "signup_date": "2024-01-15T10:30:00"
}

Name: Test User
Email:test@example.com
Status : active
Balance:500.75
Verified: TRUE
Last-Login: 2024/11/15

Random noise text here.
Lorem ipsum dolor sit amet.

```json
{"embedded": "code block"}
```

| id | name | value |
|----|------|-------|
| 1 | A | 100 |
| 2 | B | 200 |

<div>HTML content</div>

id,name,value
3,C,300
4,D,400

price: ₹999
temperature: 25°C
message: Hello 👋

nested.field.one: value1
nested.field.two: value2

MORE_NOISE_TEXT_TO_IGNORE
12345 !@#$%^&*()

final_field: final_value
end_marker: true"""
}

if __name__ == "__main__":
    # Verify all payloads
    print(f"Total test payloads: {len(TEST_PAYLOADS)}")
    for name, payload in TEST_PAYLOADS.items():
        lines = payload.count('\n') + 1
        chars = len(payload)
        print(f"  {name}: {lines} lines, {chars} chars")
