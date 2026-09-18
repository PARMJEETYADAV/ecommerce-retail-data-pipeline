from postgresql_operator import PostgresOperators
import pandas as pd
import logging

# Configure logging
logger = logging.getLogger(__name__)

def validate_sellers_data(df):
    """
    Validate seller dimension data quality.
    
    Args:
        df (pd.DataFrame): Seller dataframe to validate
        
    Raises:
        ValueError: If any validation check fails
    """
    checks = {
        'no_null_seller_id': df['seller_id'].notna().all(),
        'valid_state_code': df['seller_state'].str.len().eq(2).all(),
        'valid_zip_code': df['seller_zip_code_prefix'].str.len().eq(5).all(),
        'not_empty': len(df) > 0
    }
    
    failed_checks = [check_name for check_name, passed in checks.items() if not passed]
    
    if failed_checks:
        error_msg = f"Data validation failed for checks: {', '.join(failed_checks)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("✓ All validation checks passed for dim_sellers")

def transform_dim_sellers():
    """
    Transform seller dimension with location standardization.
    
    Source: staging.stg_sellers
    Target: warehouse.dim_sellers
    
    Transformations:
    - Standardize zip codes (5 digits with leading zeros)
    - Title case for city names
    - Upper case for state codes
    - Generate surrogate keys
    - Add last_updated timestamp for SCD Type 1
    
    Raises:
        ValueError: If data validation fails
        Exception: If database operations fail
    """
    try:
        logger.info("Starting dim_sellers transformation")
        
        staging_operator = PostgresOperators('postgres')
        warehouse_operator = PostgresOperators('postgres')
        
        # Extract from staging
        logger.info("Extracting data from staging.stg_sellers")
        df = staging_operator.get_data_to_pd("SELECT * FROM staging.stg_sellers")
        logger.info(f"Extracted {len(df)} rows from staging")
        
        # Transform and clean data
        logger.info("Applying transformations")
        df['seller_zip_code_prefix'] = df['seller_zip_code_prefix'].astype(str).str.zfill(5)
        df['seller_city'] = df['seller_city'].str.title()
        df['seller_state'] = df['seller_state'].str.upper()
        
        # Validate data quality
        validate_sellers_data(df)
        
        # Create surrogate key
        df['seller_key'] = df.index + 1
        
        # Add last updated timestamp
        df['last_updated'] = pd.Timestamp.now().date()
        
        logger.info(f"Transformed {len(df)} rows successfully")
        
        # Load to warehouse
        logger.info("Loading data to warehouse.dim_sellers")
        warehouse_operator.save_data_to_postgres(
            df,
            'dim_sellers',
            schema='warehouse',
            if_exists='replace'
        )
        
        logger.info(f"✓ Successfully loaded {len(df)} rows to dim_sellers")
        
    except ValueError as ve:
        logger.error(f"✗ Data validation error in dim_sellers: {str(ve)}")
        raise
    except Exception as e:
        logger.error(f"✗ Failed to transform dim_sellers: {str(e)}")
        raise
