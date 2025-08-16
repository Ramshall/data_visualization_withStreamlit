import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import altair as alt


# set configuration for page
st.set_page_config(
    page_title='E-commerce Analysis and Visualization',
    page_icon='📈',
    layout='wide',
    initial_sidebar_state='expanded'
)

# function to load data
@st.cache_data
def load_data():
    df = pd.read_csv('data/data_ecommerce_cleaned.csv', index_col=0)
    df.columns = df.columns.str.lower()
    df['invoicedate'] = pd.to_datetime(df['invoicedate'])
    return df

# load data
df_ecommerce = load_data()

# Title
st.title('E-commerce Performance')
st.markdown("Analisis visualisasi ini berdasarkan EDA yang sudah dilakukan [sebelumnya](https://drive.google.com/file/d/1dAjg_r5oaoYhGH8AvF1IlV11kiory9Kc/view?usp=sharing). Hasil analisis dan visualisasi tidak jauh berbeda dengan link yang tertera, mungkin ada perbedaan sedikit dari segi viusal, filter, dsb.") 


# bar for filter and navigating
st.sidebar.header('Setting & Filtering')

# create filter based on date
st.sidebar.markdown('## Date Filter')
min_date = df_ecommerce['invoicedate'].min()
max_date = df_ecommerce['invoicedate'].max()

# initialize session_state if isn't it
if 'date_selection' not in st.session_state:
    st.session_state.date_selection = (min_date, max_date)

# create function to reset_date
def reset_date_filter():
    st.session_state.date_selection = (min_date, max_date)

# create range from date
date_range = st.sidebar.date_input(
    'Select Range:',
    key='date_selection'
)

# add button for reset date
st.sidebar.button("Reset Date Filter", on_click=reset_date_filter)

# create filter based on country
st.sidebar.markdown('## Country Filter')
all_countries_option = ['All Countries'] + df_ecommerce['country'].unique().tolist()

selected_country = st.sidebar.selectbox(
    'Select country:',
    options=all_countries_option
)

# create defence if input is invalid
if len(date_range) == 2:
    start_date, end_date = date_range
    if start_date > end_date:
        st.error('Tanggal mulai tidak boleh lebih dari tanggal akhir')
        st.stop()
else:
    # if date range selecting not complete
    st.warning("Pilih rentang tanggal yang lengkap (star date dan end date).")
    st.stop()
    
# apply date filter
df_filtered = df_ecommerce[
    (df_ecommerce['invoicedate'] >= pd.to_datetime(start_date)) &
    (df_ecommerce['invoicedate'] <= pd.to_datetime(end_date) + timedelta(days=1))
]

# apply filter
if selected_country != 'All Countries':
    df_filtered = df_filtered[df_filtered['country'] == selected_country]


# create tab for overview and dataset
tab_overview, tab_dataset = st.tabs(["Overview", "Dataset"])

with tab_overview:
    st.header(f"Performance Analysis")
    st.write(f"Berdasarkan data dari rentang tanggal **{start_date.strftime('%d %b %Y')}** hingga **{end_date.strftime('%d %b %Y')}**.")
    
    # first visz: create metrics 
    st.subheader('Summarize Performance')

    # create col
    col1, col2, col3, col4 = st.columns([3,3,3,3])
    
    # totalcustomer
    total_custs = df_filtered['customerid'].nunique()
    # total order, nunqiue is choseen because the invoice possible same for different product
    total_orders = df_filtered['invoiceno'].nunique()
    # total quantity_sold
    total_products_sold = df_filtered['quantity'].sum()
    # total sales
    total_sales = df_filtered['sales'].sum()
    
    with col1:
        st.metric(label="Total Sales", value=f"£ {total_sales:,.2f}")
    with col2:
        st.metric(label="Total Orders", value=f"{total_orders:,}")
    with col3:
        st.metric(label="Total Quantity Sold", value=f"£ {total_products_sold:,.2f}")
    with col4:
        st.metric(label="Total Customers", value=f"{total_custs:,}")
    st.markdown("---")
    
    # Sales Trend
    st.subheader(f'Sales Trend in {selected_country}')
    st.info(f"Konteks data: **{start_date.strftime('%d %b %Y')}** hingga **{end_date.strftime('%d %b %Y')}**")

    # agrgeate month-year sales
    monthly_sales = df_filtered.groupby(
        df_filtered['invoicedate'].dt.to_period('M')
    ).agg(total_sales=('sales', 'sum')).reset_index()
    
    monthly_sales['month_year'] = monthly_sales['invoicedate'].dt.to_timestamp()
    
    # create line chart with plotly
    fig_monthly_trend = px.line(
        monthly_sales,
        x='month_year',
        y='total_sales',
        title='Monthly-Yearly Sales Trend',
        markers=True,
        labels={'month_year': 'Month-Year', 'total_sales': 'Total Sales (£)'}
    )
    # update x-axes
    fig_monthly_trend.update_xaxes(tickformat='%b %Y')
    fig_monthly_trend.update_layout(showlegend=False)
    
    st.plotly_chart(fig_monthly_trend, use_container_width=True)
    
    st.markdown("---")
    
    # Customers Analysis
    st.subheader(f'Customer Analysis in {selected_country}')
    
    # create col
    bar_chart1, bar_chart2 = st.columns([3, 3])
    
    # create top 10 custo from total saels
    top_10_sales_cust = df_filtered.groupby('customerid') \
                        .agg({'sales': 'sum'}) \
                        .rename(columns={'sales': 'total_sales'}) \
                        .sort_values(by='total_sales', ascending=False) \
                        .head(10) \
                        .reset_index()
                               
    # create top 10 custo from total orders
    top_10_orders_cust = df_filtered.groupby('customerid') \
                        .agg({'invoiceno': 'nunique'}) \
                        .rename(columns={'invoiceno': 'total_orders'}) \
                        .sort_values(by='total_orders', ascending=False) \
                        .head(10) \
                        .reset_index()

    # change dtype to handle ambigu for visualization
    top_10_sales_cust['customerid'] = top_10_sales_cust['customerid'].astype(str)
    top_10_orders_cust['customerid'] = top_10_orders_cust['customerid'].astype(str)
    
    # first bar chart (top 10 sales by vustomer)
    with bar_chart1:
        # creat visz with altair
        bar_chart1 = alt.Chart(top_10_sales_cust).mark_bar().encode(
            x=alt.X('total_sales:Q', title='Total Sales (£)'),
            y=alt.Y('customerid:O', title='Customer ID', sort='-x')
        ).properties(title='Top 10 Customers by Total Sales')
        
        st.altair_chart(bar_chart1, use_container_width=True)
    
    # second bar chart (top 10 order by customer)
    with bar_chart2:
        bar_chart2 = alt.Chart(top_10_orders_cust).mark_bar().encode(
            x=alt.X('total_orders:Q', title='Total Orders'),
            y=alt.Y('customerid:O', title='Customer ID', sort='-x')
        ).properties(title='Top 10 Customers by Total Orders')
        
        st.altair_chart(bar_chart2, use_container_width=True)
    
    st.markdown("---")

    # Hour Analysis with Plotly
    st.subheader(f'Trend Order by Hour in {selected_country}')
    
    col_pie, col_trend_hour = st.columns([3, 3])
    
    with col_pie:
        # agregate by dayperiod
        day_period_orders = df_filtered.groupby('dayperiod', as_index=False).agg(
        total_orders=('invoiceno', 'nunique')
        )
        # crreat pie chart
        fig_pie_period = px.pie(
            day_period_orders,
            names='dayperiod',
            values='total_orders',
            title='Distribution of Orders',
            hole=0.4
        )
        fig_pie_period.update_layout(showlegend=True, title_x=0.05)
        st.plotly_chart(fig_pie_period, use_container_width=True)
        
    
    with col_trend_hour:
        # agregate order by hour
        hourly_orders = df_filtered.groupby('invoicehour', as_index=False).agg(
            total_orders=('invoiceno', 'nunique')
        )
        
        # create line chart
        fig_line_hour = px.line(
            hourly_orders,
            x='invoicehour',
            y='total_orders',
            markers=True,  
            title='Trend of Orders per Hour'
        )
        
        # naming axis
        fig_line_hour.update_layout(
            xaxis_title='Hour of Day',
            yaxis_title='Number of Orders'
        )
        
        # order hour
        fig_line_hour.update_xaxes(
            tickvals=hourly_orders['invoicehour'], 
            tickmode='linear'
        )
        
        st.plotly_chart(fig_line_hour, use_container_width=True)
        
    st.markdown("---")
    
    # Trend Order by day in week
    st.subheader(f'Heatmap of Orders by Day and Hour in {selected_country}')
    
    # agregate total order by dayofweek and invoicehour
    hourly_day_orders = df_filtered.groupby(['dayofweek', 'invoicehour'], as_index=False).agg(
        total_orders=('invoiceno', 'nunique')
    )
    
    # create pivot tabele
    pivot_table = hourly_day_orders.pivot(
        index='dayofweek',
        columns='invoicehour',
        values='total_orders'
    ).fillna(0)
    
    # define order
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    pivot_table = pivot_table.reindex(day_order)
    
    # create heatmap with Plotly
    fig_heatmap = px.imshow(
        pivot_table,
        labels=dict(x="Hour of Day", y="Day of Week", color="Total Orders"),
        title="Heatmap of Orders by Day and Hour",
        color_continuous_scale='YlGnBu',
        text_auto=True
    )
    
    st.plotly_chart(fig_heatmap, use_container_width=True)

# other tab (tab dataset)
with tab_dataset:
    st.header("Detail Dataset")
    st.write(f"Data yang ditampilkan berdasarkan rentang tanggal dari **{start_date.strftime('%d %b %Y')}** hingga **{end_date.strftime('%d %b %Y')}** untuk {selected_country}.")
    st.info(f"Jumlah baris data yang ditampilkan **{len(df_filtered)}** dari total keseluruhan {len(df_ecommerce)}")
    
    st.dataframe(df_filtered)