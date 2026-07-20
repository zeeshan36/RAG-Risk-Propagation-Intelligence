"""Tests for the in-memory repository."""
import pytest

from common.exceptions import RepositoryError
from data_ingestion.batch.loaders import load_records
from data_ingestion.batch.simple_repository import SimpleRepository
from models.domain import Customer, Supplier


def test_upsert_and_get():
    repo = SimpleRepository()
    supplier = Supplier(id="S1", name="Acme", country="US", criticality_score=0.5)
    repo.upsert(supplier)
    fetched = repo.get(Supplier, "S1")
    assert fetched.name == "Acme"


def test_get_missing_raises():
    repo = SimpleRepository()
    with pytest.raises(RepositoryError):
        repo.get(Supplier, "missing")


def test_load_many_and_count():
    repo = SimpleRepository()
    records = [
        {"id": "S1", "name": "A", "country": "US", "criticality_score": 0.1},
        {"id": "S2", "name": "B", "country": "CA", "criticality_score": 0.2},
    ]
    suppliers = load_records(records, Supplier)
    repo.load_many(suppliers)
    assert repo.count(Supplier) == 2
    assert repo.type_count() == 1


def test_find_and_delete():
    repo = SimpleRepository()
    repo.load_many([
        Customer(id="C1", name="A", region_id="R1", criticality_score=0.1),
        Customer(id="C2", name="B", region_id="R2", criticality_score=0.2),
    ])
    found = repo.find(Customer, lambda c: c.region_id == "R1")
    assert len(found) == 1
    assert repo.delete(Customer, "C1") is True
    assert repo.count(Customer) == 1
