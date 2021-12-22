from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from stock.models import Stock, AccountCurrency, AccountStock
from stock.forms import BuySellForm
from django.core.cache import cache

def stock_list(request):
    stocks = Stock.objects.all()
    context= {
        'stocks': stocks,
    }
    return render(request, 'stocks.html', context)
    
@login_required   
def stock_detail(request, pk):
    stock = get_object_or_404(Stock, pk=pk)
    acc_stock, created = AccountStock.objects.get_or_create(account=request.user.account, stock=stock,
                                                                defaults={'average_buy_cost': 0, 'amount': 0})
    
    random_price = stock.get_random_price()
    amount = 0
    if acc_stock is not None:
        amount = acc_stock.amount
    context = {
        'stock': stock,
        'amount': amount,
        'buyForm': BuySellForm(initial={'price': random_price}),
        'sellForm': BuySellForm(initial={'price': random_price}),
        'currencies': updateCurrenciesCache(request)
    }
    return render(request, 'stock.html', context)
@login_required   
def stock_buy(request, pk):
    if request.method != "POST":
        return redirect('stock:detail', pk=pk)

    stock = get_object_or_404(Stock, pk=pk)
    form = BuySellForm(request.POST)

    if form.is_valid():
        amount = form.cleaned_data['amount']
        price = form.cleaned_data['price']
        buy_cost = price * amount

        acc_stock, created = AccountStock.objects.get_or_create(account=request.user.account, stock=stock,
                                                                defaults={'average_buy_cost': 0, 'amount': 0})
        current_cost = acc_stock.average_buy_cost * acc_stock.amount

        total_cost = current_cost + buy_cost
        total_amount = acc_stock.amount + amount


        acc_currency, created = AccountCurrency.objects.get_or_create(account=request.user.account, currency=stock.currency,
                                                                      defaults={'amount': 0})

        if acc_currency.amount < buy_cost:
            form.add_error(None, f'На счёте недостаточно средств в валюте {stock.currency.sign}')
        else:
            acc_stock.amount = total_amount
            acc_stock.average_buy_cost = total_cost / total_amount
            acc_currency.amount = acc_currency.amount - buy_cost
            acc_stock.save()
            acc_currency.save()
            updateCurrenciesCache(request)
            updateStocksCache(request)
            return redirect('stock:list')

    context = {
        'stock': get_object_or_404(Stock, pk=pk),
        'buyForm': form,
        'sellForm': BuySellForm(initial={'price': price})
    }

    return render(request, 'stock.html', context)
@login_required   
def stock_sell(request, pk):
    if request.method != "POST":
        return redirect('stock:detail', pk=pk)

    stock = get_object_or_404(Stock, pk=pk)
    form = BuySellForm(request.POST)

    if form.is_valid():
        amount = form.cleaned_data['amount']
        price = form.cleaned_data['price']
        sell_cost = price * amount

        acc_stock, created = AccountStock.objects.get_or_create(account=request.user.account, stock=stock,
                                                                defaults={'average_buy_cost': 0, 'amount': 0})
        
        current_cost = acc_stock.average_buy_cost * acc_stock.amount


        acc_currency, created = AccountCurrency.objects.get_or_create(account=request.user.account, currency=stock.currency,
                                                                      defaults={'amount': 0})

        if acc_stock.amount < amount:
            form.add_error(None, f'На аккаунте недостаточно акций {acc_stock.stock.name}')
        else:
            acc_stock.amount = acc_stock.amount - amount
            acc_currency.amount = acc_currency.amount + sell_cost
            acc_stock.save()
            acc_currency.save()
            updateCurrenciesCache(request)
            updateStocksCache(request)
            return redirect('stock:list')

    context = {
        'stock': get_object_or_404(Stock, pk=pk),
        'sellForm': form,
        'buyForm': BuySellForm(initial={'price': price})
    }

    return render(request, 'stock.html', context)

@login_required
def updateCurrenciesCache(request):
    currencies = [
        {
            'amount': acc_currency.amount,
            'sign': acc_currency.currency.sign
        } for acc_currency in request.user.account.accountcurrency_set.select_related('currency')
    ]
    cache.set(f'currencies_{request.user.username}', currencies, 300)
    return currencies

@login_required
def updateStocksCache(request):
    stocks = [
        {
            'ticker': acc_stock.stock.ticker,
            'amount': acc_stock.amount,
            'avg': acc_stock.average_buy_cost
        } for acc_stock in request.user.account.accountstock_set.select_related('stock').all()
    ]
    cache.set(f'stocks_{request.user.username}', stocks, 300)
    return stocks
    
@login_required
def account(request):
    currencies = cache.get(f'currencies{request.user.username}')
    stocks = cache.get(f'stocks_{request.user.username}')
    if currencies is None:
        currencies = updateCurrenciesCache(request)

    if stocks is None:
        stocks = updateStocksCache(request)
    context = {
        'currencies': currencies,
        'stocks': stocks
    }

    return render(request, template_name='account.html', context=context)
