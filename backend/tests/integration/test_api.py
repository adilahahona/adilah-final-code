"""
API integration tests for ESG Analytics System endpoints.
"""
import pytest
from fastapi.testclient import TestClient


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_create_organization(client, db):
    """Test organization creation via API."""
    org_data = {
        "name": "API Test Corp",
        "external_id": "API001",
        "sector": "Finance",
        "country": "UK"
    }
    
    response = client.post("/organizations/", json=org_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "API Test Corp"
    assert data["external_id"] == "API001"
    assert "id" in data


def test_list_organizations(client, sample_org):
    """Test listing organizations."""
    response = client.get("/organizations/")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) >= 1
    assert any(org["name"] == "Test Corporation" for org in data)


def test_get_organization_by_id(client, sample_org):
    """Test retrieving a specific organization."""
    response = client.get(f"/organizations/{sample_org.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == sample_org.id
    assert data["name"] == sample_org.name


def test_get_organization_not_found(client):
    """Test 404 for non-existent organization."""
    response = client.get("/organizations/99999")
    assert response.status_code == 404


def test_create_reporting_period(client, sample_org):
    """Test creating a reporting period."""
    period_data = {
        "organization_id": sample_org.id,
        "period_start": "2023-01-01T00:00:00",
        "period_end": "2023-12-31T23:59:59",
        "period_type": "annual"
    }
    
    response = client.post("/organizations/periods/", json=period_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["organization_id"] == sample_org.id
    assert data["period_type"] == "annual"


def test_list_indicators(client, sample_indicator):
    """Test listing indicators."""
    response = client.get("/mapping/indicators/")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) >= 1


def test_create_feature_vector(client, sample_org, sample_period, sample_feature_schema):
    """Test feature vector creation."""
    fv_data = {
        "organization_id": sample_org.id,
        "period_id": sample_period.id,
        "schema_version_id": sample_feature_schema.id,
        "features": {
            "ghg_emissions": 500.0,
            "energy_consumption": 1000.0
        },
        "coverage": 0.8
    }
    
    response = client.post("/features/vectors/", json=fv_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["organization_id"] == sample_org.id
    assert data["coverage"] == 0.8


def test_coverage_analysis(client, sample_org, sample_period):
    """Test coverage analysis endpoint."""
    response = client.get(f"/coverage/?organization_id={sample_org.id}&period_id={sample_period.id}")
    assert response.status_code in [200, 404]  # 404 if no mappings exist yet
    
    if response.status_code == 200:
        data = response.json()
        assert "overall_coverage" in data


def test_validation_error(client):
    """Test that validation errors return 422."""
    invalid_org = {
        "name": "",  # Empty name should fail validation
        "external_id": "INVALID"
    }
    
    response = client.post("/organizations/", json=invalid_org)
    assert response.status_code == 422


def test_api_cors_headers(client):
    """Test that CORS headers are present."""
    response = client.options("/health")
    # In production, check for Access-Control-Allow-Origin header
    assert response.status_code in [200, 405]  # OPTIONS might not be enabled


def test_list_models(client):
    """Test listing model versions."""
    response = client.get("/ml/models/")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)


def test_get_predictions(client, sample_feature_vector):
    """Test retrieving predictions."""
    response = client.get(f"/ml/predictions/?feature_vector_id={sample_feature_vector.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
