
from django.views import generic
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie

from django.http import HttpResponse, HttpResponseBadRequest
from django.conf import settings


class AWSMessage(generic.View):

    def get(self, request, *args, **kwargs):
        import json
        print("HOLA GET")
        #body = json.loads(request.body)
        print("request", request)
        #mode = request.GET.get("hub.mode", False)
        #token = request.GET["token"]
        #print("TOKEN: ", token)
        return HttpResponse("error")

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        print("DISPATCH")
        return generic.View.dispatch(self, request, *args, **kwargs)

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        import json
        import requests
        import time
        print("HOLA POST")
        print(request.body)
        return HttpResponse(request.body)
