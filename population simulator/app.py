import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd
import requests
from dash.dependencies import Input, Output

app = dash.Dash(__name__)
server = app.server

API_URL = "http://api.worldbank.org/v2/country/{}/indicator/{}?format=json"

def fetch_vital_stats_data(indicator_code, country="world"):
    response = requests.get(API_URL.format(country, indicator_code))
    try:
        data = response.json()
    except ValueError:
        print("Invalid JSON response")
        return pd.DataFrame()

    if len(data) < 2 or not isinstance(data[1], list):
        print(f"No data available for {indicator_code} in {country}")
        return pd.DataFrame()
    
    data = data[1]
    df = pd.DataFrame(data)
    
    # Check for 'country' field being a dictionary
    if 'country' in df.columns and isinstance(df['country'][0], dict):
        df['Country'] = df['country'].apply(lambda x: x.get('value', 'Unknown'))
    else:
        df.rename(columns={'country': 'Country'}, inplace=True)

    df = df[['Country', 'date', 'value']]
    df.rename(columns={'date': 'Year', 'value': indicator_code}, inplace=True)
    df['Year'] = df['Year'].astype(int)  # Convert year to integer for consistency
    return df

app.layout = html.Div([
    html.H1("Real-Time Global Population and Vital Statistics Dashboard"),
    dcc.Dropdown(
        id='country-dropdown',
        options=[
            {'label': 'World', 'value': 'world'}, 
            {'label': 'India', 'value': 'IN'}, 
            {'label': 'United States', 'value': 'US'},
            {'label': 'Brazil', 'value': 'BR'}
        ],  
        value='world',
        style={'width': '50%'}
    ),
    dcc.Graph(id='population-graph'),
    dcc.Graph(id='birth-rate-graph'),
    dcc.Graph(id='death-rate-graph'),
    dcc.Graph(id='life-expectancy-graph'),
    dcc.Graph(id='fertility-rate-graph'),
    dcc.Graph(id='infant-mortality-graph'),
    dcc.Graph(id='gdp-graph'),
    dcc.Interval(
        id='interval-component',
        interval=60000,
        n_intervals=0
    )
])

@app.callback(
    [Output('population-graph', 'figure'),
     Output('birth-rate-graph', 'figure'),
     Output('death-rate-graph', 'figure'),
     Output('life-expectancy-graph', 'figure'),
     Output('fertility-rate-graph', 'figure'),
     Output('infant-mortality-graph', 'figure'),
     Output('gdp-graph', 'figure')],
    [Input('country-dropdown', 'value'),
     Input('interval-component', 'n_intervals')]
)
def update_graphs(selected_country, n_intervals):
    population_data = fetch_vital_stats_data("SP.POP.TOTL", selected_country)
    birth_rate_data = fetch_vital_stats_data("SP.DYN.BIRT.IN", selected_country)
    death_rate_data = fetch_vital_stats_data("SP.DYN.DEAT.IN", selected_country)
    life_expectancy_data = fetch_vital_stats_data("SP.DYN.LE00.IN", selected_country)
    fertility_rate_data = fetch_vital_stats_data("SP.DYN.TFRT.IN", selected_country)
    infant_mortality_data = fetch_vital_stats_data("SH.DYN.MORT", selected_country)
    gdp_per_capita_data = fetch_vital_stats_data("NY.GDP.PCAP.CD", selected_country)

    # Initialize data with population_data
    data = population_data
    for df in [birth_rate_data, death_rate_data, life_expectancy_data, fertility_rate_data, infant_mortality_data, gdp_per_capita_data]:
        if not df.empty:
            try:
                data = pd.merge(data, df, on=['Country', 'Year'], how='outer')
            except Exception as e:
                print(f"Error merging data: {e}")

    population_fig = px.line(data, x='Year', y='SP.POP.TOTL', title=f'Population of {selected_country} Over Time')
    birth_rate_fig = px.line(data, x='Year', y='SP.DYN.BIRT.IN', title=f'Birth Rate in {selected_country} Over Time')
    death_rate_fig = px.line(data, x='Year', y='SP.DYN.DEAT.IN', title=f'Death Rate in {selected_country} Over Time')
    life_expectancy_fig = px.line(data, x='Year', y='SP.DYN.LE00.IN', title=f'Life Expectancy in {selected_country} Over Time')
    fertility_rate_fig = px.line(data, x='Year', y='SP.DYN.TFRT.IN', title=f'Fertility Rate in {selected_country} Over Time')
    infant_mortality_fig = px.line(data, x='Year', y='SH.DYN.MORT', title=f'Infant Mortality Rate in {selected_country} Over Time')
    gdp_fig = px.line(data, x='Year', y='NY.GDP.PCAP.CD', title=f'GDP per Capita in {selected_country} Over Time')

    return population_fig, birth_rate_fig, death_rate_fig, life_expectancy_fig, fertility_rate_fig, infant_mortality_fig, gdp_fig

if __name__ == '__main__':
    app.run_server(debug=True)
