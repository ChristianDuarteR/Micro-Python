from app.config import Settings


def test_cors_star_and_list():
    assert Settings(cors_origins="*").cors_origin_list == ["*"]
    assert Settings(cors_origins="http://a, http://b").cors_origin_list == [
        "http://a",
        "http://b",
    ]


def test_cors_defaults_to_deployed_clients():
    assert Settings().cors_origin_list == [
        "https://global-invoice-virid.vercel.app",
        "https://micro-java-core.onrender.com",
    ]
