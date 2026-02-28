"""
Page 4: Unit Economics & Profitability
Margin analysis, cost structure, and profitability trends
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
    page_title="Unit Economics",
    page_icon="💹",
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
        # return None

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

# @st.cache_data(ttl=600)
# def load_economics_data():
#     """Load transaction data for economics analysis"""
#     return load_data("SELECT * FROM transactions;")


def load_csv(filename):
            path = f'C:/My_Projects/All_Projects/cx_product_cap/02_data_generation/data/{filename}'
            if os.path.exists(path):
                return pd.read_csv(path)
            else:
                st.error(f"File not found: {path}")
                return pd.DataFrame()

def load_economics_data():
    return load_csv('transactions.csv')

# @st.cache_data(ttl=600)
# def load_product_data():
#     """Load product data"""
#     return load_data("SELECT * FROM products;")

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
# ANALYSIS FUNCTIONS
# ============================================================================

def calculate_margin_metrics(transactions_df, products_df):
    """Calculate margin metrics"""
    
    completed = transactions_df[transactions_df['order_status'] == 'completed'].copy()
    
    metrics = {
        'total_revenue': completed['transaction_amount'].sum(),
        'total_profit': completed['profit_amount'].sum(),
        'total_cost': completed['transaction_amount'].sum() - completed['profit_amount'].sum(),
        'total_orders': len(completed),
        'avg_order_value': completed['transaction_amount'].mean(),
        'avg_profit_per_order': completed['profit_amount'].mean(),
    }
    
    metrics['gross_margin_percent'] = (metrics['total_profit'] / metrics['total_revenue'] * 100) if metrics['total_revenue'] > 0 else 0
    metrics['cost_of_goods_sold_percent'] = (metrics['total_cost'] / metrics['total_revenue'] * 100) if metrics['total_revenue'] > 0 else 0
    
    return metrics

def analyze_margin_by_category(transactions_df, products_df):
    """Analyze margins by category"""
    
    completed = transactions_df[transactions_df['order_status'] == 'completed'].copy()
    
    margin_by_cat = completed.merge(
        products_df[['product_id', 'category', 'cost', 'price']],
        on='product_id'
    ).groupby('category').agg({
        'transaction_amount': 'sum',
        'profit_amount': 'sum',
        'transaction_id': 'count'
    }).reset_index()
    
    margin_by_cat.columns = ['category', 'revenue', 'profit', 'orders']
    margin_by_cat['margin_percent'] = (margin_by_cat['profit'] / margin_by_cat['revenue'] * 100).round(2)
    margin_by_cat['avg_order_value'] = (margin_by_cat['revenue'] / margin_by_cat['orders']).round(2)
    margin_by_cat['avg_profit_per_order'] = (margin_by_cat['profit'] / margin_by_cat['orders']).round(2)
    
    return margin_by_cat.sort_values('revenue', ascending=False)

def analyze_monthly_profitability(transactions_df):
    """Analyze monthly profit trends"""
    
    completed = transactions_df[transactions_df['order_status'] == 'completed'].copy()
    completed['transaction_date'] = pd.to_datetime(completed['transaction_date'])
    
    monthly = completed.groupby(completed['transaction_date'].dt.to_period('M')).agg({
        'transaction_amount': 'sum',
        'profit_amount': 'sum',
        'transaction_id': 'count'
    }).reset_index()
    
    monthly.columns = ['month', 'revenue', 'profit', 'orders']
    monthly['month'] = monthly['month'].astype(str)
    monthly['margin_percent'] = (monthly['profit'] / monthly['revenue'] * 100).round(2)
    monthly['avg_order_value'] = (monthly['revenue'] / monthly['orders']).round(2)
    
    return monthly

def analyze_product_economics(transactions_df, products_df):
    """Analyze economics by product"""
    
    completed = transactions_df[transactions_df['order_status'] == 'completed'].copy()
    
    prod_econ = completed.merge(
        products_df[['product_id', 'product_name', 'category']],
        on='product_id'
    ).groupby(['product_id', 'product_name', 'category']).agg({
        'transaction_amount': 'sum',
        'profit_amount': 'sum',
        'transaction_id': 'count'
    }).reset_index()
    
    prod_econ.columns = ['product_id', 'product_name', 'category', 'revenue', 'profit', 'units_sold']
    prod_econ['margin_percent'] = (prod_econ['profit'] / prod_econ['revenue'] * 100).round(2)
    
    return prod_econ

# ============================================================================
# PAGE CONTENT
# ============================================================================

def main():
    st.title("💹 Unit Economics & Profitability Analysis")
    st.markdown("---")
    
    # Load data
    with st.spinner("Loading economics data..."):
        transactions_df = load_economics_data()
        products_df = load_product_data()
    
    if transactions_df.empty:
        st.warning("No transaction data available")
        return
    
    # Calculate metrics
    metrics = calculate_margin_metrics(transactions_df, products_df)
    
    # Key metrics
    st.markdown("### 📊 Key Economics Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💰 Total Revenue",
            f"${metrics['total_revenue']:,.0f}",
            delta=f"{metrics['total_orders']:,} Orders"
        )
    
    with col2:
        st.metric(
            "💵 Total Profit",
            f"${metrics['total_profit']:,.0f}",
            delta=f"{metrics['gross_margin_percent']:.1f}% Margin"
        )
    
    with col3:
        st.metric(
            "💸 Total Cost",
            f"${metrics['total_cost']:,.0f}",
            delta=f"{metrics['cost_of_goods_sold_percent']:.1f}% of Revenue"
        )
    
    with col4:
        st.metric(
            "📈 Avg Profit/Order",
            f"${metrics['avg_profit_per_order']:.2f}",
            delta=f"AOV: ${metrics['avg_order_value']:.2f}"
        )
    
    # Revenue vs Profit analysis
    st.markdown("---")
    st.markdown("### 💹 Revenue vs Profit Analysis")
    
    # Monthly profitability
    monthly_prof = analyze_monthly_profitability(transactions_df)
    
    fig_monthly = go.Figure()
    
    fig_monthly.add_trace(go.Bar(
        x=monthly_prof['month'],
        y=monthly_prof['revenue'],
        name='Revenue',
        marker=dict(color='#636EFA'),
        text=monthly_prof['revenue'],
        texttemplate='$%{text:,.0f}',
        textposition='outside'
    ))
    
    fig_monthly.add_trace(go.Bar(
        x=monthly_prof['month'],
        y=monthly_prof['profit'],
        name='Profit',
        marker=dict(color='#00CC96'),
        text=monthly_prof['profit'],
        texttemplate='$%{text:,.0f}',
        textposition='outside'
    ))
    
    fig_monthly.update_layout(
        title='Monthly Revenue vs Profit',
        barmode='group',
        height=400,
        xaxis_title='Month',
        yaxis_title='Amount ($)',
        hovermode='x unified',
        template='plotly_white'
    )
    
    st.plotly_chart(fig_monthly, use_container_width=True)
    
    # Profit margin trend
    st.markdown("### 📈 Gross Margin Trend")
    
    fig_margin = px.line(
        monthly_prof,
        x='month',
        y='margin_percent',
        title='Monthly Gross Margin %',
        labels={'margin_percent': 'Gross Margin (%)', 'month': 'Month'},
        markers=True,
        line_shape='linear'
    )
    
    fig_margin.update_traces(
        line=dict(color='#FFA15A', width=3),
        marker=dict(size=8)
    )
    
    fig_margin.update_layout(
        height=400,
        hovermode='x unified',
        template='plotly_white'
    )
    
    st.plotly_chart(fig_margin, use_container_width=True)
    
    # Margin by category
    st.markdown("---")
    st.markdown("### 🏷️ Profitability by Category")
    
    margin_by_cat = analyze_margin_by_category(transactions_df, products_df)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_cat_margin = px.bar(
            margin_by_cat,
            x='category',
            y='margin_percent',
            color='margin_percent',
            title='Gross Margin by Category',
            labels={'margin_percent': 'Margin (%)', 'category': 'Category'},
            text='margin_percent',
            color_continuous_scale='RdYlGn'
        )
        fig_cat_margin.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_cat_margin.update_xaxes(tickangle=-45)
        fig_cat_margin.update_layout(height=400)
        st.plotly_chart(fig_cat_margin, use_container_width=True)
    
    with col2:
        fig_cat_profit = px.bar(
            margin_by_cat,
            x='category',
            y='profit',
            color='profit',
            title='Total Profit by Category',
            labels={'profit': 'Profit ($)', 'category': 'Category'},
            text='profit',
            color_continuous_scale='Blues'
        )
        fig_cat_profit.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
        fig_cat_profit.update_xaxes(tickangle=-45)
        fig_cat_profit.update_layout(height=400)
        st.plotly_chart(fig_cat_profit, use_container_width=True)
    
    # Category metrics table
    st.markdown("### 📊 Category Profitability Table")
    
    cat_table = margin_by_cat[['category', 'revenue', 'profit', 'orders', 'avg_order_value', 'margin_percent']].copy()
    cat_table.columns = ['Category', 'Revenue', 'Profit', 'Orders', 'Avg Order Value', 'Margin %']
    
    st.dataframe(cat_table, use_container_width=True)
    
    # Top and bottom products by margin
    st.markdown("---")
    st.markdown("### 🏆 Product Profitability Analysis")
    
    prod_econ = analyze_product_economics(transactions_df, products_df)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🥇 Top 10 Products by Profit")
        top_products = prod_econ.nlargest(10, 'profit')[['product_name', 'profit', 'margin_percent', 'units_sold']]
        top_products.columns = ['Product', 'Profit', 'Margin %', 'Units Sold']
        st.dataframe(top_products, use_container_width=True)
    
    with col2:
        st.markdown("### 📉 Top 10 Products by Margin %")
        top_margin = prod_econ.nlargest(10, 'margin_percent')[['product_name', 'profit', 'margin_percent', 'revenue']]
        top_margin.columns = ['Product', 'Profit', 'Margin %', 'Revenue']
        st.dataframe(top_margin, use_container_width=True)
    
    # Cost structure waterfall
    st.markdown("---")
    st.markdown("### 🏗️ Cost Structure Breakdown")
    
    cost_structure = [
        {'category': 'Revenue', 'value': metrics['total_revenue']},
        {'category': 'COGS', 'value': -metrics['total_cost']},
        {'category': 'Gross Profit', 'value': metrics['total_profit']},
    ]
    
    cost_df = pd.DataFrame(cost_structure)
    
    fig_waterfall = go.Figure(go.Waterfall(
        x=['Revenue', 'COGS', 'Gross Profit'],
        y=[metrics['total_revenue'], -metrics['total_cost'], metrics['total_profit']],
        measure=['relative', 'relative', 'total'],
        text=[f'${metrics["total_revenue"]:,.0f}', f'-${metrics["total_cost"]:,.0f}', f'${metrics["total_profit"]:,.0f}'],
        textposition='outside',
        connector=dict(line=dict(dash='solid')),
        decreasing=dict(marker=dict(color='#EF553B')),
        increasing=dict(marker=dict(color='#00CC96')),
        totals=dict(marker=dict(color='#636EFA'))
    ))
    
    fig_waterfall.update_layout(
        title='Revenue to Profit Waterfall',
        height=400,
        template='plotly_white'
    )
    
    st.plotly_chart(fig_waterfall, use_container_width=True)
    
    # Unit economics metrics
    st.markdown("---")
    st.markdown("### 📐 Unit Economics Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"""
        **Average Order Value (AOV)**
        
        ${metrics['avg_order_value']:.2f}
        """)
    
    with col2:
        st.info(f"""
        **Average Profit Per Order**
        
        ${metrics['avg_profit_per_order']:.2f}
        """)
    
    with col3:
        profit_per_revenue = (metrics['avg_profit_per_order'] / metrics['avg_order_value'] * 100)
        st.info(f"""
        **Profit Per Revenue**
        
        {profit_per_revenue:.1f}%
        """)
    
    # Key insights
    st.markdown("---")
    st.markdown("### 💡 Key Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        best_margin_cat = margin_by_cat.nlargest(1, 'margin_percent')
        if not best_margin_cat.empty:
            st.success(f"""
            **Highest Margin Category**
            
            {best_margin_cat['category'].values[0]}
            Margin: {best_margin_cat['margin_percent'].values[0]:.1f}%
            """)
    
    with col2:
        most_profitable = margin_by_cat.nlargest(1, 'profit')
        if not most_profitable.empty:
            st.success(f"""
            **Most Profitable Category**
            
            {most_profitable['category'].values[0]}
            Profit: ${most_profitable['profit'].values[0]:,.0f}
            """)
    
    with col3:
        st.metric(
            "📊 Overall Health",
            f"{metrics['gross_margin_percent']:.1f}%",
            delta="Gross Margin"
        )

if __name__ == "__main__":
    main()