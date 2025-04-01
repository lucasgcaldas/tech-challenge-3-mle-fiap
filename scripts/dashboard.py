import os
import dash
from dash import dcc, html
import plotly.graph_objs as go
import pandas as pd
import psycopg2
from dash.dependencies import Input, Output

from dotenv import load_dotenv
load_dotenv()

# Função para conectar ao PostgreSQL usando psycopg2
def get_data_from_postgresql():
    # Conectar ao PostgreSQL
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    
    # Definir a consulta SQL
    query = """
    SELECT timestamp, forecast_rain
    FROM fiap_lab3.weather_forecast
    WHERE city = 'brasilia'
    ORDER BY timestamp;
    """
    
    # Ler os dados da consulta SQL diretamente no Pandas
    df = pd.read_sql(query, conn)
    
    # Fechar a conexão com o banco de dados
    conn.close()
    
    return df

# Carregar os dados do PostgreSQL
df = get_data_from_postgresql()

# Iniciar a aplicação Dash
app = dash.Dash(__name__)

# Layout do dashboard
app.layout = html.Div([
    html.H1("Previsão de Chuva - Brasília"),
    
    # Gráfico com Plotly
    dcc.Graph(
        id='rain-forecast-graph',
        figure={
            'data': [
                go.Scatter(
                    x=df['timestamp'],
                    y=df['forecast_rain'],
                    mode='lines+markers',
                    name='Previsão de Chuva',
                    line={'color': 'blue'}
                )
            ],
            'layout': go.Layout(
                title='Previsão de Chuva para os Próximos 7 Dias',
                xaxis={'title': 'Data'},
                yaxis={'title': 'Precipitação (mm)'},
                hovermode='closest'
            )
        }
    )
])

# Rodar o servidor
if __name__ == '__main__':
    app.run(debug=True)
