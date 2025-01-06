from django.db import models
import requests
import json
from datetime import datetime, timedelta

class StockData(models.Model):
    timestamp = models.DateTimeField()
    price = models.FloatField()

    objects = models.Manager()

    @staticmethod
    def fetch_and_process_data(search, window):
        SERP_API_KEY = '3e59356712e9917d51d96eb521ace6d4f60291e1fa0b28e1237feb4d7440613c'
        response = requests.get(f'https://serpapi.com/search.json?engine=google_finance&q={search}&window={window}&api_key={SERP_API_KEY}')
        data = response.json()

        stock_data = data.get('graph', [])
        filtered_stock_data = []
        last_timestamp = None

        # Determine the time delta based on the window
        time_delta = {
            '1d': timedelta(minutes=10),
            '5d': timedelta(hours=2),
            '1m': timedelta(days=1),
            '6m': timedelta(weeks=1),
            '1y': timedelta(weeks=2),
            '5y': timedelta(weeks=4)
        }.get(window, timedelta(minutes=10))  # Default to 10 minutes if window is unknown

        for item in stock_data:
            timestamp = datetime.strptime(item['date'], '%b %d %Y, %I:%M %p %Z')
            rounded_timestamp = timestamp.replace(minute=0, second=0, microsecond=0)
            if timestamp.minute >= 30:
                rounded_timestamp += timedelta(hours=1)
            if last_timestamp is None or rounded_timestamp >= last_timestamp + time_delta:
                filtered_stock_data.append({'timestamp': rounded_timestamp.isoformat(), 'price': item['price']})
                last_timestamp = rounded_timestamp

        return json.dumps(filtered_stock_data)

    @staticmethod
    def get_available_windows():
        return ['1d', '5d', '1m', '6m', '1y', '5y']

class Article(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()

    objects = models.Manager()

class Currency(models.Model):
    name = models.CharField(max_length=50)
    value = models.FloatField()

    objects = models.Manager()