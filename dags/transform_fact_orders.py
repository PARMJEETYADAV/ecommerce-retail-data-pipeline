import pandas as pd
from postgresql_operator import PostgresOperators
import logging

# Configure logging
logger = logging.getLogger(__name__)

def validate_fact_orders_data(df):
    """
    Validate fact orders data quality.
    
    Args:
        df (pd.DataFrame): Fact orders dataframe to validate
        
    Raises:
        ValueError: If any validation check fails
    """
    checks = {
        'no_null_order_id': df['order_id'].notna().all(),
        'no_null_customer_key': df['customer_key'].notna().all(),
        'no_null_product_key': df['product_key'].notna().all(),
        'valid_price': (df['price'] >= 0).all(),
        'valid_freight': (df['freight_value'] >= 0).all(),
        'valid_total_amount': (df['total_amount'] >= 0).all(),
        'not_empty': len(df) > 0
    }
    
    failed_checks = [check_name for check_name, passed in checks.items() if not passed]
    
    if failed_checks:
        error_msg = f"Data validation failed for checks: {', '.join(failed_checks)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("✓ All validation checks passed for fact_orders")

def transform_fact_orders():
    """
    Transform fact orders table with metrics calculation.
    
    Source: 
        - staging.stg_orders
        - staging.stg_order_items
        - staging.stg_payments
        - staging.stg_customers
    Target: warehouse.fact_orders
    
    Transformations:
    - Merge multiple staging tables (orders, items, payments, customers)
    - Parse and convert timestamp columns
    - Calculate derived metrics (total_amount, delivery_time, etc.)
    - Create foreign keys to dimension tables
    - Validate data quality
    
    Metrics Calculated:
    - total_amount: price + freight_value
    - delivery_time: Days from purchase to delivery
    - estimated_delivery_time: Days from purchase to estimated delivery
    
    Raises:
        ValueError: If data validation fails
        Exception: If database operations fail
    """
    try:
        logger.info("Starting fact_orders transformation")
        
        staging_operator = PostgresOperators('postgres')
        warehouse_operator = PostgresOperators('postgres')
        
        # Extract from staging
        logger.info("Extracting data from staging tables")
        df_orders = staging_operator.get_data_to_pd("SELECT * FROM staging.stg_orders")
        df_order_items = staging_operator.get_data_to_pd("SELECT * FROM staging.stg_order_items")
        df_order_payments = staging_operator.get_data_to_pd("SELECT * FROM staging.stg_payments")
        df_customers = staging_operator.get_data_to_pd("SELECT customer_id, customer_zip_code_prefix FROM staging.stg_customers")
        
        logger.info(f"Extracted {len(df_orders)} orders, {len(df_order_items)} items, "
                   f"{len(df_order_payments)} payments, {len(df_customers)} customers")
        
        # Merge data from multiple sources
        logger.info("Merging staging tables")
        df = pd.merge(df_orders, df_order_items, on='order_id', how='left')
        df = pd.merge(df, df_order_payments, on='order_id', how='left')
        df = pd.merge(df, df_customers, on='customer_id', how='left')
        
        logger.info(f"Merged result: {len(df)} rows with {len(df.columns)} columns")
        
        # Transform and clean data
        logger.info("Applying transformations")
        df['order_status'] = df['order_status'].str.lower()
        
        # Parse timestamp columns
        df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
        df['order_approved_at'] = pd.to_datetime(df['order_approved_at'])
        df['order_delivered_carrier_date'] = pd.to_datetime(df['order_delivered_carrier_date'])
        df['order_delivered_customer_date'] = pd.to_datetime(df['order_delivered_customer_date'])
        df['order_estimated_delivery_date'] = pd.to_datetime(df['order_estimated_delivery_date'])
        
        # Calculate metrics
        logger.info("Calculating derived metrics")
        df['total_amount'] = df['price'] + df['freight_value']
        df['delivery_time'] = (df['order_delivered_customer_date'] - df['order_purchase_timestamp']).dt.total_seconds() / 86400
        df['estimated_delivery_time'] = (df['order_estimated_delivery_date'] - df['order_purchase_timestamp']).dt.total_seconds() / 86400
        
        # Create foreign keys
        df['customer_key'] = df['customer_id']
        df['product_key'] = df['product_id']
        df['seller_key'] = df['seller_id']
        
        # Handle geolocation key
        if 'customer_zip_code_prefix' in df.columns:
            df['geolocation_key'] = df['customer_zip_code_prefix']
        else:
            logger.warning("customer_zip_code_prefix column not found, using 'unknown'")
            df['geolocation_key'] = 'unknown'
        
        df['payment_key'] = df['payment_type'].astype('category').cat.codes + 1
        df['order_date_key'] = df['order_purchase_timestamp'].dt.date
        
        # Select fact columns
        fact_columns = ['order_id', 'customer_key', 'product_key', 'seller_key', 'geolocation_key', 
                       'payment_key', 'order_date_key', 'order_status', 'price', 'freight_value', 
                       'total_amount', 'payment_value', 'delivery_time', 'estimated_delivery_time']
        
        df_fact = df[fact_columns]
        
        # Validate data quality
        validate_fact_orders_data(df_fact)
        
        logger.info(f"Transformed {len(df_fact)} fact records successfully")
        
        # Load to warehouse
        logger.info("Loading data to warehouse.fact_orders")
        warehouse_operator.save_data_to_postgres(
            df_fact,
            'fact_orders',
            schema='warehouse',
            if_exists='replace'
        )
        
        logger.info(f"✓ Successfully loaded {len(df_fact)} rows to fact_orders")
        
        # Log summary statistics
        logger.info(f"Summary - Avg delivery time: {df_fact['delivery_time'].mean():.1f} days, "
                   f"Total revenue: ${df_fact['total_amount'].sum():,.2f}")
        
    except ValueError as ve:
        logger.error(f"✗ Data validation error in fact_orders: {str(ve)}")
        raise
    except Exception as e:
        logger.error(f"✗ Failed to transform fact_orders: {str(e)}")
        raise