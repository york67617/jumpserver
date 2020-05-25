#  coding: utf-8
#

from rest_framework.views import Response
from rest_framework.decorators import action

from common.permissions import IsOrgAdmin
from common.const.http import GET
from orgs.mixins.api import OrgModelViewSet
from orgs.mixins import generics
from ..models import RemoteAppPermission
from ..serializers import (
    RemoteAppPermissionSerializer,
    RemoteAppPermissionUpdateUserSerializer,
    RemoteAppPermissionUpdateRemoteAppSerializer,
    PermissionAllUserSerializer,
)


__all__ = [
    'RemoteAppPermissionViewSet',
    'RemoteAppPermissionAddUserApi', 'RemoteAppPermissionAddRemoteAppApi',
    'RemoteAppPermissionRemoveUserApi', 'RemoteAppPermissionRemoveRemoteAppApi',
]


class RemoteAppPermissionViewSet(OrgModelViewSet):
    model = RemoteAppPermission
    filter_fields = ('name', )
    search_fields = filter_fields
    serializer_class = RemoteAppPermissionSerializer
    permission_classes = (IsOrgAdmin,)

    def get_serializer_class(self):
        if self.action == 'all_users':
            return PermissionAllUserSerializer
        else:
            return super().get_serializer_class()

    @action(methods=[GET], detail=True, url_path='users/all')
    def all_users(self):
        obj = self.get_object()
        users = obj.all_users.only(
            *self.get_serializer_class().Meta.only_fields
        )
        return self.action_list(users)


class RemoteAppPermissionAddUserApi(generics.RetrieveUpdateAPIView):
    model = RemoteAppPermission
    permission_classes = (IsOrgAdmin,)
    serializer_class = RemoteAppPermissionUpdateUserSerializer

    def update(self, request, *args, **kwargs):
        perm = self.get_object()
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            users = serializer.validated_data.get('users')
            if users:
                perm.users.add(*tuple(users))
            return Response({"msg": "ok"})
        else:
            return Response({"error": serializer.errors})


class RemoteAppPermissionRemoveUserApi(generics.RetrieveUpdateAPIView):
    model = RemoteAppPermission
    permission_classes = (IsOrgAdmin,)
    serializer_class = RemoteAppPermissionUpdateUserSerializer

    def update(self, request, *args, **kwargs):
        perm = self.get_object()
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            users = serializer.validated_data.get('users')
            if users:
                perm.users.remove(*tuple(users))
            return Response({"msg": "ok"})
        else:
            return Response({"error": serializer.errors})


class RemoteAppPermissionAddRemoteAppApi(generics.RetrieveUpdateAPIView):
    model = RemoteAppPermission
    permission_classes = (IsOrgAdmin,)
    serializer_class = RemoteAppPermissionUpdateRemoteAppSerializer

    def update(self, request, *args, **kwargs):
        perm = self.get_object()
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            remote_apps = serializer.validated_data.get('remote_apps')
            if remote_apps:
                perm.remote_apps.add(*tuple(remote_apps))
            return Response({"msg": "ok"})
        else:
            return Response({"error": serializer.errors})


class RemoteAppPermissionRemoveRemoteAppApi(generics.RetrieveUpdateAPIView):
    model = RemoteAppPermission
    permission_classes = (IsOrgAdmin,)
    serializer_class = RemoteAppPermissionUpdateRemoteAppSerializer

    def update(self, request, *args, **kwargs):
        perm = self.get_object()
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            remote_apps = serializer.validated_data.get('remote_apps')
            if remote_apps:
                perm.remote_apps.remove(*tuple(remote_apps))
            return Response({"msg": "ok"})
        else:
            return Response({"error": serializer.errors})


