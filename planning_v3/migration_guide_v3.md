# Migration Guide V3: Hybrid Architecture Implementation

**Document Version:** 3.0
**Date:** 2025-11-09
**Purpose:** Step-by-step guide to implement the hybrid PostgreSQL + DuckDB architecture
**Estimated Time:** 2-3 days for complete setup

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [PostgreSQL Installation & Configuration](#postgresql-installation--configuration)
4. [DuckDB Installation & Configuration](#duckdb-installation--configuration)
5. [dbt Setup for Dual Databases](#dbt-setup-for-dual-databases)
6. [Domain Layer Implementation](#domain-layer-implementation)
7. [ETL Pipeline Setup](#etl-pipeline-setup)
8. [First Pipeline Run](#first-pipeline-run)
9. [Testing & Validation](#testing--validation)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Hardware Requirements

**Minimum:**
- CPU: 4 cores
- RAM: 8GB
- Disk: 50GB free space
- Network: Stable internet connection

**Recommended:**
- CPU: 8 cores
- RAM: 16GB
- Disk: 100GB SSD
- Network: High-speed connection

### Software Requirements

**Required:**
- Ubuntu 20.04+ / macOS 12+ / Windows 10+ with WSL2
- Python 3.10 or higher
- Git 2.30+
- PostgreSQL 15+ client tools
- Docker (optional, for containerized setup)

**Optional:**
- VS Code with Python extension
- DataGrip or DBeaver (database IDE)
- Postman (for API testing)

### Skills Required

**Essential:**
- Basic SQL knowledge
- Python programming
- Command line proficiency
- Git basics

**Helpful:**
- Docker basics
- PostgreSQL administration
- Data warehouse concepts
- Domain-Driven Design

### Access Requirements

**Data:**
- Olist CSV files at: `/media/dhafin/42a9538d-5eb4-4681-ad99-92d4f59d5f9a/dhafin/datasets/Kaggle/Olist/`

**Credentials:**
- PostgreSQL admin credentials (for local setup)
- AWS/GCP credentials (for cloud setup, optional)

---

## Environment Setup

### Step 1: System Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y  # Ubuntu/Debian
# OR
brew update && brew upgrade             # macOS

# Install essential build tools
sudo apt install -y build-essential git curl wget  # Ubuntu
# OR
xcode-select --install                             # macOS

# Install Python 3.10+
sudo apt install -y python3.10 python3.10-venv python3-pip  # Ubuntu
# OR
brew install python@3.10                                      # macOS

# Verify Python version
python3 --version  # Should be 3.10 or higher
```

### Step 2: Create Project Directory

```bash
# Create project root
mkdir -p ~/projects/olist-dw-v3
cd ~/projects/olist-dw-v3

# Create directory structure
mkdir -p {src,tests,sql,dbt,data,logs,config}
mkdir -p src/{domain,infrastructure,application}
mkdir -p sql/{postgresql,duckdb}
mkdir -p data/{raw,processed}

# Initialize Git repository
git init
git branch -m main

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
*.egg-info/

# Database files
*.duckdb
*.duckdb.wal
*.db

# Logs
logs/
*.log

# Environment variables
.env
.env.local

# IDE
.vscode/
.idea/
*.swp

# dbt
dbt/target/
dbt/dbt_packages/
dbt/logs/

# Data files (large)
data/raw/*.csv
data/processed/*.parquet
EOF
```

### Step 3: Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# OR
.venv\Scripts\activate     # Windows

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Create requirements.txt
cat > requirements.txt << 'EOF'
# Database drivers
psycopg2-binary==2.9.9
duckdb==0.10.0

# ETL & Orchestration
pandas==2.1.4
numpy==1.26.2
dagster==1.6.0
dagster-dbt==0.22.0
dagster-postgres==0.22.0

# dbt
dbt-core==1.7.0
dbt-postgres==1.7.0
dbt-duckdb==1.7.0

# Data Quality
great-expectations==0.18.0

# Visualization
marimo==0.2.0
plotly==5.18.0

# Domain Layer
pydantic==2.5.0
python-dotenv==1.0.0

# Testing
pytest==7.4.3
pytest-cov==4.1.0

# Development
black==23.12.0
ruff==0.1.8
mypy==1.7.0
EOF

# Install dependencies
pip install -r requirements.txt

# Verify installations
python -c "import duckdb; print(f'DuckDB: {duckdb.__version__}')"
python -c "import psycopg2; print(f'psycopg2: {psycopg2.__version__}')"
dbt --version
```

---

## PostgreSQL Installation & Configuration

### Option 1: Local Installation (Recommended for Development)

#### Ubuntu/Debian

```bash
# Add PostgreSQL APT repository
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

# Install PostgreSQL 15
sudo apt update
sudo apt install -y postgresql-15 postgresql-contrib-15

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Check status
sudo systemctl status postgresql
```

#### macOS

```bash
# Install PostgreSQL using Homebrew
brew install postgresql@15

# Start PostgreSQL service
brew services start postgresql@15

# Verify installation
psql --version
```

#### Create Database and User

```bash
# Switch to postgres user (Ubuntu)
sudo -u postgres psql

# Or connect directly (macOS)
psql postgres
```

```sql
-- Create database
CREATE DATABASE olist_operational;

-- Create user
CREATE USER olist_admin WITH PASSWORD 'your_secure_password_here';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE olist_operational TO olist_admin;

-- Connect to database
\c olist_operational

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO olist_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO olist_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO olist_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO olist_admin;

-- Exit psql
\q
```

### Option 2: Docker Setup (Alternative)

```bash
# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgresql:
    image: postgres:15-alpine
    container_name: olist-postgresql
    environment:
      POSTGRES_DB: olist_operational
      POSTGRES_USER: olist_admin
      POSTGRES_PASSWORD: your_secure_password_here
      POSTGRES_HOST_AUTH_METHOD: trust
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./sql/postgresql:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U olist_admin -d olist_operational"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres-data:
EOF

# Start PostgreSQL container
docker-compose up -d postgresql

# Check logs
docker-compose logs -f postgresql

# Test connection
psql -h localhost -U olist_admin -d olist_operational -c "SELECT version();"
```

### Create Operational Schemas

```bash
# Create schema SQL file
cat > sql/postgresql/01_create_schemas.sql << 'EOF'
-- Operational schemas for PostgreSQL
CREATE SCHEMA IF NOT EXISTS etl_orchestration;
CREATE SCHEMA IF NOT EXISTS data_quality;
CREATE SCHEMA IF NOT EXISTS security_audit;

-- Set search path
ALTER DATABASE olist_operational SET search_path TO etl_orchestration, data_quality, security_audit, public;

-- Grant schema usage
GRANT USAGE ON SCHEMA etl_orchestration TO olist_admin;
GRANT USAGE ON SCHEMA data_quality TO olist_admin;
GRANT USAGE ON SCHEMA security_audit TO olist_admin;

GRANT ALL ON ALL TABLES IN SCHEMA etl_orchestration TO olist_admin;
GRANT ALL ON ALL TABLES IN SCHEMA data_quality TO olist_admin;
GRANT ALL ON ALL TABLES IN SCHEMA security_audit TO olist_admin;

COMMENT ON SCHEMA etl_orchestration IS 'ETL pipeline metadata and orchestration state';
COMMENT ON SCHEMA data_quality IS 'Data quality rules, checks, and reports';
COMMENT ON SCHEMA security_audit IS 'User authentication, authorization, and audit logs';
EOF

# Execute schema creation
psql -h localhost -U olist_admin -d olist_operational -f sql/postgresql/01_create_schemas.sql
```

### Create Operational Tables

```bash
# Create tables SQL file
cat > sql/postgresql/02_create_tables.sql << 'EOF'
-- =============================================================================
-- ETL Orchestration Schema
-- =============================================================================

CREATE TABLE etl_orchestration.pipeline_runs (
    run_id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(100) NOT NULL,
    run_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL CHECK (status IN ('running', 'success', 'failed', 'cancelled')),
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER GENERATED ALWAYS AS (EXTRACT(EPOCH FROM (completed_at - started_at))) STORED,
    rows_processed INTEGER,
    error_message TEXT,
    metadata JSONB,
    created_by VARCHAR(100) DEFAULT CURRENT_USER
);

CREATE INDEX idx_pipeline_runs_status ON etl_orchestration.pipeline_runs(status);
CREATE INDEX idx_pipeline_runs_timestamp ON etl_orchestration.pipeline_runs(run_timestamp DESC);

COMMENT ON TABLE etl_orchestration.pipeline_runs IS 'Tracks all ETL pipeline executions';

-- Task executions within pipeline runs
CREATE TABLE etl_orchestration.task_executions (
    task_id SERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES etl_orchestration.pipeline_runs(run_id) ON DELETE CASCADE,
    task_name VARCHAR(100) NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'running', 'success', 'failed', 'skipped')),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER GENERATED ALWAYS AS (EXTRACT(EPOCH FROM (completed_at - started_at))) STORED,
    rows_affected INTEGER,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    metadata JSONB
);

CREATE INDEX idx_task_executions_run ON etl_orchestration.task_executions(run_id);
CREATE INDEX idx_task_executions_status ON etl_orchestration.task_executions(status);

COMMENT ON TABLE etl_orchestration.task_executions IS 'Individual task executions within pipeline runs';

-- =============================================================================
-- Data Quality Schema
-- =============================================================================

CREATE TABLE data_quality.quality_rules (
    rule_id SERIAL PRIMARY KEY,
    rule_name VARCHAR(100) NOT NULL UNIQUE,
    rule_type VARCHAR(50) NOT NULL CHECK (rule_type IN ('completeness', 'accuracy', 'consistency', 'timeliness', 'validity')),
    description TEXT,
    sql_check TEXT,
    threshold_value DECIMAL(5,2),
    severity VARCHAR(20) DEFAULT 'medium' CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_quality_rules_active ON data_quality.quality_rules(is_active) WHERE is_active = TRUE;

COMMENT ON TABLE data_quality.quality_rules IS 'Data quality rule definitions';

-- Quality check results
CREATE TABLE data_quality.quality_checks (
    check_id SERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES etl_orchestration.pipeline_runs(run_id) ON DELETE CASCADE,
    rule_id INTEGER NOT NULL REFERENCES data_quality.quality_rules(rule_id),
    check_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pass', 'fail', 'warn', 'error')),
    rows_checked INTEGER,
    rows_failed INTEGER,
    failure_rate DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE
            WHEN rows_checked > 0 THEN (rows_failed::DECIMAL / rows_checked * 100)
            ELSE 0
        END
    ) STORED,
    execution_time_ms INTEGER,
    failure_details JSONB,
    remediation_status VARCHAR(20) DEFAULT 'pending' CHECK (remediation_status IN ('pending', 'in_progress', 'resolved', 'ignored'))
);

CREATE INDEX idx_quality_checks_run ON data_quality.quality_checks(run_id);
CREATE INDEX idx_quality_checks_status ON data_quality.quality_checks(status);
CREATE INDEX idx_quality_checks_timestamp ON data_quality.quality_checks(check_timestamp DESC);

COMMENT ON TABLE data_quality.quality_checks IS 'Results of quality checks executed during ETL runs';

-- Quality reports (daily aggregates)
CREATE TABLE data_quality.quality_reports (
    report_id SERIAL PRIMARY KEY,
    report_date DATE NOT NULL UNIQUE,
    overall_quality_score DECIMAL(5,2),
    total_checks INTEGER,
    checks_passed INTEGER,
    checks_failed INTEGER,
    checks_warned INTEGER,
    critical_failures INTEGER,
    generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_quality_reports_date ON data_quality.quality_reports(report_date DESC);

COMMENT ON TABLE data_quality.quality_reports IS 'Daily data quality summary reports';

-- =============================================================================
-- Security & Audit Schema
-- =============================================================================

CREATE TABLE security_audit.users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(200),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

CREATE INDEX idx_users_active ON security_audit.users(is_active) WHERE is_active = TRUE;

COMMENT ON TABLE security_audit.users IS 'Application users for authentication';

-- Roles
CREATE TABLE security_audit.roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    permissions JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE security_audit.roles IS 'User roles and permissions';

-- User-Role mapping
CREATE TABLE security_audit.user_roles (
    user_id INTEGER NOT NULL REFERENCES security_audit.users(user_id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES security_audit.roles(role_id) ON DELETE CASCADE,
    assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    assigned_by INTEGER REFERENCES security_audit.users(user_id),
    PRIMARY KEY (user_id, role_id)
);

-- Audit logs
CREATE TABLE security_audit.audit_logs (
    log_id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES security_audit.users(user_id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    action_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    status VARCHAR(20) CHECK (status IN ('success', 'failure', 'error')),
    details JSONB
);

CREATE INDEX idx_audit_logs_user ON security_audit.audit_logs(user_id);
CREATE INDEX idx_audit_logs_timestamp ON security_audit.audit_logs(action_timestamp DESC);
CREATE INDEX idx_audit_logs_action ON security_audit.audit_logs(action);

COMMENT ON TABLE security_audit.audit_logs IS 'Audit trail of all user actions';

-- =============================================================================
-- Insert seed data
-- =============================================================================

-- Default roles
INSERT INTO security_audit.roles (role_name, description, permissions) VALUES
('admin', 'Full system access', '{"all": true}'),
('data_engineer', 'Can run pipelines and view quality reports', '{"pipelines": "write", "quality": "read"}'),
('analyst', 'Read-only access to analytics', '{"analytics": "read"}')
ON CONFLICT (role_name) DO NOTHING;

-- Default admin user (change password in production!)
INSERT INTO security_audit.users (username, email, full_name, is_active) VALUES
('admin', 'admin@olist-dw.local', 'System Administrator', TRUE)
ON CONFLICT (username) DO NOTHING;

-- Assign admin role
INSERT INTO security_audit.user_roles (user_id, role_id)
SELECT u.user_id, r.role_id
FROM security_audit.users u
CROSS JOIN security_audit.roles r
WHERE u.username = 'admin' AND r.role_name = 'admin'
ON CONFLICT DO NOTHING;
EOF

# Execute table creation
psql -h localhost -U olist_admin -d olist_operational -f sql/postgresql/02_create_tables.sql
```

### Verify PostgreSQL Setup

```bash
# Test connection and verify tables
psql -h localhost -U olist_admin -d olist_operational << 'EOF'
-- List schemas
\dn

-- List tables in each schema
\dt etl_orchestration.*
\dt data_quality.*
\dt security_audit.*

-- Verify seed data
SELECT COUNT(*) FROM security_audit.users;
SELECT COUNT(*) FROM security_audit.roles;

-- Test insert
INSERT INTO etl_orchestration.pipeline_runs (pipeline_name, status)
VALUES ('test_pipeline', 'success')
RETURNING run_id, pipeline_name, status, started_at;

-- Clean up test data
DELETE FROM etl_orchestration.pipeline_runs WHERE pipeline_name = 'test_pipeline';

\q
EOF

echo "✅ PostgreSQL setup complete!"
```

---

## DuckDB Installation & Configuration

### Install DuckDB

DuckDB is already installed via pip (in requirements.txt), but you can also install the CLI:

```bash
# Download DuckDB CLI (optional)
# Ubuntu/Linux
wget https://github.com/duckdb/duckdb/releases/download/v0.10.0/duckdb_cli-linux-amd64.zip
unzip duckdb_cli-linux-amd64.zip
sudo mv duckdb /usr/local/bin/
rm duckdb_cli-linux-amd64.zip

# macOS
brew install duckdb

# Verify installation
duckdb --version
python -c "import duckdb; print(f'DuckDB Python: {duckdb.__version__}')"
```

### Create DuckDB Database File

```bash
# Create data directory
mkdir -p data/duckdb

# Create initialization script
cat > sql/duckdb/01_init.sql << 'EOF'
-- DuckDB Initialization Script
-- This script sets up the analytical database schemas

-- Create schemas
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS mart;

-- Set default schema
SET search_path = 'core,staging,raw,mart';

-- Display schemas
SELECT schema_name
FROM information_schema.schemata
WHERE schema_name IN ('raw', 'staging', 'core', 'mart')
ORDER BY schema_name;
EOF

# Initialize DuckDB database
duckdb data/duckdb/olist_analytical.duckdb < sql/duckdb/01_init.sql

echo "✅ DuckDB database created at: data/duckdb/olist_analytical.duckdb"
```

### Test DuckDB Connection

```python
# Create test script
cat > tests/test_duckdb_connection.py << 'EOF'
#!/usr/bin/env python3
"""Test DuckDB connection and basic operations"""

import duckdb
from pathlib import Path

def test_duckdb_connection():
    """Test DuckDB database connection"""
    db_path = Path("data/duckdb/olist_analytical.duckdb")

    print(f"Connecting to DuckDB at: {db_path}")
    conn = duckdb.connect(str(db_path))

    # Test query
    result = conn.execute("SELECT current_database(), current_schema()").fetchone()
    print(f"✅ Connected to database: {result[0]}, schema: {result[1]}")

    # List schemas
    schemas = conn.execute("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name NOT LIKE 'pg_%' AND schema_name != 'information_schema'
        ORDER BY schema_name
    """).fetchall()

    print(f"✅ Schemas found: {[s[0] for s in schemas]}")

    # Test table creation
    conn.execute("""
        CREATE TABLE IF NOT EXISTS raw.test_table (
            id INTEGER,
            name VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Insert test data
    conn.execute("INSERT INTO raw.test_table (id, name) VALUES (1, 'test')")

    # Query test data
    result = conn.execute("SELECT * FROM raw.test_table").fetchdf()
    print(f"✅ Test table created and queried: {len(result)} rows")
    print(result)

    # Clean up
    conn.execute("DROP TABLE raw.test_table")
    print("✅ Test table dropped")

    conn.close()
    print("✅ DuckDB connection test successful!")

if __name__ == "__main__":
    test_duckdb_connection()
EOF

# Run test
python tests/test_duckdb_connection.py
```

---

## dbt Setup for Dual Databases

### Initialize dbt Project

```bash
# Create dbt project directory
mkdir -p dbt
cd dbt

# Initialize dbt project
dbt init olist_dw --skip-profile-setup

cd olist_dw

# Create profiles.yml for both databases
cat > ~/.dbt/profiles.yml << 'EOF'
olist_dw:
  target: dev
  outputs:
    # PostgreSQL target (operational)
    postgresql:
      type: postgres
      host: localhost
      port: 5432
      user: olist_admin
      password: your_secure_password_here
      dbname: olist_operational
      schema: public
      threads: 4
      keepalives_idle: 0

    # DuckDB target (analytical)
    duckdb:
      type: duckdb
      path: '../data/duckdb/olist_analytical.duckdb'
      schema: core
      threads: 4

    # Development target (default to DuckDB)
    dev:
      type: duckdb
      path: '../data/duckdb/olist_analytical.duckdb'
      schema: core
      threads: 4

    # Production target
    prod:
      type: duckdb
      path: '../data/duckdb/olist_analytical_prod.duckdb'
      schema: core
      threads: 8
EOF

# Update dbt_project.yml
cat > dbt_project.yml << 'EOF'
name: 'olist_dw'
version: '1.0.0'
config-version: 2

profile: 'olist_dw'

model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

clean-targets:
  - "target"
  - "dbt_packages"

models:
  olist_dw:
    # Staging models (DuckDB)
    staging:
      +materialized: view
      +schema: staging

    # Core models (DuckDB)
    core:
      +materialized: table
      +schema: core

      dimensions:
        +tags: ['dimension']

      facts:
        +tags: ['fact']

    # Mart models (DuckDB)
    marts:
      +materialized: table
      +schema: mart
      +tags: ['mart']

vars:
  # Data source location
  csv_source_path: '/media/dhafin/42a9538d-5eb4-4681-ad99-92d4f59d5f9a/dhafin/datasets/Kaggle/Olist/'
EOF

# Test dbt configuration
dbt debug --target duckdb
dbt debug --target postgresql
```

### Create dbt Sources

```bash
# Create sources configuration
mkdir -p models/staging
cat > models/staging/_sources.yml << 'EOF'
version: 2

sources:
  - name: raw_csv
    description: "Raw CSV files from Olist dataset"
    meta:
      owner: "data_engineering"

    tables:
      - name: orders
        description: "Order header information"
        external:
          location: "{{ var('csv_source_path') }}/olist_orders_dataset.csv"
          file_format: csv
          skip_header: 1

      - name: order_items
        description: "Order line items"
        external:
          location: "{{ var('csv_source_path') }}/olist_order_items_dataset.csv"
          file_format: csv
          skip_header: 1

      - name: customers
        description: "Customer master data"
        external:
          location: "{{ var('csv_source_path') }}/olist_customers_dataset.csv"
          file_format: csv
          skip_header: 1

      - name: products
        description: "Product catalog"
        external:
          location: "{{ var('csv_source_path') }}/olist_products_dataset.csv"
          file_format: csv
          skip_header: 1

      - name: sellers
        description: "Seller marketplace data"
        external:
          location: "{{ var('csv_source_path') }}/olist_sellers_dataset.csv"
          file_format: csv
          skip_header: 1
EOF
```

### Create First dbt Model (Test)

```bash
# Create a simple staging model
cat > models/staging/stg_orders.sql << 'EOF'
-- Staging model for orders
-- Reads CSV and applies basic transformations

WITH source AS (
    SELECT *
    FROM read_csv_auto('{{ var("csv_source_path") }}/olist_orders_dataset.csv')
),

renamed AS (
    SELECT
        order_id,
        customer_id,
        order_status,
        CAST(order_purchase_timestamp AS TIMESTAMP) AS order_purchase_timestamp,
        CAST(order_approved_at AS TIMESTAMP) AS order_approved_at,
        CAST(order_delivered_carrier_date AS TIMESTAMP) AS order_delivered_carrier_date,
        CAST(order_delivered_customer_date AS TIMESTAMP) AS order_delivered_customer_date,
        CAST(order_estimated_delivery_date AS TIMESTAMP) AS order_estimated_delivery_date
    FROM source
)

SELECT * FROM renamed
EOF

# Run the model
cd ~/projects/olist-dw-v3/dbt/olist_dw
dbt run --select stg_orders --target duckdb

# Verify the model
duckdb ~/projects/olist-dw-v3/data/duckdb/olist_analytical.duckdb \
  -c "SELECT COUNT(*) FROM staging.stg_orders"
```

---

## Domain Layer Implementation

### Create Domain Structure

```bash
cd ~/projects/olist-dw-v3

# Create domain package structure
mkdir -p src/domain/{entities,value_objects,aggregates,events,repositories}

# Create __init__.py files
touch src/__init__.py
touch src/domain/__init__.py
touch src/domain/entities/__init__.py
touch src/domain/value_objects/__init__.py
touch src/domain/aggregates/__init__.py
touch src/domain/events/__init__.py
touch src/domain/repositories/__init__.py
```

### Example: Order Aggregate

```python
# Create Order aggregate
cat > src/domain/aggregates/order.py << 'EOF'
"""
Order Aggregate Root
Enforces business rules for orders
"""

from datetime import datetime
from decimal import Decimal
from typing import List
from dataclasses import dataclass, field

from ..entities.order_item import OrderItem
from ..value_objects.money import Money
from ..events.order_events import OrderPlaced, OrderCancelled


@dataclass
class Order:
    """Order aggregate root"""

    order_id: str
    customer_id: str
    status: str
    items: List[OrderItem] = field(default_factory=list)
    order_date: datetime = field(default_factory=datetime.now)
    _events: List = field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        """Validate order after initialization"""
        if not self.items:
            raise ValueError("Order must have at least one item")

        if self.status not in ['pending', 'approved', 'delivered', 'cancelled']:
            raise ValueError(f"Invalid order status: {self.status}")

    @property
    def total_amount(self) -> Money:
        """Calculate total order amount"""
        total = Decimal('0.00')
        for item in self.items:
            total += item.price.amount + item.freight.amount
        return Money(total, 'BRL')

    @property
    def total_items(self) -> int:
        """Count total items"""
        return len(self.items)

    def add_item(self, item: OrderItem) -> None:
        """Add item to order"""
        if self.status != 'pending':
            raise ValueError(f"Cannot add items to {self.status} order")

        self.items.append(item)

    def approve(self) -> None:
        """Approve the order"""
        if self.status != 'pending':
            raise ValueError(f"Cannot approve {self.status} order")

        self.status = 'approved'
        self._events.append(OrderPlaced(self.order_id, self.order_date))

    def cancel(self, reason: str) -> None:
        """Cancel the order"""
        if self.status in ['delivered', 'cancelled']:
            raise ValueError(f"Cannot cancel {self.status} order")

        self.status = 'cancelled'
        self._events.append(OrderCancelled(self.order_id, reason))

    def get_events(self) -> List:
        """Get domain events"""
        events = self._events.copy()
        self._events.clear()
        return events
EOF
```

### Example: Money Value Object

```python
# Create Money value object
cat > src/domain/value_objects/money.py << 'EOF'
"""Money value object for handling currency"""

from decimal import Decimal
from dataclasses import dataclass


@dataclass(frozen=True)
class Money:
    """Immutable money value object"""

    amount: Decimal
    currency: str = 'BRL'

    def __post_init__(self):
        """Validate money"""
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")

        if self.currency not in ['BRL', 'USD', 'EUR']:
            raise ValueError(f"Unsupported currency: {self.currency}")

    def __add__(self, other: 'Money') -> 'Money':
        """Add money"""
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")

        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: 'Money') -> 'Money':
        """Subtract money"""
        if self.currency != other.currency:
            raise ValueError("Cannot subtract different currencies")

        return Money(self.amount - other.amount, self.currency)

    def __str__(self) -> str:
        return f"{self.currency} {self.amount:.2f}"
EOF
```

---

## ETL Pipeline Setup

### Create Environment Configuration

```bash
# Create .env file
cat > .env << 'EOF'
# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=olist_operational
POSTGRES_USER=olist_admin
POSTGRES_PASSWORD=your_secure_password_here

# DuckDB Configuration
DUCKDB_PATH=data/duckdb/olist_analytical.duckdb

# CSV Source
CSV_SOURCE_PATH=/media/dhafin/42a9538d-5eb4-4681-ad99-92d4f59d5f9a/dhafin/datasets/Kaggle/Olist/

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/etl.log
EOF

# Create config loader
cat > src/config.py << 'EOF'
"""Configuration management"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration"""

    # PostgreSQL
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', 5432))
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'olist_operational')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'olist_admin')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')

    @property
    def postgres_url(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # DuckDB
    DUCKDB_PATH = Path(os.getenv('DUCKDB_PATH', 'data/duckdb/olist_analytical.duckdb'))

    # CSV Source
    CSV_SOURCE_PATH = Path(os.getenv('CSV_SOURCE_PATH'))

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = Path(os.getenv('LOG_FILE', 'logs/etl.log'))


config = Config()
EOF
```

### Create Database Connections

```python
# Create database connection utilities
cat > src/infrastructure/database.py << 'EOF'
"""Database connection management"""

import psycopg2
import duckdb
from contextlib import contextmanager
from typing import Generator

from ..config import config


class PostgreSQLConnection:
    """PostgreSQL connection manager"""

    @staticmethod
    @contextmanager
    def get_connection() -> Generator:
        """Get PostgreSQL connection"""
        conn = None
        try:
            conn = psycopg2.connect(config.postgres_url)
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()


class DuckDBConnection:
    """DuckDB connection manager"""

    @staticmethod
    @contextmanager
    def get_connection() -> Generator:
        """Get DuckDB connection"""
        conn = None
        try:
            conn = duckdb.connect(str(config.DUCKDB_PATH))
            yield conn
        finally:
            if conn:
                conn.close()
EOF
```

### Create Simple ETL Script

```python
# Create basic ETL pipeline
cat > src/etl_pipeline.py << 'EOF'
"""
Simple ETL Pipeline for Olist Data Warehouse V3
Demonstrates hybrid PostgreSQL + DuckDB approach
"""

import logging
from datetime import datetime
from pathlib import Path

from infrastructure.database import PostgreSQLConnection, DuckDBConnection
from config import config

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class OlistETL:
    """Main ETL pipeline class"""

    def __init__(self):
        self.run_id = None
        self.csv_path = config.CSV_SOURCE_PATH

    def run(self):
        """Execute ETL pipeline"""
        logger.info("Starting Olist ETL Pipeline V3 (Hybrid Architecture)")

        try:
            # Step 1: Log pipeline start (PostgreSQL)
            self.run_id = self._log_pipeline_start()
            logger.info(f"Pipeline run ID: {self.run_id}")

            # Step 2: Load CSV to DuckDB staging
            self._load_to_duckdb_staging()

            # Step 3: Run dbt transformations (DuckDB)
            self._run_dbt_transformations()

            # Step 4: Run quality checks
            quality_results = self._run_quality_checks()

            # Step 5: Log quality results (PostgreSQL)
            self._log_quality_results(quality_results)

            # Step 6: Log pipeline success (PostgreSQL)
            self._log_pipeline_success()

            logger.info("✅ ETL Pipeline completed successfully")

        except Exception as e:
            logger.error(f"❌ ETL Pipeline failed: {e}")
            self._log_pipeline_failure(str(e))
            raise

    def _log_pipeline_start(self) -> int:
        """Log pipeline start to PostgreSQL"""
        logger.info("Logging pipeline start to PostgreSQL...")

        with PostgreSQLConnection.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO etl_orchestration.pipeline_runs (pipeline_name, status)
                    VALUES (%s, %s)
                    RETURNING run_id
                """, ('olist_etl_v3', 'running'))

                run_id = cursor.fetchone()[0]
                return run_id

    def _load_to_duckdb_staging(self):
        """Load CSV files to DuckDB staging schema"""
        logger.info("Loading CSV files to DuckDB staging...")

        csv_files = {
            'stg_orders': 'olist_orders_dataset.csv',
            'stg_customers': 'olist_customers_dataset.csv',
            'stg_products': 'olist_products_dataset.csv',
        }

        with DuckDBConnection.get_connection() as conn:
            for table_name, csv_file in csv_files.items():
                csv_path = self.csv_path / csv_file

                logger.info(f"Loading {csv_file} to staging.{table_name}...")

                conn.execute(f"DROP TABLE IF EXISTS staging.{table_name}")
                conn.execute(f"""
                    CREATE TABLE staging.{table_name} AS
                    SELECT * FROM read_csv_auto('{csv_path}')
                """)

                row_count = conn.execute(f"SELECT COUNT(*) FROM staging.{table_name}").fetchone()[0]
                logger.info(f"  ✓ Loaded {row_count:,} rows")

    def _run_dbt_transformations(self):
        """Run dbt transformations on DuckDB"""
        logger.info("Running dbt transformations...")

        import subprocess

        # Run dbt (simplified for now - would use dbt-core API in production)
        result = subprocess.run(
            ['dbt', 'run', '--target', 'duckdb'],
            cwd='dbt/olist_dw',
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise Exception(f"dbt run failed: {result.stderr}")

        logger.info("  ✓ dbt transformations completed")

    def _run_quality_checks(self) -> dict:
        """Run data quality checks"""
        logger.info("Running data quality checks...")

        checks_passed = 0
        checks_failed = 0

        # Example: Check for nulls in critical columns
        with DuckDBConnection.get_connection() as conn:
            null_orders = conn.execute("""
                SELECT COUNT(*) FROM staging.stg_orders WHERE order_id IS NULL
            """).fetchone()[0]

            if null_orders == 0:
                checks_passed += 1
            else:
                checks_failed += 1

        return {
            'checks_passed': checks_passed,
            'checks_failed': checks_failed
        }

    def _log_quality_results(self, results: dict):
        """Log quality check results to PostgreSQL"""
        logger.info("Logging quality results to PostgreSQL...")

        with PostgreSQLConnection.get_connection() as conn:
            with conn.cursor() as cursor:
                # Insert quality check (simplified)
                cursor.execute("""
                    INSERT INTO data_quality.quality_checks
                    (run_id, rule_id, status, rows_checked, rows_failed)
                    VALUES (%s, 1, %s, 100, %s)
                """, (self.run_id, 'pass' if results['checks_failed'] == 0 else 'fail', results['checks_failed']))

    def _log_pipeline_success(self):
        """Log pipeline success to PostgreSQL"""
        logger.info("Logging pipeline success to PostgreSQL...")

        with PostgreSQLConnection.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE etl_orchestration.pipeline_runs
                    SET status = 'success', completed_at = NOW()
                    WHERE run_id = %s
                """, (self.run_id,))

    def _log_pipeline_failure(self, error_message: str):
        """Log pipeline failure to PostgreSQL"""
        logger.info("Logging pipeline failure to PostgreSQL...")

        try:
            with PostgreSQLConnection.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE etl_orchestration.pipeline_runs
                        SET status = 'failed', completed_at = NOW(), error_message = %s
                        WHERE run_id = %s
                    """, (error_message, self.run_id))
        except Exception as e:
            logger.error(f"Failed to log pipeline failure: {e}")


def main():
    """Main entry point"""
    pipeline = OlistETL()
    pipeline.run()


if __name__ == '__main__':
    main()
EOF
```

---

## First Pipeline Run

### Pre-flight Checklist

```bash
# 1. Verify PostgreSQL is running
psql -h localhost -U olist_admin -d olist_operational -c "SELECT version();"

# 2. Verify DuckDB file exists
ls -lh data/duckdb/olist_analytical.duckdb

# 3. Verify CSV files exist
ls -lh /media/dhafin/42a9538d-5eb4-4681-ad99-92d4f59d5f9a/dhafin/datasets/Kaggle/Olist/

# 4. Create logs directory
mkdir -p logs

# 5. Activate virtual environment
source .venv/bin/activate
```

### Run the Pipeline

```bash
# Run the ETL pipeline
cd ~/projects/olist-dw-v3
python src/etl_pipeline.py

# Monitor logs
tail -f logs/etl.log
```

### Verify Results

```bash
# Check PostgreSQL (pipeline metadata)
psql -h localhost -U olist_admin -d olist_operational << 'EOF'
-- Check pipeline runs
SELECT
    run_id,
    pipeline_name,
    status,
    started_at,
    completed_at,
    duration_seconds
FROM etl_orchestration.pipeline_runs
ORDER BY run_id DESC
LIMIT 5;

-- Check quality checks
SELECT
    check_id,
    status,
    rows_checked,
    rows_failed,
    check_timestamp
FROM data_quality.quality_checks
ORDER BY check_id DESC
LIMIT 5;
\q
EOF

# Check DuckDB (analytical data)
duckdb data/duckdb/olist_analytical.duckdb << 'EOF'
-- Check staging tables
SELECT 'stg_orders' AS table_name, COUNT(*) AS row_count FROM staging.stg_orders
UNION ALL
SELECT 'stg_customers', COUNT(*) FROM staging.stg_customers
UNION ALL
SELECT 'stg_products', COUNT(*) FROM staging.stg_products;

-- List all tables
SELECT table_schema, table_name, estimated_size
FROM information_schema.tables
WHERE table_schema IN ('staging', 'core', 'mart')
ORDER BY table_schema, table_name;
.quit
EOF
```

---

## Testing & Validation

### Run Tests

```bash
# Create test file
cat > tests/test_hybrid_setup.py << 'EOF'
"""Test hybrid database setup"""

import pytest
import psycopg2
import duckdb
from src.config import config


def test_postgresql_connection():
    """Test PostgreSQL connection"""
    conn = psycopg2.connect(config.postgres_url)
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    assert version is not None
    conn.close()


def test_duckdb_connection():
    """Test DuckDB connection"""
    conn = duckdb.connect(str(config.DUCKDB_PATH))
    result = conn.execute("SELECT current_database()").fetchone()
    assert result is not None
    conn.close()


def test_postgresql_schemas():
    """Test PostgreSQL schemas exist"""
    conn = psycopg2.connect(config.postgres_url)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name IN ('etl_orchestration', 'data_quality', 'security_audit')
    """)
    schemas = cursor.fetchall()
    assert len(schemas) == 3
    conn.close()


def test_duckdb_schemas():
    """Test DuckDB schemas exist"""
    conn = duckdb.connect(str(config.DUCKDB_PATH))
    result = conn.execute("""
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name IN ('raw', 'staging', 'core', 'mart')
    """).fetchall()
    assert len(result) == 4
    conn.close()
EOF

# Run tests
pytest tests/test_hybrid_setup.py -v
```

---

## Troubleshooting

### Common Issues

#### 1. PostgreSQL Connection Refused

**Problem:** `psycopg2.OperationalError: connection refused`

**Solution:**
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start PostgreSQL
sudo systemctl start postgresql

# Check port
sudo netstat -plnt | grep 5432
```

#### 2. DuckDB File Permission Error

**Problem:** `Permission denied` when accessing DuckDB file

**Solution:**
```bash
# Fix permissions
chmod 644 data/duckdb/olist_analytical.duckdb
chown $USER:$USER data/duckdb/olist_analytical.duckdb
```

#### 3. CSV Files Not Found

**Problem:** `FileNotFoundError: CSV file not found`

**Solution:**
```bash
# Verify CSV path
ls -lh /media/dhafin/42a9538d-5eb4-4681-ad99-92d4f59d5f9a/dhafin/datasets/Kaggle/Olist/

# Update .env if path is different
nano .env
# Set: CSV_SOURCE_PATH=/correct/path/to/csv/files
```

#### 4. dbt Command Not Found

**Problem:** `dbt: command not found`

**Solution:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dbt
pip install dbt-core dbt-postgres dbt-duckdb

# Verify
dbt --version
```

#### 5. Import Errors

**Problem:** `ModuleNotFoundError: No module named 'src'`

**Solution:**
```bash
# Add project to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or install as editable package
pip install -e .
```

---

## Next Steps

✅ **Setup Complete!** You now have:
- PostgreSQL with operational schemas
- DuckDB with analytical schemas
- dbt configured for both databases
- Domain layer structure
- Basic ETL pipeline

### What's Next?

1. **Build Complete Domain Model** - Implement all aggregates, entities, value objects
2. **Create dbt Models** - Build complete star schema (6 dimensions + 4 facts)
3. **Implement Quality Framework** - Add comprehensive data quality checks
4. **Add Dagster Orchestration** - Replace simple ETL script with Dagster
5. **Build Dashboards** - Create Marimo notebooks for analytics
6. **Deploy to Production** - Follow production deployment guide

---

**Migration Guide Complete!** 🎉

**Estimated Setup Time:** 2-3 hours for first-time setup

**Questions?** See troubleshooting section or consult the architecture documents.
