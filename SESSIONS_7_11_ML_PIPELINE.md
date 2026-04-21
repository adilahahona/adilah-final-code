# ESG Analytics System - Sessions 7-11 ML Pipeline

## Overview
Sessions 7-11 implement the complete supervised machine learning pipeline for ESG score prediction with full provenance tracking, model registry, explainability, and deterministic subscoring.

## Architecture

### Database Schema (Migration 004)

#### External Ratings
- **Purpose**: Store third-party ESG ratings as training targets
- **Table**: `external_ratings`
- **Key Fields**: `organization_id`, `period_id`, `provider`, `composite_score`, `e_score`, `s_score`, `g_score`

#### Dataset Snapshots  
- **Purpose**: Immutable dataset versions for reproducibility
- **Table**: `dataset_snapshots`
- **Key Fields**: `snapshot_name`, `feature_schema_version_id`, `feature_vector_ids`, `train_ids`, `val_ids`, `test_ids`
- **Immutability**: Once created, train/val/test splits are frozen

#### Model Versions
- **Purpose**: Track all trained models with full provenance
- **Table**: `model_versions`
- **Key Fields**: `model_name`, `algorithm`, `hyperparameters`, `dataset_snapshot_id`, `train_metrics`, `val_metrics`, `status`
- **Statuses**: `TRAINED` → `APPROVED` → `DEPRECATED`
- **Supported Algorithms**: 
  - `linear_regression`
  - `ridge` (L2 regularization)
  - `lasso` (L1 regularization)
  - `random_forest`
  - `gradient_boosting`

#### Predictions
- **Purpose**: Store model inference results
- **Table**: `predictions`
- **Key Fields**: `feature_vector_id`, `model_version_id`, `composite_score`, `e_score`, `s_score`, `g_score`, `coverage`
- **Cascading**: Drivers auto-deleted when prediction is deleted

#### Prediction Drivers
- **Purpose**: Explain predictions via feature contributions
- **Table**: `prediction_drivers`
- **Key Fields**: `prediction_id`, `feature_name`, `contribution`, `rank`, `direction`
- **Methods**: 
  - Linear models: Coefficient * scaled feature value
  - Tree models: Feature importance (future: SHAP values)

#### Scoring Config Versions
- **Purpose**: Deterministic E/S/G subscore computation
- **Table**: `scoring_config_versions`
- **Key Fields**: `pillar_weights`, `indicator_bounds`, `normalization_method`, `is_active`
- **Default Config**: Min-max normalization with equal pillar weights (0.33, 0.33, 0.34)

## Services

### DatasetService (`app/domain/ml/datasets.py`)
- **create_snapshot()**: Joins feature vectors with external ratings, creates train/val/test splits with sklearn
- **load_dataset()**: Loads split data as numpy arrays with correct feature ordering from schema
- **Reproducibility**: Fixed random seeds ensure identical splits

### ModelTrainingService (`app/domain/ml/training.py`)
- **train_model()**: Trains sklearn models with StandardScaler normalization
- **Metrics**: MSE, MAE, R² computed for train and validation sets
- **Artifacts**: Saves {model, scaler, hyperparameters} to `artifacts/models/*.joblib`
- **approve_model()**: Changes status to APPROVED for production inference

### ExplainabilityService (`app/domain/ml/explainability.py`)
- **compute_linear_contributions()**: For linear models, contribution = coefficient × scaled_feature_value
- **save_prediction_drivers()**: Stores top-K drivers with rank and direction
- **Future**: SHAP integration for tree models

### Inference Service (`app/domain/ml/inference.py`)
- **generate_prediction()**: Loads latest APPROVED model, generates score, computes subscores and drivers
- **batch_predict()**: Scores all feature vectors for an organization
- **Default Behavior**: Uses latest APPROVED model if no model_version_id specified

### ScoringService (`app/domain/ml/scoring.py`)
- **compute_subscores()**: Deterministic E/S/G scores from mapped indicators
- **Normalization**: Min-max scaling based on indicator_bounds configuration
- **Direction Handling**: Minimization indicators (GHG, waste) are inverted (1 - normalized)
- **Aggregation**: Simple average of normalized indicators per pillar

## API Endpoints

### Dataset Management (`/api/v1/ml`)

```python
POST /ml/datasets
{
  "snapshot_name": "training_2024_q1",
  "feature_schema_version_id": 1,
  "provider": "MSCI",  # optional filter
  "test_size": 0.2,
  "val_size": 0.1,
  "random_seed": 42
}
# Returns: DatasetSnapshot with train/val/test counts

GET /ml/datasets
# Returns: List of all dataset snapshots

GET /ml/datasets/{id}
# Returns: Snapshot details
```

### Model Training (`/api/v1/ml`)

```python
POST /ml/models/train
{
  "model_name": "ridge_baseline_v1",
  "dataset_snapshot_id": 1,
  "algorithm": "ridge",
  "hyperparameters": {"alpha": 1.0},
  "description": "Baseline Ridge model with alpha=1.0"
}
# Returns: ModelVersion with train/val metrics

GET /ml/models?status=APPROVED
# Returns: List of models, optionally filtered by status

POST /ml/models/{id}/approve
# Changes status to APPROVED (admin only)
```

### Inference (`/api/v1/ml`)

```python
POST /ml/predict
{
  "feature_vector_id": 123,
  "model_version_id": 5,  # optional, defaults to latest APPROVED
  "compute_subscores": true,
  "compute_drivers": true,
  "top_k_drivers": 10
}
# Returns: Prediction with scores, subscores, and top drivers

POST /ml/predict/batch
{
  "organization_id": 1,
  "period_id": 2  # optional
}
# Returns: List of predictions for all feature vectors (admin only)

GET /ml/predictions?feature_vector_id=123
# Returns: Prediction history
```

### Scoring Configuration (`/api/v1/ml`)

```python
GET /ml/scoring/config
# Returns: Active scoring configuration

POST /ml/scoring/subscores?organization_id=1&period_id=2
# Returns: Deterministic E/S/G subscores
```

### External Ratings (`/api/v1/ml`)

```python
POST /ml/ratings
{
  "organization_id": 1,
  "period_id": 2,
  "provider": "MSCI",
  "composite_score": 7.5,
  "e_score": 8.0,
  "s_score": 7.2,
  "g_score": 7.3
}
# Returns: Created rating (admin only)

GET /ml/ratings?organization_id=1&provider=MSCI
# Returns: List of external ratings
```

## Workflow Example

### 1. Ingest External Ratings
```bash
curl -X POST http://localhost:8000/api/v1/ml/ratings \
  -H "X-Admin-Key: dev-admin-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": 1,
    "period_id": 1,
    "provider": "MSCI",
    "composite_score": 7.5,
    "e_score": 8.0,
    "s_score": 7.2,
    "g_score": 7.3
  }'
```

### 2. Create Dataset Snapshot
```bash
curl -X POST http://localhost:8000/api/v1/ml/datasets \
  -H "X-Admin-Key: dev-admin-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{
    "snapshot_name": "msci_2024_q1",
    "feature_schema_version_id": 1,
    "provider": "MSCI",
    "test_size": 0.2,
    "val_size": 0.1,
    "random_seed": 42
  }'
```

### 3. Train Model
```bash
curl -X POST http://localhost:8000/api/v1/ml/models/train \
  -H "X-Admin-Key: dev-admin-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "ridge_msci_v1",
    "dataset_snapshot_id": 1,
    "algorithm": "ridge",
    "hyperparameters": {"alpha": 1.0},
    "description": "Ridge regression on MSCI ratings"
  }'
```

### 4. Approve Model
```bash
curl -X POST http://localhost:8000/api/v1/ml/models/1/approve \
  -H "X-Admin-Key: dev-admin-key-change-me"
```

### 5. Generate Predictions
```bash
curl -X POST http://localhost:8000/api/v1/ml/predict \
  -H "Content-Type: application/json" \
  -d '{
    "feature_vector_id": 1,
    "compute_subscores": true,
    "compute_drivers": true,
    "top_k_drivers": 10
  }'
```

Response:
```json
{
  "id": 1,
  "feature_vector_id": 1,
  "model_version_id": 1,
  "composite_score": 7.45,
  "e_score": 78.5,
  "s_score": 72.3,
  "g_score": 68.9,
  "coverage": 0.85,
  "drivers": [
    {
      "feature_name": "GHG_SCOPE1",
      "contribution": 0.32,
      "rank": 1,
      "direction": "negative"
    },
    {
      "feature_name": "RENEWABLE_ENERGY_PCT",
      "contribution": 0.28,
      "rank": 2,
      "direction": "positive"
    }
  ],
  "created_at": "2024-02-22T14:30:00Z"
}
```

## Key Features

### Provenance Tracking
- Every prediction links to:
  - Feature vector (with schema version)
  - Model version (with dataset snapshot)
  - Dataset snapshot (with feature schema version)
- Full audit trail from raw data → features → training → inference

### Reproducibility
- Immutable dataset snapshots with fixed train/val/test splits
- Random seeds recorded in dataset metadata
- Model artifacts stored with checksums (future)

### Explainability
- Top-K driver features computed for every prediction
- Linear model contributions: `coefficient × scaled_feature_value`
- Ranked by absolute contribution magnitude

### Production Safety
- Only APPROVED models used for inference (unless explicitly overridden)
- Model status lifecycle: TRAINED → APPROVED → DEPRECATED
- Validation metrics tracked separately from training metrics

### Hybrid Scoring
- **Supervised ML**: Composite score from model trained on external ratings
- **Deterministic subscores**: E/S/G scores computed directly from mapped indicators
- Enables transparency: "Model predicts 7.5 overall, but E pillar is 85/100 based on renewable energy, emissions, etc."

## Files Created (Session 7-11)

### Migrations
- `backend/alembic/versions/004_ml_pipeline.py` - 6 new tables

### Models
- `backend/app/models/sql_models.py` - Added: ExternalRating, DatasetSnapshot, ModelVersion, Prediction, PredictionDriver, ScoringConfigVersion

### Services
- `backend/app/domain/ml/__init__.py`
- `backend/app/domain/ml/datasets.py` - Dataset assembly and loading
- `backend/app/domain/ml/training.py` - Model training and registry
- `backend/app/domain/ml/explainability.py` - Feature contribution computation
- `backend/app/domain/ml/inference.py` - Prediction generation
- `backend/app/domain/ml/scoring.py` - Deterministic E/S/G subscores

### Schemas
- `backend/app/models/ml_schemas.py` - Complete Pydantic schemas for ML endpoints

### API Routes
- `backend/app/api/v1/routes_ml.py` - 15 endpoints for datasets, training, inference, scoring, ratings

### Integration
- `backend/app/main.py` - Added routes_ml to router

## Notable Implementation Details

### SQLAlchemy Reserved Name Fix
- Renamed all `metadata` columns to `extra_metadata` to avoid SQLAlchemy conflict
- Applied across all models, migrations, and service code

### Model Version Simplification
- Removed `task_type`, `feature_schema_version_id`, `artifact_checksum`, `training_duration_seconds`, `random_seed` from schema
- Kept: `model_name`, `algorithm`, `hyperparameters`, `dataset_snapshot_id`, `train_metrics`, `val_metrics`, `artifact_path`, `status`, `description`
- Rationale: Dataset snapshot already links to feature schema; simpler schema reduces migration complexity

### Prediction Schema Simplification
- Changed from `organization_id + period_id` to `feature_vector_id` foreign key
- Removed `risk_probability`, `risk_label`, `coverage_overall`, `coverage_by_pillar`, `output_json`
- Added simple `coverage` float field
- Rationale: Feature vector already contains org/period; cleaner joins

## Next Steps (Sessions 12-15)

### Session 12: Frontend Dashboard
- Next.js/React dashboard with TypeScript
- Pages: Organizations list, Org detail, Period detail with scores/drivers, Models registry
- Charts: Coverage radar, Score trends, Driver waterfall

### Session 13: PDF Ingestion v2
- PDF upload endpoint with PyPDF2 extraction
- Manual indicator entry UI linked to PDF documents
- OCR integration (optional)

### Session 14: Governance Hardening
- RBAC beyond admin key (user roles: viewer, analyst, admin)
- Immutability enforcement at ORM layer for audit/snapshots
- Artifact integrity verification (SHA256 checksums on load)
- Restrict inference to APPROVED models only (already implemented)

### Session 15: Testing & Reproducibility
- pytest suite with fixtures for orgs, periods, features, models
- Integration tests: full pipeline (upload → map → features → train → infer)
- Golden reproducibility test with fixed seeds
- CI configuration with GitHub Actions

## Verification

```bash
# Check migrations applied
docker exec meg_postgres psql -U esg_user -d esg_analytics -c "\dt" | grep -E "model_versions|predictions|dataset_snapshots"

# Verify models load
cd backend && python3 -c "from app.models import sql_models; print('✓ Models imported')"

# Test API startup (from next session)
uvicorn app.main:app --reload
```

## Status: ✅ COMPLETED
Sessions 7-11 (ML Pipeline) are fully implemented with database schema, services, API endpoints, and documentation.
