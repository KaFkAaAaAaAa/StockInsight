from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from .models import StockData, Transaction
from .forms import LoginForm, RegisterForm, AccountForm

from django.http import JsonResponse
from urllib.parse import urljoin, urlparse
import json
import requests
from bs4 import BeautifulSoup

DISABLE_ARTICLES = True


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
    else:
        form = LoginForm()
    return render(request, 'portfolio/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return render(request, 'portfolio/logout.html')

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

@login_required
def account_edit_view(request):
    if request.method == 'POST':
        form = AccountForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('account_edit')
    else:
        form = AccountForm(instance=request.user)
    return render(request, 'portfolio/account_edit.html', {'form': form})

@login_required
def account_history_view(request):
    transactions = Transaction.objects.filter(user=request.user)
    return render(request, 'portfolio/account_history.html', {'transactions': transactions})

def portfolio_view(request):
    return render(request, 'portfolio/portfolio.html')



@login_required
def market_view(request):
    if request.method == 'POST':
        company = request.POST['company']
        quantity = int(request.POST['quantity'])
        Transaction.objects.create(user=request.user, company=company, quantity=quantity)
        messages.success(request, f'You have successfully bought {quantity} shares of {company}. <a href="{reverse("account_history")}">View History</a>')
    return render(request, 'market.html')

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

    if DISABLE_ARTICLES:
        return []

    query = "t=earnings report"
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
            print(urlparse(i['link']).netloc)
            i['title_image'] = get_website_logo(i['link'])
            if urlparse(i['link']).netloc == "finance.yahoo.com":
                i['title_image'] = "https://upload.wikimedia.org/wikipedia/commons/8/8f/Yahoo%21_Finance_logo_2021.png"
            elif urlparse(i['link']).netloc == "www.globenewswire.com":
                i['title_image'] = "https://www.globenewswire.com/content/logo/color.svg"

            if len(i['content']) > 50:
                i['content'] = i['content'][:250] + "..."

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
