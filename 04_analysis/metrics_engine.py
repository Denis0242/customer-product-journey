"""
Metrics Engine: Calculate all KPIs and metrics for analysis
This module computes customer, product, and business metrics
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# ============================================================================
# CUSTOMER METRICS
# ============================================================================

class CustomerMetrics:
    """Calculate customer-related metrics"""
    
    @staticmethod
    def calculate_ltv(transactions_df, customers_df):
        """Calculate Customer Lifetime Value"""
        completed_trans = transactions_df[transactions_df['order_status'] == 'completed'].copy()
        
        ltv = completed_trans.groupby('customer_id').agg({
            'transaction_amount': 'sum',
            'transaction_id': 'count'
        }).rename(columns={
            'transaction_amount': 'ltv',
            'transaction_id': 'purchase_count'
        }).reset_index()
        
        ltv['avg_order_value'] = ltv['ltv'] / ltv['purchase_count']
        return ltv
    
    @staticmethod
    def calculate_cac(customers_df, transactions_df, marketing_spend=100000):
        """Calculate Customer Acquisition Cost"""
        # Simplified: total marketing spend / new customers in period
        period_customers = len(customers_df)
        cac = marketing_spend / period_customers if period_customers > 0 else 0
        return cac
    
    @staticmethod
    def calculate_ltv_cac_ratio(ltv_df, cac):
        """Calculate LTV:CAC Ratio"""
        ltv_df['ltv_cac_ratio'] = ltv_df['ltv'] / cac if cac > 0 else 0
        return ltv_df
    
    @staticmethod
    def calculate_churn_rate(customers_df, period_days=30):
        """Calculate churn rate for period"""
        churned = (customers_df['customer_status'] == 'churned').sum()
        total = len(customers_df)
        churn_rate = (churned / total * 100) if total > 0 else 0
        return churn_rate
    
    @staticmethod
    def calculate_retention_rate(customers_df):
        """Calculate retention rate"""
        active = (customers_df['customer_status'] == 'active').sum()
        total = len(customers_df)
        retention = (active / total * 100) if total > 0 else 0
        return retention
    
    @staticmethod
    def calculate_rfm_score(transactions_df, customers_df, reference_date=None):
        """Calculate RFM (Recency, Frequency, Monetary) score"""
        if reference_date is None:
            reference_date = pd.to_datetime(datetime.now())
        else:
            reference_date = pd.to_datetime(reference_date)
        
        # Filter completed transactions
        trans = transactions_df[transactions_df['order_status'] == 'completed'].copy()
        trans['transaction_date'] = pd.to_datetime(trans['transaction_date'])
        
        # Calculate RFM components
        rfm = trans.groupby('customer_id').agg({
            'transaction_date': lambda x: (reference_date - x.max()).days,  # Recency
            'transaction_id': 'count',  # Frequency
            'transaction_amount': 'sum'  # Monetary
        }).rename(columns={
            'transaction_date': 'recency',
            'transaction_id': 'frequency',
            'transaction_amount': 'monetary'
        }).reset_index()
        
        # Score each component (1-5 scale)
        rfm['r_score'] = pd.qcut(rfm['recency'], q=5, labels=[5, 4, 3, 2, 1], duplicates='drop')
        rfm['f_score'] = pd.qcut(rfm['frequency'].rank(method='first'), q=5, 
                                 labels=[1, 2, 3, 4, 5], duplicates='drop')
        rfm['m_score'] = pd.qcut(rfm['monetary'], q=5, labels=[1, 2, 3, 4, 5], duplicates='drop')
        
        # Convert to numeric
        rfm['r_score'] = pd.to_numeric(rfm['r_score'])
        rfm['f_score'] = pd.to_numeric(rfm['f_score'])
        rfm['m_score'] = pd.to_numeric(rfm['m_score'])
        
        rfm['rfm_score'] = (rfm['r_score'] * 100 + rfm['f_score'] * 10 + rfm['m_score'])
        
        return rfm
    
    @staticmethod
    def calculate_customer_segments(transactions_df, customers_df):
        """Segment customers using RFM + clustering"""
        rfm = CustomerMetrics.calculate_rfm_score(transactions_df, customers_df)
        
        # Prepare features for clustering
        features = rfm[['recency', 'frequency', 'monetary']].copy()
        features = features.fillna(0)
        
        # Standardize
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # K-means clustering
        kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
        rfm['cluster'] = kmeans.fit_predict(features_scaled)
        
        # Map clusters to segments
        cluster_names = {
            0: 'standard',
            1: 'high_value',
            2: 'at_risk',
            3: 'premium'
        }
        rfm['segment'] = rfm['cluster'].map(cluster_names)
        
        return rfm[['customer_id', 'recency', 'frequency', 'monetary', 'rfm_score', 'segment']]

# ============================================================================
# PRODUCT METRICS
# ============================================================================

class ProductMetrics:
    """Calculate product-related metrics"""
    
    @staticmethod
    def calculate_product_performance(transactions_df, products_df):
        """Calculate overall product performance metrics"""
        trans = transactions_df[transactions_df['order_status'] == 'completed'].copy()
        
        perf = trans.groupby('product_id').agg({
            'transaction_id': 'count',
            'transaction_amount': ['sum', 'mean'],
            'quantity': 'sum',
            'profit_amount': 'sum'
        }).reset_index()
        
        perf.columns = ['product_id', 'units_sold', 'total_revenue', 'avg_price', 'quantity_sold', 'total_profit']
        perf['margin_percent'] = (perf['total_profit'] / perf['total_revenue'] * 100).round(2)
        perf['avg_profit_per_unit'] = (perf['total_profit'] / perf['quantity_sold']).round(2)
        
        return perf
    
    @staticmethod
    def calculate_conversion_rates(transactions_df, journey_df):
        """Calculate conversion rates by stage"""
        # Page views to add to cart
        page_views = len(journey_df[journey_df['event_type'] == 'page_view'])
        add_to_cart = len(journey_df[journey_df['event_type'] == 'add_to_cart'])
        checkout = len(journey_df[journey_df['event_type'] == 'checkout_start'])
        conversions = len(journey_df[journey_df['event_type'] == 'checkout_complete'])
        
        conversion_data = {
            'funnel_stage': ['Page View', 'Add to Cart', 'Checkout', 'Conversion'],
            'count': [page_views, add_to_cart, checkout, conversions],
            'conversion_rate': [
                100.0,
                (add_to_cart / page_views * 100) if page_views > 0 else 0,
                (checkout / page_views * 100) if page_views > 0 else 0,
                (conversions / page_views * 100) if page_views > 0 else 0
            ]
        }
        
        return pd.DataFrame(conversion_data)
    
    @staticmethod
    def calculate_product_lifecycle_metrics(products_df, transactions_df):
        """Analyze metrics by product lifecycle stage"""
        trans = transactions_df[transactions_df['order_status'] == 'completed'].copy()
        
        lifecycle_metrics = trans.merge(
            products_df[['product_id', 'product_lifecycle_stage']],
            on='product_id'
        ).groupby('product_lifecycle_stage').agg({
            'transaction_id': 'count',
            'transaction_amount': ['sum', 'mean'],
            'customer_id': 'nunique'
        }).round(2)
        
        lifecycle_metrics.columns = ['transactions', 'total_revenue', 'avg_transaction', 'unique_customers']
        
        return lifecycle_metrics.reset_index()
    
    @staticmethod
    def calculate_category_performance(products_df, transactions_df):
        """Analyze performance by product category"""
        trans = transactions_df[transactions_df['order_status'] == 'completed'].copy()
        
        category_perf = trans.merge(
            products_df[['product_id', 'category', 'subcategory']],
            on='product_id'
        ).groupby('category').agg({
            'transaction_id': 'count',
            'transaction_amount': 'sum',
            'customer_id': 'nunique',
            'profit_amount': 'sum'
        }).round(2)
        
        category_perf.columns = ['transactions', 'revenue', 'customers', 'profit']
        category_perf['avg_transaction_value'] = (category_perf['revenue'] / category_perf['transactions']).round(2)
        category_perf['margin_percent'] = (category_perf['profit'] / category_perf['revenue'] * 100).round(2)
        
        return category_perf.reset_index().sort_values('revenue', ascending=False)

# ============================================================================
# GROWTH METRICS
# ============================================================================

class GrowthMetrics:
    """Calculate growth-related metrics"""
    
    @staticmethod
    def calculate_monthly_growth(transactions_df):
        """Calculate month-over-month growth"""
        trans = transactions_df[transactions_df['order_status'] == 'completed'].copy()
        trans['transaction_date'] = pd.to_datetime(trans['transaction_date'])
        trans['month'] = trans['transaction_date'].dt.to_period('M')
        
        monthly = trans.groupby('month').agg({
            'transaction_amount': 'sum',
            'transaction_id': 'count',
            'customer_id': 'nunique'
        }).reset_index()
        
        monthly.columns = ['month', 'revenue', 'transactions', 'unique_customers']
        monthly['mom_revenue_growth'] = monthly['revenue'].pct_change() * 100
        monthly['mom_transaction_growth'] = monthly['transactions'].pct_change() * 100
        
        return monthly
    
    @staticmethod
    def calculate_cohort_analysis(transactions_df, customers_df):
        """Calculate cohort retention analysis"""
        trans = transactions_df[transactions_df['order_status'] == 'completed'].copy()
        trans['transaction_date'] = pd.to_datetime(trans['transaction_date'])
        customers_df['signup_date'] = pd.to_datetime(customers_df['signup_date'])
        
        # Merge to get signup dates
        trans = trans.merge(customers_df[['customer_id', 'signup_date']], on='customer_id')
        
        # Create cohort
        trans['cohort'] = trans['signup_date'].dt.to_period('M')
        trans['month'] = trans['transaction_date'].dt.to_period('M')
        
        # Calculate months since signup
        trans['months_since_signup'] = (trans['month'] - trans['cohort']).apply(lambda x: x.n)
        
        # Cohort analysis
        cohort = trans.groupby(['cohort', 'months_since_signup']).agg({
            'customer_id': 'nunique'
        }).reset_index()
        
        cohort.columns = ['cohort', 'months_since_signup', 'customers']
        
        # Pivot for cohort table
        cohort_pivot = cohort.pivot_table(
            index='cohort',
            columns='months_since_signup',
            values='customers',
            fill_value=0
        )
        
        return cohort_pivot
    
    @staticmethod
    def calculate_payback_period(transactions_df, customers_df, cac):
        """Calculate payback period in months"""
        trans = transactions_df[transactions_df['order_status'] == 'completed'].copy()
        trans['transaction_date'] = pd.to_datetime(trans['transaction_date'])
        customers_df['signup_date'] = pd.to_datetime(customers_df['signup_date'])
        
        trans = trans.merge(customers_df[['customer_id', 'signup_date']], on='customer_id')
        
        # Calculate cumulative revenue by customer
        trans = trans.sort_values(['customer_id', 'transaction_date'])
        trans['days_since_signup'] = (trans['transaction_date'] - trans['signup_date']).dt.days
        trans['months_since_signup'] = trans['days_since_signup'] / 30
        
        # Calculate when customer pays back CAC
        trans['cumulative_revenue'] = trans.groupby('customer_id')['transaction_amount'].cumsum()
        trans['payback'] = trans['cumulative_revenue'] >= cac
        
        # Find first payback date
        payback_analysis = trans[trans['payback']].groupby('customer_id').agg({
            'months_since_signup': 'min'
        }).reset_index()
        
        payback_analysis.columns = ['customer_id', 'payback_period_months']
        avg_payback = payback_analysis['payback_period_months'].mean()
        
        return {'avg_payback_months': avg_payback, 'details': payback_analysis}

# ============================================================================
# EXPERIENCE METRICS
# ============================================================================

class ExperienceMetrics:
    """Calculate customer experience metrics"""
    
    @staticmethod
    def calculate_nps_by_product(metrics_df, products_df):
        """Calculate Net Promoter Score by product"""
        if metrics_df.empty or 'nps_score' not in metrics_df.columns:
            return pd.DataFrame()
        
        nps_data = metrics_df.groupby('product_id').agg({
            'nps_score': 'mean'
        }).reset_index()
        
        nps_data.columns = ['product_id', 'avg_nps']
        nps_data = nps_data.merge(products_df[['product_id', 'product_name']], on='product_id')
        
        return nps_data.sort_values('avg_nps', ascending=False)
    
    @staticmethod
    def calculate_feature_adoption(metrics_df):
        """Calculate feature adoption rates"""
        if metrics_df.empty or 'feature_adoption_rate' not in metrics_df.columns:
            return pd.DataFrame()
        
        adoption = metrics_df.groupby('product_id').agg({
            'feature_adoption_rate': 'mean',
            'metric_date': 'count'
        }).reset_index()
        
        adoption.columns = ['product_id', 'avg_adoption_rate', 'days_measured']
        
        return adoption.sort_values('avg_adoption_rate', ascending=False)
    
    @staticmethod
    def calculate_engagement_score(transactions_df, journey_df, customers_df):
        """Calculate engagement score per customer"""
        # Transactions per customer
        trans_score = transactions_df.groupby('customer_id').size().reset_index(name='purchase_count')
        
        # Journey events per customer
        journey_score = journey_df.groupby('customer_id').size().reset_index(name='event_count')
        
        # Merge
        engagement = trans_score.merge(journey_score, on='customer_id', how='outer')
        engagement = engagement.fillna(0)
        
        # Create engagement score (0-100)
        max_purchases = trans_score['purchase_count'].max()
        max_events = journey_score['event_count'].max()
        
        engagement['engagement_score'] = (
            (engagement['purchase_count'] / max_purchases * 50) +
            (engagement['event_count'] / max_events * 50)
        ).round(2)
        
        # Normalize to 0-100
        engagement['engagement_score'] = engagement['engagement_score'].clip(0, 100)
        
        return engagement[['customer_id', 'engagement_score', 'purchase_count', 'event_count']]
    
    @staticmethod
    def calculate_return_rate(transactions_df):
        """Calculate return rate"""
        completed = len(transactions_df[transactions_df['order_status'] == 'completed'])
        returned = len(transactions_df[transactions_df['order_status'] == 'returned'])
        
        return_rate = (returned / completed * 100) if completed > 0 else 0
        return return_rate
    
    @staticmethod
    def calculate_crosssell_performance(transactions_df, customers_df):
        """Calculate cross-sell and upsell metrics"""
        trans = transactions_df[transactions_df['order_status'] == 'completed'].copy()
        
        cross_sell = trans.groupby('customer_id').agg({
            'product_id': 'nunique',
            'transaction_id': 'count',
            'transaction_amount': 'sum'
        }).reset_index()
        
        cross_sell.columns = ['customer_id', 'products_purchased', 'purchase_count', 'total_spent']
        cross_sell['avg_products_per_purchase'] = (cross_sell['products_purchased'] / cross_sell['purchase_count']).round(2)
        
        # Categorize
        cross_sell['cross_sell_level'] = pd.cut(
            cross_sell['products_purchased'],
            bins=[0, 1, 2, 5, float('inf')],
            labels=['Single', 'Couple', 'Multiple', 'Power Buyer']
        )
        
        return cross_sell

# ============================================================================
# CHURN PREDICTION FEATURES
# ============================================================================

class ChurnPrediction:
    """Calculate features for churn prediction"""
    
    @staticmethod
    def calculate_churn_features(transactions_df, customers_df, journey_df, reference_date=None):
        """Calculate churn risk features"""
        if reference_date is None:
            reference_date = pd.to_datetime(datetime.now())
        else:
            reference_date = pd.to_datetime(reference_date)
        
        trans = transactions_df[transactions_df['order_status'] == 'completed'].copy()
        trans['transaction_date'] = pd.to_datetime(trans['transaction_date'])
        customers_df['signup_date'] = pd.to_datetime(customers_df['signup_date'])
        
        # Days since last purchase
        last_purchase = trans.groupby('customer_id')['transaction_date'].max().reset_index()
        last_purchase.columns = ['customer_id', 'last_purchase_date']
        last_purchase['days_since_last_purchase'] = (reference_date - last_purchase['last_purchase_date']).dt.days
        
        # Purchase frequency
        purchase_freq = trans.groupby('customer_id').size().reset_index(name='purchase_frequency')
        
        # Average purchase value
        avg_purchase = trans.groupby('customer_id')['transaction_amount'].mean().reset_index()
        avg_purchase.columns = ['customer_id', 'avg_purchase_value']
        
        # Total spent
        total_spent = trans.groupby('customer_id')['transaction_amount'].sum().reset_index()
        total_spent.columns = ['customer_id', 'total_spent']
        
        # Journey engagement
        journey_engagement = journey_df.groupby('customer_id').size().reset_index(name='journey_events')
        
        # Merge all features
        churn_features = customers_df[['customer_id', 'signup_date']].copy()
        churn_features = churn_features.merge(last_purchase, on='customer_id', how='left')
        churn_features = churn_features.merge(purchase_freq, on='customer_id', how='left')
        churn_features = churn_features.merge(avg_purchase, on='customer_id', how='left')
        churn_features = churn_features.merge(total_spent, on='customer_id', how='left')
        churn_features = churn_features.merge(journey_engagement, on='customer_id', how='left')
        
        # Fill NAs
        churn_features = churn_features.fillna(0)
        
        # Calculate churn risk score
        churn_features['days_since_signup'] = (reference_date - churn_features['signup_date']).dt.days
        
        # Risk score (0-100): higher = more likely to churn
        max_days_inactive = churn_features['days_since_last_purchase'].quantile(0.95)
        
        churn_features['churn_risk_score'] = (
            (churn_features['days_since_last_purchase'] / max_days_inactive) * 50 +
            (1 - churn_features['purchase_frequency'] / churn_features['purchase_frequency'].max()) * 30 +
            (1 - churn_features['engagement_score'] / 100) * 20 if 'engagement_score' in churn_features.columns else 0
        ).clip(0, 100).round(2)
        
        # Categorize risk
        churn_features['churn_risk_label'] = pd.cut(
            churn_features['churn_risk_score'],
            bins=[0, 33, 66, 100],
            labels=['Low', 'Medium', 'High']
        )
        
        return churn_features

# ============================================================================
# CLV PREDICTION
# ============================================================================

class CLVPrediction:
    """Calculate features for CLV prediction"""
    
    @staticmethod
    def calculate_clv_features(transactions_df, customers_df):
        """Calculate CLV prediction features"""
        trans = transactions_df[transactions_df['order_status'] == 'completed'].copy()
        trans['transaction_date'] = pd.to_datetime(trans['transaction_date'])
        customers_df['signup_date'] = pd.to_datetime(customers_df['signup_date'])
        
        # Historical CLV
        historical_clv = trans.groupby('customer_id')['transaction_amount'].sum().reset_index()
        historical_clv.columns = ['customer_id', 'historical_clv']
        
        # Purchase frequency
        trans_grouped = trans.groupby('customer_id').agg({
            'transaction_id': 'count',
            'transaction_date': 'min'
        }).reset_index()
        trans_grouped.columns = ['customer_id', 'lifetime_purchases', 'first_purchase_date']
        trans_grouped['purchase_frequency'] = trans_grouped['lifetime_purchases'] / (
            (pd.to_datetime(datetime.now()) - pd.to_datetime(trans_grouped['first_purchase_date'])).dt.days / 30 + 1
        )
        
        # Average order value
        avg_order = trans.groupby('customer_id')['transaction_amount'].mean().reset_index()
        avg_order.columns = ['customer_id', 'avg_order_value']
        
        # Months as customer
        months_customer = customers_df[['customer_id', 'signup_date']].copy()
        months_customer['months_as_customer'] = (
            (pd.to_datetime(datetime.now()) - pd.to_datetime(months_customer['signup_date'])).dt.days / 30
        ).round(0)
        
        # Merge
        clv_df = historical_clv.merge(trans_grouped[['customer_id', 'lifetime_purchases', 'purchase_frequency']], 
                                      on='customer_id')
        clv_df = clv_df.merge(avg_order, on='customer_id')
        clv_df = clv_df.merge(months_customer[['customer_id', 'months_as_customer']], on='customer_id')
        
        # Predict 12-month and 24-month CLV
        clv_df['predicted_clv_12m'] = clv_df['avg_order_value'] * clv_df['purchase_frequency'] * 12
        clv_df['predicted_clv_24m'] = clv_df['predicted_clv_12m'] * 2
        
        return clv_df

# ============================================================================
# SUMMARY METRICS
# ============================================================================

def calculate_all_metrics(transactions_df, customers_df, products_df, journey_df, metrics_df):
    """Calculate all metrics at once"""
    
    print("\n" + "=" * 80)
    print("CALCULATING METRICS")
    print("=" * 80)
    
    metrics_dict = {
        'customer_ltv': CustomerMetrics.calculate_ltv(transactions_df, customers_df),
        'product_performance': ProductMetrics.calculate_product_performance(transactions_df, products_df),
        'conversion_funnel': ProductMetrics.calculate_conversion_rates(transactions_df, journey_df),
        'monthly_growth': GrowthMetrics.calculate_monthly_growth(transactions_df),
        'experience_engagement': ExperienceMetrics.calculate_engagement_score(transactions_df, journey_df, customers_df),
    }
    
    print("✓ All metrics calculated successfully")
    return metrics_dict