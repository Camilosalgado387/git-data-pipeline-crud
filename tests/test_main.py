import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from app import database
from app.main import app


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch):
    """
    Sets up an isolated SQLite database for each test and tears it down afterwards.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        test_db_path = tmp.name

    monkeypatch.setattr(database, "DEFAULT_DB_PATH", test_db_path)
    database.init_db(test_db_path)

    yield test_db_path

    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except OSError:
            pass


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "Data Pipeline & Dataset Catalog API"
    assert data["status"] == "healthy"


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_get_dataset(client):
    payload = {
        "name": "customer_churn_features",
        "source": "s3://lakehouse/features/churn.parquet",
        "format": "parquet",
        "row_count": 50000,
        "schema_version": "v1.2",
        "status": "active",
        "owner": "camilo@data-eng.io",
    }
    # Create dataset
    post_res = client.post("/datasets", json=payload)
    assert post_res.status_code == 201
    created = post_res.json()
    assert created["id"] is not None
    assert created["name"] == payload["name"]
    assert created["source"] == payload["source"]
    assert created["row_count"] == 50000

    dataset_id = created["id"]

    # Retrieve dataset
    get_res = client.get(f"/datasets/{dataset_id}")
    assert get_res.status_code == 200
    fetched = get_res.json()
    assert fetched["id"] == dataset_id
    assert fetched["owner"] == payload["owner"]


def test_get_dataset_not_found(client):
    response = client.get("/datasets/999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_validation_error_on_create(client):
    # Missing required 'name', 'source', 'owner'
    invalid_payload = {"format": "parquet", "row_count": -5}
    response = client.post("/datasets", json=invalid_payload)
    assert response.status_code == 422


def test_list_datasets(client):
    for i in range(3):
        client.post(
            "/datasets",
            json={
                "name": f"dataset_{i}",
                "source": f"db://warehouse/table_{i}",
                "owner": "team@data.io",
            },
        )

    response = client.get("/datasets?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_update_dataset(client):
    created = client.post(
        "/datasets",
        json={
            "name": "raw_events",
            "source": "kafka://events-topic",
            "owner": "ingestion-team",
        },
    ).json()

    dataset_id = created["id"]

    update_payload = {"row_count": 120000, "status": "deprecated"}
    put_res = client.put(f"/datasets/{dataset_id}", json=update_payload)
    assert put_res.status_code == 200
    updated = put_res.json()
    assert updated["row_count"] == 120000
    assert updated["status"] == "deprecated"
    assert updated["name"] == "raw_events"


def test_delete_dataset(client):
    created = client.post(
        "/datasets",
        json={
            "name": "temp_staging_table",
            "source": "staging://raw/temp",
            "owner": "etl-runner",
        },
    ).json()

    dataset_id = created["id"]

    # Delete
    del_res = client.delete(f"/datasets/{dataset_id}")
    assert del_res.status_code == 200

    # Ensure it no longer exists
    get_res = client.get(f"/datasets/{dataset_id}")
    assert get_res.status_code == 404


def test_pipeline_runs_lifecycle(client):
    created = client.post(
        "/datasets",
        json={
            "name": "daily_metrics",
            "source": "s3://lake/daily_metrics.parquet",
            "owner": "bi-team",
        },
    ).json()

    dataset_id = created["id"]

    # Log pipeline run
    run_payload = {
        "run_type": "ingestion",
        "status": "success",
        "records_processed": 45000,
    }
    run_res = client.post(f"/datasets/{dataset_id}/runs", json=run_payload)
    assert run_res.status_code == 201
    run_data = run_res.json()
    assert run_data["dataset_id"] == dataset_id
    assert run_data["records_processed"] == 45000

    # List pipeline runs
    runs_res = client.get(f"/datasets/{dataset_id}/runs")
    assert runs_res.status_code == 200
    runs_list = runs_res.json()
    assert len(runs_list) == 1
    assert runs_list[0]["run_type"] == "ingestion"
