#!/bin/bash
# Setup Script for Option B (dbt-Only) Implementation
# Olist Data Warehouse V3

set -e  # Exit on error

echo "=========================================="
echo "Option B Setup: dbt-Only Architecture"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the right directory
cd /home/dhafin/Documents/Projects/EDA

echo -e "${BLUE}Step 1: Creating Python virtual environment...${NC}"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

echo ""
echo -e "${BLUE}Step 2: Activating virtual environment...${NC}"
source .venv/bin/activate

echo ""
echo -e "${BLUE}Step 3: Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel -q

echo ""
echo -e "${BLUE}Step 4: Installing dependencies...${NC}"
cat > requirements_option_b.txt << 'EOF'
# dbt for DuckDB
dbt-core==1.7.0
dbt-duckdb==1.7.0
dbt-duckdb[sources]==1.7.0

# DuckDB
duckdb==0.10.0

# Data processing
pandas==2.1.4
numpy==1.26.2

# Visualization (for later)
plotly==5.18.0

# Development tools
pytest==7.4.3
black==23.12.0
ruff==0.1.8

# Utilities
python-dotenv==1.0.0
pyyaml==6.0.1
EOF

pip install -r requirements_option_b.txt -q
echo -e "${GREEN}✓ All dependencies installed${NC}"

echo ""
echo -e "${BLUE}Step 5: Verifying installations...${NC}"
echo "dbt version:"
dbt --version
echo ""
echo "DuckDB version:"
python -c "import duckdb; print(f'DuckDB: {duckdb.__version__}')"

echo ""
echo -e "${BLUE}Step 6: Creating directory structure...${NC}"
mkdir -p dbt
mkdir -p data/duckdb
mkdir -p sql
mkdir -p logs

echo -e "${GREEN}✓ Directories created${NC}"

echo ""
echo "=========================================="
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source .venv/bin/activate"
echo "2. Initialize dbt project: cd dbt && dbt init olist_dw_dbt"
echo "3. Configure profiles.yml"
echo ""
echo "Virtual environment is currently active."
echo ""
