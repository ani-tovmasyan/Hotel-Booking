import streamlit as st
import pandas as pd
import plotly.express as px

# Load and preprocess data
hotel_bookings = pd.read_csv('hotel_bookings.csv')
hotel_bookings['arrival_date'] = pd.to_datetime(hotel_bookings['arrival_date_year'].astype(str) + '-' +
                                                hotel_bookings['arrival_date_month'] + '-' +
                                                hotel_bookings['arrival_date_day_of_month'].astype(str))
bookings_by_date = hotel_bookings.groupby('arrival_date').size().reset_index(name='number_of_bookings')

hotel_bookings['is_canceled'] = pd.to_numeric(hotel_bookings['is_canceled'], errors='coerce')
hotel_bookings['days_in_waiting_list'] = pd.to_numeric(hotel_bookings['days_in_waiting_list'], errors='coerce')
hotel_bookings['required_car_parking_spaces'] = pd.to_numeric(hotel_bookings['required_car_parking_spaces'], errors='coerce')
hotel_bookings['total_of_special_requests'] = pd.to_numeric(hotel_bookings['total_of_special_requests'], errors='coerce')

options = [{'label': 'Select All', 'value': 'ALL'}]
options += [{'label': i, 'value': i} for i in hotel_bookings['country'].unique() if pd.notnull(i)]

feature_options = [{'label': 'Booking Count', 'value': 'booking_count'},
                   {'label': 'Cancellation Rate', 'value': 'cancellation_rate'},
                   {'label': 'Load Time', 'value': 'load_time'},
                   {'label': 'Days in Waiting List', 'value': 'days_in_waiting_list'},
                   {'label': 'Required Car Parking Spaces', 'value': 'required_car_parking_spaces'}]

metric_options = [{'label': 'Cancellation Rate', 'value': 'cancellation_rate'},
                  {'label': 'Days in Waiting List', 'value': 'average_days_in_waiting_list'},
                  {'label': 'Required Car Parking Spaces', 'value': 'average_required_car_parking_spaces'},
                  {'label': 'Total of Special Requests', 'value': 'average_total_of_special_requests'}]

# Streamlit App with Tabs
st.title("Hotel Booking Dashboard")

tab1, tab2, tab3, tab4 = st.tabs(["Booking Trends", "Guest Analysis", "Cancellation Analysis", "Customer Type Analysis"])

# Booking Trends Tab
with tab1:
    st.header("Booking Trends")
    year_slider = st.slider(
        "Select Year",
        min_value=int(hotel_bookings['arrival_date_year'].min()),
        max_value=int(hotel_bookings['arrival_date_year'].max()),
        value=int(hotel_bookings['arrival_date_year'].min()),
        step=1,
        key="year_slider"
    )
    
    filtered_data = bookings_by_date[bookings_by_date['arrival_date'].dt.year == year_slider]
    fig = px.line(filtered_data, x='arrival_date', y='number_of_bookings', title='Hotel Bookings Trend Over Time')
    
    # Find all weekends in the year
    start_date = str(year_slider) + "-01-01"
    end_date = str(year_slider) + "-12-31"
    weekends = pd.date_range(start=start_date, end=end_date, freq='W-SAT')
    
    # Add shapes for each weekend
    for date in weekends:
        fig.add_vrect(
            x0=date, x1=date + pd.Timedelta(days=1),
            fillcolor="grey", opacity=0.2,
            layer="below", line_width=0,
        )
    
    st.plotly_chart(fig)

# Guest Analysis Tab
with tab2:
    st.header("Guest Analysis")
    selected_countries = st.multiselect("Select Countries", [i['value'] for i in options], default=['ALL'], key="country_multiselect")
    selected_feature = st.selectbox("Select Feature", [i['value'] for i in feature_options], key="feature_selectbox")
    
    if 'ALL' not in selected_countries:
        filtered_data = hotel_bookings[hotel_bookings['country'].isin(selected_countries)]
    else:
        filtered_data = hotel_bookings.copy()

    if selected_feature == 'cancellation_rate':
        feature_data = filtered_data.groupby('country')['is_canceled'].mean().reset_index()
        feature_data.columns = ['country', 'value']
        color_scale = px.colors.sequential.Blues
        title = 'Cancellation Rate by Country'
    elif selected_feature == 'days_in_waiting_list':
        feature_data = filtered_data.groupby('country')['days_in_waiting_list'].mean().reset_index()
        feature_data.columns = ['country', 'value']
        color_scale = px.colors.sequential.Greens
        title = 'Average Days in Waiting List by Country'
    elif selected_feature == 'required_car_parking_spaces':
        feature_data = filtered_data.groupby('country')['required_car_parking_spaces'].mean().reset_index()
        feature_data.columns = ['country', 'value']
        color_scale = px.colors.sequential.Purples
        title = 'Average Required Car Parking Spaces by Country'
    else:  
        feature_data = filtered_data.groupby('country').size().reset_index(name='value')
        feature_data.columns = ['country', 'value']
        color_scale = px.colors.sequential.Plasma
        title = 'Booking Count by Country'
    
    fig = px.choropleth(feature_data, locations='country',
                        color='value', scope="world",
                        title=title,
                        color_continuous_scale=color_scale)
    st.plotly_chart(fig)

# Cancellation Analysis Tab
with tab3:
    st.header("Cancellation Analysis")
    selected_countries = st.multiselect("Select Countries", [i['value'] for i in options], default=[options[0]['value']], key="cancel_country_multiselect")
    start_date = st.date_input("Start Date", hotel_bookings['arrival_date'].min(), key="cancel_start_date")
    end_date = st.date_input("End Date", hotel_bookings['arrival_date'].max(), key="cancel_end_date")
    
    if 'ALL' in selected_countries or not selected_countries:
        selected_countries = [option['value'] for option in options if option['value'] != 'ALL']
    
    filtered_data = hotel_bookings[
        (hotel_bookings['country'].isin(selected_countries)) &
        (hotel_bookings['arrival_date'] >= pd.to_datetime(start_date)) &
        (hotel_bookings['arrival_date'] <= pd.to_datetime(end_date))
    ]
    
    cancellation_data = filtered_data.groupby('country').agg(
        total_bookings=pd.NamedAgg(column='is_canceled', aggfunc='size'),
        canceled_bookings=pd.NamedAgg(column='is_canceled', aggfunc='sum')
    )
    cancellation_data['cancellation_rate'] = (cancellation_data['canceled_bookings'] / cancellation_data['total_bookings']) * 100
    cancellation_data.reset_index(inplace=True)
    
    fig = px.pie(cancellation_data, values='cancellation_rate', names='country',
                 title='Cancellation Rates by Selected Countries',
                 color_discrete_sequence=px.colors.sequential.RdBu)
    st.plotly_chart(fig)

# Customer Type Analysis Tab
with tab4:
    st.header("Customer Type Analysis")
    selected_metrics = st.multiselect("Select Metrics", [i['value'] for i in metric_options], default=['cancellation_rate'], key="metrics_multiselect")

    if selected_metrics:
        aggregates = {
            'cancellation_rate': pd.NamedAgg(column='is_canceled', aggfunc='mean'),
            'average_days_in_waiting_list': pd.NamedAgg(column='days_in_waiting_list', aggfunc='mean'),
            'average_required_car_parking_spaces': pd.NamedAgg(column='required_car_parking_spaces', aggfunc='mean'),
            'average_total_of_special_requests': pd.NamedAgg(column='total_of_special_requests', aggfunc='mean')
        }
        
        selected_aggregates = {key: aggregates[key] for key in selected_metrics}
        
        customer_metrics = hotel_bookings.groupby('customer_type').agg(**selected_aggregates).reset_index()
        
        customer_metrics_melted = customer_metrics.melt(id_vars='customer_type', var_name='Metric', value_name='Value')

        fig = px.bar(customer_metrics_melted, x='customer_type', y='Value', color='Metric',
                     title='Metrics by Customer Type',
                     barmode='group')
        st.plotly_chart(fig)

