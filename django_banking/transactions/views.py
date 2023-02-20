from dateutil.relativedelta import relativedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView
from accounts.models import User
from decimal import Decimal
from django.http import HttpResponseRedirect

from .constants import DEPOSIT, WITHDRAWAL, TRANSFER
from .forms import (
    DepositForm,
    TransferForm,
    TransactionDateRangeForm,
    WithdrawForm,
)
from .models import Transaction


# class for transaction_report page
class TransactionRepostView(LoginRequiredMixin, ListView):
    template_name = 'transactions/transaction_report.html'
    model = Transaction
    form_data = {}

    def get(self, request, *args, **kwargs):
        form = TransactionDateRangeForm(request.GET or None)
        if form.is_valid():
            self.form_data = form.cleaned_data

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            account=self.request.user.account
        )

        daterange = self.form_data.get("daterange")

        if daterange:
            queryset = queryset.filter(timestamp__date__range=daterange)

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'account': self.request.user.account,
            'form': TransactionDateRangeForm(self.request.GET or None)
        })

        return context


class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    template_name = 'transactions/transaction_form.html'
    model = Transaction
    title = ''
    success_url = reverse_lazy('transactions:transaction_report')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'account': self.request.user.account
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': self.title
        })

        return context


# class for deposit page
class DepositMoneyView(TransactionCreateMixin):
    form_class = DepositForm
    title = 'Deposit Money'

    def get_initial(self):
        initial = {'transaction_type': DEPOSIT}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account

        if not account.initial_deposit_date:
            now = timezone.now()
            next_interest_month = int(
                12 / account.account_type.interest_calculation_per_year
            )
            account.initial_deposit_date = now
            account.interest_start_date = (
                now + relativedelta(
                    months=+next_interest_month
                )
            )

        # update account_balance after deposit
        account.balance += amount
        account.save(
            update_fields=[
                'initial_deposit_date',
                'balance',
                'interest_start_date'
            ]
        )

        # throw success message
        messages.success(
            self.request,
            f'{"{:,.2f}".format(float(amount))}$ was deposited to your account successfully'
        )

        return super().form_valid(form)


# class for withdraw page
class WithdrawMoneyView(TransactionCreateMixin):
    form_class = WithdrawForm
    title = 'Withdraw Money'

    def get_initial(self):
        initial = {'transaction_type': WITHDRAWAL}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')

        # update account_balance after withdrawal
        self.request.user.account.balance -= form.cleaned_data.get('amount')
        self.request.user.account.save(update_fields=['balance'])

        # throw success message
        messages.success(
            self.request,
            f'Successfully withdrawn {"{:,.2f}".format(float(amount))}$ from your account'
        )

        return super().form_valid(form)


# class for transfer page
class TransferMoneyView(TransactionCreateMixin):
    form_class = TransferForm
    template_name = 'transactions/transaction_transfer.html'
    title = 'Transfer Money'

    def get_initial(self):
        initial = {'transaction_type': TRANSFER}
        return initial

    def post(self, request, *args, **kwargs):
        accNum = -1
        amount = 0
        # get target account number and transfer amount
        if request.method == 'POST':
            accNum = request.POST['accNum']
            amount = Decimal(request.POST['amount'])

        tmpUsers = User.objects.filter(is_staff=False)
        target = None

        # search for the target account in the database
        for i in tmpUsers:
            account_num = i.account.account_no

            # if account is found, update the user account balance and target account balance
            if account_num == int(accNum):
                self.request.user.account.balance -= amount
                self.request.user.account.save(update_fields=['balance'])
                i.account.balance += amount
                i.account.save(update_fields=['balance'])

        # throw success message
        messages.success(
            self.request,
            f'Successfully transfer {"{:,.2f}".format(amount)}$ from your account to target account :{accNum}'
        )

        return HttpResponseRedirect(self.request.path_info)

    def form_valid(self, form):
        return super().form_valid(form)

