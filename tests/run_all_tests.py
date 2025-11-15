"""
Master Test Runner - Runs all test tiers sequentially

This script runs all test tiers in order:
- Tier 1: Basic Extraction
- Tier 2: Normalization
- Tier 3: Schema Generation

Each tier must pass before proceeding to the next tier.
"""

import sys
import os
import subprocess

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(text.center(80))
    print("=" * 80 + "\n")


def run_test_tier(tier_name, script_name):
    """Run a test tier script."""
    print_header(f"RUNNING {tier_name}")
    
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    
    try:
        # Run the test script
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=False,
            text=True
        )
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running {tier_name}: {str(e)}")
        return False


def main():
    """Run all test tiers."""
    print_header("DYNAMIC ETL PIPELINE - COMPREHENSIVE TEST SUITE")
    
    print("This test suite validates all implemented features:")
    print("  ✓ Extraction (JSON & KV)")
    print("  ✓ Normalization (Type inference, key standardization)")
    print("  ✓ Schema Generation (Field detection, confidence scoring)")
    print("")
    
    results = []
    
    # Tier 1: Extraction
    tier1_passed = run_test_tier("TIER 1: EXTRACTION", "run_tier1_extraction.py")
    results.append(("Tier 1: Extraction", tier1_passed))
    
    if not tier1_passed:
        print("\n⚠️  Tier 1 failed. Stopping tests.")
        print_summary(results)
        return 1
    
    # Tier 2: Normalization
    tier2_passed = run_test_tier("TIER 2: NORMALIZATION", "run_tier2_normalization.py")
    results.append(("Tier 2: Normalization", tier2_passed))
    
    if not tier2_passed:
        print("\n⚠️  Tier 2 failed. Stopping tests.")
        print_summary(results)
        return 1
    
    # Tier 3: Schema Generation
    tier3_passed = run_test_tier("TIER 3: SCHEMA GENERATION", "run_tier3_schema_generation.py")
    results.append(("Tier 3: Schema Generation", tier3_passed))
    
    # Final summary
    print_summary(results)
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n" + "🎉" * 20)
        print("ALL TESTS PASSED!".center(80))
        print("🎉" * 20)
        return 0
    else:
        return 1


def print_summary(results):
    """Print final summary."""
    print_header("FINAL SUMMARY")
    
    for tier_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{tier_name}: {status}")
    
    passed_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    print(f"\nTiers Passed: {passed_count}/{total_count}")
    print(f"Success Rate: {(passed_count/total_count)*100:.1f}%")


if __name__ == "__main__":
    sys.exit(main())
