"""
ETL Pipeline: Load Synthetic Data into MySQL
Includes data validation, transformation, and error handling
"""

import pandas as pd
import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Change this if you have a root password
    'database': 'customer_analytics'
}

DATA_DIR = './data'

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

class DatabaseConnection:
    def __init__(self, config):
        self.config = config
        self.connection = None
    
    def connect(self):
        """Establish MySQL connection"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            if self.connection.is_connected():
                print("✓ Successfully connected to MySQL database")
                return True
        except Error as e:
            print(f"✗ Error connecting to MySQL: {e}")
            return False
    
    def disconnect(self):
        """Close MySQL connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("✓ Database connection closed")
    
    def execute_query(self, query, data=None):
        """Execute query with optional data"""
        try:
            cursor = self.connection.cursor()
            if data:
                cursor.executemany(query, data)
            else:
                cursor.execute(query)
            self.connection.commit()
            return True, cursor.rowcount
        except Error as e:
            print(f"✗ Query error: {e}")
            return False, 0
    
    def execute_insert_batch(self, table, dataframe, batch_size=1000):
        """Insert data in batches for better performance"""
        try:
            cursor = self.connection.cursor()
            
            # Prepare column names and placeholders
            columns = ', '.join(dataframe.columns)
            placeholders = ', '.join(['%s'] * len(dataframe.columns))
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            
            # Convert dataframe to list of tuples
            data_tuples = [tuple(row) for row in dataframe.values]
            
            # Insert in batches
            for i in range(0, len(data_tuples), batch_size):
                batch = data_tuples[i:i + batch_size]
                cursor.executemany(query, batch)
                self.connection.commit()
                print(f"  Inserted {min(i + batch_size, len(data_tuples))}/{len(data_tuples)} rows")
            
            print(f"✓ Successfully inserted {len(data_tuples)} records into {table}")
            return True
        except Error as e:
            print(f"✗ Error inserting into {table}: {e}")
            return False

# ============================================================================
# DATA VALIDATION
# ============================================================================

class DataValidator:
    @staticmethod
    def validate_customers(df):
        """Validate customers data"""
        print("\n  Validating customers data...")
        
        required_cols = ['customer_id', 'customer_name', 'email', 'signup_date', 'segment']
        
        # Check required columns
        if not all(col in df.columns for col in required_cols):
            print("  ✗ Missing required columns")
            return False
        
        # Check for nulls in critical columns
        if df[required_cols].isnull().any().any():
            print("  ✗ Found null values in critical columns")
            return False
        
        # Check for duplicates
        if df['email'].duplicated().any():
            print("  ✗ Found duplicate emails")
            return False
        
        print("  ✓ Customers data validation passed")
        return True
    
    @staticmethod
    def validate_products(df):
        """Validate products data"""
        print("\n  Validating products data...")
        
        required_cols = ['product_id', 'product_name', 'sku', 'price', 'cost']
        
        if not all(col in df.columns for col in required_cols):
            print("  ✗ Missing required columns")
            return False
        
        if df[required_cols].isnull().any().any():
            print("  ✗ Found null values")
            return False
        
        if (df['price'] <= 0).any() or (df['cost'] <= 0).any():
            print("  ✗ Invalid prices or costs")
            return False
        
        print("  ✓ Products data validation passed")
        return True
    
    @staticmethod
    def validate_transactions(df):
        """Validate transactions data"""
        print("\n  Validating transactions data...")
        
        required_cols = ['transaction_id', 'customer_id', 'product_id', 'transaction_date', 'transaction_amount']
        
        if not all(col in df.columns for col in required_cols):
            print("  ✗ Missing required columns")
            return False
        
        if df[required_cols].isnull().any().any():
            print("  ✗ Found null values")
            return False
        
        if (df['transaction_amount'] < 0).any():
            print("  ✗ Negative transaction amounts found")
            return False
        
        print("  ✓ Transactions data validation passed")
        return True
    
    @staticmethod
    def validate_journey(df):
        """Validate customer journey data"""
        print("\n  Validating customer journey data...")
        
        required_cols = ['journey_id', 'customer_id', 'journey_date', 'event_type']
        
        if not all(col in df.columns for col in required_cols):
            print("  ✗ Missing required columns")
            return False
        
        if df[required_cols].isnull().any().any():
            print("  ✗ Found null values in critical columns")
            return False
        
        print("  ✓ Journey data validation passed")
        return True
    
    @staticmethod
    def validate_metrics(df):
        """Validate product metrics data"""
        print("\n  Validating product metrics data...")
        
        required_cols = ['metric_id', 'product_id', 'metric_date']
        
        if not all(col in df.columns for col in required_cols):
            print("  ✗ Missing required columns")
            return False
        
        if df[required_cols].isnull().any().any():
            print("  ✗ Found null values")
            return False
        
        print("  ✓ Metrics data validation passed")
        return True

# ============================================================================
# DATA TRANSFORMATION
# ============================================================================

class DataTransformer:
    @staticmethod
    def transform_customers(df):
        """Transform and clean customers data"""
        df = df.copy()
        
        # Remove whitespace
        df['customer_name'] = df['customer_name'].str.strip()
        df['email'] = df['email'].str.strip().str.lower()
        
        # Fill missing status
        if 'customer_status' not in df.columns:
            df['customer_status'] = 'active'
        
        return df
    
    @staticmethod
    def transform_transactions(df):
        """Transform and clean transactions data"""
        df = df.copy()
        
        # Ensure numeric columns
        numeric_cols = ['customer_id', 'product_id', 'quantity', 'unit_price', 
                       'discount_applied', 'transaction_amount', 'profit_amount']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remove rows with invalid data
        df = df.dropna(subset=['customer_id', 'product_id', 'transaction_amount'])
        
        return df
    
    @staticmethod
    def transform_all(customers_df, products_df, transactions_df, journey_df, metrics_df):
        """Apply all transformations"""
        print("\n" + "=" * 80)
        print("TRANSFORMING DATA")
        print("=" * 80)
        
        print("\n[1/3] Transforming Customers...")
        customers_df = DataTransformer.transform_customers(customers_df)
        print(f"  ✓ Customers transformed: {len(customers_df)} records")
        
        print("\n[2/3] Transforming Products...")
        print(f"  ✓ Products data: {len(products_df)} records")
        
        print("\n[3/3] Transforming Transactions...")
        transactions_df = DataTransformer.transform_transactions(transactions_df)
        print(f"  ✓ Transactions transformed: {len(transactions_df)} records")
        
        return customers_df, products_df, transactions_df, journey_df, metrics_df

# ============================================================================
# MAIN ETL PROCESS
# ============================================================================

def run_etl_pipeline():
    """Execute the complete ETL pipeline"""
    
    print("\n" + "=" * 80)
    print("CUSTOMER ANALYTICS ETL PIPELINE")
    print("=" * 80)
    
    # Step 1: Load CSV files
    print("\n" + "=" * 80)
    print("LOADING DATA FROM CSV FILES")
    print("=" * 80)
    
    try:
        print("\n[1/5] Loading Customers...")
        customers_df = pd.read_csv(f'{DATA_DIR}/customers.csv')
        print(f"✓ Loaded {len(customers_df)} customer records")
        
        print("\n[2/5] Loading Products...")
        products_df = pd.read_csv(f'{DATA_DIR}/products.csv')
        print(f"✓ Loaded {len(products_df)} product records")
        
        print("\n[3/5] Loading Transactions...")
        transactions_df = pd.read_csv(f'{DATA_DIR}/transactions.csv')
        print(f"✓ Loaded {len(transactions_df)} transaction records")
        
        print("\n[4/5] Loading Customer Journey...")
        journey_df = pd.read_csv(f'{DATA_DIR}/customer_journey.csv')
        print(f"✓ Loaded {len(journey_df)} journey records")
        
        print("\n[5/5] Loading Product Metrics...")
        metrics_df = pd.read_csv(f'{DATA_DIR}/product_metrics.csv')
        print(f"✓ Loaded {len(metrics_df)} metric records")
        
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        print("  Please ensure you've run generate_synthetic_data.py first")
        return False
    
    # Step 2: Validate data
    print("\n" + "=" * 80)
    print("VALIDATING DATA")
    print("=" * 80)
    
    validator = DataValidator()
    
    if not validator.validate_customers(customers_df):
        return False
    if not validator.validate_products(products_df):
        return False
    if not validator.validate_transactions(transactions_df):
        return False
    if not validator.validate_journey(journey_df):
        return False
    if not validator.validate_metrics(metrics_df):
        return False
    
    # Step 3: Transform data
    customers_df, products_df, transactions_df, journey_df, metrics_df = \
        DataTransformer.transform_all(customers_df, products_df, transactions_df, journey_df, metrics_df)
    
    # Step 4: Connect to database
    print("\n" + "=" * 80)
    print("CONNECTING TO DATABASE")
    print("=" * 80)
    
    db = DatabaseConnection(DB_CONFIG)
    if not db.connect():
        print("\n✗ Failed to connect to database")
        print("  Please ensure MySQL is running and create the database:")
        print("  mysql -u root -p < 01_database_schema.sql")
        return False
    
    # Step 5: Load data into database
    print("\n" + "=" * 80)
    print("LOADING DATA INTO DATABASE")
    print("=" * 80)
    
    print("\n[1/5] Loading Customers...")
    if not db.execute_insert_batch('customers', customers_df, batch_size=1000):
        db.disconnect()
        return False
    
    print("\n[2/5] Loading Products...")
    if not db.execute_insert_batch('products', products_df, batch_size=500):
        db.disconnect()
        return False
    
    print("\n[3/5] Loading Transactions...")
    if not db.execute_insert_batch('transactions', transactions_df, batch_size=5000):
        db.disconnect()
        return False
    
    print("\n[4/5] Loading Customer Journey...")
    if not db.execute_insert_batch('customer_journey', journey_df, batch_size=5000):
        db.disconnect()
        return False
    
    print("\n[5/5] Loading Product Metrics...")
    if not db.execute_insert_batch('product_metrics', metrics_df, batch_size=1000):
        db.disconnect()
        return False
    
    # Step 6: Verify data
    print("\n" + "=" * 80)
    print("VERIFYING DATA LOAD")
    print("=" * 80)
    
    db.disconnect()
    
    print("\n✅ ETL PIPELINE COMPLETED SUCCESSFULLY!")
    print("\nNext steps:")
    print("1. Start the Streamlit dashboard: cd 05_dashboard && streamlit run app.py")
    print("2. Or run analysis scripts directly")
    print("=" * 80)
    
    return True

# ============================================================================
# EXECUTION
# ============================================================================

if __name__ == "__main__":
    success = run_etl_pipeline()
    exit(0 if success else 1)