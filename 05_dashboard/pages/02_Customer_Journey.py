"""
Page 2: Customer Journey & Funnel Analysis
Conversion funnel, device tracking, and event flow
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import mysql.connector
from datetime import datetime, timedelta
import os

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Customer Journey",
    page_icon="🛤️",
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

# @st.cache_data(ttl=600)
# def load_journey_data():
#     """Load customer journey data"""
#     return load_data("SELECT * FROM customer_journey LIMIT 100000;")

# @st.cache_data(ttl=600)
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


def load_customer_journey_csv():
    """
    Load customer journey data from CSV
    
    Returns:
        pd.DataFrame: Journey data with columns:
            - journey_id, customer_id, product_id, journey_date
            - journey_time, event_type, device_type, page_url
            - session_duration, is_conversion_event, conversion_value
    """
    path = r'C:/My_Projects/All_Projects/cx_product_cap/02_data_generation/data/customer_journey.csv'
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    return pd.read_csv(path)


# ============================================================================
# CSV DATA LOADING
# ============================================================================

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

def analyze_conversion_funnel(journey_df):
    """Analyze conversion funnel stages"""
    
    funnel_stages = ['page_view', 'product_view', 'add_to_cart', 'checkout_start', 'checkout_complete']
    funnel_data = []
    
    for stage in funnel_stages:
        count = len(journey_df[journey_df['event_type'] == stage])
        funnel_data.append({'stage': stage.replace('_', ' ').title(), 'count': count})
    
    funnel_df = pd.DataFrame(funnel_data)
    
    if len(funnel_df) > 0 and funnel_df['count'].iloc[0] > 0:
        funnel_df['percentage'] = (funnel_df['count'] / funnel_df['count'].iloc[0] * 100).round(2)
        funnel_df['conversion_rate'] = (funnel_df['count'] / funnel_df['count'].iloc[0] * 100).round(2)
    else:
        funnel_df['percentage'] = 0
        funnel_df['conversion_rate'] = 0
    
    return funnel_df

def analyze_device_performance(journey_df):
    """Analyze performance by device type"""
    
    device_analysis = journey_df.groupby('device_type').agg({
        'journey_id': 'count',
        'is_conversion_event': 'sum',
        'conversion_value': 'sum',
        'session_duration': 'mean'
    }).reset_index()
    
    device_analysis.columns = ['device', 'total_events', 'conversions', 'total_value', 'avg_session_duration']
    device_analysis['conversion_rate'] = (device_analysis['conversions'] / device_analysis['total_events'] * 100).round(2)
    
    return device_analysis

def analyze_event_flow(journey_df):
    """Analyze most common event sequences"""
    
    event_dist = journey_df['event_type'].value_counts()
    return event_dist

def analyze_journey_metrics(journey_df):
    """Calculate journey-related metrics"""
    
    metrics = {
        'total_events': len(journey_df),
        'unique_users': journey_df['customer_id'].nunique(),
        'avg_session_duration': journey_df['session_duration'].mean(),
        'total_conversions': journey_df['is_conversion_event'].sum(),
        'conversion_rate': (journey_df['is_conversion_event'].sum() / len(journey_df) * 100),
        'avg_conversion_value': journey_df[journey_df['is_conversion_event'] == 1]['conversion_value'].mean(),
    }
    
    return metrics

# ============================================================================
# PAGE CONTENT
# ============================================================================

def main():
    st.title("🛤️ Customer Journey & Funnel Analysis")
    st.markdown("---")
    
    # Load data
    with st.spinner("Loading journey data..."):
        journey_df = load_customer_journey_csv()
        transactions_df = load_transactions_csv()
    
    if journey_df.empty:
        st.warning("No journey data available")
        return
    
    # Filters
    st.markdown("### 🔍 Filters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_device = st.multiselect(
            "Device Type",
            journey_df['device_type'].unique(),
            default=journey_df['device_type'].unique(),
            key="device_filter"
        )
    
    with col2:
        selected_events = st.multiselect(
            "Event Types",
            journey_df['event_type'].unique(),
            default=['page_view', 'product_view', 'add_to_cart', 'checkout_complete'],
            key="event_filter"
        )
    
    with col3:
        date_range = st.date_input(
            "Date Range",
            value=(datetime.now() - timedelta(days=30), datetime.now()),
            max_value=datetime.now(),
            key="journey_date_filter"
        )
    
    # Filter data
    filtered_journey = journey_df[
        (journey_df['device_type'].isin(selected_device)) &
        (journey_df['event_type'].isin(selected_events))
    ].copy()
    
    filtered_journey['journey_date'] = pd.to_datetime(filtered_journey['journey_date'])
    filtered_journey = filtered_journey[
        (filtered_journey['journey_date'].dt.date >= date_range[0]) &
        (filtered_journey['journey_date'].dt.date <= date_range[1])
    ]
    
    # Journey metrics
    journey_metrics = analyze_journey_metrics(filtered_journey)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📊 Total Events",
            f"{journey_metrics['total_events']:,}",
            delta=f"{journey_metrics['unique_users']:,} Users"
        )
    
    with col2:
        st.metric(
            "⏱️ Avg Session Duration",
            f"{journey_metrics['avg_session_duration']:.0f}s",
            delta="Seconds"
        )
    
    with col3:
        st.metric(
            "✅ Total Conversions",
            f"{journey_metrics['total_conversions']:,}",
            delta=f"{journey_metrics['conversion_rate']:.2f}%"
        )
    
    with col4:
        st.metric(
            "💵 Avg Conversion Value",
            f"${journey_metrics['avg_conversion_value']:.2f}",
            delta="Per conversion"
        )
    
    # Conversion funnel
    st.markdown("---")
    st.markdown("### 📊 Conversion Funnel")
    
    # Use all journey data for funnel (not filtered by event type for completeness)
    funnel_df = analyze_conversion_funnel(journey_df)
    
    fig_funnel = go.Figure(go.Funnel(
        y=funnel_df['stage'],
        x=funnel_df['count'],
        textposition='inside',
        textinfo='value+percent initial',
        marker=dict(
            color=['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A'],
            line=dict(width=2)
        )
    ))
    
    fig_funnel.update_layout(
        title='Customer Conversion Funnel',
        height=400,
        template='plotly_white'
    )
    
    st.plotly_chart(fig_funnel, use_container_width=True)
    
    # Display conversion rates
    st.markdown("### 📈 Funnel Conversion Rates")
    
    conversion_col1, conversion_col2, conversion_col3 = st.columns(3)
    
    with conversion_col1:
        st.metric(
            "Page View → Product View",
            f"{(funnel_df.iloc[1]['count'] / funnel_df.iloc[0]['count'] * 100):.1f}%"
        )
    
    with conversion_col2:
        st.metric(
            "Add to Cart → Checkout",
            f"{(funnel_df.iloc[3]['count'] / funnel_df.iloc[2]['count'] * 100):.1f}%" if len(funnel_df) > 3 else "N/A"
        )
    
    with conversion_col3:
        st.metric(
            "Overall Conversion Rate",
            f"{(funnel_df.iloc[-1]['count'] / funnel_df.iloc[0]['count'] * 100):.2f}%"
        )
    
    # Device analysis
    st.markdown("---")
    st.markdown("### 📱 Device Type Performance")
    
    device_perf = analyze_device_performance(filtered_journey)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_device_events = px.bar(
            device_perf,
            x='device',
            y='total_events',
            color='device',
            title='Events by Device Type',
            labels={'total_events': 'Events', 'device': 'Device'},
            text='total_events',
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_device_events.update_traces(textposition='outside')
        fig_device_events.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_device_events, use_container_width=True)
    
    with col2:
        fig_device_conv = px.bar(
            device_perf,
            x='device',
            y='conversion_rate',
            color='device',
            title='Conversion Rate by Device',
            labels={'conversion_rate': 'Conversion Rate (%)', 'device': 'Device'},
            text='conversion_rate',
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_device_conv.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig_device_conv.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_device_conv, use_container_width=True)
    
    # Device metrics table
    st.markdown("### 📊 Device Performance Table")
    
    device_table = device_perf.copy()
    device_table.columns = ['Device', 'Total Events', 'Conversions', 'Total Value', 'Avg Session (s)', 'Conv Rate (%)']
    st.dataframe(device_table, use_container_width=True)
    
    # Event type distribution
    st.markdown("---")
    st.markdown("### 🔄 Event Type Distribution")
    
    event_dist = analyze_event_flow(filtered_journey)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_events_bar = px.bar(
            x=event_dist.index,
            y=event_dist.values,
            title='Top Events by Count',
            labels={'x': 'Event Type', 'y': 'Count'},
            color=event_dist.index,
            text=event_dist.values,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_events_bar.update_traces(textposition='outside')
        fig_events_bar.update_xaxes(tickangle=-45)
        fig_events_bar.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_events_bar, use_container_width=True)
    
    with col2:
        fig_events_pie = px.pie(
            values=event_dist.values,
            names=event_dist.index,
            title='Event Type Distribution',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_events_pie.update_layout(height=400)
        st.plotly_chart(fig_events_pie, use_container_width=True)
    
    # Journey duration analysis
    st.markdown("---")
    st.markdown("### ⏱️ Session Duration Analysis")
    
    fig_duration = px.histogram(
        filtered_journey,
        x='session_duration',
        nbins=50,
        title='Distribution of Session Durations',
        labels={'session_duration': 'Duration (seconds)', 'count': 'Frequency'},
        color_discrete_sequence=['#636EFA']
    )
    fig_duration.update_layout(height=400)
    st.plotly_chart(fig_duration, use_container_width=True)
    
    # Key insights
    st.markdown("---")
    st.markdown("### 💡 Key Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        most_used_device = device_perf.nlargest(1, 'total_events')
        if not most_used_device.empty:
            st.info(f"""
            **Most Used Device:** {most_used_device['device'].values[0].title()}
            
            Events: {most_used_device['total_events'].values[0]:,}
            """)
    
    with col2:
        best_conv_device = device_perf.nlargest(1, 'conversion_rate')
        if not best_conv_device.empty:
            st.info(f"""
            **Best Converting Device:** {best_conv_device['device'].values[0].title()}
            
            Conv Rate: {best_conv_device['conversion_rate'].values[0]:.2f}%
            """)
    
    with col3:
        most_common_event = event_dist.idxmax()
        st.info(f"""
            **Most Common Event:** {most_common_event.replace('_', ' ').title()}
            
            Occurrences: {event_dist.max():,}
            """)

if __name__ == "__main__":
    main()