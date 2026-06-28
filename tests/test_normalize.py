from api_warehouse.normalize import to_snake_case, normalize_record_keys

def test_to_snake_case_camel():
    assert to_snake_case("userId") == "user_id"
    assert to_snake_case("firstName") == "first_name"
    assert to_snake_case("addressLine1") == "address_line1"
    assert to_snake_case("ID") == "id"
    assert to_snake_case("id") == "id"

def test_normalize_record_keys():
    out = normalize_record_keys([{"userId": 1, "title": "x"}])
    assert out == [{"user_id": 1, "title": "x"}]
