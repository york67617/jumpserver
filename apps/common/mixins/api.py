# -*- coding: utf-8 -*-
#
import time
from hashlib import md5
from threading import Thread

from django.core.cache import cache
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.settings import api_settings

from common.drf.filters import IDSpmFilter, CustomFilter, IDInFilter
from ..utils import lazyproperty

__all__ = [
    "JSONResponseMixin", "CommonApiMixin",
    'AsyncApiMixin',
]


class JSONResponseMixin(object):
    """JSON mixin"""
    @staticmethod
    def render_json_response(context):
        return JsonResponse(context)


class SerializerMixin:
    def get_serializer_class(self):
        serializer_class = None
        if hasattr(self, 'serializer_classes') and isinstance(self.serializer_classes, dict):
            if self.action in ['list', 'metadata'] and self.request.query_params.get('draw'):
                serializer_class = self.serializer_classes.get('display')
            if serializer_class is None:
                serializer_class = self.serializer_classes.get(
                    self.action, self.serializer_classes.get('default')
                )
        print(serializer_class)
        if serializer_class:
            return serializer_class
        return super().get_serializer_class()


class ExtraFilterFieldsMixin:
    """
    额外的 api filter
    """
    default_added_filters = [CustomFilter, IDSpmFilter, IDInFilter]
    filter_backends = api_settings.DEFAULT_FILTER_BACKENDS
    extra_filter_fields = []
    extra_filter_backends = []

    def get_filter_backends(self):
        if self.filter_backends != self.__class__.filter_backends:
            return self.filter_backends
        backends = list(self.filter_backends) + \
                   list(self.default_added_filters) + \
                   list(self.extra_filter_backends)
        return backends

    def filter_queryset(self, queryset):
        for backend in self.get_filter_backends():
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset


class CommonApiMixin(SerializerMixin, ExtraFilterFieldsMixin):
    def action_list(self, queryset):
        queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class InterceptMixin:
    """
    Hack默认的dispatch, 让用户可以实现 self.do
    """
    def dispatch(self, request, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        request = self.initialize_request(request, *args, **kwargs)
        self.request = request
        self.headers = self.default_response_headers  # deprecate?

        try:
            self.initial(request, *args, **kwargs)

            # Get the appropriate handler method
            if request.method.lower() in self.http_method_names:
                handler = getattr(self, request.method.lower(),
                                  self.http_method_not_allowed)
            else:
                handler = self.http_method_not_allowed

            response = self.do(handler, request, *args, **kwargs)

        except Exception as exc:
            response = self.handle_exception(exc)

        self.response = self.finalize_response(request, response, *args, **kwargs)
        return self.response


class AsyncApiMixin(InterceptMixin):
    def get_request_user_id(self):
        user = self.request.user
        if hasattr(user, 'id'):
            return str(user.id)
        return ''

    @lazyproperty
    def async_cache_key(self):
        method = self.request.method
        path = self.get_request_md5()
        user = self.get_request_user_id()
        key = '{}_{}_{}'.format(method, path, user)
        return key

    def get_request_md5(self):
        path = self.request.path
        query = {k: v for k, v in self.request.GET.items()}
        query.pop("_", None)
        query.pop('refresh', None)
        query = "&".join(["{}={}".format(k, v) for k, v in query.items()])
        full_path = "{}?{}".format(path, query)
        return md5(full_path.encode()).hexdigest()

    @lazyproperty
    def initial_data(self):
        data = {
            "status": "running",
            "start_time": time.time(),
            "key": self.async_cache_key,
        }
        return data

    def get_cache_data(self):
        key = self.async_cache_key
        if self.is_need_refresh():
            cache.delete(key)
            return None
        data = cache.get(key)
        return data

    def do(self, handler, *args, **kwargs):
        if not self.is_need_async():
            return handler(*args, **kwargs)
        resp = self.do_async(handler, *args, **kwargs)
        return resp

    def is_need_refresh(self):
        if self.request.GET.get("refresh"):
            return True
        return False

    def is_need_async(self):
        return False

    def do_async(self, handler, *args, **kwargs):
        data = self.get_cache_data()
        if not data:
            t = Thread(
                target=self.do_in_thread,
                args=(handler, *args),
                kwargs=kwargs
            )
            t.start()
            resp = Response(self.initial_data)
            return resp
        status = data.get("status")
        resp = data.get("resp")
        if status == "ok" and resp:
            resp = Response(**resp)
        else:
            resp = Response(data)
        return resp

    def do_in_thread(self, handler, *args, **kwargs):
        key = self.async_cache_key
        data = self.initial_data
        cache.set(key, data, 600)
        try:
            response = handler(*args, **kwargs)
            data["status"] = "ok"
            data["resp"] = {
                "data": response.data,
                "status": response.status_code
            }
            cache.set(key, data, 600)
        except Exception as e:
            data["error"] = str(e)
            data["status"] = "error"
            cache.set(key, data, 600)
