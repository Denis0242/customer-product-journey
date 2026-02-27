"""
Generate Synthetic Data for Customer Experience & Product Analytics
This creates realistic data that simulates real e-commerce/SaaS behavior
Modified to properly create and save data to the data/ folder
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os
import sys

# Set random seeds for reproducibility
np.random.seed(42)
random.seed(42)

# ============================================================================
# CONFIGURATION
# ============================================================================

NUM_CUSTOMERS = 5000
NUM_PRODUCTS = 500
NUM_MONTHS = 12
START_DATE = datetime(2023, 1, 1)

# Create output directory path - works from any location
# Get the script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(script_dir, 'data')

# Ensure output directory exists
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    print(f"✓ Created data folder: {OUTPUT_DIR}")
else:
    print(f"✓ Data folder exists: {OUTPUT_DIR}")

print("=" * 80)
print("GENERATING SYNTHETIC DATA FOR CUSTOMER ANALYTICS")
print("=" * 80)
print(f"📂 Output directory: {OUTPUT_DIR}\n")

# ============================================================================
# 1. GENERATE CUSTOMERS DATA
# ============================================================================
print("[1/5] Generating Customers Data...")

countries = ['USA', 'UK', 'Canada', 'Australia', 'Germany', 'France', 'Japan', 'India']
cities = {
    'USA': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'],
    'UK': ['London', 'Manchester', 'Birmingham', 'Leeds'],
    'Canada': ['Toronto', 'Vancouver', 'Montreal', 'Calgary'],
    'Australia': ['Sydney', 'Melbourne', 'Brisbane', 'Perth'],
    'Germany': ['Berlin', 'Munich', 'Hamburg', 'Cologne'],
    'France': ['Paris', 'Lyon', 'Marseille', 'Toulouse'],
    'Japan': ['Tokyo', 'Osaka', 'Yokohama', 'Kobe'],
    'India': ['Mumbai', 'Delhi', 'Bangalore', 'Chennai']
}

acquisition_channels = ['organic', 'paid_search', 'social_media', 'referral', 'direct', 'partnership']
segments = ['premium', 'high_value', 'standard', 'at_risk', 'churned']

customers_data = []

for i in range(NUM_CUSTOMERS):
    country = np.random.choice(countries)
    city = np.random.choice(cities[country])
    
    # Signup dates distributed over past 2 years
    days_ago = np.random.randint(0, 730)
    signup_date = START_DATE - timedelta(days=days_ago)
    
    # Acquisition channel biased distribution
    acq_dist = np.random.random()
    if acq_dist < 0.3:
        acq_channel = 'organic'
    elif acq_dist < 0.5:
        acq_channel = 'paid_search'
    elif acq_dist < 0.65:
        acq_channel = 'social_media'
    elif acq_dist < 0.8:
        acq_channel = 'referral'
    elif acq_dist < 0.9:
        acq_channel = 'direct'
    else:
        acq_channel = 'partnership'
    
    # Segment distribution
    seg_dist = np.random.random()
    if seg_dist < 0.05:
        segment = 'premium'
    elif seg_dist < 0.15:
        segment = 'high_value'
    elif seg_dist < 0.7:
        segment = 'standard'
    elif seg_dist < 0.95:
        segment = 'at_risk'
    else:
        segment = 'churned'
    
    # Customer status
    if segment == 'churned':
        status = 'churned'
    elif segment == 'at_risk' and random.random() < 0.4:
        status = 'inactive'
    elif random.random() < 0.1:
        status = 'dormant'
    else:
        status = 'active'
    
    customers_data.append({
        'customer_id': i + 1,
        'customer_name': f"Customer_{i+1:05d}",
        'email': f"customer_{i+1:05d}@email.com",
        # 'phone': f"+1{np.random.randint(2000000000, 9999999999)}",
        'phone' : f"+1{random.randint(2000000000, 9999999999)}",
        'country': country,
        'city': city,
        'signup_date': signup_date.strftime('%Y-%m-%d'),
        'acquisition_channel': acq_channel,
        'segment': segment,
        'customer_status': status
    })

customers_df = pd.DataFrame(customers_data)
customers_file = os.path.join(OUTPUT_DIR, 'customers.csv')
customers_df.to_csv(customers_file, index=False)
print(f"✓ Generated {len(customers_df)} customer records")
print(f"  Saved to: {customers_file}\n")

# ============================================================================
# 2. GENERATE PRODUCTS DATA
# ============================================================================
print("[2/5] Generating Products Data...")

categories = ['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books', 
              'Beauty', 'Toys', 'Food & Beverage', 'Furniture', 'Accessories']

subcategories = {
    'Electronics': ['Phones', 'Laptops', 'Tablets', 'Accessories'],
    'Clothing': ['Men', 'Women', 'Kids', 'Shoes'],
    'Home & Garden': ['Kitchen', 'Bedroom', 'Living Room', 'Outdoor'],
    'Sports': ['Equipment', 'Apparel', 'Footwear', 'Accessories'],
    'Books': ['Fiction', 'Non-Fiction', 'Educational', 'Comics'],
    'Beauty': ['Skincare', 'Makeup', 'Haircare', 'Fragrance'],
    'Toys': ['Action Figures', 'Building Sets', 'Puzzles', 'Games'],
    'Food & Beverage': ['Snacks', 'Beverages', 'Organic', 'International'],
    'Furniture': ['Chairs', 'Tables', 'Storage', 'Outdoor'],
    'Accessories': ['Bags', 'Jewelry', 'Watches', 'Belts']
}

lifecycle_stages = ['introduction', 'growth', 'maturity', 'decline']

products_data = []

for i in range(NUM_PRODUCTS):
    category = np.random.choice(categories)
    subcategory = np.random.choice(subcategories[category])
    
    # Price distribution (realistic)
    price = np.random.lognormal(mean=3.5, sigma=1.2)
    price = np.round(max(5, price), 2)  # Minimum $5
    
    # Cost is 40-60% of price
    cost = np.round(price * np.random.uniform(0.4, 0.6), 2)
    
    # Launch date distributed across 24 months
    days_ago = np.random.randint(0, 730)
    launch_date = START_DATE - timedelta(days=days_ago)
    
    # Lifecycle stage correlation with age
    days_in_market = (datetime.now() - launch_date).days
    if days_in_market < 90:
        lifecycle = 'introduction'
    elif days_in_market < 270:
        lifecycle = 'growth'
    elif days_in_market < 540:
        lifecycle = 'maturity'
    else:
        lifecycle = np.random.choice(['maturity', 'decline'], p=[0.7, 0.3])
    
    products_data.append({
        'product_id': i + 1,
        'product_name': f"{category}_{subcategory}_Product_{i+1:04d}",
        'sku': f"SKU{i+1:06d}",
        'category': category,
        'subcategory': subcategory,
        'price': price,
        'cost': cost,
        'product_lifecycle_stage': lifecycle,
        'launch_date': launch_date.strftime('%Y-%m-%d'),
        'is_active': np.random.choice([True, False], p=[0.9, 0.1])
    })

products_df = pd.DataFrame(products_data)
products_file = os.path.join(OUTPUT_DIR, 'products.csv')
products_df.to_csv(products_file, index=False)
print(f"✓ Generated {len(products_df)} product records")
print(f"  Saved to: {products_file}\n")

# ============================================================================
# 3. GENERATE TRANSACTIONS DATA
# ============================================================================
print("[3/5] Generating Transactions Data...")

payment_methods = ['credit_card', 'debit_card', 'paypal', 'bank_transfer', 'wallet']
order_statuses = ['completed', 'pending', 'cancelled', 'returned']

transactions_data = []
transaction_id = 1

# Create realistic purchase patterns
for customer_id in customers_df['customer_id'].values:
    customer_segment = customers_df.loc[customers_df['customer_id'] == customer_id, 'segment'].values[0]
    
    # Segment-based purchase frequency
    if customer_segment == 'premium':
        num_purchases = np.random.poisson(2.5) + 1
        discount_rate = 0.15
    elif customer_segment == 'high_value':
        num_purchases = np.random.poisson(2.0)
        discount_rate = 0.1
    elif customer_segment == 'standard':
        num_purchases = np.random.poisson(1.0)
        discount_rate = 0.05
    elif customer_segment == 'at_risk':
        num_purchases = max(0, np.random.poisson(0.5))
        discount_rate = 0.08
    else:  # churned
        num_purchases = 0
        discount_rate = 0
    
    # Generate purchase dates within customer's tenure
    customer_signup = datetime.strptime(
        customers_df.loc[customers_df['customer_id'] == customer_id, 'signup_date'].values[0], 
        '%Y-%m-%d'
    )
    days_as_customer = (datetime.now() - customer_signup).days
    
    for _ in range(num_purchases):
        # Random date within customer tenure
        transaction_date = customer_signup + timedelta(days=np.random.randint(0, days_as_customer))
        
        # Select product
        product_id = np.random.randint(1, NUM_PRODUCTS + 1)
        product = products_df[products_df['product_id'] == product_id].iloc[0]
        
        # Quantity (mostly 1, sometimes more)
        quantity = np.random.choice([1, 2, 3], p=[0.7, 0.2, 0.1])
        
        # Unit price (with some variation)
        unit_price = product['price'] * np.random.uniform(0.95, 1.05)
        
        # Discount
        discount = unit_price * np.random.binomial(1, discount_rate) * np.random.uniform(0.05, 0.25)
        
        # Amount and profit
        transaction_amount = (unit_price - discount) * quantity
        profit_amount = (product['cost'] * quantity) - ((unit_price - discount) * quantity * 0.15)
        
        # Order status (mostly completed)
        status_dist = np.random.random()
        if status_dist < 0.85:
            status = 'completed'
        elif status_dist < 0.93:
            status = 'pending'
        elif status_dist < 0.98:
            status = 'cancelled'
        else:
            status = 'returned'
        
        transactions_data.append({
            'transaction_id': transaction_id,
            'customer_id': customer_id,
            'product_id': product_id,
            'transaction_date': transaction_date.strftime('%Y-%m-%d'),
            'transaction_time': f"{np.random.randint(0, 24):02d}:{np.random.randint(0, 60):02d}:00",
            'quantity': quantity,
            'unit_price': np.round(unit_price, 2),
            'discount_applied': np.round(discount, 2),
            'transaction_amount': np.round(transaction_amount, 2),
            'profit_amount': np.round(profit_amount, 2),
            'payment_method': np.random.choice(payment_methods),
            'order_status': status,
            'is_repeat_purchase': 1 if _ > 0 else 0
        })
        
        transaction_id += 1

transactions_df = pd.DataFrame(transactions_data)
transactions_file = os.path.join(OUTPUT_DIR, 'transactions.csv')
transactions_df.to_csv(transactions_file, index=False)
print(f"✓ Generated {len(transactions_df)} transaction records")
print(f"  Saved to: {transactions_file}\n")

# ============================================================================
# 4. GENERATE PRODUCT METRICS (Daily snapshots)
# ============================================================================
print("[4/5] Generating Product Metrics...")

product_metrics_data = []
metric_id = 1

for product_id in products_df['product_id'].values[:100]:  # 100 sample products for performance
    product = products_df[products_df['product_id'] == product_id].iloc[0]
    lifecycle = product['product_lifecycle_stage']
    
    # Base metrics by lifecycle stage
    if lifecycle == 'introduction':
        base_dau = np.random.randint(10, 50)
        base_conversion = np.random.uniform(0.01, 0.03)
    elif lifecycle == 'growth':
        base_dau = np.random.randint(100, 300)
        base_conversion = np.random.uniform(0.04, 0.08)
    elif lifecycle == 'maturity':
        base_dau = np.random.randint(200, 500)
        base_conversion = np.random.uniform(0.06, 0.10)
    else:  # decline
        base_dau = np.random.randint(20, 100)
        base_conversion = np.random.uniform(0.02, 0.04)
    
    # Generate metrics for 365 days
    for days_back in range(365):
        metric_date = datetime.now() - timedelta(days=days_back)
        
        # Add some seasonality and randomness
        seasonality = 1 + 0.3 * np.sin(2 * np.pi * days_back / 365)
        noise = np.random.normal(1, 0.1)
        
        dau = max(1, int(base_dau * seasonality * noise))
        mau = dau * np.random.randint(15, 30)
        conversion = base_conversion * seasonality * np.random.uniform(0.8, 1.2)
        
        product_metrics_data.append({
            'metric_id': metric_id,
            'product_id': product_id,
            'metric_date': metric_date.strftime('%Y-%m-%d'),
            'dau': dau,
            'mau': mau,
            'conversion_rate': np.round(min(conversion, 0.5), 4),
            'avg_session_duration': np.random.randint(30, 600),
            'page_views': dau * np.random.randint(2, 10),
            'add_to_cart': int(dau * np.random.uniform(0.1, 0.3)),
            'checkout_initiated': int(dau * np.random.uniform(0.05, 0.15)),
            'purchases': int(dau * conversion),
            'revenue': np.round(dau * conversion * products_df[products_df['product_id'] == product_id]['price'].values[0], 2),
            'refund_rate': np.round(np.random.uniform(0.01, 0.08), 4),
            'nps_score': np.random.randint(20, 80),
            'feature_adoption_rate': np.round(np.random.uniform(0.2, 0.9), 4),
            'time_to_first_action': np.random.randint(5, 300)
        })
        
        metric_id += 1

product_metrics_df = pd.DataFrame(product_metrics_data)
metrics_file = os.path.join(OUTPUT_DIR, 'product_metrics.csv')
product_metrics_df.to_csv(metrics_file, index=False)
print(f"✓ Generated {len(product_metrics_df)} product metric records")
print(f"  Saved to: {metrics_file}\n")

# ============================================================================
# 5. GENERATE CUSTOMER JOURNEY DATA
# ============================================================================
print("[5/5] Generating Customer Journey Data...")

event_types = ['page_view', 'add_to_cart', 'remove_from_cart', 'checkout_start', 
               'checkout_complete', 'product_view', 'wishlist_add', 'feature_usage', 
               'support_contact', 'review_submitted']
devices = ['mobile', 'tablet', 'desktop']

journey_data = []
journey_id = 1

# Generate journey events for customers with transactions
for _, trans in transactions_df.head(10000).iterrows():
    customer_id = int(trans['customer_id'])
    product_id = int(trans['product_id'])
    transaction_date = datetime.strptime(trans['transaction_date'], '%Y-%m-%d')
    
    # Generate journey events leading up to purchase
    num_events = np.random.randint(3, 15)
    
    for event_num in range(num_events):
        # Events distributed over days before purchase
        days_before = np.random.randint(0, 30)
        event_date = transaction_date - timedelta(days=days_before)
        
        # Event distribution
        event_dist = np.random.random()
        if event_dist < 0.3:
            event_type = 'page_view'
        elif event_dist < 0.45:
            event_type = 'product_view'
        elif event_dist < 0.6:
            event_type = 'add_to_cart'
        elif event_dist < 0.75:
            event_type = 'feature_usage'
        elif event_dist < 0.85:
            event_type = 'checkout_start'
        elif event_dist < 0.95:
            event_type = 'checkout_complete'
        else:
            event_type = np.random.choice(['wishlist_add', 'support_contact', 'review_submitted'])
        
        # Final event is typically checkout_complete
        if event_num == num_events - 1:
            event_type = 'checkout_complete'
        
        device = np.random.choice(devices, p=[0.5, 0.2, 0.3])
        
        journey_data.append({
            'journey_id': journey_id,
            'customer_id': customer_id,
            'product_id': product_id if event_type in ['product_view', 'add_to_cart'] else None,
            'journey_date': event_date.strftime('%Y-%m-%d'),
            'journey_time': f"{np.random.randint(0, 24):02d}:{np.random.randint(0, 60):02d}:00",
            'event_type': event_type,
            'device_type': device,
            'page_url': f"/product/{product_id}" if product_id else "/home",
            'session_duration': np.random.randint(30, 1800),
            'is_conversion_event': 1 if event_type == 'checkout_complete' else 0,
            'conversion_value': trans['transaction_amount'] if event_type == 'checkout_complete' else 0
        })
        
        journey_id += 1

journey_df = pd.DataFrame(journey_data)
journey_file = os.path.join(OUTPUT_DIR, 'customer_journey.csv')
journey_df.to_csv(journey_file, index=False)
print(f"✓ Generated {len(journey_df)} customer journey records")
print(f"  Saved to: {journey_file}\n")

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================
print("=" * 80)
print("SYNTHETIC DATA GENERATION COMPLETE ✅")
print("=" * 80)

print("\n📊 SUMMARY STATISTICS:\n")
print(f"Customers: {len(customers_df):,}")
print(f"  - Premium: {(customers_df['segment'] == 'premium').sum():,}")
print(f"  - High Value: {(customers_df['segment'] == 'high_value').sum():,}")
print(f"  - Standard: {(customers_df['segment'] == 'standard').sum():,}")
print(f"  - At Risk: {(customers_df['segment'] == 'at_risk').sum():,}")
print(f"  - Churned: {(customers_df['segment'] == 'churned').sum():,}")

print(f"\nProducts: {len(products_df):,}")
print(f"  - Active: {products_df['is_active'].sum():,}")
print(f"  - Introduction: {(products_df['product_lifecycle_stage'] == 'introduction').sum():,}")
print(f"  - Growth: {(products_df['product_lifecycle_stage'] == 'growth').sum():,}")
print(f"  - Maturity: {(products_df['product_lifecycle_stage'] == 'maturity').sum():,}")
print(f"  - Decline: {(products_df['product_lifecycle_stage'] == 'decline').sum():,}")

print(f"\nTransactions: {len(transactions_df):,}")
print(f"  - Total Revenue: ${transactions_df[transactions_df['order_status'] == 'completed']['transaction_amount'].sum():,.2f}")
print(f"  - Completed: {(transactions_df['order_status'] == 'completed').sum():,}")
print(f"  - Pending: {(transactions_df['order_status'] == 'pending').sum():,}")
print(f"  - Cancelled: {(transactions_df['order_status'] == 'cancelled').sum():,}")
print(f"  - Returned: {(transactions_df['order_status'] == 'returned').sum():,}")

print(f"\nProduct Metrics: {len(product_metrics_df):,}")
print(f"\nCustomer Journey Events: {len(journey_df):,}")

print(f"\n✅ All CSV files saved to: {OUTPUT_DIR}")
print("\n📁 Files created:")
print(f"  ✓ customers.csv")
print(f"  ✓ products.csv")
print(f"  ✓ transactions.csv")
print(f"  ✓ customer_journey.csv")
print(f"  ✓ product_metrics.csv")

print("\n🚀 Next step: Run the ETL loader or use CSV version of dashboard")
print("=" * 80)