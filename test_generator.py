from modules.generator import is_valid_label, generate_urls

def test_generator():
    print("🧪 Testing Generator Strictness...")
    
    # Test 1: Valid Labels
    valid_labels = ["example", "test-site", "site123", "a", "1", "a-b"]
    for l in valid_labels:
        assert is_valid_label(l), f"❌ Should be valid: {l}"
    print("✅ Valid labels passed.")

    # Test 2: Invalid Labels
    invalid_labels = [
        "-start", "end-", "double..dot", "space in", "under_score", 
        "!", "@", "toolong" * 10, ""
    ]
    for l in invalid_labels:
        assert not is_valid_label(l), f"❌ Should be invalid: {l}"
    print("✅ Invalid labels passed.")

    # Test 3: Generation
    print("\n🧪 Testing Generation...")
    domains = ["com", "net"]
    words = ["test", "demo"]
    urls = generate_urls(5, domains, words)
    print(f"Generated {len(urls)} URLs:")
    for u in urls:
        print(f"  - {u}")
        assert u.startswith("https://"), "Invalid protocol"
        assert "." in u, "Invalid format"

if __name__ == "__main__":
    test_generator()
