import pytest
from shop.db import DatabaseClient


def test_find_user_normal():
    client = DatabaseClient()
    results = client.find_user_by_name("alice")
    assert len(results) == 1
    assert results[0][1] == "alice"


def test_find_user_missing():
    client = DatabaseClient()
    results = client.find_user_by_name("bob")
    assert len(results) == 0


def test_find_user_safe():
    client = DatabaseClient()
    results = client.find_user_safely("alice")
    assert len(results) == 1

