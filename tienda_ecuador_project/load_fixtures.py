import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                      'tienda_ecuador_project.settings')

import django
django.setup()

import yaml


fn = 'tax_rates.yaml'

docs = yaml.load_all(open(fn, "r"))

def try_load(module, class_):
    m = __import__(module)
    m = m.models
    try:
        return getattr(m, class_)
    except AttributeError:
        pass

    return getattr(m, class_.capitalize())


for doc in docs:
    for item in doc:
        class_ = item['model']
        params = item['fields']
        pk = item['pk']
        module, class_ = class_.split(".")
        model = try_load(module, class_)
        m = model(pk=pk, **params)
        print m
        m.save()

        #print module, class_, params, pk
