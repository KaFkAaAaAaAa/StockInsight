from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import StockData
from .forms import RegisterForm
from django.http import JsonResponse

from urllib.parse import urljoin
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


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

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            profile_picture = form.cleaned_data.get('profile_picture')
            if profile_picture:
                user.profile.profile_picture = profile_picture
                user.profile.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'portfolio/register.html', {'form': form})


def portfolio_view(request):
    return render(request, 'portfolio/portfolio.html')


@login_required
def dashboard_view(request, window="1d"):
    search = "EUR-USD"
    stock_data = StockData.fetch_and_process_data(search, window)
    stock_data_json = json.dumps(stock_data) if stock_data else '[]'
    available_windows = StockData.get_available_windows()
    available_currencies = StockData.get_currencies()
    currencies = search.split('-')
    context = {
        'search': search,
        'window': window,
        'stock_data': stock_data,
        'stock_data_json': stock_data_json,
        'available_currencies': available_currencies,
        'available_windows': available_windows,
        'from_currency': currencies[0],
        'to_currency': currencies[1],
        # ARTICLES
        'articles': fetch_articles(),
    }
    return render(request, 'dashboard.html', context)


@login_required
def currency_view(request, search, window="1d"):
    stock_data = StockData.fetch_and_process_data(search, window)
    stock_data_json = json.dumps(stock_data) if stock_data else '[]'
    available_windows = StockData.get_available_windows()
    available_currencies = StockData.get_currencies()
    currencies = search.split('-')
    context = {
        'search': search,
        'window': window,
        'stock_data': stock_data,
        'stock_data_json': stock_data_json,
        'available_currencies': available_currencies,
        'available_windows': available_windows,
        'from_currency': currencies[0],
        'to_currency': currencies[1],
        # ARTICLES
        'articles': fetch_articles(search),
    }
    return render(request, 'currencies/currency.html', context)


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

# --------------------------------------------
# --------------- FUNCTIONS ------------------
# --------------------------------------------


def fetch_articles(stocks=None):

    query = "t=financial results"
    if stocks is not None:
        query = f"s={stocks.split("-")[0]}"

    api_url = (f"https://eodhd.com/api/news"
               f"?{query}"
               "&offset=0"
               "&limit=5"
               "&api_token=677d6de70b8ae8.08841936"
               "&fmt=json")

    print(api_url)
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        response_json = response.json()

        for i in response_json:
            i['title_image'] = get_website_logo(i['link'])
            print()
            if urlparse(i['link']).netloc == "finance.yahoo.com":
                i['title_image'] = "https://upload.wikimedia.org/wikipedia/commons/8/8f/Yahoo%21_Finance_logo_2021.png"

        return response_json
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return []


def get_website_logo(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        html_content = response.text

        soup = BeautifulSoup(html_content, 'html.parser')

        icon_link = soup.find("link", rel=lambda x: x and 'icon' in x.lower())
        if icon_link and 'href' in icon_link.attrs:
            logo_url = urljoin(url, icon_link['href'])
            return logo_url

        meta_logo = soup.find("meta", property="og:image")
        if meta_logo and 'content' in meta_logo.attrs:
            logo_url = urljoin(url, meta_logo['content'])
            return logo_url

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the website: {e}")
        return None

    return None
