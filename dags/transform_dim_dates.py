import pandas as pd
from postgresql_operator import PostgresOperators
import logging

# Configure logging
logger = logging.getLogger(__name__)

def transform_dim_dates():
    """
    Generate and load date dimension table.
    
    Target: warehouse.dim_dates
    
    Generated Attributes:
    - date_key: Date value (primary key)
    - day, month, year, quarter: Date components
    - day_of_week: 0=Monday to 6=Sunday
    - day_name: Full day name (e.g., 'Monday')
    - month_name: Full month name (e.g., 'January')
    - is_weekend: Boolean flag for Saturday/Sunday
    
    Date Range: 2016-01-01 to 2025-12-31
    
    Raises:
        Exception: If database operations fail
    """
    try:
        logger.info("Starting dim_dates generation")
        
        warehouse_operator = PostgresOperators('postgres')
        
        # Generate date range
        start_date = pd.Timestamp('2016-01-01')
        end_date = pd.Timestamp('2025-12-31')
        date_range = pd.date_range(start=start_date, end=end_date)
        
        logger.info(f"Generating date dimension from {start_date.date()} to {end_date.date()}")
        
        # Create date dimension dataframe
        df = pd.DataFrame({
            'date_key': date_range,
            'day': date_range.day,
            'month': date_range.month,
            'year': date_range.year,
            'quarter': date_range.quarter,
            'day_of_week': date_range.dayofweek,
            'day_name': date_range.strftime('%A'),
            'month_name': date_range.strftime('%B'),
            'is_weekend': date_range.dayofweek.isin([5, 6])
        })
        
        logger.info(f"Generated {len(df)} date records ({len(df) / 365.25:.1f} years)")
        
        # Load to warehouse
        logger.info("Loading data to warehouse.dim_dates")
        warehouse_operator.save_data_to_postgres(
            df,
            'dim_dates',
            schema='warehouse',
            if_exists='replace'
        )
        
        logger.info(f"✓ Successfully loaded {len(df)} rows to dim_dates")
        
    except Exception as e:
        logger.error(f"✗ Failed to generate dim_dates: {str(e)}")
        raise
