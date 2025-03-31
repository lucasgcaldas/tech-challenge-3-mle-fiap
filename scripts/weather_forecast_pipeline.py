import os
import requests
import psycopg2
import pandas as pd
from datetime import datetime, timedelta
from prophet import Prophet
from airflow import DAG
from airflow.operators.python import PythonOperator

# Carregar variáveis de ambiente
from dotenv import load_dotenv
load_dotenv()

# Configuração do banco de dados e API
API_KEY=os.getenv('API_KEY')
DB_NAME=os.getenv('DB_NAME')
DB_USER=os.getenv('DB_USER')
DB_PASSWORD=os.getenv('DB_PASSWORD')
DB_HOST=os.getenv('DB_HOST')
DB_PORT=os.getenv('DB_PORT')
DB_SCHEMA=os.getenv('DB_SCHEMA')

# Função para conectar ao PostgreSQL
def connect_to_postgres():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

# Função para coletar dados históricos do PostgreSQL
def collect_historical_data(city, **kwargs):
    conn = connect_to_postgres()
    cur = conn.cursor()
    
    # Consultar os dados históricos de clima para a cidade no banco de dados
    cur.execute(f"""
        SELECT year, month, day, temperature_mean, temperature_max, temperature_min, rain FROM fiap_lab3.weather_data
        WHERE city = %s
        ORDER BY year, month, day;
    """, (city,))

    # Recuperar os dados e convertê-los para um DataFrame
    data = cur.fetchall()
    df = pd.DataFrame(data, columns=['year', 'month', 'day', 'temperature_mean', 'temperature_max', 'temperature_min', 'rain'])

    # Criar uma coluna `date` usando `month` e `day`
    df['date'] = pd.to_datetime(df[['year', 'month', 'day']])

    # Agora, a coluna `date` contém as datas completas (ano, mês e dia)
    df = df[['date', 'temperature_mean', 'temperature_max', 'temperature_min', 'rain']]  # Selecionando as colunas que você precisa

    # Fechar a conexão
    cur.close()
    conn.close()

    # Salvar o DataFrame em XCom para passar para a próxima tarefa
    kwargs['ti'].xcom_push(key=f'historical_data_{city}', value=df.to_json())

    print(f"Historical data for {city} collected.")
    
# Função para coletar dados atuais da API OpenWeatherMap
def collect_current_data(city, lat, lon, **kwargs):
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    
    response = requests.get(url)
    response.raise_for_status()

    data = response.json()
    temperature = data['main']['temp']
    temperature_min = data['main']['temp_min']
    temperature_max = data['main']['temp_max']
    rain = data['rain']['1h']

    # Inserir os dados no banco de dados
    conn = connect_to_postgres()
    cur = conn.cursor()
    
    current_date = datetime.today()
    current_year = current_date.year
    current_month = current_date.month
    current_day = current_date.day
    
    try:
        # Inserir dados no banco de dados
        cur.execute("""
            INSERT INTO fiap_lab3.weather_data (city, year, month, day, temperature_mean, temperature_max, temperature_min, rain)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """, (city, current_year, current_month, current_day, temperature, temperature_max, temperature_min, rain))

        conn.commit()
        print(f"Current data for {city} inserted into database.")

    except psycopg2.IntegrityError as e:
        # Se ocorrer um erro de violação de constraint (duplicação de dados), ignorar e continuar
        print(f"Data for {city} on {current_year}-{current_month}-{current_day} already exists. Skipping insertion.")

        # Faz o commit da transação para garantir que a conexão seja mantida aberta
        conn.commit()

    finally:
        # Fechar a conexão
        cur.close()
        conn.close()

# Função para treinar o modelo Prophet
def train_prophet_model(city, **kwargs):
    # Recuperar os dados históricos do XCom
    historical_data_json = kwargs['ti'].xcom_pull(key=f'historical_data_{city}')

    # Carregar os dados históricos do JSON para DataFrame
    historical_data = pd.read_json(historical_data_json)
    print(historical_data.head()) 

    # Usar a temperatura média histórica (preencher na coluna 'y') e a data no formato que o Prophet usa
    historical_data['ds'] = historical_data['date']  # A coluna 'ds' é necessária para o Prophet
    historical_data['y'] = historical_data['rain']  # A variável alvo é a precipitação (rain)

    # Adicionando as variáveis explicativas (regressores)
    historical_data['temp_min'] = historical_data['temperature_min']
    historical_data['temp_max'] = historical_data['temperature_max']
    historical_data['temp_mean'] = historical_data['temperature_mean']

    # Instanciar o modelo Prophet
    model = Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=True, seasonality_prior_scale=10.0, changepoint_prior_scale=0.05)

    # Adicionar as variáveis explicativas (regressores)
    model.add_regressor('temp_min')
    model.add_regressor('temp_max')
    model.add_regressor('temp_mean')

    # Treinar o modelo com os dados históricos
    model.fit(historical_data[['ds', 'y', 'temp_min', 'temp_max', 'temp_mean']])

    # Criar um DataFrame para a previsão para os próximos 7 dias
    future = model.make_future_dataframe(periods=7)

    # Adicionar as variáveis explicativas para o futuro
    # Preencher as variáveis de temperatura para os próximos 7 dias com a média histórica
    future['temp_min'] = historical_data['temp_min'].mean()  # Preenchendo com a média histórica
    future['temp_max'] = historical_data['temp_max'].mean()  # Preenchendo com a média histórica
    future['temp_mean'] = historical_data['temp_mean'].mean()  # Preenchendo com a média histórica

    # Filtrar o DataFrame 'future' para obter apenas os 7 dias de previsão
    future = future.tail(7)

    # Fazer a previsão com o modelo Prophet
    forecast = model.predict(future)

    # Exibir as previsões a partir da data de hoje
    current_date = datetime.today()
    print(f"Forecast starting from {current_date}:")
    print(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail())  # Exibindo as previsões

    # Salvar as previsões no banco de dados
    conn = connect_to_postgres()
    cur = conn.cursor()

    for _, row in forecast.iterrows():
        timestamp = row['ds']
        forecast_rain = row['yhat']  # A previsão de precipitação

        # Inserir previsões no banco de dados
        cur.execute("""
            INSERT INTO fiap_lab3.weather_forecast (city, timestamp, forecast_rain)
            VALUES (%s, %s, %s);
        """, (city, timestamp, forecast_rain))

    # Commit e fechamento da conexão
    conn.commit()
    cur.close()
    conn.close()

    print(f"Rain predictions for {city} saved to PostgreSQL.")

# Configuração do DAG
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 3, 30),
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

dag = DAG(
    'weather_forecast_pipeline',
    default_args=default_args,
    description='Pipeline para coletar dados climáticos, treinar o modelo Prophet e salvar previsões no PostgreSQL',
    schedule_interval=timedelta(days=1),  # Roda uma vez por dia
    catchup=False,
)

# Tarefas do DAG
# Coordenadas para as cidades
city_coordinates = {
    'brasilia': {'lat': -15.7934036, 'lon': -47.8823172},
    # 'porto-seguro': {'lat': -16.443473, 'lon': -39.064251}
}

for city, coords in city_coordinates.items():
    collect_current_task = PythonOperator(
        task_id=f'collect_current_data_{city}',
        python_callable=collect_current_data,
        op_args=[city, coords['lat'], coords['lon']],
        provide_context=True,
        dag=dag,
    )

    
    collect_historical_task = PythonOperator(
        task_id=f'collect_historical_data_{city}',
        python_callable=collect_historical_data,
        op_args=[city],
        provide_context=True,
        dag=dag,
    )

    train_model_task = PythonOperator(
        task_id=f'train_prophet_model_{city}',
        python_callable=train_prophet_model,
        op_args=[city],
        provide_context=True,
        dag=dag,
    )

    # Definir a ordem das tarefas
    collect_current_task >> collect_historical_task >> train_model_task

