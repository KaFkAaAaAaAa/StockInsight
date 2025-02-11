from django.db import models
import requests
import json
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django import forms


class AccountForm(forms.ModelForm):
    profile_picture = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ['username', 'profile_picture']


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)

    def __str__(self):
        return self.user.username


class StockData(models.Model):
    timestamp = models.DateTimeField()
    price = models.FloatField()

    objects = models.Manager()

    @staticmethod
    def fetch_and_process_data(search, window):
        SERP_API_KEY = '675093b1d4f189f365f7642d8c97aebbc69de8b3d21bac35f6dbab3d8d1be778'
        response = requests.get(f'https://serpapi.com/search.json?engine=google_finance&q={search}&window={window}&api_key={SERP_API_KEY}')
        data = response.json()
        print(data)

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
            date_str = item['date'].replace('-05:00', '')
            timestamp = datetime.strptime(date_str, '%b %d %Y, %I:%M %p %Z')
            rounded_timestamp = timestamp.replace(minute=0, second=0, microsecond=0)
            if timestamp.minute >= 30:
                rounded_timestamp += timedelta(hours=1)
            if last_timestamp is None or rounded_timestamp >= last_timestamp + time_delta:
                filtered_stock_data.append({'timestamp': rounded_timestamp.isoformat(), 'price': item['price']})
                last_timestamp = rounded_timestamp
        print(json.dumps(filtered_stock_data))
        return json.dumps(filtered_stock_data)

    @staticmethod
    def get_available_windows():
        return ['1d', '5d', '1m', '6m', '1y', '5y']

    @staticmethod
    def get_currencies():
        return ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "NZD", "BTC", "ETH", "XRP", "BCH", "ADA", "DOT", "BNB", "USDT"]

    @staticmethod
    def get_available_stocks():
        return ['AAPL', 'GOOGL', 'AMZN', 'MSFT', 'TSLA', 'FB', 'NVDA', 'PYPL', 'ADBE', 'INTC']

class Article(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()

    objects = models.Manager()


class Currency(models.Model):
    name = models.CharField(max_length=50)
    value = models.FloatField()

    objects = models.Manager()


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts', null=True, blank=True)
    title = models.CharField(max_length=255)
    related_tickers = models.CharField(max_length=25)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments', null=True, blank=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment on {self.post.title}'

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} bought {self.quantity} shares of {self.company}"

