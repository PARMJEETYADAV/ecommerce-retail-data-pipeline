import pandas as pd
from datetime import datetime, timedelta
from postgresql_operator import PostgresOperators
import logging

# Configure logging
logger = logging.getLogger(__name__)

def validate_customers_data(df):
    """
    Validate customer dimension data quality.
    
    Args:
        df (pd.DataFrame): Customer dataframe to validate
        
    Raises:
        ValueError: If any validation check fails
    """
    checks = {
        'no_null_customer_id': df['customer_id'].notna().all(),
        'no_null_unique_id': df['customer_unique_id'].notna().all(),
        'valid_state_code': df['customer_state'].str.len().eq(2).all(),
        'valid_zip_code': df['customer_zip_code_prefix'].str.len().eq(5).all(),
        'not_empty': len(df) > 0
    }
    
    failed_checks = [check_name for check_name, passed in checks.items() if not passed]
    
    if failed_checks:
        error_msg = f"Data validation failed for checks: {', '.join(failed_checks)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("✓ All validation checks passed for dim_customers")

def transform_dim_customers():
    """
    Transform customer dimension with SCD Type 2 tracking.
    
    Source: staging.stg_customers
    Target: warehouse.dim_customers
    
    Transformations:
    - Standardize zip codes (5 digits with leading zeros)
    - Title case for city names
    - Upper case for state codes
    - Generate surrogate keys
    - Add SCD Type 2 metadata (effective_date, end_date, is_current)
    
    Raises:
        ValueError: If data validation fails
        Exception: If database operations fail
    """
    try:
        logger.info("Starting dim_customers transformation")
        
        staging_operator = PostgresOperators('postgres')
        warehouse_operator = PostgresOperators('postgres')
        
        # Extract from staging
        logger.info("Extracting data from staging.stg_customers")
        df = staging_operator.get_data_to_pd("SELECT * FROM staging.stg_customers")
        logger.info(f"Extracted {len(df)} rows from staging")
        
        # Transform and clean data
        logger.info("Applying transformations")
        df['customer_unique_id'] = df['customer_unique_id'].astype(str)
        df['customer_zip_code_prefix'] = df['customer_zip_code_prefix'].astype(str).str.zfill(5)
        df['customer_city'] = df['customer_city'].str.title()
        df['customer_state'] = df['customer_state'].str.upper()
        
        # Validate data quality
        validate_customers_data(df)
        
        # Create surrogate key
        df['customer_key'] = df.index + 1
        
        # Add columns for SCD Type 2 tracking
        current_date = datetime.now().date()
        future_date = current_date + timedelta(days=365*10)
        
        df['effective_date'] = current_date
        df['end_date'] = future_date
        df['is_current'] = True
        
        logger.info(f"Transformed {len(df)} rows successfully")
        
        # Load to warehouse
        logger.info("Loading data to warehouse.dim_customers")
        warehouse_operator.save_data_to_postgres(
            df,
            'dim_customers',
            schema='warehouse',
            if_exists='replace'
        )
        
        logger.info(f"✓ Successfully loaded {len(df)} rows to dim_customers")
        
    except ValueError as ve:
        logger.error(f"✗ Data validation error in dim_customers: {str(ve)}")
        raise
    except Exception as e:
        logger.error(f"✗ Failed to transform dim_customers: {str(e)}")
        raise