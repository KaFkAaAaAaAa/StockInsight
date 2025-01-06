from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


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


@login_required
def portfolio_view(request):
    return render(request, 'portfolio/portfolio.html')
