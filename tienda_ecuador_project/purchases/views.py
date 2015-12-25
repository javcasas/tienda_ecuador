from datetime import date, timedelta
import pytz
import json

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, FormView
from django.core.urlresolvers import reverse
from django.db.models import Count

import models
import forms
from licence_helpers import LicenceControlMixin, valid_licence, licence_required
from util import signature
from sri.models import AmbienteSRI


tz = pytz.timezone('America/Guayaquil')


