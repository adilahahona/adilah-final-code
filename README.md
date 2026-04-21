# ESG Analytics System

End-to-end ESG data ingestion, mapping, feature engineering, ML pipeline, model registry, and scoring dashboard with full provenance tracking.

## Status



## Architecture

- **Backend**: FastAPI 0.109.0 + SQLAlchemy 2.0.25 + PostgreSQL 16 + Alembic
- **ML Stack**: scikit-learn 1.4.0, XGBoost 2.0.3, pandas, numpy, joblib
- **File Parsing**: openpyxl (XLSX), PyPDF2 (PDF), CSV
- **Model Registry**: Versioned artifacts with immutable snapshots
- **Feature Engineering**: Versioned schemas, derived features, imputation
- **Scoring**: Hybrid (supervised ML + deterministic E/S/G subscores)
- **Governance**: Immutable audit logs, append-only provenance, RBAC-ready
- **Deployment**: Docker Compose with auto-reload

## Implemented Features (Sessions 1-11)

### ✅ Session 1: Foundation
- FastAPI application with structured JSON logging, request ID tracking
- PostgreSQL database connection with SQLAlchemy
- Environment configuration via Pydantic Settings
- Docker Compose setup with health checks
- Admin API key authentication
- Exception handlers with consistent error format

### ✅ Session 2: Database Schema v1
- Core entities: Organization, ReportingPeriod, DataSource, UploadBatch
- Document storage: RawDocument with SHA256 checksums
- Raw indicator values with provenance tracking
- Indicator catalog and framework mappings (GRI, SASB, TCFD)
- Immutable audit_events table (append-only)
- Alembic migration 001_initial_schema

### ✅ Session 3: Indicator Catalog & Frameworks
- 40+ canonical ESG indicators across E/S/G pillars
  - Environmental: GHG emissions (Scopes 1/2/3), energy, water, waste, biodiversity
  - Social: Employees, diversity, training, safety, human rights
  - Governance: Board independence, ethics, corruption, reporting
- Framework mappings: GRI, SASB, TCFD items → canonical codes
- Alias-based mapping engine (MappingRulesEngine)
- Seeding endpoints for catalog and mappings

### ✅ Session 4: Ingestion Pipeline
- CSV/XLSX file upload with multipart form data
- FileParser with SHA256 checksum computation
- IndicatorRowValidator for required fields
- Auto-creation of organizations and reporting periods
- Batch processing with summary stats (rows received/inserted/rejected)
- Detailed rejection reasons with field-level validation

### ✅ Session 5: ESG Mapping & Coverage
- ESGMappingService: Raw indicators → canonical codes via aliases
- UnitNormalizer: kg→tonnes, kWh→MWh, m³→ML conversions
- Coverage computation: % of required indicators present by pillar
- Missing indicator tracking with pillar breakdown
- Mapping versioning and provenance
- Alembic migration 002_mapped_indicators

### ✅ Session 6: Feature Engineering
- FeatureSchemaVersion: Immutable feature definitions (v1.0)
- 45+ features: Raw indicators + derived + missingness flags
- Derived features:
  - DERIVED_GHG_TOTAL = Scope1 + Scope2 + Scope3
  - DERIVED_WASTE_INTENSITY = Total Waste / Employees
  - DERIVED_SAFETY_SCORE = Weighted safety metric
- Imputation: constant (0) and median strategies
- Feature vector storage with schema linkage
- Alembic migration 003_feature_schema

### ✅ Sessions 7-11: ML Pipeline (See [SESSIONS_7_11_ML_PIPELINE.md](SESSIONS_7_11_ML_PIPELINE.md))
- **External Ratings**: Store MSCI/Sustainalytics ratings as training targets
- **Dataset Snapshots**: Immutable train/val/test splits with reproducible seeds
- **Model Training**: Ridge, Lasso, RandomForest, GradientBoosting with StandardScaler
- **Model Registry**: TRAINED → APPROVED → DEPRECATED lifecycle
- **Inference**: Latest APPROVED model auto-selection with batch scoring
- **Explainability**: Top-K driver features via coefficient × scaled_value
- **Deterministic Subscores**: E/S/G scores from mapped indicators with min-max normalization
- **Scoring Config**: Pillar weights, indicator bounds, direction (minimize/maximize)
- **Alembic migration**: 004_ml_pipeline (6 new tables)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend)

### Running with Docker

```bash
# Start database and backend
docker-compose up -d

# Check logs
docker-compose logs -f backend

# Access API documentation
open http://localhost:8000/docs
```

### Local Development (Backend)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your settings
# Ensure PostgreSQL is running (via Docker or locally)

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

### Database Migrations

```bash
cd backend

# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current revision
alembic current
```

## API Endpoints

### Health & Meta
- `GET /health` - Health check
- `GET /api/v1/meta` - Service metadata

### Catalog & Frameworks (Session 3)
- `GET /api/v1/catalog/indicators` - List indicators
- `GET /api/v1/frameworks/{name}/items` - Framework items
- `POST /api/v1/mappings` - Create indicator mapping

### Ingestion (Session 4)
- `POST /api/v1/ingestion/uploads` - Upload CSV/XLSX indicators
- `POST /api/v1/ingestion/ratings` - Upload ratings data

### Mapping & Features (Sessions 5-6)
- `POST /api/v1/mapping/run` - Run mapping pipeline
- `GET /api/v1/coverage` - Get indicator coverage
- `POST /api/v1/features/build` - Build feature vectors
- `GET /api/v1/features/schema/latest` - Get feature schema

### Models (Sessions 7-8)
- `POST /api/v1/models/train` - Train models
- `POST /api/v1/models/{id}/approve` - Approve model
- `GET /api/v1/models` - List models
- `GET /api/v1/models/{id}` - Get model details

### Inference (Sessions 9-10)
- `POST /api/v1/inference/score` - Score organization
- `GET /api/v1/predictions` - List predictions
- `GET /api/v1/predictions/{id}` - Get prediction details

### Organizations
- `GET /api/v1/orgs` - List organizations
- `POST /api/v1/orgs` - Create organization
- `GET /api/v1/orgs/{id}/periods` - List reporting periods

## Project Structure

```
esg-analytics/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application
│   │   ├── api/
│   │   │   └── v1/                 # API v1 routes
│   │   ├── core/                   # Config, logging, security
│   │   ├── db/                     # Database session & base
│   │   ├── domain/                 # Business logic modules
│   │   │   ├── ingestion/
│   │   │   ├── mapping/
│   │   │   ├── features/
│   │   │   ├── ml/
│   │   │   └── audit/
│   │   ├── models/                 # SQLAlchemy & Pydantic models
│   │   └── utils/
│   ├── alembic/                    # Database migrations
│   ├── tests/
│   └── requirements.txt
├── frontend/                       # Next.js dashboard
├── artifacts/                      # Model artifacts & schemas
├── docker/
├── docker-compose.yml
└── README.md
```

## Development Workflow

1. **Make code changes** in `backend/app/`
2. **Create migration** if schema changes: `alembic revision --autogenerate -m "msg"`
3. **Apply migration**: `alembic upgrade head`
4. **Test endpoints** via Swagger UI at `/docs`
5. **Check logs** for structured JSON output
6. **Run tests**: `pytest`

## Environment Variables

See `.env.example` for all configuration options:

- `DATABASE_URL` - PostgreSQL connection string
- `ADMIN_API_KEY` - Admin API key for protected routes
- `SERVICE_VERSION` - Service version
- `GIT_SHA` - Git commit SHA
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `ENVIRONMENT` - Environment name (development, staging, production)

## Security

- Admin endpoints require `X-Admin-Key` header
- All audit events are immutable (append-only)
- Model artifacts include checksums for integrity verification
- Database credentials should be rotated regularly
- Use strong `ADMIN_API_KEY` in production

## Monitoring & Observability

- Structured JSON logging with request IDs
- Health check endpoint for load balancers
- Request/response tracking via `X-Request-ID` header
- Performance metrics (to be added)

## Data Provenance

Every transformation records:
- Source document checksum
- Parsing version
- Mapping version  
- Feature schema version
- Model version
- Inference parameters
- Coverage metrics

## Testing

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_ingestion.py

# Run golden reproducibility test
pytest tests/test_reproducibility.py -v
```

## Deployment

Production deployment checklist:

1. Set strong `ADMIN_API_KEY`
2. Use managed PostgreSQL with backups
3. Configure SSL/TLS for database connection
4. Set `ENVIRONMENT=production`
5. Enable request rate limiting
6. Set up monitoring and alerting
7. Configure log aggregation
8. Back up artifacts directory
9. Document model approval workflow
10. Set up CI/CD pipeline

## License

Proprietary - All rights reserved

## Support

For issues and questions, contact the ESG Analytics team.
