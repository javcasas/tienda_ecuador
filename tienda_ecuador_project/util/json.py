import json
from decimal import Decimal

from django.http import JsonResponse, HttpResponse


class ListJSONResponseMixin(object):
    """
    A mixin that can be used to render a JSON response.
    """
    # List of fields in the model
    # Can be either 'field'
    fields_to_return = None

    def render_to_json_response(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """
        return JsonResponse(
            self.get_data(context),
            safe=False,
            **response_kwargs
        )

    def render_to_response(self, context, **response_kwargs):
        return self.render_to_json_response(context, **response_kwargs)

    def get_data(self, context):
        """
        Returns an object that will be serialized as JSON by json.dumps().
        """
        items = self.get_queryset()

        def model_to_dict(item, fields=self.fields_to_return):
            fields = sorted(fields)
            res = {}
            for key in self.fields_to_return:
                field_val = getattr(item, key)
                if isinstance(field_val, Decimal):
                    field_val = float(field_val)
                res[key] = field_val
            return res
        return map(model_to_dict, items)


class mydict(dict):
    def __getitem__(self, name):
        if name in self:
            return super(mydict, self).__getitem__(name)
        else:
            ob = mydict()
            self[name] = ob
            return ob


def success(msg):
    return HttpResponse(
        json.dumps({
            'success': True,
            'msg': msg
        }))


def failure(msg):
    return HttpResponse(
        json.dumps({
            'success': False,
            'msg': msg
        }))


def not_yet(msg):
    return HttpResponse(
        json.dumps({
            'success': False,
            'msg': msg
        }))
