"""
Page 1: Executive Overview (CSV Version)
Main dashboard with KPIs, trends, and segment analysis
Modified to read from CSV files instead of MySQL
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Executive Overview",
    page_icon="📊",
    layout="wide"
)

# ============================================================================
# MAIN PAGE FUNCTION (Called from main app with data parameter)
# ============================================================================

def main(data=None):
    """Main function that receives data from parent app"""
    
    st.title("📊 Executive Overview")
    st.markdown("---")
    
    # If data is not passed (running standalone), load from CSV
    if data is None:
        import os
        @st.cache_data(ttl=600)
        def load_csv(filename):
            path = f'C:/Users/Admin/Desktop/Freelance/Denis/Projects/cx_product_ds_capstone/02_data_generation/data/{filename}'
            if os.path.exists(path):
                return pd.read_csv(path)
            else:
                st.error(f"File not found: {path}")
                return pd.DataFrame()
        
        data = {
            'customers': load_csv('customers.csv'),
            'transactions': load_csv('transactions.csv'),
            'journey': load_csv('customer_journey.csv')
        }
    
    customers = data['customers']
    transactions = data['transactions']
    
    if customers.empty or transactions.empty:
        st.error("Data not loaded. Please ensure CSV files are in the data/ folder.")
        return
    
    # Filter options
    st.markdown("### 🔍 Filters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_segment = st.multiselect(
            "Customer Segment",
            customers['segment'].unique(),
            default=customers['segment'].unique(),
            key="segment_filter"
        )
    
    with col2:
        selected_status = st.multiselect(
            "Customer Status",
            customers['customer_status'].unique(),
            default=['active'],
            key="status_filter"
        )
    
    with col3:
        date_range = st.date_input(
            "Date Range",
            value=(datetime.now() - timedelta(days=90), datetime.now()),
            max_value=datetime.now(),
            key="date_filter"
        )
    
    # Filter data
    filtered_customers = customers[
        (customers['segment'].isin(selected_segment)) &
        (customers['customer_status'].isin(selected_status))
    ]
    
    filtered_transactions = transactions[
        (transactions['customer_id'].isin(filtered_customers['customer_id']))
    ]
    
    # Calculate metrics
    completed_trans = filtered_transactions[filtered_transactions['order_status'] == 'completed']
    
    metrics = {
        'total_revenue': completed_trans['transaction_amount'].sum(),
        'total_profit': completed_trans['profit_amount'].sum(),
        'total_customers': len(filtered_customers),
        'active_customers': len(filtered_customers[filtered_customers['customer_status'] == 'active']),
        'total_orders': len(completed_trans),
        'avg_order_value': completed_trans['transaction_amount'].mean(),
        'repeat_customers': len(completed_trans[completed_trans['is_repeat_purchase'] == True]['customer_id'].unique()),
    }
    
    metrics['gross_margin'] = (metrics['total_profit'] / metrics['total_revenue'] * 100) if metrics['total_revenue'] > 0 else 0
    metrics['churn_rate'] = (len(filtered_customers[filtered_customers['customer_status'] == 'churned']) / len(filtered_customers) * 100) if len(filtered_customers) > 0 else 0
    metrics['repeat_rate'] = (metrics['repeat_customers'] / metrics['total_customers'] * 100) if metrics['total_customers'] > 0 else 0
    
    # Display KPI cards
    st.markdown("### 📈 Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💰 Total Revenue",
            f"${metrics['total_revenue']:,.0f}",
            delta=f"{metrics['gross_margin']:.1f}% Margin"
        )
    
    with col2:
        st.metric(
            "👥 Total Customers",
            f"{metrics['total_customers']:,}",
            delta=f"{metrics['active_customers']} Active"
        )
    
    with col3:
        st.metric(
            "🛒 Avg Order Value",
            f"${metrics['avg_order_value']:.2f}",
            delta=f"{metrics['repeat_rate']:.1f}% Repeat"
        )
    
    with col4:
        st.metric(
            "⚠️ Churn Rate",
            f"{metrics['churn_rate']:.2f}%",
            delta="Monitor this metric"
        )
    
    # Second row of metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📊 Total Orders",
            f"{metrics['total_orders']:,}",
            delta=f"{len(filtered_transactions[filtered_transactions['is_repeat_purchase'] == True]):,} Repeat"
        )
    
    with col2:
        st.metric(
            "💵 Total Profit",
            f"${metrics['total_profit']:,.0f}",
            delta=f"${metrics['total_profit']/metrics['total_orders']:.2f} Per Order" if metrics['total_orders'] > 0 else "N/A"
        )
    
    with col3:
        st.metric(
            "🎯 Repeat Rate",
            f"{metrics['repeat_rate']:.2f}%",
            delta=f"{metrics['repeat_customers']:,} Customers"
        )
    
    with col4:
        ltv_cac = (metrics['total_revenue'] / metrics['total_customers'] / 100) if metrics['total_customers'] > 0 else 0
        st.metric(
            "📈 LTV:CAC Ratio",
            f"{ltv_cac:.2f}x",
            delta="Healthy if > 3x" if ltv_cac > 3 else "Needs improvement"
        )
    
    # Revenue trend
    st.markdown("---")
    st.markdown("### 💹 Revenue Trend (Last 90 Days)")
    
    trans_copy = filtered_transactions.copy()
    trans_copy['transaction_date'] = pd.to_datetime(trans_copy['transaction_date'])
    daily_revenue = trans_copy[trans_copy['order_status'] == 'completed'].groupby(
        trans_copy['transaction_date'].dt.date
    )['transaction_amount'].agg(['sum', 'count']).reset_index()
    daily_revenue.columns = ['date', 'revenue', 'orders']
    daily_revenue['avg_order_value'] = daily_revenue['revenue'] / daily_revenue['orders']
    
    # Create dual-axis chart
    fig_revenue = go.Figure()
    
    fig_revenue.add_trace(go.Scatter(
        x=daily_revenue['date'],
        y=daily_revenue['revenue'],
        mode='lines',
        name='Revenue',
        line=dict(color='#636EFA', width=3),
        hovertemplate='<b>%{x}</b><br>Revenue: $%{y:,.0f}<extra></extra>'
    ))
    
    fig_revenue.add_trace(go.Bar(
        x=daily_revenue['date'],
        y=daily_revenue['orders'],
        name='Orders',
        yaxis='y2',
        marker=dict(color='rgba(99, 110, 250, 0.3)'),
        hovertemplate='<b>%{x}</b><br>Orders: %{y}<extra></extra>'
    ))
    
    fig_revenue.update_layout(
        title='Daily Revenue & Order Count',
        hovermode='x unified',
        height=400,
        yaxis=dict(title='Revenue ($)'),
        yaxis2=dict(
            title='Orders',
            overlaying='y',
            side='right'
        ),
        xaxis=dict(title='Date'),
        template='plotly_white'
    )
    
    st.plotly_chart(fig_revenue, use_container_width=True)
    
    # Customer and Order distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 👥 Customer Distribution by Segment")
        segment_dist = filtered_customers['segment'].value_counts()
        
        colors = {
            'premium': '#FFD700',
            'high_value': '#87CEEB',
            'standard': '#90EE90',
            'at_risk': '#FF6B6B',
            'churned': '#808080'
        }
        
        fig_segment = px.pie(
            values=segment_dist.values,
            names=segment_dist.index,
            title='Customers by Segment',
            color=segment_dist.index,
            color_discrete_map=colors
        )
        fig_segment.update_layout(height=400)
        st.plotly_chart(fig_segment, use_container_width=True)
    
    with col2:
        st.markdown("### 📊 Order Status Distribution")
        status_dist = filtered_transactions['order_status'].value_counts()
        
        status_colors = {
            'completed': '#00CC96',
            'pending': '#FFA15A',
            'cancelled': '#EF553B',
            'returned': '#AB63FA'
        }
        
        fig_status = px.bar(
            x=status_dist.index,
            y=status_dist.values,
            title='Orders by Status',
            labels={'x': 'Status', 'y': 'Count'},
            color=status_dist.index,
            color_discrete_map=status_colors
        )
        fig_status.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_status, use_container_width=True)
    
    # Revenue by segment
    st.markdown("---")
    st.markdown("### 💰 Revenue by Segment")
    
    revenue_by_segment = filtered_transactions[filtered_transactions['order_status'] == 'completed'].merge(
        filtered_customers[['customer_id', 'segment']],
        on='customer_id'
    ).groupby('segment')['transaction_amount'].agg(['sum', 'count']).reset_index()
    
    revenue_by_segment.columns = ['segment', 'revenue', 'orders']
    revenue_by_segment['avg_order_value'] = revenue_by_segment['revenue'] / revenue_by_segment['orders']
    
    fig_revenue_segment = px.bar(
        revenue_by_segment,
        x='segment',
        y='revenue',
        color='segment',
        title='Total Revenue by Customer Segment',
        labels={'revenue': 'Revenue ($)', 'segment': 'Segment'},
        color_discrete_map=colors,
        text='revenue'
    )
    fig_revenue_segment.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
    fig_revenue_segment.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_revenue_segment, use_container_width=True)
    
    # Key insights
    st.markdown("---")
    st.markdown("### 💡 Key Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        top_segment = revenue_by_segment.nlargest(1, 'revenue')
        if not top_segment.empty:
            st.info(f"""
            **Top Segment:** {top_segment['segment'].values[0].title()}
            
            Revenue: ${top_segment['revenue'].values[0]:,.0f}
            """)
    
    with col2:
        completion_rate = (filtered_transactions['order_status'] == 'completed').sum() / len(filtered_transactions) * 100
        st.info(f"""
            **Order Completion Rate:** {completion_rate:.1f}%
            
            Completed: {(filtered_transactions['order_status'] == 'completed').sum():,} orders
            """)
    
    with col3:
        if metrics['total_orders'] > 0:
            profit_margin = metrics['total_profit'] / metrics['total_revenue'] * 100
            st.info(f"""
            **Profit Margin:** {profit_margin:.1f}%
            
            Profit: ${metrics['total_profit']:,.0f}
            """)

if __name__ == "__main__":
    main()