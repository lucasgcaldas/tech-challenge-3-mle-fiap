import os
import requests
import psycopg2
import json
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

# Initialize S3 client
API_KEY = os.getenv('API_KEY')
DB_SCHEMA = os.getenv('DB_SCHEMA')

def connect_to_postgres():
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    return conn


def get_weather_data(lat, lon, city):
    try:
        url = f"https://history.openweathermap.org/data/2.5/aggregated/year?lat={lat}&lon={lon}&appid={API_KEY}"
        
        # Request weather data from OpenWeatherMap API
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx, 5xx)
        
        data = response.json()
        # Verificar se a resposta contém a chave 'result' com os dados
        if 'result' not in data:
            raise ValueError(f"Invalid data received for {city}: {data}")
        
        # Conectar ao PostgreSQL
        conn = connect_to_postgres()
        cur = conn.cursor()

        year = 2024

        # Iterar sobre os registros de dados agregados (pode conter dados diários)
        for record in data['result']:
            temperature_kelvin_mean = record['temp']['mean']  # Temperatura média do dia em Kelvin
            temperature_kelvin_max = record['temp']['average_max']  # Temperatura média max do dia em Kelvin
            temperature_kelvin_min = record['temp']['average_min']  # Temperatura média min do dia em Kelvin
            rain = record['precipitation']['mean']  # Precipitação total do dia em mm

            # Converter a temperatura de Kelvin para Celsius
            temperature_celsius_mean = temperature_kelvin_mean - 273.15
            temperature_celsius_max = temperature_kelvin_max - 273.15
            temperature_celsius_min = temperature_kelvin_min - 273.15
            # Inserir os dados no PostgreSQL, incluindo o schema
            cur.execute(f"""
                INSERT INTO {DB_SCHEMA}.weather_data (city, year, month, day, temperature_mean, temperature_max, temperature_min, rain)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """, (city, year, record['month'], record['day'], temperature_celsius_mean, temperature_celsius_max, temperature_celsius_min, rain))

        # Commit da transação e fechar a conexão
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"Data for {city} saved successfully in PostgreSQL.")

    except Exception as e:
        # Captura qualquer outra exceção
        print(f"Unexpected error for {city}: {str(e)}")
        raise  # Re-levanta o erro para ser tratado pela função de chamador

if __name__ == "__main__":
    try:
        # Calling the function for multiple cities
        get_weather_data(lat=-15.7934036, lon=-47.8823172, city='brasilia')
        get_weather_data(lat=-16.443473, lon=-39.064251, city='porto-seguro')
        
        print(f'Data collected and stored in PostgreSQL')

    except Exception as e:
        # Catch any exception in the main handler
        print(f"An error occurred: {str(e)}")