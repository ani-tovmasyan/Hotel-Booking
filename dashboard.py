import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from pandas import date_range

# Load and preprocess data
hotel_bookings = pd.read_csv('hotel_bookings.csv')
hotel_bookings['arrival_date'] = pd.to_datetime(hotel_bookings['arrival_date_year'].astype(str) + '-' +
                                                hotel_bookings['arrival_date_month'] + '-' +
                                                hotel_bookings['arrival_date_day_of_month'].astype(str))
bookings_by_date = hotel_bookings.groupby('arrival_date').size().reset_index(name='number_of_bookings')

app = dash.Dash(__name__)
hotel_bookings['is_canceled'] = pd.to_numeric(hotel_bookings['is_canceled'], errors='coerce')
hotel_bookings['days_in_waiting_list'] = pd.to_numeric(hotel_bookings['days_in_waiting_list'], errors='coerce')
hotel_bookings['required_car_parking_spaces'] = pd.to_numeric(hotel_bookings['required_car_parking_spaces'], errors='coerce')
hotel_bookings['total_of_special_requests'] = pd.to_numeric(hotel_bookings['total_of_special_requests'], errors='coerce')

app = dash.Dash(__name__)

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


app.layout = html.Div([
    dcc.Tabs([
        dcc.Tab(label='Booking Trends', children=[
            dcc.Graph(id='booking-trend'),
            dcc.Slider(
                id='year-slider',
                min=hotel_bookings['arrival_date_year'].min(),
                max=hotel_bookings['arrival_date_year'].max(),
                value=hotel_bookings['arrival_date_year'].min(),
                marks={str(year): str(year) for year in hotel_bookings['arrival_date_year'].unique()},
                step=None
            )
        ]),
        dcc.Tab(label='Guest Analysis', children=[
            dcc.Graph(id='guest-geo-dist'),
            dcc.Dropdown(
                id='country-dropdown',
                options=options,
                value=['ALL'],
                multi=True
            ),
            dcc.Dropdown(
                id='feature-dropdown',
                options=feature_options,
                value='booking_count'
            )
        ]),
        dcc.Tab(label='Cancellation Analysis', children=[
            html.Div([
                dcc.Dropdown(
                    id='country-select',
                    options=options,
                    value=[options[0]['value']],  # Default to 'Select All'
                    multi=True
                ),
                dcc.DatePickerRange(
                    id='date-range-select',
                    min_date_allowed=hotel_bookings['arrival_date'].min(),
                    max_date_allowed=hotel_bookings['arrival_date'].max(),
                    start_date=hotel_bookings['arrival_date'].min(),
                    end_date=hotel_bookings['arrival_date'].max()
                ),
                dcc.Graph(id='cancellation-pie-chart')
            ])
        ]),
        dcc.Tab(label='Customer Type Analysis', children=[
            html.Div([
                dcc.Dropdown(
                    id='metrics-dropdown',
                    options=metric_options,
                    value=['cancellation_rate'],  # Default selected metrics
                    multi=True
                ),
                dcc.Graph(id='customer-type-stacked-bar')
            ])
        ])
    ])
])


@app.callback(
    Output('booking-trend', 'figure'),
    Input('year-slider', 'value'))
def update_booking_trend(selected_year):
    filtered_data = bookings_by_date[bookings_by_date['arrival_date'].dt.year == selected_year]
    fig = px.line(filtered_data, x='arrival_date', y='number_of_bookings', title='Hotel Bookings Trend Over Time')
    
    # Find all weekends in the year
    start_date = str(selected_year) + "-01-01"
    end_date = str(selected_year) + "-12-31"
    weekends = date_range(start=start_date, end=end_date, freq='W-SAT')
    
    # Add shapes for each weekend
    for date in weekends:
        fig.add_vrect(
            x0=date, x1=date + pd.Timedelta(days=1),
            fillcolor="grey", opacity=0.2,
            layer="below", line_width=0,
        )

    return fig

@app.callback(
    Output('guest-geo-dist', 'figure'),
    [Input('country-dropdown', 'value'),
     Input('feature-dropdown', 'value')])
def update_geo_distribution(selected_countries, selected_feature):
    if selected_countries is None or len(selected_countries) == 0:
        return px.choropleth(title='Select countries for the distribution')
    
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
    return fig

@app.callback(
    Output('cancellation-pie-chart', 'figure'),
    [Input('country-select', 'value'),
     Input('date-range-select', 'start_date'),
     Input('date-range-select', 'end_date')])
def update_cancellation_pie(selected_countries, start_date, end_date):
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
    return fig

@app.callback(
    Output('customer-type-stacked-bar', 'figure'),
    [Input('metrics-dropdown', 'value')])
def update_customer_type_metrics(selected_metrics):
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
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)

