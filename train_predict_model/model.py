import os
import pandas as pd
from prophet import Prophet
import boto3
import json
from datetime import datetime
from io import BytesIO

# Initialize S3 client
s3 = boto3.client('s3')
BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

def lambda_handler(event, context):
    # Define city
    city = 'brasilia'
    prefix = f'raw/{city}/'

    try:
        # Step 1: Load historical weather data from S3
        weather_data = load_weather_data_from_s3(prefix)

        if not weather_data:
            raise ValueError(f"No valid data found for {city} in S3.")

        # Step 2: Train Prophet model on the collected data
        df = pd.DataFrame(weather_data)
        model = Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=True)
        model.fit(df)

        # Step 3: Generate future predictions (next 48 hours)
        future = model.make_future_dataframe(periods=48, freq='H')
        forecast = model.predict(future)

        # Step 4: Save predictions to S3
        save_predictions_to_s3(forecast, city)

        return {
            'statusCode': 200,
            'body': f'Model trained and predictions saved for {city} in S3'
        }
    
    except Exception as e:
        # Log error in case of failure
        print(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': f"Error occurred: {str(e)}"
        }

def load_weather_data_from_s3(prefix):
    """
    Load weather data for the specified city from S3.
    """
    try:
        # List all objects for the given city in S3
        objects = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)['Contents']
        weather_data = []

        # Loop through each file (object) in the S3 bucket
        for obj in objects:
            obj_body = s3.get_object(Bucket=BUCKET_NAME, Key=obj['Key'])['Body'].read()
            data = json.loads(obj_body)
            
            # Extract relevant data
            weather_data.append({
                'ds': datetime.fromtimestamp(data['dt']),
                'y': data['main']['temp']
            })
        
        return weather_data
    
    except Exception as e:
        print(f"Error loading data from S3: {str(e)}")
        return []

def save_predictions_to_s3(forecast, city):
    """
    Save the forecast predictions to S3 in CSV format.
    """
    try:
        # Convert forecast DataFrame to CSV format
        predictions_key = f'predictions/{city}/forecast.csv'
        buffer = BytesIO()
        forecast.to_csv(buffer, index=False)
        buffer.seek(0)

        # Upload the CSV predictions file to S3
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=predictions_key,
            Body=buffer.getvalue()
        )
        
        print(f"Predictions for {city} saved successfully in S3.")

    except Exception as e:
        print(f"Error saving predictions to S3: {str(e)}")
        raise
