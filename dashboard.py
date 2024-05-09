import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd

# Load and preprocess data
hotel_bookings = pd.read_csv('hotel_bookings.csv')
hotel_bookings['arrival_date'] = pd.to_datetime(hotel_bookings['arrival_date_year'].astype(str) + '-' +
                                                hotel_bookings['arrival_date_month'] + '-' +
                                                hotel_bookings['arrival_date_day_of_month'].astype(str))
bookings_by_date = hotel_bookings.groupby('arrival_date').size().reset_index(name='number_of_bookings')

hotel_bookings = hotel_bookings.dropna(subset=['country'])  # Ensure no NA values in 'country'

app = dash.Dash(__name__)

options = [{'label': 'Select All', 'value': 'ALL'}]
options += [{'label': i, 'value': i} for i in hotel_bookings['country'].unique()]

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
                value=['PRT'],  
                multi=True  
            )
        ])
    ])
])

@app.callback(
    Output('booking-trend', 'figure'),
    Input('year-slider', 'value'))
def update_booking_trend(selected_year):
    filtered_data = bookings_by_date[bookings_by_date['arrival_date'].dt.year == selected_year]
    fig = px.line(filtered_data, x='arrival_date', y='number_of_bookings', title='Hotel Bookings Trend Over Time')
    return fig

@app.callback(
    Output('guest-geo-dist', 'figure'),
    Input('country-dropdown', 'value'))
def update_geo_distribution(selected_countries):
    # Check if no countries are selected explicitly by checking the length of the list
    if selected_countries is None or len(selected_countries) == 0:
        return px.choropleth(title='Select countries for the distribution')
    
    # Handling "Select All" option
    if 'ALL' in selected_countries:
        selected_countries = hotel_bookings['country'].unique()

    filtered_data = hotel_bookings[hotel_bookings['country'].isin(selected_countries)]
    country_bookings = filtered_data.groupby('country').size().reset_index(name='number_of_bookings')
    
    fig = px.choropleth(country_bookings, locations='country', locationmode='country names',
                        color='number_of_bookings', scope="world",
                        title='Guest Geographic Distribution',
                        color_continuous_scale=px.colors.sequential.Plasma)
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)

