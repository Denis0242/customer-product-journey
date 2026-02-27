"""
Page 5: Growth Metrics & Trends
Month-over-month growth, cohort analysis, retention curves
"""

import streamlit as st
import pandas as pd
import os
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import mysql.connector
from datetime import datetime, timedelta

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Growth Metrics",
    page_icon="🚀",
    layout="wide"
)

# ============================================================================
# DATABASE CONNECTION
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
#     except Exception as e:
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
#         except Exception as e:
#             st.error(f"Query error: {e}")
#             return pd.DataFrame()
#     return pd.DataFrame()

# ============================================================================
# DATA LOADING
# ============================================================================

def load_csv(filename):
            path = f'C:/Users/Admin/Desktop/Freelance/Denis/Projects/cx_product_ds_capstone/02_data_generation/data/{filename}'
            if os.path.exists(path):
                return pd.read_csv(path)
            else:
                st.error(f"File not found: {path}")
                return pd.DataFrame()

# def load_economics_data():
#     return load_csv('transactions.csv')


@st.cache_data(ttl=600)
def load_growth_data():
    """Load transaction and customer data"""
    trans = load_csv('transactions.csv')
    cust = load_csv('customers.csv')
    return trans, cust



# ============================================================================
# ANALYSIS FUNCTIONS
# ============================================================================

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
    
    monthly.columns = ['month', 'revenue', 'orders', 'unique_customers']
    monthly['month'] = monthly['month'].astype(str)
    monthly['mom_revenue_growth'] = monthly['revenue'].pct_change() * 100
    monthly['mom_order_growth'] = monthly['orders'].pct_change() * 100
    monthly['mom_customer_growth'] = monthly['unique_customers'].pct_change() * 100
    
    return monthly

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

def calculate_retention_by_cohort(transactions_df, customers_df):
    """Calculate retention rate by cohort"""
    
    trans = transactions_df[transactions_df['order_status'] == 'completed'].copy()
    trans['transaction_date'] = pd.to_datetime(trans['transaction_date'])
    customers_df['signup_date'] = pd.to_datetime(customers_df['signup_date'])
    
    trans = trans.merge(customers_df[['customer_id', 'signup_date']], on='customer_id')
    
    trans['cohort'] = trans['signup_date'].dt.to_period('M')
    trans['month'] = trans['transaction_date'].dt.to_period('M')
    trans['months_since_signup'] = (trans['month'] - trans['cohort']).apply(lambda x: x.n)
    
    # First month cohort size
    cohort_size = trans[trans['months_since_signup'] == 0].groupby('cohort')['customer_id'].nunique()
    
    # Users returning by month
    cohort_return = trans.groupby(['cohort', 'months_since_signup'])['customer_id'].nunique()
    
    # Retention rate
    retention = cohort_return.div(cohort_size, level='cohort') * 100
    
    return retention.unstack(fill_value=0)

def calculate_customer_acquisition(customers_df):
    """Calculate monthly customer acquisition"""
    
    cust = customers_df.copy()
    cust['signup_date'] = pd.to_datetime(cust['signup_date'])
    
    monthly_acq = cust.groupby(cust['signup_date'].dt.to_period('M')).agg({
        'customer_id': 'count'
    }).reset_index()
    
    monthly_acq.columns = ['month', 'new_customers']
    monthly_acq['month'] = monthly_acq['month'].astype(str)
    
    return monthly_acq

# ============================================================================
# PAGE CONTENT
# ============================================================================

def main():
    st.title("🚀 Growth Metrics & Analysis")
    st.markdown("---")
    
    # Load data
    with st.spinner("Loading growth data..."):
        transactions_df, customers_df = load_growth_data()
    
    if transactions_df.empty:
        st.warning("No data available")
        return
    
    # Monthly growth metrics
    monthly_growth = calculate_monthly_growth(transactions_df)
    
    st.markdown("### 📊 Month-over-Month Growth")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        latest_revenue = monthly_growth['revenue'].iloc[-1]
        st.metric(
            "💰 Latest Month Revenue",
            f"${latest_revenue:,.0f}",
            delta=f"{monthly_growth['mom_revenue_growth'].iloc[-1]:.1f}%" if not pd.isna(monthly_growth['mom_revenue_growth'].iloc[-1]) else "N/A"
        )
    
    with col2:
        latest_orders = monthly_growth['orders'].iloc[-1]
        st.metric(
            "📦 Latest Month Orders",
            f"{latest_orders:,.0f}",
            delta=f"{monthly_growth['mom_order_growth'].iloc[-1]:.1f}%" if not pd.isna(monthly_growth['mom_order_growth'].iloc[-1]) else "N/A"
        )
    
    with col3:
        latest_customers = monthly_growth['unique_customers'].iloc[-1]
        st.metric(
            "👥 Unique Customers",
            f"{latest_customers:,.0f}",
            delta=f"{monthly_growth['mom_customer_growth'].iloc[-1]:.1f}%" if not pd.isna(monthly_growth['mom_customer_growth'].iloc[-1]) else "N/A"
        )
    
    with col4:
        avg_order_value = latest_revenue / latest_orders if latest_orders > 0 else 0
        st.metric(
            "🛒 Avg Order Value",
            f"${avg_order_value:.2f}",
            delta="Per order"
        )
    
    # Revenue trend
    st.markdown("---")
    st.markdown("### 💹 Monthly Revenue & Order Trend")
    
    fig_monthly = go.Figure()
    
    fig_monthly.add_trace(go.Bar(
        x=monthly_growth['month'],
        y=monthly_growth['revenue'],
        name='Revenue',
        marker=dict(color='#636EFA'),
        yaxis='y'
    ))
    
    fig_monthly.add_trace(go.Scatter(
        x=monthly_growth['month'],
        y=monthly_growth['mom_revenue_growth'],
        name='MoM Growth %',
        marker=dict(color='#FFA15A', size=8),
        line=dict(width=3),
        yaxis='y2'
    ))
    
    fig_monthly.update_layout(
        title='Monthly Revenue with Growth Rate',
        hovermode='x unified',
        height=400,
        yaxis=dict(title='Revenue ($)'),
        yaxis2=dict(
            title='MoM Growth (%)',
            overlaying='y',
            side='right'
        ),
        xaxis=dict(title='Month'),
        template='plotly_white'
    )
    
    st.plotly_chart(fig_monthly, use_container_width=True)
    
    # Customer acquisition
    st.markdown("---")
    st.markdown("### 👥 Customer Acquisition Trend")
    
    monthly_acq = calculate_customer_acquisition(customers_df)
    
    fig_acq = px.bar(
        monthly_acq,
        x='month',
        y='new_customers',
        title='New Customers per Month',
        labels={'new_customers': 'New Customers', 'month': 'Month'},
        color='new_customers',
        text='new_customers',
        color_continuous_scale='Viridis'
    )
    fig_acq.update_traces(textposition='outside')
    fig_acq.update_xaxes(tickangle=-45)
    fig_acq.update_layout(height=400)
    st.plotly_chart(fig_acq, use_container_width=True)
    
    # Cohort analysis
    st.markdown("---")
    st.markdown("### 📊 Cohort Analysis (User Count)")
    
    cohort_table = calculate_cohort_analysis(transactions_df, customers_df)
    
    if not cohort_table.empty:
        # Heatmap
        fig_cohort = px.imshow(
            cohort_table,
            labels=dict(x='Months Since Signup', y='Cohort Month', color='Customers'),
            title='Customer Cohort Analysis Heatmap',
            color_continuous_scale='Blues',
            aspect='auto'
        )
        fig_cohort.update_layout(height=500)
        st.plotly_chart(fig_cohort, use_container_width=True)
        
        # Display table
        st.markdown("### 📈 Cohort Table")
        st.dataframe(cohort_table, use_container_width=True)
    
    # Retention analysis
    st.markdown("---")
    st.markdown("### 📉 Cohort Retention Rate (%)")
    
    retention_table = calculate_retention_by_cohort(transactions_df, customers_df)
    
    if not retention_table.empty:
        # Retention heatmap
        fig_retention = px.imshow(
            retention_table,
            labels=dict(x='Months Since Signup', y='Cohort Month', color='Retention %'),
            title='Customer Retention Rate Heatmap (%)',
            color_continuous_scale='RdYlGn',
            aspect='auto',
            zmin=0,
            zmax=100
        )
        fig_retention.update_layout(height=500)
        st.plotly_chart(fig_retention, use_container_width=True)
        
        # Display table
        st.markdown("### 📊 Retention Rate Table (%)")
        st.dataframe(retention_table.round(1), use_container_width=True)
    
    # Growth rate analysis
    st.markdown("---")
    st.markdown("### 📈 Growth Rate Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_rev_growth = px.line(
            monthly_growth,
            x='month',
            y='mom_revenue_growth',
            title='Month-over-Month Revenue Growth %',
            labels={'mom_revenue_growth': 'Growth (%)', 'month': 'Month'},
            markers=True
        )
        fig_rev_growth.update_traces(
            line=dict(color='#636EFA', width=3),
            marker=dict(size=8)
        )
        fig_rev_growth.add_hline(y=0, line_dash='dash', line_color='red')
        fig_rev_growth.update_layout(height=400, template='plotly_white')
        st.plotly_chart(fig_rev_growth, use_container_width=True)
    
    with col2:
        fig_customer_growth = px.line(
            monthly_growth,
            x='month',
            y='mom_customer_growth',
            title='Month-over-Month Customer Growth %',
            labels={'mom_customer_growth': 'Growth (%)', 'month': 'Month'},
            markers=True
        )
        fig_customer_growth.update_traces(
            line=dict(color='#00CC96', width=3),
            marker=dict(size=8)
        )
        fig_customer_growth.add_hline(y=0, line_dash='dash', line_color='red')
        fig_customer_growth.update_layout(height=400, template='plotly_white')
        st.plotly_chart(fig_customer_growth, use_container_width=True)
    
    # Growth metrics table
    st.markdown("---")
    st.markdown("### 📊 Monthly Growth Metrics Table")
    
    growth_table = monthly_growth[['month', 'revenue', 'orders', 'unique_customers', 'mom_revenue_growth', 'mom_order_growth']].copy()
    growth_table.columns = ['Month', 'Revenue', 'Orders', 'Customers', 'Revenue Growth %', 'Order Growth %']
    
    st.dataframe(growth_table, use_container_width=True)
    
    # Key insights
    st.markdown("---")
    st.markdown("### 💡 Key Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_mom_growth = monthly_growth['mom_revenue_growth'].mean()
        st.info(f"""
        **Average MoM Revenue Growth**
        
        {avg_mom_growth:.1f}%
        """)
    
    with col2:
        total_new_customers = monthly_acq['new_customers'].sum()
        st.info(f"""
        **Total New Customers (Period)**
        
        {total_new_customers:,}
        """)
    
    with col3:
        best_month = monthly_growth.nlargest(1, 'revenue')
        if not best_month.empty:
            st.success(f"""
            **Best Month**
            
            {best_month['month'].values[0]}: ${best_month['revenue'].values[0]:,.0f}
            """)

if __name__ == "__main__":
    main()