# Customer Experience & Product Data Science - End-to-End Project

## Project Overview
This is a comprehensive portfolio project that demonstrates advanced data science, analytics, and engineering skills through building a complete Customer Experience analysis platform.

### What You'll Build:
1. **Database Architecture** - MySQL database design for e-commerce/SaaS metrics
2. **Synthetic Data Generation** - Realistic customer, product, and behavioral data in CSV format
3. **ETL Pipeline** - Python scripts to load data into MySQL
4. **Exploratory Data Analysis** - Story-driven, interactive Streamlit dashboard
5. **Predictive Analytics** - Customer segmentation, CLV prediction, churn analysis
6. **Deployment** - Full deployment instructions for portfolio showcase

---

## Project Structure

```
customer_experience_analytics/
├── 01_database/
│   ├── schema.sql                    # Database schema
│   └── setup_database.py             # MySQL connection setup
├── 02_data_generation/
│   ├── generate_synthetic_data.py   # Data generator
│   └── data/
│       ├── customers.csv            # Synthetic customer data
│       ├── products.csv             # Synthetic product data
│       ├── transactions.csv         # Purchase transactions
│       ├── product_metrics.csv      # Product KPIs
│       └── customer_journey.csv     # Customer interaction journey
├── 03_etl_pipeline/
│   ├── etl_loader.py               # Load data to MySQL
│   └── data_validation.py           # Validate data quality
├── 04_analysis/
│   ├── exploratory_analysis.py     # EDA computations
│   ├── predictive_models.py        # CLV, churn, segmentation
│   └── metrics_engine.py            # Metric calculations
├── 05_dashboard/
│   ├── app.py                       # Main Streamlit app
│   ├── pages/
│   │   ├── 01_Executive_Overview.py
│   │   ├── 02_Customer_Journey.py
│   │   ├── 03_Product_Analysis.py
│   │   ├── 04_Unit_Economics.py
│   │   ├── 05_Growth_Metrics.py
│   │   ├── 06_Customer_Experience_3D.py
│   │   └── 07_Predictions.py
│   ├── utils/
│   │   ├── db_connection.py        # Database utilities
│   │   ├── charts.py               # Chart components
│   │   └── style.py                # CSS styling
│   └── requirements.txt
├── 06_deployment/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── deployment_guide.md
│   └── heroku_deployment.sh
├── 07_documentation/
│   ├── methodology.md              # Analysis methodology
│   ├── metrics_dictionary.md       # Metric definitions
│   └── assumptions.md              # Data assumptions
└── README.md
```

---

## Technology Stack

### Core Technologies:
- **Database**: MySQL 8.0+
- **Backend**: Python 3.9+
- **Data Processing**: Pandas, NumPy
- **Analysis**: Scikit-learn, Statsmodels
- **Visualization**: Plotly, Streamlit
- **Deployment**: Docker, Heroku/AWS

### Libraries:
```
pandas==2.0.0
numpy==1.23.0
mysql-connector-python==8.0.33
scikit-learn==1.2.0
plotly==5.14.0
streamlit==1.28.0
streamlit-option-menu==0.3.2
pyarrow==12.0.0
```

---

## Setup Instructions

### Step 1: Install MySQL
```bash
# macOS
brew install mysql

# Ubuntu/Debian
sudo apt-get install mysql-server

# Windows - Download from mysql.com
```

### Step 2: Create Project Structure
```bash
mkdir customer_experience_analytics
cd customer_experience_analytics
```

### Step 3: Create Python Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows
```

### Step 4: Install Dependencies
```bash
pip install -r 05_dashboard/requirements.txt
```

### Step 5: Setup Database
```bash
# Start MySQL service
mysql.server start  # macOS
# or
sudo service mysql start  # Linux

# Create database
mysql -u root -p < 01_database/schema.sql
```

### Step 6: Generate Synthetic Data
```bash
python 02_data_generation/generate_synthetic_data.py
```

### Step 7: Load Data to MySQL
```bash
python 03_etl_pipeline/etl_loader.py
```

### Step 8: Run Streamlit Dashboard
```bash
cd 05_dashboard
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`

---

## Project Components Explained

### 1. Database Schema
- **Customers**: Customer profiles, segments, acquisition channels
- **Products**: Product catalog, categories, pricing, lifecycle stage
- **Transactions**: Purchase history, order details, revenue
- **Product_Metrics**: Product KPIs (conversion, DAU, retention)
- **Customer_Journey**: User interactions (clicks, views, cart actions)

### 2. Synthetic Data
- 5,000 customers across 4 segments
- 500+ products in 10 categories
- 50,000+ transactions over 12 months
- 100,000+ journey events
- Realistic patterns: seasonality, cohort behavior, churn dynamics

### 3. Analysis Features
- **Customer Segmentation**: RFM + clustering
- **CLV Prediction**: Revenue forecasting
- **Churn Prediction**: Risk scoring
- **Growth Metrics**: CAC, LTV, payback period, retention curves
- **Product Lifecycle**: Stage analysis (intro, growth, maturity, decline)
- **Unit Economics**: Margin analysis, cost attribution

### 4. Dashboard Pages
Each page tells a story with interactive filters:

1. **Executive Overview**: KPI cards, trend analysis
2. **Customer Journey**: Funnel analysis, touchpoint performance
3. **Product Analysis**: Portfolio performance, category insights
4. **Unit Economics**: Margin analysis, CAC/LTV ratios
5. **Growth Metrics**: Cohort analysis, retention curves
6. **Customer Experience 3D**: Multi-dimensional view
7. **Predictions**: CLV, churn risk, next-best actions

---

## Key Metrics You'll Analyze

### Customer Metrics
- Customer Acquisition Cost (CAC)
- Customer Lifetime Value (CLV)
- Churn Rate
- Net Retention Rate
- Customer Satisfaction Score (CSAT)

### Product Metrics
- Conversion Rate
- Daily Active Users (DAU)
- Monthly Active Users (MAU)
- Product Adoption Rate
- Time to First Action

### Growth Metrics
- Month-over-Month (MoM) Growth
- Year-over-Year (YoY) Growth
- Unit Economics
- Payback Period
- Gross Margin

### Experience Metrics
- NPS (Net Promoter Score)
- Feature Adoption
- Time in App
- Return Rate
- Cross-sell/Upsell Rates

---

## Running Locally

### Quick Start (5 minutes)
```bash
# 1. Clone and setup
mkdir project && cd project

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install pandas numpy mysql-connector-python scikit-learn plotly streamlit

# 4. Copy all provided files to respective folders

# 5. Setup MySQL (ensure server is running)
mysql -u root -p < 01_database/schema.sql

# 6. Generate and load data
python 02_data_generation/generate_synthetic_data.py
python 03_etl_pipeline/etl_loader.py

# 7. Run dashboard
cd 05_dashboard && streamlit run app.py
```

### Verify Installation
```bash
# Check MySQL is running
mysql -u root -p -e "SELECT VERSION();"

# Check Python version
python --version

# Check key libraries
python -c "import pandas, streamlit, mysql.connector; print('All imports successful')"
```

---

## Deployment Options

### Local Deployment
Perfect for local testing and development

### Docker Deployment
```bash
docker-compose up --build
# Access at http://localhost:8501
```

### Heroku Deployment
```bash
# See deployment guide in 06_deployment/
heroku create your-app-name
git push heroku main
```

### AWS Deployment
Using EC2 + RDS MySQL + ECS for containerization

---

## Expected Output

After running the complete pipeline, you'll have:

✅ MySQL database with 5 tables and 150,000+ records
✅ 5 CSV files with realistic synthetic data
✅ Clean ETL pipeline with validation
✅ Story-driven Streamlit dashboard with 7 interactive pages
✅ Predictive models for CLV and churn
✅ Deployment-ready Docker configuration
✅ Complete documentation and methodology

---

## Time to Completion

- Database Setup: 5 minutes
- Data Generation: 2 minutes
- ETL Loading: 3 minutes
- Dashboard Development: 20 minutes (already provided)
- Deployment: 10 minutes
- **Total: ~40 minutes end-to-end**

---

## Portfolio Showcase Tips

1. **Create a GitHub Repository**
   - Push all code with clear commit history
   - Write comprehensive README
   - Include screenshots of dashboard

2. **Deploy Publicly**
   - Use Heroku free tier or AWS free tier
   - Create a live link for portfolio

3. **Document Your Analysis**
   - Screenshot key insights
   - Write blog post about methodology
   - Highlight technical skills demonstrated

4. **Highlight Skills**
   - Database design & SQL
   - Python ETL pipelines
   - Statistical analysis
   - Predictive modeling
   - Data visualization
   - Dashboard development
   - DevOps/Deployment

---

## Next Steps

Start with **02_data_generation/generate_synthetic_data.py** to understand the data model, then follow the project structure in order.

Good luck! 🚀
