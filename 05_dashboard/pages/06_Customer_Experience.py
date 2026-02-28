"""
Page 6: Customer Experience 3D View
Multi-dimensional analysis of engagement, purchases, and spending
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
    page_title="Customer Experience 3D",
    page_icon="🎯",
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
            path = f'C:/My_Projects/All_Projects/cx_product_cap/02_data_generation/data/{filename}'
            if os.path.exists(path):
                return pd.read_csv(path)
            else:
                st.error(f"File not found: {path}")
                return pd.DataFrame()

@st.cache_data(ttl=600)
def load_customer_experience_data():
    """Load all data for customer experience analysis"""
    trans = load_csv('transactions.csv')
    cust = load_csv('customers.csv')
    journey = load_csv("customer_journey.csv")
    return cust, trans, journey

# ============================================================================
# ANALYSIS FUNCTIONS
# ============================================================================

def calculate_customer_dimensions(transactions_df, customers_df, journey_df):
    """Calculate engagement, loyalty, and value dimensions"""
    
    trans = transactions_df[transactions_df['order_status'] == 'completed'].copy()
    
    # Calculate engagement score
    engagement = journey_df.groupby('customer_id').size().reset_index(name='engagement')
    engagement['engagement'] = (engagement['engagement'] / engagement['engagement'].max() * 100).round(2)
    
    # Calculate loyalty score (repeat purchases)
    loyalty = trans.groupby('customer_id').agg({
        'transaction_id': 'count',
        'customer_id': 'count'
    }).reset_index()
    loyalty = loyalty.rename(columns={'transaction_id': 'purchases'})
    loyalty['loyalty'] = (loyalty['purchases'] / loyalty['purchases'].max() * 100).round(2)
    
    # Calculate value (total spent)
    value = trans.groupby('customer_id')['transaction_amount'].sum().reset_index()
    value = value.rename(columns={'transaction_amount': 'total_spent'})
    value['value'] = (value['total_spent'] / value['total_spent'].max() * 100).round(2)
    
    # Merge all dimensions
    customer_3d = customers_df[['customer_id', 'segment', 'customer_status']].copy()
    customer_3d = customer_3d.merge(engagement, on='customer_id', how='left')
    customer_3d = customer_3d.merge(loyalty[['customer_id', 'purchases', 'loyalty']], on='customer_id', how='left')
    customer_3d = customer_3d.merge(value[['customer_id', 'total_spent', 'value']], on='customer_id', how='left')
    
    customer_3d = customer_3d.fillna(0)
    
    return customer_3d

def calculate_segment_metrics(customer_3d):
    """Calculate aggregate metrics by segment"""
    
    segment_metrics = customer_3d.groupby('segment').agg({
        'engagement': 'mean',
        'loyalty': 'mean',
        'value': 'mean',
        'total_spent': 'mean',
        'purchases': 'mean',
        'customer_id': 'count'
    }).reset_index()
    
    segment_metrics.columns = ['segment', 'avg_engagement', 'avg_loyalty', 'avg_value', 'avg_spent', 'avg_purchases', 'count']
    
    return segment_metrics

# ============================================================================
# PAGE CONTENT
# ============================================================================

def main():
    st.title("🎯 Customer Experience 3D View")
    st.markdown("---")
    
    st.markdown("""
    This page provides a multi-dimensional view of your customers across three key dimensions:
    - **Engagement**: How actively customers interact with your platform (clicks, views, events)
    - **Loyalty**: How frequently customers make repeat purchases
    - **Value**: How much customers spend in total
    """)
    
    # Load data
    with st.spinner("Loading customer data..."):
        customers_df, transactions_df, journey_df = load_customer_experience_data()
    
    if customers_df.empty:
        st.warning("No customer data available")
        return
    
    # Calculate dimensions
    customer_3d = calculate_customer_dimensions(transactions_df, customers_df, journey_df)
    
    # Filters
    st.markdown("---")
    st.markdown("### 🔍 Filters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_segments = st.multiselect(
            "Customer Segment",
            customer_3d['segment'].unique(),
            default=customer_3d['segment'].unique(),
            key="segment_filter_3d"
        )
    
    with col2:
        selected_status = st.multiselect(
            "Customer Status",
            customer_3d['customer_status'].unique(),
            default=['active'],
            key="status_filter_3d"
        )
    
    # Filter data
    filtered_3d = customer_3d[
        (customer_3d['segment'].isin(selected_segments)) &
        (customer_3d['customer_status'].isin(selected_status))
    ]
    
    # 3D Scatter plot
    st.markdown("---")
    st.markdown("### 📊 3D Customer Experience View")
    
    fig_3d = px.scatter_3d(
        filtered_3d,
        x='engagement',
        y='loyalty',
        z='value',
        color='segment',
        hover_data={'customer_id': False, 'purchases': True, 'total_spent': ':.2f'},
        title='Customer Experience 3D (Engagement vs Loyalty vs Value)',
        labels={
            'engagement': 'Engagement Score',
            'loyalty': 'Loyalty Score',
            'value': 'Value Score',
            'segment': 'Segment'
        },
        color_discrete_sequence=px.colors.qualitative.Set2,
        size='total_spent',
        size_max=20
    )
    
    fig_3d.update_layout(
        height=600,
        scene=dict(
            xaxis=dict(title='Engagement Score (0-100)'),
            yaxis=dict(title='Loyalty Score (0-100)'),
            zaxis=dict(title='Value Score (0-100)')
        )
    )
    
    st.plotly_chart(fig_3d, use_container_width=True)
    
    # 2D scatter plots
    st.markdown("---")
    st.markdown("### 📈 2D Dimension Relationships")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fig_eng_loy = px.scatter(
            filtered_3d,
            x='engagement',
            y='loyalty',
            color='segment',
            title='Engagement vs Loyalty',
            labels={'engagement': 'Engagement', 'loyalty': 'Loyalty'},
            color_discrete_sequence=px.colors.qualitative.Set2,
            size='total_spent',
            size_max=15
        )
        fig_eng_loy.update_layout(height=400)
        st.plotly_chart(fig_eng_loy, use_container_width=True)
    
    with col2:
        fig_eng_val = px.scatter(
            filtered_3d,
            x='engagement',
            y='value',
            color='segment',
            title='Engagement vs Value',
            labels={'engagement': 'Engagement', 'value': 'Value'},
            color_discrete_sequence=px.colors.qualitative.Set2,
            size='total_spent',
            size_max=15
        )
        fig_eng_val.update_layout(height=400)
        st.plotly_chart(fig_eng_val, use_container_width=True)
    
    with col3:
        fig_loy_val = px.scatter(
            filtered_3d,
            x='loyalty',
            y='value',
            color='segment',
            title='Loyalty vs Value',
            labels={'loyalty': 'Loyalty', 'value': 'Value'},
            color_discrete_sequence=px.colors.qualitative.Set2,
            size='total_spent',
            size_max=15
        )
        fig_loy_val.update_layout(height=400)
        st.plotly_chart(fig_loy_val, use_container_width=True)
    
    # Segment analysis
    st.markdown("---")
    st.markdown("### 📊 Segment Performance Metrics")
    
    segment_metrics = calculate_segment_metrics(filtered_3d)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_seg_metrics = px.bar(
            segment_metrics,
            x='segment',
            y=['avg_engagement', 'avg_loyalty', 'avg_value'],
            title='Average Scores by Segment',
            labels={
                'value': 'Score (0-100)',
                'segment': 'Segment',
                'avg_engagement': 'Engagement',
                'avg_loyalty': 'Loyalty',
                'avg_value': 'Value'
            },
            barmode='group',
            color_discrete_sequence=['#636EFA', '#00CC96', '#FFA15A']
        )
        fig_seg_metrics.update_layout(height=400)
        st.plotly_chart(fig_seg_metrics, use_container_width=True)
    
    with col2:
        fig_seg_spend = px.bar(
            segment_metrics,
            x='segment',
            y='avg_spent',
            color='avg_spent',
            title='Average Customer Spend by Segment',
            labels={'avg_spent': 'Avg Spend ($)', 'segment': 'Segment'},
            text='avg_spent',
            color_continuous_scale='Blues'
        )
        fig_seg_spend.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
        fig_seg_spend.update_layout(height=400)
        st.plotly_chart(fig_seg_spend, use_container_width=True)
    
    # Segment metrics table
    st.markdown("### 📈 Segment Metrics Table")
    
    seg_table = segment_metrics[['segment', 'count', 'avg_engagement', 'avg_loyalty', 'avg_value', 'avg_spent', 'avg_purchases']].copy()
    seg_table.columns = ['Segment', 'Customers', 'Engagement', 'Loyalty', 'Value', 'Avg Spend', 'Avg Purchases']
    seg_table['Avg Spend'] = seg_table['Avg Spend'].apply(lambda x: f"${x:,.2f}")
    
    st.dataframe(seg_table, use_container_width=True)
    
    # Customer tier classification
    st.markdown("---")
    st.markdown("### 🏆 Customer Tier Classification")
    
    # Calculate composite score
    filtered_3d_copy = filtered_3d.copy()
    filtered_3d_copy['composite_score'] = (
        filtered_3d_copy['engagement'] * 0.3 +
        filtered_3d_copy['loyalty'] * 0.3 +
        filtered_3d_copy['value'] * 0.4
    )
    
    # Tier classification
    def classify_tier(score):
        if score >= 75:
            return 'VIP'
        elif score >= 50:
            return 'Premium'
        elif score >= 25:
            return 'Standard'
        else:
            return 'At Risk'
    
    filtered_3d_copy['tier'] = filtered_3d_copy['composite_score'].apply(classify_tier)
    
    tier_dist = filtered_3d_copy['tier'].value_counts()
    
    tier_colors = {
        'VIP': '#FFD700',
        'Premium': '#87CEEB',
        'Standard': '#90EE90',
        'At Risk': '#FF6B6B'
    }
    
    fig_tier = px.pie(
        values=tier_dist.values,
        names=tier_dist.index,
        title='Customer Tier Distribution',
        color=tier_dist.index,
        color_discrete_map=tier_colors
    )
    fig_tier.update_layout(height=400)
    st.plotly_chart(fig_tier, use_container_width=True)
    
    # Tier metrics
    st.markdown("### 📊 Metrics by Customer Tier")
    
    tier_metrics = filtered_3d_copy.groupby('tier').agg({
        'customer_id': 'count',
        'engagement': 'mean',
        'loyalty': 'mean',
        'value': 'mean',
        'total_spent': 'mean',
        'purchases': 'mean',
        'composite_score': 'mean'
    }).reset_index()
    
    tier_metrics.columns = ['Tier', 'Customers', 'Engagement', 'Loyalty', 'Value', 'Avg Spend', 'Avg Purchases', 'Composite Score']
    tier_metrics = tier_metrics.sort_values('Composite Score', ascending=False)
    
    st.dataframe(tier_metrics, use_container_width=True)
    
    # Key insights
    st.markdown("---")
    st.markdown("### 💡 Key Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        vip_count = (filtered_3d_copy['tier'] == 'VIP').sum()
        total_count = len(filtered_3d_copy)
        vip_pct = (vip_count / total_count * 100) if total_count > 0 else 0
        st.metric(
            "🏆 VIP Customers",
            f"{vip_count:,}",
            delta=f"{vip_pct:.1f}% of total"
        )
    
    with col2:
        top_segment = segment_metrics.nlargest(1, 'avg_spent')
        if not top_segment.empty:
            st.info(f"""
            **Highest Spending Segment**
            
            {top_segment['segment'].values[0].title()}
            Avg: ${top_segment['avg_spent'].values[0]:,.2f}
            """)
    
    with col3:
        most_engaged = segment_metrics.nlargest(1, 'avg_engagement')
        if not most_engaged.empty:
            st.info(f"""
            **Most Engaged Segment**
            
            {most_engaged['segment'].values[0].title()}
            Score: {most_engaged['avg_engagement'].values[0]:.1f}
            """)
    
    # Top customers by composite score
    st.markdown("---")
    st.markdown("### ⭐ Top 20 Customers by Composite Score")
    
    top_customers = filtered_3d_copy.nlargest(20, 'composite_score')[
        ['customer_id', 'segment', 'engagement', 'loyalty', 'value', 'total_spent', 'tier', 'composite_score']
    ].copy()
    
    top_customers.columns = ['Customer ID', 'Segment', 'Engagement', 'Loyalty', 'Value', 'Total Spent', 'Tier', 'Score']
    top_customers['Total Spent'] = top_customers['Total Spent'].apply(lambda x: f"${x:,.2f}")
    
    st.dataframe(top_customers, use_container_width=True)

if __name__ == "__main__":
    main()