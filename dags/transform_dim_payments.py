from postgresql_operator import PostgresOperators
import pandas as pd
import logging

# Configure logging
logger = logging.getLogger(__name__)

def validate_payments_data(df):
    """
    Validate payment dimension data quality.
    
    Args:
        df (pd.DataFrame): Payment dataframe to validate
        
    Raises:
        ValueError: If any validation check fails
    """
    checks = {
        'no_null_payment_type': df['payment_type'].notna().all(),
        'valid_installments': (df['payment_installments'] >= 1).all(),
        'not_empty': len(df) > 0
    }
    
    failed_checks = [check_name for check_name, passed in checks.items() if not passed]
    
    if failed_checks:
        error_msg = f"Data validation failed for checks: {', '.join(failed_checks)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("✓ All validation checks passed for dim_payments")

def transform_dim_payments():
    """
    Transform payment dimension with deduplication.
    
    Source: staging.stg_payments
    Target: warehouse.dim_payments
    
    Transformations:
    - Lowercase payment types for standardization
    - Fill missing installments with 1 (single payment)
    - Remove duplicates based on payment_type and installments
    - Generate surrogate keys
    
    Raises:
        ValueError: If data validation fails
        Exception: If database operations fail
    """
    try:
        logger.info("Starting dim_payments transformation")
        
        staging_operator = PostgresOperators('postgres')
        warehouse_operator = PostgresOperators('postgres')
        
        # Extract from staging
        logger.info("Extracting data from staging.stg_payments")
        df = staging_operator.get_data_to_pd("SELECT * FROM staging.stg_payments")
        initial_count = len(df)
        logger.info(f"Extracted {initial_count} rows from staging")
        
        # Transform and clean data
        logger.info("Applying transformations")
        df['payment_type'] = df['payment_type'].str.lower()
        df['payment_installments'] = df['payment_installments'].fillna(1).astype(int)
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['payment_type', 'payment_installments'])
        logger.info(f"Removed {initial_count - len(df)} duplicate payment combinations")
        
        # Validate data quality
        validate_payments_data(df)
        
        # Create surrogate key
        df['payment_key'] = df.index + 1
        
        logger.info(f"Transformed {len(df)} unique payment types successfully")
        
        # Load to warehouse
        logger.info("Loading data to warehouse.dim_payments")
        warehouse_operator.save_data_to_postgres(
            df,
            'dim_payments',
            schema='warehouse',
            if_exists='replace'
        )
        
        logger.info(f"✓ Successfully loaded {len(df)} rows to dim_payments")
        
    except ValueError as ve:
        logger.error(f"✗ Data validation error in dim_payments: {str(ve)}")
        raise
    except Exception as e:
        logger.error(f"✗ Failed to transform dim_payments: {str(e)}")
        raise
