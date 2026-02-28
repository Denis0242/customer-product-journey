"""
Page 3: Product Analysis
Product performance, lifecycle stages, and category insights
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.graph_objects as go
import plotly.express as px
import mysql.connector
from datetime import datetime, timedelta

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Product Analysis",
    page_icon="🏆",
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

def load_csv(filename):
            path = f'C:/My_Projects/All_Projects/cx_product_cap/02_data_generation/data/{filename}'
            if os.path.exists(path):
                return pd.read_csv(path)
            else:
                st.error(f"File not found: {path}")
                return pd.DataFrame()

def load_product_data():
    return load_csv('products.csv')


# ============================================================================
# DATA LOADING
# ============================================================================

# @st.cache_data(ttl=600)
# def load_product_data():
#     """Load product data"""
#     return load_data("SELECT * FROM products;")

@st.cache_data(ttl=600)
# def load_transactions_data():
#     """Load transaction data"""
#     return load_data("SELECT * FROM transactions;")
def load_transactions_csv():
    """
    Load transactions data from CSV
    
    Returns:
        pd.DataFrame: Transaction data with columns:
            - transaction_id, customer_id, product_id, transaction_date
            - transaction_time, quantity, unit_price, discount_applied
            - transaction_amount, profit_amount, payment_method
            - order_status, is_repeat_purchase
    """
    path = r'C:/My_Projects/All_Projects/cx_product_cap/02_data_generation/data/transactions.csv'
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    return pd.read_csv(path)


@st.cache_data(ttl=600)
def load_csv(filename):
    """Load CSV file from data folder"""
    data_dir = 'C:/My_Projects/All_Projects/cx_product_cap/02_data_generation/data/'
    file_path = os.path.join(data_dir, filename)
    
    try:
        if not os.path.exists(file_path):
            st.warning(f"File not found: {file_path}")
            return pd.DataFrame()
        
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        st.error(f"Error loading {filename}: {e}")
        return pd.DataFrame()

# ============================================================================
# ANALYSIS FUNCTIONS
# ============================================================================

def analyze_product_performance(transactions_df, products_df):
    """Calculate product performance metrics"""
    
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
    
    # Merge with product info
    perf = perf.merge(products_df[['product_id', 'product_name', 'category', 'product_lifecycle_stage']], on='product_id')
    
    return perf

def analyze_lifecycle_stage(transactions_df, products_df):
    """Analyze metrics by product lifecycle stage"""
    
    trans = transactions_df[transactions_df['order_status'] == 'completed'].copy()
    
    lifecycle_metrics = trans.merge(
        products_df[['product_id', 'product_lifecycle_stage']],
        on='product_id'
    ).groupby('product_lifecycle_stage').agg({
        'transaction_id': 'count',
        'transaction_amount': ['sum', 'mean'],
        'customer_id': 'nunique',
        'profit_amount': 'sum'
    }).round(2)
    
    lifecycle_metrics.columns = ['transactions', 'total_revenue', 'avg_transaction', 'unique_customers', 'profit']
    lifecycle_metrics['avg_profit'] = (lifecycle_metrics['profit'] / lifecycle_metrics['transactions']).round(2)
    
    return lifecycle_metrics.reset_index()

def analyze_category_performance(transactions_df, products_df):
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
# PAGE CONTENT
# ============================================================================

def main():
    st.title("🏆 Product Performance Analysis")
    st.markdown("---")
    
    # Load data
    with st.spinner("Loading product data..."):
        products_df = load_product_data()
        transactions_df = load_transactions_csv()
    
    if products_df.empty or transactions_df.empty:
        st.warning("No product data available")
        return
    
    # Filters
    st.markdown("### 🔍 Filters")
    col1, col2 = st.columns(2)
    
    with col1:
        selected_lifecycle = st.multiselect(
            "Product Lifecycle Stage",
            products_df['product_lifecycle_stage'].unique(),
            default=products_df['product_lifecycle_stage'].unique(),
            key="lifecycle_filter"
        )
    
    with col2:
        selected_category = st.multiselect(
            "Product Category",
            products_df['category'].unique(),
            default=products_df['category'].unique(),
            key="category_filter"
        )
    
    # Filter data
    filtered_products = products_df[
        (products_df['product_lifecycle_stage'].isin(selected_lifecycle)) &
        (products_df['category'].isin(selected_category))
    ]
    
    filtered_transactions = transactions_df[
        transactions_df['product_id'].isin(filtered_products['product_id'])
    ]
    
    # Key metrics
    completed_trans = filtered_transactions[filtered_transactions['order_status'] == 'completed']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📦 Total Products",
            f"{len(filtered_products):,}",
            delta=f"Active: {filtered_products['is_active'].sum()}"
        )
    
    with col2:
        st.metric(
            "💰 Total Revenue",
            f"${completed_trans['transaction_amount'].sum():,.0f}",
            delta=f"{len(completed_trans):,} Orders"
        )
    
    with col3:
        st.metric(
            "🎯 Avg Product Price",
            f"${filtered_products['price'].mean():.2f}",
            delta=f"${filtered_products['price'].min():.2f} - ${filtered_products['price'].max():.2f}"
        )
    
    with col4:
        profit_margin = (completed_trans['profit_amount'].sum() / completed_trans['transaction_amount'].sum() * 100) if completed_trans['transaction_amount'].sum() > 0 else 0
        st.metric(
            "📊 Profit Margin",
            f"{profit_margin:.2f}%",
            delta=f"${completed_trans['profit_amount'].sum():,.0f} Profit"
        )
    
    # Product lifecycle distribution
    st.markdown("---")
    st.markdown("### 📦 Product Lifecycle Stage Distribution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        lifecycle_dist = products_df['product_lifecycle_stage'].value_counts()
        
        lifecycle_colors = {
            'introduction': '#FFA15A',
            'growth': '#00CC96',
            'maturity': '#636EFA',
            'decline': '#EF553B'
        }
        
        fig_lifecycle = px.pie(
            values=lifecycle_dist.values,
            names=lifecycle_dist.index,
            title='Products by Lifecycle Stage',
            color=lifecycle_dist.index,
            color_discrete_map=lifecycle_colors
        )
        fig_lifecycle.update_layout(height=400)
        st.plotly_chart(fig_lifecycle, use_container_width=True)
    
    with col2:
        category_dist = products_df['category'].value_counts()
        
        fig_category = px.bar(
            x=category_dist.index,
            y=category_dist.values,
            title='Products by Category',
            labels={'x': 'Category', 'y': 'Count'},
            color=category_dist.index,
            text=category_dist.values,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_category.update_traces(textposition='outside')
        fig_category.update_xaxes(tickangle=-45)
        fig_category.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_category, use_container_width=True)
    
    # Top products by revenue
    st.markdown("---")
    st.markdown("### 💰 Top 15 Products by Revenue")
    
    perf = analyze_product_performance(filtered_transactions, filtered_products)
    top_products = perf.nlargest(15, 'total_revenue')
    
    fig_top = px.bar(
        top_products,
        x='product_name',
        y='total_revenue',
        color='total_revenue',
        title='Top 15 Products by Revenue',
        labels={'total_revenue': 'Revenue ($)', 'product_name': 'Product'},
        color_continuous_scale='Blues',
        text='total_revenue'
    )
    fig_top.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
    fig_top.update_xaxes(tickangle=-45)
    fig_top.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_top, use_container_width=True)
    
    # Lifecycle stage metrics
    st.markdown("---")
    st.markdown("### 📊 Metrics by Lifecycle Stage")
    
    lifecycle_perf = analyze_lifecycle_stage(filtered_transactions, filtered_products)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_lifecycle_rev = px.bar(
            lifecycle_perf,
            x='product_lifecycle_stage',
            y='total_revenue',
            color='product_lifecycle_stage',
            title='Revenue by Lifecycle Stage',
            labels={'total_revenue': 'Revenue ($)', 'product_lifecycle_stage': 'Stage'},
            text='total_revenue',
            color_discrete_map=lifecycle_colors
        )
        fig_lifecycle_rev.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
        fig_lifecycle_rev.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_lifecycle_rev, use_container_width=True)
    
    with col2:
        fig_lifecycle_trans = px.bar(
            lifecycle_perf,
            x='product_lifecycle_stage',
            y='transactions',
            color='product_lifecycle_stage',
            title='Transactions by Lifecycle Stage',
            labels={'transactions': 'Count', 'product_lifecycle_stage': 'Stage'},
            text='transactions',
            color_discrete_map=lifecycle_colors
        )
        fig_lifecycle_trans.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig_lifecycle_trans.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_lifecycle_trans, use_container_width=True)
    
    # Category performance
    st.markdown("---")
    st.markdown("### 🏷️ Category Performance")
    
    category_perf = analyze_category_performance(filtered_transactions, filtered_products)
    
    fig_category_perf = px.bar(
        category_perf,
        x='category',
        y='revenue',
        color='margin_percent',
        title='Category Revenue with Margin',
        labels={'revenue': 'Revenue ($)', 'category': 'Category', 'margin_percent': 'Margin %'},
        text='revenue',
        color_continuous_scale='RdYlGn'
    )
    fig_category_perf.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
    fig_category_perf.update_xaxes(tickangle=-45)
    fig_category_perf.update_layout(height=400)
    st.plotly_chart(fig_category_perf, use_container_width=True)
    
    # Category metrics table
    st.markdown("### 📊 Category Performance Table")
    
    category_table = category_perf[['category', 'transactions', 'revenue', 'customers', 'avg_transaction_value', 'margin_percent']].copy()
    category_table.columns = ['Category', 'Transactions', 'Revenue', 'Customers', 'Avg Transaction', 'Margin %']
    
    st.dataframe(category_table, use_container_width=True)
    
    # Price analysis
    st.markdown("---")
    st.markdown("### 💲 Product Price Distribution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_price = px.histogram(
            filtered_products,
            x='price',
            nbins=50,
            title='Product Price Distribution',
            labels={'price': 'Price ($)', 'count': 'Number of Products'},
            color_discrete_sequence=['#636EFA']
        )
        fig_price.update_layout(height=400)
        st.plotly_chart(fig_price, use_container_width=True)
    
    with col2:
        fig_cost = px.histogram(
            filtered_products,
            x='cost',
            nbins=50,
            title='Product Cost Distribution',
            labels={'cost': 'Cost ($)', 'count': 'Number of Products'},
            color_discrete_sequence=['#EF553B']
        )
        fig_cost.update_layout(height=400)
        st.plotly_chart(fig_cost, use_container_width=True)
    
    # Key insights
    st.markdown("---")
    st.markdown("### 💡 Key Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        top_product = perf.nlargest(1, 'total_revenue')
        if not top_product.empty:
            st.info(f"""
            **Top Product:** {top_product['product_name'].values[0]}
            
            Revenue: ${top_product['total_revenue'].values[0]:,.0f}
            """)
    
    with col2:
        lifecycle_with_most_products = products_df['product_lifecycle_stage'].value_counts().idxmax()
        st.info(f"""
            **Most Common Stage:** {lifecycle_with_most_products.title()}
            
            Products: {products_df['product_lifecycle_stage'].value_counts().max():,}
            """)
    
    with col3:
        top_category = category_perf.nlargest(1, 'revenue')
        if not top_category.empty:
            st.info(f"""
            **Top Category:** {top_category['category'].values[0]}
            
            Revenue: ${top_category['revenue'].values[0]:,.0f}
            """)

if __name__ == "__main__":
    main()