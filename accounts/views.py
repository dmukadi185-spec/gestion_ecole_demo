from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View

from .forms import ActivateAccountForm, SignInForm


def _get_redirect_for_user(user):
    """Return the appropriate home URL based on user role."""
    if user.is_staff:
        return "admin_panel:index"
    try:
        _ = user.directeur
        return "direction:index"
    except Exception:
        pass
    return "dashboard:index"


def home(request):
    if request.user.is_authenticated:
        return redirect(_get_redirect_for_user(request.user))

    form = SignInForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect(_get_redirect_for_user(user))

    return render(request, "home.html", {"form": form})


class SignInView(LoginView):
    template_name = "accounts/signin.html"
    authentication_form = SignInForm
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if user.is_staff:
            return reverse_lazy("admin_panel:index")
        try:
            _ = user.directeur
            return reverse_lazy("direction:index")
        except Exception:
            pass
        return reverse_lazy("dashboard:index")


def activate_account(request):
    if request.user.is_authenticated:
        return redirect(_get_redirect_for_user(request.user))

    form = ActivateAccountForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(
            request,
            "Votre mot de passe a été créé. Bienvenue sur votre espace élève.",
        )
        return redirect("dashboard:index")
    return render(request, "accounts/activate_account.html", {"form": form})


class SignOutView(View):
    def post(self, request):
        logout(request)
        return redirect("home")

    def get(self, request):
        logout(request)
        return redirect("home")
