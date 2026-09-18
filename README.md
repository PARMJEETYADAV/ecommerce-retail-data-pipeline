# Ecommerce-retail-data-pipeline

# E-commerce Data Warehouse with Apache Airflow

A production-ready ELT (Extract, Load, Transform) data pipeline system built with Apache Airflow for e-commerce analytics. This project demonstrates end-to-end data engineering practices including automated data extraction, dimensional modeling, data warehouse construction, and business intelligence visualization.

## 🎯 Overview

This project implements a complete data warehouse solution for e-commerce business analytics, processing Brazilian e-commerce public dataset from Olist. The pipeline orchestrates the entire workflow from raw data extraction to actionable business insights through Power BI dashboards.

### Key Highlights

- **Automated ELT Pipeline**: Scheduled data extraction, staging, and transformation workflows
- **Star Schema Design**: Optimized dimensional modeling with fact and dimension tables
- **Scalable Architecture**: Containerized deployment with Docker and Docker Compose
- **Orchestration**: Apache Airflow with CeleryExecutor for distributed task execution
- **Data Warehouse**: PostgreSQL-based staging and production warehouse
- **Business Intelligence**: Interactive Power BI dashboards for sales analytics

## 🏗️ Architecture

### Pipeline Workflow
![Pipeline Architecture](https://github.com/user-attachments/assets/6eaf6963-8272-437a-9bdf-1b57bfc538e2)

### Airflow DAG Structure
![Airflow DAG](https://github.com/user-attachments/assets/45bd11be-7501-4d12-b33a-47399a763518)

### Data Warehouse Schema

**Dimension Tables:**
- `dim_customers` - Customer information and demographics
- `dim_products` - Product catalog with categories
- `dim_sellers` - Seller profiles and locations
- `dim_geolocation` - Geographic coordinates and regions
- `dim_dates` - Date dimension for time-based analysis
- `dim_payments` - Payment method details

**Fact Table:**
- `fact_orders` - Order transactions with foreign keys to all dimensions

## 🚀 Features

✅ **Automated Data Ingestion**: Extract data from CSV files and MySQL databases  
✅ **Staging Layer**: PostgreSQL staging area for data validation and cleansing  
✅ **Dimensional Modeling**: Star schema implementation for optimized query performance  
✅ **Task Orchestration**: Airflow DAGs with task groups for logical workflow separation  
✅ **Parallel Processing**: Independent dimension table transformations run concurrently  
✅ **Docker Containerization**: Consistent environment with Airflow, PostgreSQL, Redis, and Celery  
✅ **Data Quality**: Built-in data validation and error handling  
✅ **BI Integration**: Power BI dashboards for sales insights and KPI monitoring

## 📁 Project Structure

```
.
├── dags/                                 # Airflow DAG definitions
│   ├── e_commerce_dw_dag.py             # Main ELT pipeline DAG
│   ├── extract_data.py                  # Data extraction logic
│   ├── transform_dim_customers.py       # Customer dimension transformation
│   ├── transform_dim_products.py        # Product dimension transformation
│   ├── transform_dim_sellers.py         # Seller dimension transformation
│   ├── transform_dim_geolocation.py     # Geolocation dimension transformation
│   ├── transform_dim_dates.py           # Date dimension transformation
│   ├── transform_dim_payments.py        # Payment dimension transformation
│   └── transform_fact_orders.py         # Fact table transformation
├── dataset/                              # Source data files
│   ├── README.md                        # Dataset documentation
│   ├── olist_customers_dataset.csv
│   ├── olist_orders_dataset.csv
│   ├── olist_products_dataset.csv
│   ├── olist_sellers_dataset.csv
│   └── ...                              # Additional CSV files
├── images/                               # Documentation images
│   ├── data_schema.png                  # Data schema diagram
│   └── dataset_statistics.png           # Dataset statistics
├── config/                               # Configuration files
│   └── config.yaml                      # Centralized configuration
├── load_dataset_into_mysql/             # MySQL data loading scripts
├── plugins/                              # Custom Airflow plugins
├── logs/                                 # Airflow execution logs (gitignored)
├── docker-compose.yaml                   # Docker orchestration
├── Dockerfile                            # Custom Airflow image
├── requirements.txt                      # Python dependencies
├── makefile                              # Build automation
├── pg_hba.conf                          # PostgreSQL configuration
├── query.sql                             # SQL queries for analysis
├── Sales_Overview.pbix                   # Power BI dashboard
├── .env                                  # Environment variables (gitignored)
├── .gitignore                           # Git ignore rules
└── README.md                             # This file
```

## 🔄 Pipeline Workflow

### Phase 1: Extract & Load (ELT - Extract)
1. **Data Extraction**: Read CSV files from `dataset/` directory
2. **Staging Load**: Load raw data into PostgreSQL staging tables
3. **Data Validation**: Verify data integrity and completeness

### Phase 2: Transform (ELT - Transform)
Parallel transformation of dimension tables:
- Transform customer data → `dim_customers`
- Transform product catalog → `dim_products`
- Transform seller information → `dim_sellers`
- Transform geolocation data → `dim_geolocation`
- Generate date dimension → `dim_dates`
- Transform payment types → `dim_payments`

### Phase 3: Load (ELT - Load)
1. **Fact Table Construction**: Build `fact_orders` with foreign key references
2. **Data Warehouse Load**: Load transformed data into production warehouse
3. **Index Creation**: Create indexes for query optimization

## 📊 Business Intelligence

### Power BI Dashboards

The project includes comprehensive Power BI dashboards for sales analytics:

#### Sales Overview Dashboard
![Sales Overview](https://github.com/user-attachments/assets/5be72d62-6aa3-44c5-ab8d-6001057d7434)

Key metrics:
- Total revenue and order volume
- Sales trends over time
- Top-performing product categories
- Geographic sales distribution

#### Detailed Analytics
![Detailed Analytics](https://github.com/user-attachments/assets/0527464a-c116-4582-8add-ab256ba685da)

Analysis includes:
- Customer segmentation
- Seller performance metrics
- Payment method analysis
- Delivery time analytics

### Opening the Dashboard

1. Install Power BI Desktop
2. Open `Sales_Overview.pbix`
3. Configure data source connection to your PostgreSQL warehouse
4. Refresh data to load latest metrics

## 🛠️ Development

### Running the DAG Manually

1. Navigate to Airflow UI
2. Locate `e_commerce_dw_etl` DAG
3. Toggle the DAG to "On"
4. Click "Trigger DAG" to run immediately

### Adding New Transformations

```python
# Example: Adding a new dimension transformation
from airflow.operators.python_operator import PythonOperator

def transform_new_dimension():
    # Your transformation logic
    pass

task_new_dim = PythonOperator(
    task_id='transform_new_dimension',
    python_callable=transform_new_dimension,
)

# Add to transform task group
transform_group >> task_new_dim >> load_group
```

### Monitoring Pipeline Execution

```bash
# View real-time logs
docker-compose logs -f airflow-scheduler

# Check task status
docker-compose exec airflow-webserver airflow tasks list e_commerce_dw_etl

# Test specific task
docker-compose exec airflow-webserver airflow tasks test e_commerce_dw_etl extract_and_load_to_staging 2024-10-26
```

## 🧪 Testing

### Validate DAG Structure

```bash
# Check for DAG errors
docker-compose exec airflow-webserver airflow dags list

# Test DAG parsing
docker-compose exec airflow-webserver python /opt/airflow/dags/e_commerce_dw_dag.py
```

### Data Quality Checks

```sql
-- Verify dimension table row counts
SELECT 'dim_customers' as table_name, COUNT(*) as row_count FROM dim_customers
UNION ALL
SELECT 'dim_products', COUNT(*) FROM dim_products
UNION ALL
SELECT 'dim_sellers', COUNT(*) FROM dim_sellers
UNION ALL
SELECT 'fact_orders', COUNT(*) FROM fact_orders;

-- Check for null foreign keys
SELECT COUNT(*) as null_customer_keys 
FROM fact_orders 
WHERE customer_key IS NULL;
```

## 🐛 Troubleshooting

### Common Issues

**Port conflicts:**
```bash
# Check port usage
netstat -ano | findstr :8080

# Modify ports in docker-compose.yaml if needed
```

**Permission issues:**
```powershell
# Fix log directory permissions (PowerShell as Admin)
icacls .\logs /grant Users:F /t
```

**DAG not appearing:**
```bash
# Refresh DAG bag
docker-compose restart airflow-scheduler airflow-webserver

# Check for Python errors
docker-compose exec airflow-webserver airflow dags list-import-errors
```

**Database connection failures:**
```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U airflow -d warehouse_db -c "SELECT 1;"
```

## 🔐 Security Notes

⚠️ **Important**: This configuration is for development only. For production:

- Change default passwords in `.env`
- Enable Airflow authentication
- Use secrets management (e.g., Airflow Variables encryption)
- Configure SSL/TLS for database connections
- Implement network security policies
- Use volume encryption for sensitive data

## 📈 Performance Optimization

- **Parallel Execution**: Dimension transformations run concurrently
- **Indexing**: Appropriate indexes on fact and dimension tables
- **Partitioning**: Consider table partitioning for large fact tables
- **Incremental Loads**: Implement change data capture for updates
- **Resource Allocation**: Adjust Celery worker count based on workload

## 🙏 Acknowledgments

- **Dataset**: Brazilian E-Commerce Public Dataset by Olist
- **Apache Airflow**: Workflow orchestration platform
- **PostgreSQL**: Robust open-source database system
- **Docker**: Containerization platform
- **Power BI**: Business intelligence and visualization tool

---

**Built with ❤️ for data engineering and analytics**

