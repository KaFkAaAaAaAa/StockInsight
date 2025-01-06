from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
import json
from django.contrib.auth.decorators import login_required
from .models import StockData
from django.http import JsonResponse


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('portfolio')
    else:
        form = AuthenticationForm()

    return render(request, 'portfolio/login.html', {'form': form})


def portfolio_view(request):
    return render(request, 'portfolio/portfolio.html')


@login_required
def dashboard_view(request, window="1d"):
    search = "EUR-USD"
    stock_data = StockData.fetch_and_process_data(search, window)
    stock_data_json = json.dumps(stock_data) if stock_data else '[]'
    available_windows = StockData.get_available_windows()

    return render(request, 'dashboard.html', {
        'search': search,
        'window': window,
        'stock_data': stock_data,
        'stock_data_json': stock_data_json,
        'available_windows': available_windows
    })


@login_required
def currency_view(request, search, window="1d"):
    stock_data = StockData.fetch_and_process_data(search, window)
    stock_data_json = json.dumps(stock_data) if stock_data else '[]'
    available_windows = StockData.get_available_windows()

    return render(request, 'currencies/currency.html', {
        'search': search,
        'window': window,
        'stock_data': stock_data,
        'stock_data_json': stock_data_json,
        'available_windows': available_windows
    })


@login_required
def chart_view(request, search, window):
    stock_data = StockData.fetch_and_process_data(search, window)
    stock_data_json = json.dumps(stock_data) if stock_data else '[]'

    # Detect currency symbol
    currency_symbol = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥",
        "AUD": "A$",
        "CAD": "C$",
        "CHF": "CHF",
        "CNY": "¥",
        "NZD": "NZ$",
        "BTC": "₿",
        "ETH": "Ξ",
        "XRP": "XRP",
        "BCH": "BCH",
        "ADA": "₳",
        "DOT": "DOT",
        "BNB": "BNB",
        "USDT": "₮"
    }.get(search.split('-')[1], "")

    # Currency full names
    currency_names = {
        "USD": "US Dollar",
        "EUR": "Euro",
        "GBP": "British Pound",
        "JPY": "Japanese Yen",
        "AUD": "Australian Dollar",
        "CAD": "Canadian Dollar",
        "CHF": "Swiss Franc",
        "CNY": "Chinese Yuan",
        "NZD": "New Zealand Dollar",
        "BTC": "Bitcoin",
        "ETH": "Ethereum",
        "LTC": "Litecoin",
        "XRP": "Ripple",
        "BCH": "Bitcoin Cash",
        "ADA": "Cardano",
        "DOT": "Polkadot",
        "BNB": "Binance Coin",
        "USDT": "Tether"
    }

    # Generate chart label
    currencies = search.split('-')
    if len(currencies) == 2:
        from_currency = currency_names.get(currencies[0], currencies[0])
        to_currency = currency_names.get(currencies[1], currencies[1])
        chart_label = f'{from_currency} to {to_currency}'
    else:
        chart_label = f'Trending {search}'

    return render(request, 'chart.html', {
        'stock_data': stock_data_json,
        'chart_label': chart_label,
        'currency_symbol': currency_symbol
    })