from django.shortcuts import get_object_or_404, redirect

import models


def valid_licence(user, valid_licences):
    """
    Returns True iif the company from the user has
    a licence in valid_licences
    """
    cu = get_object_or_404(models.CompanyUser, user=user)
    return cu.company.licence.effective_licence in valid_licences


class licence_required(object):
    """
    Decorator that checks the licence and redirects
    to pricing
    """
    def __init__(self, *args):
        self.licences = args

    def __call__(self, f):
        orig_dispatch = f.dispatch

        def wrapper(otherself, request, *args, **kwargs):
            if not valid_licence(request.user, self.licences):
                return redirect("pricing")
            return orig_dispatch(otherself, request, *args, **kwargs)
        f.dispatch = wrapper
        return f


class LicenceControlMixin(object):
    """
    Mixin that provides the valid_licence method
    """
    licence_required = None
    def valid_licence(self, valid_licences):
        return valid_licence(self.user, valid_licences)

    def get_context_data(self, **kwargs):
        context = super(LicenceControlMixin, self).get_context_data(**kwargs)
        cu = get_object_or_404(models.CompanyUser, user=self.request.user, company=self.company)
        effective_licence = cu.company.licence.effective_licence
        licence_data = {
            'demo': effective_licence == "demo",
            'basic': effective_licence in ['basic', 'professional', 'enterprise'],
            'professional': effective_licence in ['professional', 'enterprise'],
            'enterprise': effective_licence in ['enterprise'],
        }
        context['licence'] = licence_data
        context['valid_licence'] = licence_data.get(self.licence_required, False)
        return context
