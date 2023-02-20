from django.contrib.auth import get_user_model, login, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import HttpResponseRedirect
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, RedirectView
from accounts.models import OTP
import math, random

from .forms import UserRegistrationForm, UserAddressForm

User = get_user_model()

class UserRegistrationView(TemplateView):
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/user_registration.html'

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return HttpResponseRedirect(
                reverse_lazy('transactions:transaction_report')
            )
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # create user registration form and address form with the data from request.POST
        registration_form = UserRegistrationForm(self.request.POST)
        address_form = UserAddressForm(self.request.POST)

        # if both forms are valid, save the forms and login
        if registration_form.is_valid() and address_form.is_valid():
            user = registration_form.save()
            address = address_form.save(commit=False)
            address.user = user
            address.save()

            login(self.request, user)
            messages.success(
                self.request,
                (
                    f'Thank You For Creating A Bank Account. '
                    f'Your Account Number is {user.account.account_no}. '
                )
            )
            return HttpResponseRedirect(
                reverse_lazy('transactions:deposit_money')
            )

        return self.render_to_response(
            self.get_context_data(
                registration_form=registration_form,
                address_form=address_form
            )
        )

    def get_context_data(self, **kwargs):
        if 'registration_form' not in kwargs:
            kwargs['registration_form'] = UserRegistrationForm()
        if 'address_form' not in kwargs:
            kwargs['address_form'] = UserAddressForm()

        return super().get_context_data(**kwargs)

class UserLoginView(LoginView):
    template_name = 'accounts/user_login.html'
    redirect_authenticated_user = False

class ProfileDisplayView(TemplateView):
    template_name = 'accounts/profile.html'

    def get(self, request, *args, **kwargs):

        # obtain user's information from the database
        email = request.user.email
        gender = request.user.account.gender
        account_no = request.user.account.account_no
        birth_date = request.user.account.birth_date
        balance = request.user.account.balance
        address = request.user.address.street_address + ', ' + request.user.address.city + ', ' + request.user.address.country

        # create a dictionary to keep user's information
        dict = {"email": email,
                "gender": gender,
                "account_no": account_no,
                "birth_date": birth_date,
                "balance": balance,
                "address": address,
                }

        return render(request, "accounts/profile.html", context=dict)


class LogoutView(RedirectView):
    pattern_name = 'home'

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            logout(self.request)
        return super().get_redirect_url(*args, **kwargs)


class OTPReceiveView(TemplateView):
    template_name = 'accounts/otp.html'

    def post(self, request, *args, **kwargs):

        # create otp
        if request.method == "POST":
            digits = "0123456789"
            otp = ""
            # generate a 4 digits number
            for i in range(4):
                otp += digits[math.floor(random.random() * 10)]
            print(otp)
            email = request.user.email
            # send the otp to the user's email
            send_mail(
                'OTP',
                'Your OTP is ' + otp,
                'aston.qxq@gmail.com',
                [email],
                fail_silently=False,
            )
            # save otp in database
            if OTP.objects.all().count() < 1:
                tmpOTP = OTP.objects.create()
                tmpOTP.otp = otp
                tmpOTP.save()
            else:
                tmpOTP = OTP.objects.get(id=1)
                tmpOTP.otp = otp
                tmpOTP.save()

            if request.user is not None:
                login(request, request.user)
                return redirect('/accounts/otp_submit_view')

        return render(request, "accounts/otp_submit.html")


class OTPSubmitView(TemplateView):
    template_name = 'accounts/otp_submit.html'

    def post(self, request, *args, **kwargs):
        # get otp entered by user
        otp_entered = request.POST['otp']

        # if the otp entered equals the otp in the database, proceed to profile
        if OTP.objects.get(id=1).otp == otp_entered:
            email = request.user.email
            gender = request.user.account.gender
            account_no = request.user.account.account_no
            birth_date = request.user.account.birth_date
            balance = request.user.account.balance
            address = request.user.address.street_address + ', ' + request.user.address.city + ', ' + request.user.address.country

            dict = {"email": email,
                    "gender": gender,
                    "account_no": account_no,
                    "birth_date": birth_date,
                    "balance": balance,
                    "address": address,
                    }

            return render(request, "accounts/profile.html", context=dict)

        return render(request, "accounts/user_login.html")
