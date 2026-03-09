"""
Customer Experience & Product Analytics Dashboard
Main Streamlit Application with Multi-page Navigation
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from streamlit_option_menu import option_menu
import mysql.connector
from mysql.connector import Error
from pathlib import Path

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Customer Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM STYLING
# ============================================================================

st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .metric-value {
        font-size: 32px;
        font-weight: bold;
        margin: 10px 0;
    }
    
    .metric-label {
        font-size: 14px;
        opacity: 0.9;
    }
    
    .section-title {
        color: #1f77b4;
        border-bottom: 3px solid #1f77b4;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    
    .insight-box {
        background: #f0f4ff;
        border-left: 4px solid #667eea;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DATABASE UTILITIES
# ============================================================================

# @st.cache_resource
# def get_db_connection():
#     """Get database connection"""
#     try:
#         connection = mysql.connector.connect(
#             host='localhost',
#             user='root',
#             password='',
#             database='customer_analytics'
#         )
#         return connection
#     except Error as e:
#         st.error(f"Database connection error: {e}")
#         return None

# @st.cache_data(ttl=600)
# def load_data(query):
#     """Load data from database with caching"""
#     conn = get_db_connection()
#     if conn:
#         try:
#             df = pd.read_sql(query, conn)
#             return df
#         except Error as e:
#             st.error(f"Query error: {e}")
#             return pd.DataFrame()
#     return pd.DataFrame()





def load_csv(filename):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root
    data_path = os.path.join(base_dir, "02_data_generation", "data", filename)

    if os.path.exists(data_path):
        return pd.read_csv(data_path)
    else:
        st.error(f"File not found: {data_path}")
        return pd.DataFrame()

# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

def load_all_data():
    """Load all necessary data"""
    data = {}
    
    # Customers
    data['customers'] = load_csv('customers.csv')
    
    # Products
    data['products'] = load_csv('products.csv')
    
    # Transactions
    data['transactions'] = load_csv('transactions.csv')
    
    # Customer Journey
    data['journey'] = load_csv('customer_journey.csv')
    # Product Metrics
    data['metrics'] = load_csv('product_metrics.csv')
    return data

# ============================================================================
# METRIC CALCULATION FUNCTIONS
# ============================================================================

def calculate_key_metrics(transactions_df, customers_df):
    """Calculate key performance indicators"""
    
    completed_trans = transactions_df[transactions_df['order_status'] == 'completed']
    
    metrics = {
        'total_revenue': completed_trans['transaction_amount'].sum(),
        'total_profit': completed_trans['profit_amount'].sum(),
        'total_customers': len(customers_df),
        'active_customers': len(customers_df[customers_df['customer_status'] == 'active']),
        'total_orders': len(completed_trans),
        'avg_order_value': completed_trans['transaction_amount'].mean(),
        'repeat_customers': len(completed_trans[completed_trans['is_repeat_purchase'] == True]['customer_id'].unique()),
    }
    
    # Calculate additional metrics
    metrics['gross_margin'] = (metrics['total_profit'] / metrics['total_revenue'] * 100) if metrics['total_revenue'] > 0 else 0
    metrics['churn_rate'] = (len(customers_df[customers_df['customer_status'] == 'churned']) / len(customers_df) * 100) if len(customers_df) > 0 else 0
    metrics['repeat_rate'] = (metrics['repeat_customers'] / metrics['total_customers'] * 100) if metrics['total_customers'] > 0 else 0
    metrics['cac'] = 100  # Marketing spend / new customers - simplified
    
    return metrics

# ============================================================================
# PAGE: EXECUTIVE OVERVIEW
# ============================================================================

def page_executive_overview(data):
    """Executive Overview Dashboard"""
    st.title("📊 Executive Overview")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_segment = st.multiselect(
            "Customer Segment",
            data['customers']['segment'].unique(),
            default=data['customers']['segment'].unique()
        )
    
    with col2:
        selected_status = st.multiselect(
            "Customer Status",
            data['customers']['customer_status'].unique(),
            default=['active']
        )
    
    with col3:
        date_range = st.date_input(
            "Date Range",
            value=(datetime.now() - timedelta(days=90), datetime.now()),
            max_value=datetime.now()
        )
    
    # Filter data
    filtered_customers = data['customers'][
        (data['customers']['segment'].isin(selected_segment)) &
        (data['customers']['customer_status'].isin(selected_status))
    ]
    
    filtered_transactions = data['transactions'][
        (data['transactions']['customer_id'].isin(filtered_customers['customer_id']))
    ]
    
    # Calculate metrics
    metrics = calculate_key_metrics(filtered_transactions, filtered_customers)
    
    # Display KPI cards
    st.markdown("### 📈 Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Revenue",
            f"${metrics['total_revenue']:,.2f}",
            delta=f"{metrics['gross_margin']:.1f}% Margin"
        )
    
    with col2:
        st.metric(
            "Total Customers",
            f"{metrics['total_customers']:,}",
            delta=f"{metrics['active_customers']} Active"
        )
    
    with col3:
        st.metric(
            "Avg Order Value",
            f"${metrics['avg_order_value']:.2f}",
            delta=f"{metrics['repeat_rate']:.1f}% Repeat"
        )
    
    with col4:
        st.metric(
            "Churn Rate",
            f"{metrics['churn_rate']:.2f}%",
            delta="Watch this metric"
        )
    
    # Revenue trend
    st.markdown("### 💹 Revenue Trend (Last 90 Days)")
    
    trans_copy = filtered_transactions.copy()
    trans_copy['transaction_date'] = pd.to_datetime(trans_copy['transaction_date'])
    daily_revenue = trans_copy[trans_copy['order_status'] == 'completed'].groupby(trans_copy['transaction_date'].dt.date)[
        'transaction_amount'].sum().reset_index()
    daily_revenue.columns = ['date', 'revenue']
    
    fig_revenue = px.line(daily_revenue, x='date', y='revenue', 
                          title='Daily Revenue',
                          labels={'revenue': 'Revenue ($)', 'date': 'Date'},
                          markers=True)
    fig_revenue.update_layout(hovermode='x unified', height=400)
    st.plotly_chart(fig_revenue, use_container_width=True)
    
    # Customer segment distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 👥 Customer Distribution by Segment")
        segment_dist = filtered_customers['segment'].value_counts()
        fig_segment = px.pie(values=segment_dist.values, names=segment_dist.index,
                            title='Customers by Segment',
                            color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig_segment, use_container_width=True)
    
    with col2:
        st.markdown("### 📊 Order Status Distribution")
        status_dist = filtered_transactions['order_status'].value_counts()
        fig_status = px.bar(x=status_dist.index, y=status_dist.values,
                           title='Orders by Status',
                           labels={'x': 'Status', 'y': 'Count'},
                           color=status_dist.index,
                           color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig_status, use_container_width=True)

# ============================================================================
# PAGE: CUSTOMER JOURNEY
# ============================================================================

def page_customer_journey(data):
    """Customer Journey Analysis"""
    st.title("🛤️ Customer Journey & Funnel Analysis")
    
    # Funnel analysis
    st.markdown("### 📊 Conversion Funnel")
    
    journey_copy = data['journey'].copy()
    
    funnel_stages = ['page_view', 'product_view', 'add_to_cart', 'checkout_start', 'checkout_complete']
    funnel_data = []
    
    for stage in funnel_stages:
        count = len(journey_copy[journey_copy['event_type'] == stage])
        funnel_data.append({'stage': stage.replace('_', ' ').title(), 'count': count})
    
    funnel_df = pd.DataFrame(funnel_data)
    funnel_df['percentage'] = (funnel_df['count'] / funnel_df['count'].iloc[0] * 100).round(2)
    
    fig_funnel = px.funnel(
        funnel_df,
        x='count',
        y='stage',
        title='Customer Conversion Funnel',
        labels={'count': 'Users', 'stage': 'Stage'},
        color='stage',
        color_discrete_sequence=px.colors.sequential.Blues
    )
    st.plotly_chart(fig_funnel, use_container_width=True)
    
    # Display conversion rates
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Page Views", f"{funnel_df.iloc[0]['count']:,}")
    with col2:
        if len(funnel_df) > 4:
            conversion = (funnel_df.iloc[4]['count'] / funnel_df.iloc[0]['count'] * 100)
            st.metric("Overall Conversion Rate", f"{conversion:.2f}%")
    with col3:
        st.metric("Total Conversions", f"{funnel_df.iloc[-1]['count']:,}")
    
    # Device analysis
    st.markdown("### 📱 Device Type Distribution")
    device_dist = data['journey']['device_type'].value_counts()
    fig_device = px.bar(x=device_dist.index, y=device_dist.values,
                       title='Events by Device Type',
                       labels={'x': 'Device', 'y': 'Count'},
                       color=device_dist.index,
                       color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig_device, use_container_width=True)
    
    # Event type distribution
    st.markdown("### 🔄 Event Type Distribution")
    event_dist = data['journey']['event_type'].value_counts().head(10)
    fig_events = px.bar(y=event_dist.index, x=event_dist.values,
                       orientation='h',
                       title='Top 10 Event Types',
                       labels={'x': 'Count', 'y': 'Event Type'},
                       color=event_dist.index,
                       color_discrete_sequence=px.colors.qualitative.Set3)
    st.plotly_chart(fig_events, use_container_width=True)

# ============================================================================
# PAGE: PRODUCT ANALYSIS
# ============================================================================

def page_product_analysis(data):
    """Product Performance Analysis"""
    st.title("🏆 Product Performance Analysis")
    
    st.markdown("### 📦 Product Lifecycle Distribution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        lifecycle_dist = data['products']['product_lifecycle_stage'].value_counts()
        fig_lifecycle = px.pie(values=lifecycle_dist.values, names=lifecycle_dist.index,
                              title='Products by Lifecycle Stage',
                              color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig_lifecycle, use_container_width=True)
    
    with col2:
        category_dist = data['products']['category'].value_counts()
        fig_category = px.bar(x=category_dist.index, y=category_dist.values,
                             title='Products by Category',
                             labels={'x': 'Category', 'y': 'Count'},
                             color=category_dist.index,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_category.update_xaxes(tickangle=-45)
        st.plotly_chart(fig_category, use_container_width=True)
    
    # Top products by revenue
    st.markdown("### 💰 Top 10 Products by Revenue")
    
    trans_copy = data['transactions'].copy()
    trans_copy['transaction_date'] = pd.to_datetime(trans_copy['transaction_date'])
    
    top_products = trans_copy[trans_copy['order_status'] == 'completed'].groupby('product_id').agg({
        'transaction_amount': 'sum',
        'transaction_id': 'count'
    }).reset_index().merge(data['products'][['product_id', 'product_name']], on='product_id')
    
    top_products.columns = ['product_id', 'revenue', 'orders', 'product_name']
    top_products = top_products.nlargest(10, 'revenue')
    
    fig_top = px.bar(top_products, x='product_name', y='revenue',
                    title='Top 10 Products by Revenue',
                    labels={'revenue': 'Revenue ($)', 'product_name': 'Product'},
                    color='revenue',
                    color_continuous_scale='Blues')
    fig_top.update_xaxes(tickangle=-45)
    st.plotly_chart(fig_top, use_container_width=True)
    
    # Price distribution
    st.markdown("### 💲 Price Distribution")
    fig_price = px.histogram(data['products'], x='price', nbins=50,
                            title='Product Price Distribution',
                            labels={'price': 'Price ($)', 'count': 'Number of Products'},
                            color_discrete_sequence=['#636EFA'])
    st.plotly_chart(fig_price, use_container_width=True)

# ============================================================================
# PAGE: UNIT ECONOMICS
# ============================================================================

def page_unit_economics(data):
    """Unit Economics Analysis"""
    st.title("💹 Unit Economics & Profitability")
    
    trans_copy = data['transactions'].copy()
    trans_copy['transaction_date'] = pd.to_datetime(trans_copy['transaction_date'])
    
    completed_trans = trans_copy[trans_copy['order_status'] == 'completed']
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_revenue = completed_trans['transaction_amount'].sum()
        st.metric("Total Revenue", f"${total_revenue:,.2f}")
    
    with col2:
        total_profit = completed_trans['profit_amount'].sum()
        st.metric("Total Profit", f"${total_profit:,.2f}")
    
    with col3:
        margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        st.metric("Gross Margin", f"{margin:.2f}%")
    
    with col4:
        avg_cost = data['products']['cost'].mean()
        st.metric("Avg Cost per Unit", f"${avg_cost:.2f}")
    
    # Margin by category
    st.markdown("### 📊 Profitability by Category")
    
    margin_by_category = completed_trans.merge(
        data['products'][['product_id', 'category']],
        on='product_id'
    ).groupby('category').agg({
        'transaction_amount': 'sum',
        'profit_amount': 'sum'
    }).reset_index()
    
    margin_by_category['margin_percent'] = (
        margin_by_category['profit_amount'] / margin_by_category['transaction_amount'] * 100
    ).round(2)
    margin_by_category.columns = ['category', 'revenue', 'profit', 'margin_percent']
    
    fig_margin = px.bar(margin_by_category, x='category', y='margin_percent',
                       title='Gross Margin by Category',
                       labels={'margin_percent': 'Margin (%)', 'category': 'Category'},
                       color='margin_percent',
                       color_continuous_scale='RdYlGn')
    fig_margin.update_xaxes(tickangle=-45)
    st.plotly_chart(fig_margin, use_container_width=True)
    
    # Monthly profitability trend
    st.markdown("### 📈 Monthly Profit Trend")
    
    monthly_profit = completed_trans.groupby(completed_trans['transaction_date'].dt.to_period('M')).agg({
        'transaction_amount': 'sum',
        'profit_amount': 'sum'
    }).reset_index()
    
    monthly_profit['transaction_date'] = monthly_profit['transaction_date'].astype(str)
    monthly_profit.columns = ['month', 'revenue', 'profit']
    
    fig_monthly = go.Figure()
    fig_monthly.add_trace(go.Bar(x=monthly_profit['month'], y=monthly_profit['revenue'],
                                 name='Revenue', marker_color='#636EFA'))
    fig_monthly.add_trace(go.Bar(x=monthly_profit['month'], y=monthly_profit['profit'],
                                 name='Profit', marker_color='#00CC96'))
    
    fig_monthly.update_layout(title='Monthly Revenue vs Profit',
                             barmode='group', height=400,
                             xaxis_title='Month', yaxis_title='Amount ($)')
    st.plotly_chart(fig_monthly, use_container_width=True)

# ============================================================================
# PAGE: GROWTH METRICS
# ============================================================================

def page_growth_metrics(data):
    """Growth Analysis"""
    st.title("🚀 Growth Metrics & Trends")
    
    trans_copy = data['transactions'].copy()
    trans_copy['transaction_date'] = pd.to_datetime(trans_copy['transaction_date'])
    
    completed_trans = trans_copy[trans_copy['order_status'] == 'completed']
    
    # Monthly growth
    st.markdown("### 📊 Month-over-Month Growth")
    
    monthly_metrics = completed_trans.groupby(completed_trans['transaction_date'].dt.to_period('M')).agg({
        'transaction_amount': 'sum',
        'transaction_id': 'count',
        'customer_id': 'nunique'
    }).reset_index()
    
    monthly_metrics['transaction_date'] = monthly_metrics['transaction_date'].astype(str)
    monthly_metrics.columns = ['month', 'revenue', 'orders', 'customers']
    
    fig_monthly = px.line(monthly_metrics, x='month', y='revenue',
                         title='Monthly Revenue Trend',
                         labels={'revenue': 'Revenue ($)', 'month': 'Month'},
                         markers=True)
    fig_monthly.update_layout(hovermode='x unified', height=400)
    st.plotly_chart(fig_monthly, use_container_width=True)
    
    # Customer acquisition trend
    st.markdown("### 👥 New Customers per Month")
    
    customers_copy = data['customers'].copy()
    customers_copy['signup_date'] = pd.to_datetime(customers_copy['signup_date'])
    
    new_customers = customers_copy.groupby(customers_copy['signup_date'].dt.to_period('M')).size().reset_index(name='new_customers')
    new_customers['signup_date'] = new_customers['signup_date'].astype(str)
    
    fig_customers = px.bar(new_customers, x='signup_date', y='new_customers',
                          title='New Customer Acquisitions',
                          labels={'new_customers': 'New Customers', 'signup_date': 'Month'},
                          color='new_customers',
                          color_continuous_scale='Blues')
    fig_customers.update_xaxes(tickangle=-45)
    st.plotly_chart(fig_customers, use_container_width=True)
    
    # Cohort retention
    st.markdown("### 📈 Cohort Retention Analysis")
    
    cohort_data = completed_trans.merge(
        customers_copy[['customer_id', 'signup_date']],
        on='customer_id'
    )
    
    cohort_data['cohort'] = cohort_data['signup_date'].dt.to_period('M')
    cohort_data['month'] = cohort_data['transaction_date'].dt.to_period('M')
    cohort_data['months_since_signup'] = (cohort_data['month'] - cohort_data['cohort']).apply(lambda x: x.n)
    
    cohort_retention = cohort_data[cohort_data['months_since_signup'] >= 0].groupby(
        ['cohort', 'months_since_signup']
    )['customer_id'].nunique().unstack(fill_value=0)
    
    st.write(cohort_retention.head(10))

# ============================================================================
# PAGE: CUSTOMER EXPERIENCE 3D
# ============================================================================

def page_customer_experience_3d(data):
    """Customer Experience Multi-dimensional View"""
    st.title("🎯 Customer Experience 3D View")
    
    st.markdown("""
    This page analyzes customer experience through three dimensions:
    - **Engagement** (activity & interactions)
    - **Satisfaction** (quality metrics)
    - **Loyalty** (repeat purchases & retention)
    """)
    
    # Create a 3D scatter plot
    trans_copy = data['transactions'].copy()
    completed_trans = trans_copy[trans_copy['order_status'] == 'completed']
    
    journey_copy = data['journey'].copy()
    
    # Calculate engagement score
    engagement = journey_copy.groupby('customer_id').size().reset_index(name='engagement')
    
    # Calculate loyalty score
    loyalty = completed_trans.groupby('customer_id').agg(
    purchases=('transaction_id', 'count'),
    total_spent=('transaction_amount', 'sum')
    ).reset_index()
    
    
    
    # Merge metrics
    customer_3d = data['customers'][['customer_id', 'segment']].copy()
    customer_3d = customer_3d.merge(engagement, on='customer_id', how='left')
    customer_3d = customer_3d.merge(loyalty, on='customer_id', how='left')
    customer_3d = customer_3d.fillna(0)
    customer_3d.columns = ['customer_id', 'segment', 'engagement', 'purchases', 'total_spent']
    
    # Create 3D scatter
    fig_3d = px.scatter_3d(
        customer_3d,
        x='engagement',
        y='purchases',
        z='total_spent',
        color='segment',
        title='Customer Experience 3D View (Engagement vs Purchases vs Spend)',
        labels={'engagement': 'Engagement Score', 'purchases': 'Purchase Count', 'total_spent': 'Total Spent ($)'},
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_3d.update_layout(height=600)
    st.plotly_chart(fig_3d, use_container_width=True)
    
    # Segment analysis
    st.markdown("### 📊 Metrics by Segment")
    
    segment_metrics = customer_3d.groupby('segment').agg({
        'engagement': 'mean',
        'purchases': 'mean',
        'total_spent': 'mean',
        'customer_id': 'count'
    }).reset_index().round(2)
    
    segment_metrics.columns = ['Segment', 'Avg Engagement', 'Avg Purchases', 'Avg Spent ($)', 'Customer Count']
    st.dataframe(segment_metrics, use_container_width=True)

# ============================================================================
# PAGE: PREDICTIONS
# ============================================================================

def page_predictions(data):
    """Predictive Analytics"""
    st.title("🔮 Predictive Analytics & Recommendations")
    
    st.markdown("""
    This section uses machine learning to predict customer behavior and provide actionable recommendations.
    """)
    
    trans_copy = data['transactions'].copy()
    completed_trans = trans_copy[trans_copy['order_status'] == 'completed']
    
    # CLV Prediction
    st.markdown("### 💰 Customer Lifetime Value (CLV) Prediction")
    
    clv_data = completed_trans.groupby('customer_id').agg({
        'transaction_amount': ['sum', 'count', 'mean']
    }).reset_index()
    
    clv_data.columns = ['customer_id', 'historical_clv', 'purchase_count', 'avg_order_value']
    
    # Predict 12-month CLV
    clv_data['predicted_clv_12m'] = clv_data['avg_order_value'] * (clv_data['purchase_count'] / 12) * 12
    clv_data = clv_data.merge(data['customers'][['customer_id', 'segment']], on='customer_id')
    
    # Top CLV customers
    top_clv = clv_data.nlargest(10, 'predicted_clv_12m')[['customer_id', 'historical_clv', 'predicted_clv_12m', 'segment']]
    
    st.markdown("#### Top 10 Customers by Predicted 12-Month CLV")
    st.dataframe(top_clv, use_container_width=True)
    
    # CLV distribution by segment
    st.markdown("#### CLV Distribution by Segment")
    fig_clv = px.box(clv_data, x='segment', y='predicted_clv_12m',
                    title='12-Month CLV Prediction by Segment',
                    labels={'predicted_clv_12m': 'Predicted CLV ($)', 'segment': 'Segment'},
                    color='segment',
                    color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig_clv, use_container_width=True)
    
    # Churn Risk
    st.markdown("### ⚠️ Churn Risk Prediction")
    
    # Calculate days since last purchase
    customers_copy = data['customers'].copy()
    # last_purchase = completed_trans.groupby('customer_id')['transaction_date'] = pd.to_datetime(completed_trans['transaction_date'])
    last_purchase = completed_trans.groupby('customer_id')['transaction_date'].max().reset_index()
    last_purchase['days_inactive'] = (pd.to_datetime(datetime.now()) - pd.to_datetime(last_purchase['transaction_date'])).dt.days
    
    churn_risk = customers_copy[['customer_id', 'segment']].merge(last_purchase[['customer_id', 'days_inactive']], on='customer_id', how='left')
    churn_risk['days_inactive'] = churn_risk['days_inactive'].fillna(churn_risk['days_inactive'].max())
    
    # Calculate risk score
    max_inactivity = churn_risk['days_inactive'].quantile(0.95)
    churn_risk['churn_risk_score'] = (churn_risk['days_inactive'] / max_inactivity * 100).clip(0, 100)
    churn_risk['risk_level'] = pd.cut(churn_risk['churn_risk_score'], bins=[0, 33, 66, 100], labels=['Low', 'Medium', 'High'])
    
    # High-risk customers
    high_risk = churn_risk[churn_risk['risk_level'] == 'High'].nlargest(10, 'churn_risk_score')
    
    st.markdown("#### Top 10 High-Risk Customers")
    st.dataframe(high_risk, use_container_width=True)
    
    # Risk distribution
    fig_risk = px.histogram(churn_risk, x='churn_risk_score', nbins=30,
                           title='Churn Risk Score Distribution',
                           labels={'churn_risk_score': 'Risk Score (0-100)', 'count': 'Number of Customers'},
                           color_discrete_sequence=['#EF553B'])
    st.plotly_chart(fig_risk, use_container_width=True)

# ============================================================================
# MAIN APP LOGIC
# ============================================================================

def main():
    # Sidebar navigation
    with st.sidebar:
        st.title("📊 Analytics Dashboard")
        
        page = option_menu(
            menu_title="Navigation",
            options=["Executive Overview", "Customer Journey", "Product Analysis", 
                    "Unit Economics", "Growth Metrics", "Customer Experience 3D", "Predictions"],
            icons=["bar-chart", "arrow-right", "box", "chart-line", "rocket", "box", "lightbulb"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "5!important", "background-color": "#f8f9fa"},
                "icon": {"color": "orange", "font-size": "25px"},
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "left",
                    "margin": "0px",
                    "--hover-color": "#eee",
                },
            },
        )
        
        st.markdown("---")
        st.markdown("### 📌 Data Info")
        st.info("This dashboard uses synthetic data for demonstration purposes.")
    
    # Load data
    with st.spinner("Loading data..."):
        data = load_all_data()
    
    # Route to selected page
    if page == "Executive Overview":
        page_executive_overview(data)
    elif page == "Customer Journey":
        page_customer_journey(data)
    elif page == "Product Analysis":
        page_product_analysis(data)
    elif page == "Unit Economics":
        page_unit_economics(data)
    elif page == "Growth Metrics":
        page_growth_metrics(data)
    elif page == "Customer Experience 3D":
        page_customer_experience_3d(data)
    elif page == "Predictions":
        page_predictions(data)

if __name__ == "__main__":
    main()