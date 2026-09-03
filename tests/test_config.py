from app.config import Settings


def test_cors_star_and_list():
    assert Settings(cors_origins="*").cors_origin_list == ["*"]
    assert Settings(cors_origins="http://a, http://b").cors_origin_list == [
        "http://a",
        "http://b",
    ]
