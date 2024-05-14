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

options = [{'label': 'Select All', 'value': 'ALL'}]
options += [{'label': i, 'value': i} for i in hotel_bookings['country'].unique() if type(i)==str]

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
    Input('country-dropdown', 'value'))
def update_geo_distribution(selected_countries):
    # Check if no countries are selected explicitly by checking the length of the list
    if selected_countries is None or len(selected_countries) == 0:
        return px.choropleth(title='Select countries for the distribution')
    country_counts = hotel_bookings['country'].value_counts().reset_index()
    country_counts.columns = ['country', 'number_of_bookings']

    # Handling "Select All" option
    if 'ALL' not in selected_countries:
        country_counts = country_counts[country_counts.country.isin(selected_countries)]

    
    fig = px.choropleth(country_counts, locations='country', 
                        color='number_of_bookings', scope="world",
                        title='Guest Geographic Distribution',
                        color_continuous_scale=px.colors.sequential.Plasma)
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)

