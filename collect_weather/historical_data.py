import os
import requests
import boto3
import json

# Initialize S3 client
s3 = boto3.client('s3')
BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
API_KEY = os.getenv('API_KEY')

def lambda_handler(event, context):
    try:
        # Calling the function for multiple cities
        get_weather_data(lat=-15.7934036, lon=-47.8823172, city='brasilia')
        get_weather_data(lat=-16.443473, lon=-39.064251, city='porto-seguro')
        
        return {
            'statusCode': 200,
            'body': f'Data collected and stored in S3 as JSON'
        }

    except Exception as e:
        # Catch any exception in the main handler
        print(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': f"An error occurred: {str(e)}"
        }

def get_weather_data(lat, lon, city):
    try:
        url = f"https://history.openweathermap.org/data/2.5/history/city?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&type=hour&cnt=8758"
        
        # Request weather data from OpenWeatherMap API
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx, 5xx)
        
        data = response.json()
        
        key = f"raw/historical/{city}/last_year.json"
        
        # Store the collected data in S3 as JSON
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=key,
            Body=json.dumps(data)
        )
        
        print(f"Data for {city} stored successfully in S3.")

    except Exception as e:
        # Catch any other exceptions
        print(f"Unexpected error for {city}: {str(e)}")
        raise  # Re-raise the error to be handled by the calling function
