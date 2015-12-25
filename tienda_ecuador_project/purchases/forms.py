# -*- coding: utf-8 -*-
import time
from django import forms
from company_accounts import models
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

from util import signature


