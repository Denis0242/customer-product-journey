"""
Page 7: Predictive Analytics & Recommendations
CLV prediction, churn risk scoring, customer recommendations
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
    page_title="Predictions",
    page_icon="🔮",
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
# def load_prediction_data():
#     """Load data for predictions"""
#     cust = load_data("SELECT * FROM customers;")
#     trans = load_data("SELECT * FROM transactions;")
#     journey = load_data("SELECT * FROM customer_journey LIMIT 100000;")
#     return cust, trans, journey

def load_csv(filename):
            path = f'C:/My_Projects/All_Projects/cx_product_cap/02_data_generation/data/{filename}'
            if os.path.exists(path):
                return pd.read_csv(path)
            else:
                st.error(f"File not found: {path}")
                return pd.DataFrame()

@st.cache_data(ttl=600)
def load_prediction_data():
    """Load all data for prediction"""
    trans = load_csv('transactions.csv')
    cust = load_csv('customers.csv')
    journey = load_csv("customer_journey.csv")
    return cust, trans, journey

# ============================================================================
# PREDICTION FUNCTIONS
# ============================================================================

def calculate_clv_prediction(transactions_df, customers_df):
    """Calculate Customer Lifetime Value prediction"""
    
    trans = transactions_df[transactions_df['order_status'] == 'completed'].copy()
    trans['transaction_date'] = pd.to_datetime(trans['transaction_date'])
    customers_df['signup_date'] = pd.to_datetime(customers_df['signup_date'])
    
    # Historical CLV
    historical_clv = trans.groupby('customer_id').agg({
        'transaction_amount': ['sum', 'count', 'mean']
    }).reset_index()
    
    historical_clv.columns = ['customer_id', 'historical_clv', 'purchase_count', 'avg_order_value']
    
    # Purchase frequency (per month)
    trans_grouped = trans.merge(customers_df[['customer_id', 'signup_date']], on='customer_id')
    trans_grouped['months_as_customer'] = (
        (datetime.now() - trans_grouped['signup_date']).dt.days / 30 + 1
    )
    
    purchase_freq = trans_grouped.groupby('customer_id').agg({
        'transaction_date': 'count',
        'months_as_customer': 'first'
    }).reset_index()
    
    purchase_freq.columns = ['customer_id', 'total_purchases', 'months_as_customer']
    purchase_freq['purchase_frequency'] = (
        purchase_freq['total_purchases'] / purchase_freq['months_as_customer']
    )
    
    # Merge
    clv_df = historical_clv.merge(purchase_freq[['customer_id', 'purchase_frequency', 'months_as_customer']], on='customer_id')
    
    # Predict 12-month and 24-month CLV
    clv_df['predicted_clv_12m'] = clv_df['avg_order_value'] * clv_df['purchase_frequency'] * 12
    clv_df['predicted_clv_24m'] = clv_df['predicted_clv_12m'] * 2
    
    # Add segment info
    clv_df = clv_df.merge(customers_df[['customer_id', 'segment']], on='customer_id')
    
    return clv_df

def calculate_churn_risk(transactions_df, customers_df, journey_df):
    """Calculate churn risk score"""
    
    trans = transactions_df[transactions_df['order_status'] == 'completed'].copy()
    trans['transaction_date'] = pd.to_datetime(trans['transaction_date'])
    customers_df['signup_date'] = pd.to_datetime(customers_df['signup_date'])
    
    # Days since last purchase
    last_purchase = trans.groupby('customer_id')['transaction_date'].max().reset_index()
    last_purchase.columns = ['customer_id', 'last_purchase_date']
    last_purchase['days_inactive'] = (datetime.now() - last_purchase['last_purchase_date']).dt.days
    
    # Purchase frequency
    purchase_freq = trans.groupby('customer_id').size().reset_index(name='purchase_frequency')
    
    # Journey engagement
    journey_engagement = journey_df.groupby('customer_id').size().reset_index(name='journey_events')
    
    # Merge all features
    churn_risk = customers_df[['customer_id', 'segment', 'customer_status']].copy()
    churn_risk = churn_risk.merge(last_purchase, on='customer_id', how='left')
    churn_risk = churn_risk.merge(purchase_freq, on='customer_id', how='left')
    churn_risk = churn_risk.merge(journey_engagement, on='customer_id', how='left')
    
    churn_risk = churn_risk.fillna(0)
    
    # Calculate churn risk score (0-100)
    max_days_inactive = churn_risk['days_inactive'].quantile(0.95)
    max_freq = churn_risk['purchase_frequency'].max()
    max_events = churn_risk['journey_events'].max()
    
    inactivity_score = (churn_risk['days_inactive'] / max(max_days_inactive, 1)) * 50
    frequency_score = (1 - churn_risk['purchase_frequency'] / max(max_freq, 1)) * 30
    engagement_score = (1 - churn_risk['journey_events'] / max(max_events, 1)) * 20
    
    churn_risk['churn_risk_score'] = (inactivity_score + frequency_score + engagement_score).clip(0, 100)
    
    # Risk level
    def risk_level(score):
        if score >= 70:
            return 'High'
        elif score >= 40:
            return 'Medium'
        else:
            return 'Low'
    
    churn_risk['risk_level'] = churn_risk['churn_risk_score'].apply(risk_level)
    
    return churn_risk

def calculate_ltv_cac_ratio(clv_df, cac=100):
    """Calculate LTV to CAC ratio"""
    
    clv_df_copy = clv_df.copy()
    clv_df_copy['ltv_cac_ratio'] = clv_df_copy['historical_clv'] / cac
    
    return clv_df_copy

# ============================================================================
# PAGE CONTENT
# ============================================================================

def main():
    st.title("🔮 Predictive Analytics & Recommendations")
    st.markdown("---")
    
    st.markdown("""
    This page uses machine learning to predict customer behavior and provide actionable recommendations:
    - **CLV Prediction**: Forecast 12-month and 24-month Customer Lifetime Value
    - **Churn Risk**: Identify customers at risk of churning
    - **Recommendations**: Personalized next-best actions for each customer
    """)
    
    # Load data
    with st.spinner("Loading prediction data..."):
        customers_df, transactions_df, journey_df = load_prediction_data()
    
    if customers_df.empty:
        st.warning("No data available")
        return
    
    # Calculate predictions
    clv_df = calculate_clv_prediction(transactions_df, customers_df)
    clv_df = calculate_ltv_cac_ratio(clv_df, cac=100)
    churn_risk = calculate_churn_risk(transactions_df, customers_df, journey_df)
    
    # Tabs for different analyses
    tab1, tab2, tab3 = st.tabs(["💰 CLV Prediction", "⚠️ Churn Risk", "🎯 Recommendations"])
    
    # ========================================================================
    # TAB 1: CLV PREDICTION
    # ========================================================================
    with tab1:
        st.markdown("### 💰 Customer Lifetime Value Prediction")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "💵 Avg Historical CLV",
                f"${clv_df['historical_clv'].mean():,.0f}",
                delta=f"{len(clv_df):,} Customers"
            )
        
        with col2:
            st.metric(
                "📈 Avg 12M Predicted CLV",
                f"${clv_df['predicted_clv_12m'].mean():,.0f}",
                delta=f"+${(clv_df['predicted_clv_12m'].mean() - clv_df['historical_clv'].mean()):,.0f}"
            )
        
        with col3:
            st.metric(
                "🎯 Avg LTV:CAC Ratio",
                f"{clv_df['ltv_cac_ratio'].mean():.2f}x",
                delta="Healthy if > 3x"
            )
        
        with col4:
            top_segment_clv = clv_df.groupby('segment')['predicted_clv_12m'].mean().idxmax()
            st.metric(
                "🏆 Best Segment",
                f"{top_segment_clv.title()}",
                delta=f"${clv_df[clv_df['segment'] == top_segment_clv]['predicted_clv_12m'].mean():,.0f}"
            )
        
        st.markdown("---")
        
        # CLV distribution
        col1, col2 = st.columns(2)
        
        with col1:
            fig_clv_dist = px.histogram(
                clv_df,
                x='predicted_clv_12m',
                nbins=50,
                title='Distribution of 12-Month Predicted CLV',
                labels={'predicted_clv_12m': 'Predicted CLV ($)', 'count': 'Customers'},
                color_discrete_sequence=['#636EFA']
            )
            fig_clv_dist.update_layout(height=400)
            st.plotly_chart(fig_clv_dist, use_container_width=True)
        
        with col2:
            fig_clv_segment = px.box(
                clv_df,
                x='segment',
                y='predicted_clv_12m',
                title='12-Month CLV Prediction by Segment',
                labels={'predicted_clv_12m': 'Predicted CLV ($)', 'segment': 'Segment'},
                color='segment',
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_clv_segment.update_layout(height=400)
            st.plotly_chart(fig_clv_segment, use_container_width=True)
        
        # Top CLV customers
        st.markdown("### 🥇 Top 20 Customers by Predicted 12-Month CLV")
        
        top_clv = clv_df.nlargest(20, 'predicted_clv_12m')[
            ['customer_id', 'historical_clv', 'predicted_clv_12m', 'purchase_frequency', 'segment', 'ltv_cac_ratio']
        ].copy()
        
        top_clv.columns = ['Customer ID', 'Historical CLV', 'Predicted CLV (12M)', 'Purchase Freq', 'Segment', 'LTV:CAC']
        top_clv['Historical CLV'] = top_clv['Historical CLV'].apply(lambda x: f"${x:,.2f}")
        top_clv['Predicted CLV (12M)'] = top_clv['Predicted CLV (12M)'].apply(lambda x: f"${x:,.2f}")
        top_clv['Purchase Freq'] = top_clv['Purchase Freq'].apply(lambda x: f"{x:.2f}")
        top_clv['LTV:CAC'] = top_clv['LTV:CAC'].apply(lambda x: f"{x:.2f}x")
        
        st.dataframe(top_clv, use_container_width=True)
        
        # CLV by segment
        st.markdown("### 📊 CLV Metrics by Segment")
        
        clv_segment = clv_df.groupby('segment').agg({
            'customer_id': 'count',
            'historical_clv': 'mean',
            'predicted_clv_12m': 'mean',
            'purchase_frequency': 'mean',
            'ltv_cac_ratio': 'mean'
        }).reset_index()
        
        clv_segment.columns = ['Segment', 'Customers', 'Avg Historical CLV', 'Avg 12M CLV', 'Avg Purchase Freq', 'Avg LTV:CAC']
        
        st.dataframe(clv_segment, use_container_width=True)
    
    # ========================================================================
    # TAB 2: CHURN RISK
    # ========================================================================
    with tab2:
        st.markdown("### ⚠️ Churn Risk Prediction")
        
        # Risk distribution
        risk_dist = churn_risk['risk_level'].value_counts()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            high_risk_count = (churn_risk['risk_level'] == 'High').sum()
            st.metric(
                "🔴 High Risk Customers",
                f"{high_risk_count:,}",
                delta=f"{high_risk_count/len(churn_risk)*100:.1f}%"
            )
        
        with col2:
            medium_risk_count = (churn_risk['risk_level'] == 'Medium').sum()
            st.metric(
                "🟡 Medium Risk Customers",
                f"{medium_risk_count:,}",
                delta=f"{medium_risk_count/len(churn_risk)*100:.1f}%"
            )
        
        with col3:
            low_risk_count = (churn_risk['risk_level'] == 'Low').sum()
            st.metric(
                "🟢 Low Risk Customers",
                f"{low_risk_count:,}",
                delta=f"{low_risk_count/len(churn_risk)*100:.1f}%"
            )
        
        with col4:
            avg_inactivity = churn_risk['days_inactive'].mean()
            st.metric(
                "📊 Avg Days Inactive",
                f"{avg_inactivity:.0f}",
                delta="days since last purchase"
            )
        
        st.markdown("---")
        
        # Risk distribution
        col1, col2 = st.columns(2)
        
        with col1:
            fig_risk_dist = px.histogram(
                churn_risk,
                x='churn_risk_score',
                nbins=30,
                title='Churn Risk Score Distribution',
                labels={'churn_risk_score': 'Risk Score (0-100)', 'count': 'Customers'},
                color_discrete_sequence=['#EF553B']
            )
            fig_risk_dist.update_layout(height=400)
            st.plotly_chart(fig_risk_dist, use_container_width=True)
        
        with col2:
            fig_risk_pie = px.pie(
                values=risk_dist.values,
                names=risk_dist.index,
                title='Customer Risk Level Distribution',
                color=risk_dist.index,
                color_discrete_map={'High': '#EF553B', 'Medium': '#FFA15A', 'Low': '#00CC96'}
            )
            fig_risk_pie.update_layout(height=400)
            st.plotly_chart(fig_risk_pie, use_container_width=True)
        
        # High-risk customers
        st.markdown("### 🔴 Top 20 High-Risk Customers (At Risk of Churning)")
        
        high_risk = churn_risk[churn_risk['risk_level'] == 'High'].nlargest(20, 'churn_risk_score')[
            ['customer_id', 'segment', 'churn_risk_score', 'days_inactive', 'purchase_frequency', 'journey_events']
        ].copy()
        
        high_risk.columns = ['Customer ID', 'Segment', 'Risk Score', 'Days Inactive', 'Purchase Freq', 'Engagement Events']
        high_risk['Risk Score'] = high_risk['Risk Score'].apply(lambda x: f"{x:.1f}")
        high_risk['Purchase Freq'] = high_risk['Purchase Freq'].apply(lambda x: f"{x:.2f}")
        
        st.dataframe(high_risk, use_container_width=True)
        
        # Risk by segment
        st.markdown("### 📊 Churn Risk by Segment")
        
        risk_segment = churn_risk.groupby('segment').agg({
            'customer_id': 'count',
            'churn_risk_score': 'mean',
            'days_inactive': 'mean',
            'purchase_frequency': 'mean'
        }).reset_index()
        
        risk_segment.columns = ['Segment', 'Customers', 'Avg Risk Score', 'Avg Days Inactive', 'Avg Purchase Freq']
        
        st.dataframe(risk_segment, use_container_width=True)
    
    # ========================================================================
    # TAB 3: RECOMMENDATIONS
    # ========================================================================
    with tab3:
        st.markdown("### 🎯 Customer Recommendations Engine")
        
        # Merge CLV and churn data
        recommendations = clv_df.merge(
            churn_risk[['customer_id', 'churn_risk_score', 'risk_level', 'days_inactive']],
            on='customer_id'
        )
        
        # Create recommendation logic
        def get_recommendation(row):
            if row['risk_level'] == 'High':
                if row['predicted_clv_12m'] > clv_df['predicted_clv_12m'].median():
                    return 'Win-back Campaign'
                else:
                    return 'Retention Offer'
            elif row['risk_level'] == 'Medium':
                if row['predicted_clv_12m'] > clv_df['predicted_clv_12m'].quantile(0.75):
                    return 'Loyalty Program'
                else:
                    return 'Engagement Campaign'
            else:
                if row['predicted_clv_12m'] > clv_df['predicted_clv_12m'].quantile(0.75):
                    return 'VIP Program'
                else:
                    return 'Cross-sell'
        
        recommendations['recommendation'] = recommendations.apply(get_recommendation, axis=1)
        
        # Recommendation distribution
        rec_dist = recommendations['recommendation'].value_counts()
        
        fig_rec = px.bar(
            x=rec_dist.index,
            y=rec_dist.values,
            title='Recommended Actions Distribution',
            labels={'x': 'Recommendation', 'y': 'Number of Customers'},
            color=rec_dist.index,
            text=rec_dist.values,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_rec.update_traces(textposition='outside')
        fig_rec.update_xaxes(tickangle=-45)
        fig_rec.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_rec, use_container_width=True)
        
        # Recommendations by priority
        st.markdown("---")
        st.markdown("### 🎯 Recommended Actions by Type")
        
        # Win-back
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔴 Win-Back Campaign (High Value, High Risk)")
            win_back = recommendations[recommendations['recommendation'] == 'Win-back Campaign'].nlargest(10, 'predicted_clv_12m')
            if len(win_back) > 0:
                win_back_display = win_back[['customer_id', 'segment', 'predicted_clv_12m', 'days_inactive']].copy()
                win_back_display.columns = ['Customer ID', 'Segment', 'Predicted CLV (12M)', 'Days Inactive']
                win_back_display['Predicted CLV (12M)'] = win_back_display['Predicted CLV (12M)'].apply(lambda x: f"${x:,.2f}")
                st.dataframe(win_back_display, use_container_width=True)
            else:
                st.info("No customers in this category")
        
        with col2:
            st.markdown("#### 🟡 VIP Program (High Value, Low Risk)")
            vip = recommendations[recommendations['recommendation'] == 'VIP Program'].nlargest(10, 'predicted_clv_12m')
            if len(vip) > 0:
                vip_display = vip[['customer_id', 'segment', 'predicted_clv_12m', 'purchase_frequency']].copy()
                vip_display.columns = ['Customer ID', 'Segment', 'Predicted CLV (12M)', 'Purchase Frequency']
                vip_display['Predicted CLV (12M)'] = vip_display['Predicted CLV (12M)'].apply(lambda x: f"${x:,.2f}")
                vip_display['Purchase Frequency'] = vip_display['Purchase Frequency'].apply(lambda x: f"{x:.2f}")
                st.dataframe(vip_display, use_container_width=True)
            else:
                st.info("No customers in this category")
        
        # All recommendations
        st.markdown("---")
        st.markdown("### 📊 All Recommendations")
        
        all_rec = recommendations[['customer_id', 'segment', 'predicted_clv_12m', 'risk_level', 'recommendation']].copy()
        all_rec.columns = ['Customer ID', 'Segment', 'Predicted CLV (12M)', 'Risk Level', 'Recommendation']
        all_rec['Predicted CLV (12M)'] = all_rec['Predicted CLV (12M)'].apply(lambda x: f"${x:,.2f}")
        
        # Filter by recommendation type
        rec_type = st.selectbox(
            "Filter by Recommendation Type",
            all_rec['Recommendation'].unique(),
            key="rec_filter"
        )
        
        filtered_rec = all_rec[all_rec['Recommendation'] == rec_type].head(50)
        st.dataframe(filtered_rec, use_container_width=True)
        
        # Summary
        st.markdown("---")
        st.markdown("### 📈 Action Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_win_back = len(recommendations[recommendations['recommendation'] == 'Win-back Campaign'])
            potential_revenue = recommendations[recommendations['recommendation'] == 'Win-back Campaign']['predicted_clv_12m'].sum()
            st.metric(
                "🔴 Win-Back Potential",
                f"${potential_revenue:,.0f}",
                delta=f"{total_win_back} customers"
            )
        
        with col2:
            total_vip = len(recommendations[recommendations['recommendation'] == 'VIP Program'])
            vip_revenue = recommendations[recommendations['recommendation'] == 'VIP Program']['predicted_clv_12m'].sum()
            st.metric(
                "⭐ VIP Opportunity",
                f"${vip_revenue:,.0f}",
                delta=f"{total_vip} customers"
            )
        
        with col3:
            retention_revenue = recommendations[recommendations['risk_level'] == 'High']['predicted_clv_12m'].sum()
            retention_count = len(recommendations[recommendations['risk_level'] == 'High'])
            st.metric(
                "⚠️ Retention Risk Value",
                f"${retention_revenue:,.0f}",
                delta=f"{retention_count} at-risk customers"
            )

if __name__ == "__main__":
    main()