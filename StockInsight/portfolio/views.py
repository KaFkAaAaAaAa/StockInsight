from django.contrib.auth import login, authenticate, logout
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages

from .models import StockData, Transaction, Post
from .forms import LoginForm, RegisterForm, AccountForm, PostForm, CommentForm

from django.http import JsonResponse
from urllib.parse import urljoin, urlparse
import json
import requests
from bs4 import BeautifulSoup
import ast
from datetime import datetime, timedelta

DISABLE_ARTICLES = False


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
def market_view(request, selected_stock="NVDA", window="1d"):
    search = selected_stock
    if "%3ANASDAQ" not in search or ":NASDAQ" not in search:
        search += "%3ANASDAQ"
    available_stocks = StockData.get_available_stocks()
    available_windows = StockData.get_available_windows()
    stock_data = StockData.fetch_and_process_data(search, window)

    if request.method == 'POST':
        try:
            quantity = int(request.POST['quantity'])
            Transaction.objects.create(user=request.user, company=selected_stock, quantity=quantity)
            messages.success(request, f'You have successfully bought {quantity} shares of {selected_stock}. <a href="{reverse("account_history")}">View History</a>')
        except (ValueError, KeyError):
            messages.error(request, 'Invalid quantity. Please enter a valid number.')

    # POSTS
    posts = Post.objects.filter(related_tickers__contains=selected_stock).order_by('-created_at')
    for post in posts:
        post.related_tickers = ast.literal_eval(post.related_tickers)

    # ----

    context = {
        'search': search,
        'available_stocks': available_stocks,
        'available_windows': available_windows,
        'selected_stock': selected_stock,
        'selected_window': window,
        'stock_data': stock_data,
        # ARTICLES
        'articles': fetch_articles(selected_stock),
        # POSTS
        'posts': posts,
    }
    return render(request, 'market.html', context)

@login_required
def dashboard_view(request, window="1d"):
    search = "EUR-USD"
    stock_data = StockData.fetch_and_process_data(search, window)
    stock_data_json = json.dumps(stock_data) if stock_data else '[]'
    available_windows = StockData.get_available_windows()
    available_currencies = StockData.get_currencies()
    currencies = search.split('-')

    # POSTS
    posts = Post.objects.all().order_by('-created_at')
    for post in posts:
        post.related_tickers = ast.literal_eval(post.related_tickers)

    # ----

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
        # POSTS
        'posts': posts,
    }
    return render(request, 'dashboard.html', context)


@login_required
def currency_view(request, search, window="1d"):
    stock_data = StockData.fetch_and_process_data(search, window)
    stock_data_json = json.dumps(stock_data) if stock_data else '[]'
    available_windows = StockData.get_available_windows()
    available_currencies = StockData.get_currencies()
    currencies = search.split('-')

    # POSTS
    posts = Post.objects.filter(Q(related_tickers__contains=currencies[0]) |
                                Q(related_tickers__contains=currencies[1])).order_by('-created_at')
    for post in posts:
        post.related_tickers = ast.literal_eval(post.related_tickers)

    # ----

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
        # 'articles': fetch_articles(search),
        # POSTS
        'posts': posts,
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


# FORUM MODULE

@login_required
def post_list(request):
    posts = Post.objects.all().order_by('-created_at')

    ticker_filter = request.GET.get('ticker')
    title_filter = request.GET.get('title')

    if ticker_filter:
        posts = posts.filter(related_tickers__contains=ticker_filter)

    if title_filter:
        posts = posts.filter(title__contains=title_filter)

    for post in posts:
        post.related_tickers = ast.literal_eval(post.related_tickers)

    tickers = StockData.get_currencies() + StockData.get_available_stocks()
    return render(request, 'forum/post_list.html', {
        'posts': posts,
        'tickers': tickers
    })


@login_required
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.related_tickers = ast.literal_eval(post.related_tickers)
    comments = post.comments.all().order_by('-created_at')
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.user = request.user
            comment.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = CommentForm()
    return render(request, 'forum/post_detail.html', {
                                                      'post': post,
                                                      'form': form,
                                                      'comments': comments})


@login_required
def post_new(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect('post_list')
    else:
        form = PostForm()
    return render(request, 'forum/post_form.html', {'form': form})

# --------------------------------------------
# --------------- FUNCTIONS ------------------
# --------------------------------------------


def fetch_articles(stocks=None):
    if DISABLE_ARTICLES:
        return []

    query = ""
    if stocks is not None:
        query = f"{stocks.split('-')[0]}"

    time = datetime.now() - timedelta(hours=24)
    time = str(time)
    time = time.replace(" ", "T")
    time = time.split(".")[0]

    API_KEY = "V3CqrPpcGerzNYDWXVJBAN7yrdkTmcbXImHldrbJ"
    api_url = (f"https://api.marketaux.com/v1/news/all"
               f"?countries=us"
               f"&filter_entities=true"
               f"&symbols={query}"
               f"&limit=3"
               f"&published_after={time}"
               f"&api_token={API_KEY}")

    response = requests.get(api_url)
    response.raise_for_status()
    response_json = response.json()

    articles = response_json['data']

    for article in articles:

        past_date = datetime.strptime(article['published_at'].split('.')[0], '%Y-%m-%dT%H:%M:%S')
        current_date = datetime.now()
        time_difference = current_date - past_date
        hours_passed = round(time_difference.total_seconds() / 3600)

        article['hours_ago'] = hours_passed

    print(api_url)
    return articles


def fetch_articles_deprecated(stocks=None):
    if DISABLE_ARTICLES:
        return []

    query = "t=earnings report"
    if stocks is not None:
        query = f"s={stocks.split('-')[0]}"

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

            if "finance.yahoo.com" in urlparse(i['link']).netloc:
                i['title_image'] = "https://upload.wikimedia.org/wikipedia/commons/8/8f/Yahoo%21_Finance_logo_2021.png"
            elif urlparse(i['link']).netloc == "www.globenewswire.com":
                i['title_image'] = "https://www.globenewswire.com/content/logo/color.svg"
            else:
                i['title_image'] = get_website_logo(i['link'])

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
