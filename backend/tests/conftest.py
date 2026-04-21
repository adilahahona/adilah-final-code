"""
Pytest configuration and shared fixtures for ESG Analytics System tests.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from app.db.base import Base
from app.main import app
from app.db.session import get_db
from app.models.sql_models import (
    Organization, ReportingPeriod, DataSource, UploadBatch,
    Indicator, Framework, IndicatorMapping, RawIndicatorValue,
    FeatureSchemaVersion, FeatureVector, DatasetSnapshot, ModelVersion
)
from app.models.auth_models import User, UserRole


# Test database URL (in-memory SQLite for fast tests)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """FastAPI test client with overridden database dependency."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_org(db):
    """Create a sample organization."""
    org = Organization(
        name="Test Corporation",
        external_id="TEST001",
        sector="Technology",
        country="USA"
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@pytest.fixture
def sample_period(db, sample_org):
    """Create a sample reporting period."""
    period = ReportingPeriod(
        organization_id=sample_org.id,
        period_start=datetime(2023, 1, 1),
        period_end=datetime(2023, 12, 31),
        period_type="annual"
    )
    db.add(period)
    db.commit()
    db.refresh(period)
    return period


@pytest.fixture
def sample_framework(db):
    """Create a sample ESG framework."""
    framework = Framework(
        name="GRI",
        version="2021",
        description="Global Reporting Initiative Standards"
    )
    db.add(framework)
    db.commit()
    db.refresh(framework)
    return framework


@pytest.fixture
def sample_indicator(db, sample_framework):
    """Create a sample indicator."""
    indicator = Indicator(
        framework_id=sample_framework.id,
        code="GRI-305-1",
        name="Direct GHG Emissions",
        pillar="E",
        description="Direct greenhouse gas emissions in metric tons of CO2 equivalent",
        data_type="numeric",
        unit="tCO2e"
    )
    db.add(indicator)
    db.commit()
    db.refresh(indicator)
    return indicator


@pytest.fixture
def sample_raw_value(db, sample_org, sample_period, sample_indicator):
    """Create a sample raw indicator value."""
    batch = UploadBatch(
        data_source_id=1,
        uploaded_by="test_user",
        status="completed"
    )
    db.add(batch)
    db.commit()
    
    value = RawIndicatorValue(
        organization_id=sample_org.id,
        period_id=sample_period.id,
        indicator_id=sample_indicator.id,
        upload_batch_id=batch.id,
        value_numeric=1000.0,
        unit="tCO2e",
        data_quality_score=0.9
    )
    db.add(value)
    db.commit()
    db.refresh(value)
    return value


@pytest.fixture
def sample_feature_schema(db):
    """Create a sample feature schema."""
    schema = FeatureSchemaVersion(
        version_name="test_schema_v1",
        feature_list=["ghg_emissions", "energy_consumption", "water_usage"],
        is_active=True
    )
    db.add(schema)
    db.commit()
    db.refresh(schema)
    return schema


@pytest.fixture
def sample_feature_vector(db, sample_org, sample_period, sample_feature_schema):
    """Create a sample feature vector."""
    fv = FeatureVector(
        organization_id=sample_org.id,
        period_id=sample_period.id,
        schema_version_id=sample_feature_schema.id,
        features={
            "ghg_emissions": 1000.0,
            "energy_consumption": 5000.0,
            "water_usage": 10000.0
        },
        coverage=1.0
    )
    db.add(fv)
    db.commit()
    db.refresh(fv)
    return fv


@pytest.fixture
def sample_dataset(db, sample_feature_schema):
    """Create a sample dataset snapshot."""
    dataset = DatasetSnapshot(
        schema_version_id=sample_feature_schema.id,
        snapshot_name="test_dataset_v1",
        train_size=80,
        val_size=20,
        created_by="test_user"
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


@pytest.fixture
def sample_user(db):
    """Create a sample user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=User.hash_password("testpassword"),
        full_name="Test User",
        role=UserRole.ANALYST,
        is_active=True,
        is_superuser=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=User.hash_password("adminpassword"),
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
        is_superuser=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
