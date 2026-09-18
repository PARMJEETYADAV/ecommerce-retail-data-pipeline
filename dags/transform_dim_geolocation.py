from postgresql_operator import PostgresOperators
import pandas as pd
import logging

# Configure logging
logger = logging.getLogger(__name__)

def validate_geolocation_data(df):
    """
    Validate geolocation dimension data quality.
    
    Args:
        df (pd.DataFrame): Geolocation dataframe to validate
        
    Raises:
        ValueError: If any validation check fails
    """
    checks = {
        'no_null_zip_code': df['geolocation_zip_code_prefix'].notna().all(),
        'valid_zip_code': df['geolocation_zip_code_prefix'].str.len().eq(5).all(),
        'valid_latitude': ((df['geolocation_lat'] >= -90) & (df['geolocation_lat'] <= 90)).all(),
        'valid_longitude': ((df['geolocation_lng'] >= -180) & (df['geolocation_lng'] <= 180)).all(),
        'not_empty': len(df) > 0
    }
    
    failed_checks = [check_name for check_name, passed in checks.items() if not passed]
    
    if failed_checks:
        error_msg = f"Data validation failed for checks: {', '.join(failed_checks)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("✓ All validation checks passed for dim_geolocation")

def transform_dim_geolocation():
    """
    Transform geolocation dimension with deduplication.
    
    Source: staging.stg_geolocation
    Target: warehouse.dim_geolocation
    
    Transformations:
    - Standardize zip codes (5 digits with leading zeros)
    - Title case for city names
    - Upper case for state codes
    - Remove duplicate zip codes (keep first occurrence)
    - Generate surrogate keys
    
    Raises:
        ValueError: If data validation fails
        Exception: If database operations fail
    """
    try:
        logger.info("Starting dim_geolocation transformation")
        
        staging_operator = PostgresOperators('postgres')
        warehouse_operator = PostgresOperators('postgres')
        
        # Extract from staging
        logger.info("Extracting data from staging.stg_geolocation")
        df = staging_operator.get_data_to_pd("SELECT * FROM staging.stg_geolocation")
        initial_count = len(df)
        logger.info(f"Extracted {initial_count} rows from staging")
        
        # Transform and clean data
        logger.info("Applying transformations")
        df['geolocation_zip_code_prefix'] = df['geolocation_zip_code_prefix'].astype(str).str.zfill(5)
        df['geolocation_city'] = df['geolocation_city'].str.title()
        df['geolocation_state'] = df['geolocation_state'].str.upper()
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['geolocation_zip_code_prefix'])
        logger.info(f"Removed {initial_count - len(df)} duplicate zip codes")
        
        # Validate data quality
        validate_geolocation_data(df)
        
        # Create surrogate key
        df['geolocation_key'] = df.index + 1
        
        logger.info(f"Transformed {len(df)} unique rows successfully")
        
        # Load to warehouse
        logger.info("Loading data to warehouse.dim_geolocation")
        warehouse_operator.save_data_to_postgres(
            df,
            'dim_geolocation',
            schema='warehouse',
            if_exists='replace'
        )
        
        logger.info(f"✓ Successfully loaded {len(df)} rows to dim_geolocation")
        
    except ValueError as ve:
        logger.error(f"✗ Data validation error in dim_geolocation: {str(ve)}")
        raise
    except Exception as e:
        logger.error(f"✗ Failed to transform dim_geolocation: {str(e)}")
        raise
