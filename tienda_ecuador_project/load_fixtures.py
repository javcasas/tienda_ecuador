import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                      'tienda_ecuador_project.settings')

import django
django.setup()

import yaml

to_load = ['tax_rates.yaml', 'formas_pago.yaml', 'plazos_pago.yaml']


def stdout(*args):
    for i in args:
        print i,
    print


def try_load(module, class_):
    """
    Gets the model class from the specified module, named class_
    """
    m = __import__(module)
    m = m.models
    try:
        return getattr(m, class_)
    except AttributeError:
        pass

    return getattr(m, class_.capitalize())


def load_fixture(fn):
    """
    Reads fn (yaml format),
    loads all the objects from it,
    and copies them into the django DB
    """
    res = []
    docs = yaml.load_all(open(fn, "r"))
    for doc in docs:
        for item in doc:
            class_ = item['model']
            params = item['fields']
            pk = item['pk']
            module, class_ = class_.split(".")
            model = try_load(module, class_)
            m = model(pk=pk, **params)
            stdout("    ", type(m), m)
            m.save()
            res.append(m)
    return res


def main():
    for fn in to_load:
        stdout("Loading", fn)
        load_fixture(fn)


if __name__ == '__main__':
    main()
