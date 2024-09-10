import requests
from rest_framework.response import Response


def send_sms_by_2factor(to_, message):
    if to_ and message:
        two_factor_api_key = "7872e1d5-8092-11e6-a584-00163ef91450"

        url = "http://2factor.in/API/V1/%s/ADDON_SERVICES/SEND/TSMS" % two_factor_api_key

        payload = {
            'To': to_,
            'Msg': message,
            'From': 'LYLOIN'
        }
        try:
            response = requests.request("POST", url, data=payload)
            error = False
        except Exception as e:
            error = True
            response = str(e)
    else:
        error = True
        response = "Please provide the value of to_ and message."

    return error, response


def model_field_attr(model, model_field, attr):
    """
    Returns the specified attribute for the specified field on the model class.
    """
    fields = dict([(field.name, field) for field in model._meta.fields])
    return getattr(fields[model_field], attr)
