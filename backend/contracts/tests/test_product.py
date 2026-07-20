import json
import pytest

from contracts.product import ProductCondition, ProductRecord, ProductSource


VALID_PAYLOAD = {
    "id": "prod-001",
    "source": "ebay",
    "source_record_id": "ebay-12345",
    "title": "Nike Air Max 90 — taille 42",
    "brand": "Nike",
    "model": "Air Max 90",
    "price": 79.99,
    "currency": "EUR",
    "condition": "good",
    "size_raw": "42",
    "size_eu": "42",
    "category": "sneakers",
    "image_urls": ["https://img.example.com/1.jpg", "https://img.example.com/2.jpg"],
    "affiliate_url": "https://rover.ebay.com/rover/1/...",
    "available": True,
}


def make_record(**overrides) -> ProductRecord:
    return ProductRecord(**{**VALID_PAYLOAD, **overrides})


class TestProductRecordSchema:
    def test_valid_record_creates_successfully(self):
        record = make_record()
        assert record.id == "prod-001"
        assert record.source == ProductSource.ebay
        assert record.condition == ProductCondition.good
        assert record.schema_version == 1

    def test_serialization_roundtrip_no_loss(self):
        record = make_record()
        json_str = record.model_dump_json()
        restored = ProductRecord.model_validate_json(json_str)
        assert restored == record

    def test_dict_roundtrip_no_loss(self):
        record = make_record()
        as_dict = record.model_dump()
        restored = ProductRecord.model_validate(as_dict)
        assert restored == record

    def test_json_is_valid_json(self):
        record = make_record()
        parsed = json.loads(record.model_dump_json())
        assert parsed["id"] == "prod-001"
        assert parsed["schema_version"] == 1

    def test_price_must_be_positive(self):
        with pytest.raises(Exception):
            make_record(price=0)
        with pytest.raises(Exception):
            make_record(price=-5.0)

    def test_image_urls_must_not_be_empty(self):
        with pytest.raises(Exception):
            make_record(image_urls=[])

    def test_optional_fields_default_to_none(self):
        record = make_record(brand=None, model=None, size_raw=None,
                             size_eu=None, affiliate_url=None,
                             embedding_version=None)
        assert record.brand is None
        assert record.embedding_version is None

    def test_available_defaults_to_true(self):
        record = make_record()
        assert record.available is True

    def test_currency_defaults_to_eur(self):
        record = make_record()
        assert record.currency == "EUR"

    def test_schema_version_is_1(self):
        record = make_record()
        assert record.schema_version == 1

    def test_condition_enum_values(self):
        for cond in ("new", "like_new", "good", "fair"):
            record = make_record(condition=cond)
            assert record.condition == ProductCondition(cond)

    def test_source_enum_values(self):
        for src in ("ebay", "awin", "cj"):
            record = make_record(source=src)
            assert record.source == ProductSource(src)
