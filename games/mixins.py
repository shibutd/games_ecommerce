from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect, resolve_url


class LoggedOpenCartExistsMixin(AccessMixin):
    """
    Deny access to unauthenticated user and user without OPEN cart.
    """
    permission_denied_message = 'Your cart is empty.'

    def handle_no_permission(self):
        messages.warning(self.request, self.permission_denied_message)
        return redirect('games:home')

    def dispatch(self, request, *args, **kwargs):
        # This will redirect to the login view
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(),
                                     resolve_url(self.get_login_url()),
                                     self.get_redirect_field_name())
        if not request.cart:
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)


class IsStaffMixin(AccessMixin):
    """
    Deny access if user is not authenticated or not staff.
    """

    def handle_no_permission(self):
        return redirect('games:home')

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated or not user.is_staff:
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)
