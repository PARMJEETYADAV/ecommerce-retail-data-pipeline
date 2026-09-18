from postgresql_operator import PostgresOperators
import pandas as pd
import logging

# Configure logging
logger = logging.getLogger(__name__)

def validate_products_data(df):
    """
    Validate product dimension data quality.
    
    Args:
        df (pd.DataFrame): Product dataframe to validate
        
    Raises:
        ValueError: If any validation check fails
    """
    checks = {
        'no_null_product_id': df['product_id'].notna().all(),
        'no_null_category': df['product_category_name'].notna().all(),
        'valid_weight': (df['product_weight_g'] >= 0).all(),
        'valid_dimensions': (
            (df['product_length_cm'] >= 0).all() &
            (df['product_height_cm'] >= 0).all() &
            (df['product_width_cm'] >= 0).all()
        ),
        'not_empty': len(df) > 0
    }
    
    failed_checks = [check_name for check_name, passed in checks.items() if not passed]
    
    if failed_checks:
        error_msg = f"Data validation failed for checks: {', '.join(failed_checks)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("✓ All validation checks passed for dim_products")

def transform_dim_products():
    """
    Transform product dimension with category translation and SCD Type 1.
    
    Source: 
        - staging.stg_products
        - staging.stg_product_category_name_translation
    Target: warehouse.dim_products
    
    Transformations:
    - Join products with category translations
    - Handle missing category names (set to 'Unknown')
    - Fill missing physical dimensions with 0
    - Generate surrogate keys
    - Add last_updated timestamp for SCD Type 1
    
    Raises:
        ValueError: If data validation fails
        Exception: If database operations fail
    """
    try:
        logger.info("Starting dim_products transformation")
        
        staging_operator = PostgresOperators('postgres')
        warehouse_operator = PostgresOperators('postgres')
        
        # Extract from staging
        logger.info("Extracting data from staging tables")
        df_products = staging_operator.get_data_to_pd("SELECT * FROM staging.stg_products")
        df_categories = staging_operator.get_data_to_pd("SELECT * FROM staging.stg_product_category_name_translation")
        logger.info(f"Extracted {len(df_products)} products and {len(df_categories)} category translations")
        
        # Join products with category translations
        logger.info("Merging products with category translations")
        df = pd.merge(df_products, df_categories, on='product_category_name', how='left')
        
        # Transform and clean data
        logger.info("Applying transformations")
        df['product_category_name_english'] = df['product_category_name_english'].fillna('Unknown')
        df['product_weight_g'] = df['product_weight_g'].fillna(0)
        df['product_length_cm'] = df['product_length_cm'].fillna(0)
        df['product_height_cm'] = df['product_height_cm'].fillna(0)
        df['product_width_cm'] = df['product_width_cm'].fillna(0)
        
        # Validate data quality
        validate_products_data(df)
        
        # Create surrogate key
        df['product_key'] = df.index + 1
        
        # Add last updated timestamp for SCD Type 1
        df['last_updated'] = pd.Timestamp.now().date()
        
        logger.info(f"Transformed {len(df)} rows successfully")
        
        # Load to warehouse
        logger.info("Loading data to warehouse.dim_products")
        warehouse_operator.save_data_to_postgres(
            df,
            'dim_products',
            schema='warehouse',
            if_exists='replace'
        )
        
        logger.info(f"✓ Successfully loaded {len(df)} rows to dim_products")
        
    except ValueError as ve:
        logger.error(f"✗ Data validation error in dim_products: {str(ve)}")
        raise
    except Exception as e:
        logger.error(f"✗ Failed to transform dim_products: {str(e)}")
        raise
