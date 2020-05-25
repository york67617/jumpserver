# coding: utf-8
#
from perms.api.base import RelationMixin
from rest_framework import generics
from django.db.models import F, Value
from django.db.models.functions import Concat
from django.shortcuts import get_object_or_404

from common.permissions import IsOrgAdmin
from .. import models, serializers

__all__ = [
    'RemoteAppPermissionUserRelationViewSet'
]


class RemoteAppPermissionUserRelationViewSet(RelationMixin):
    serializer_class = serializers.PermissionAllUserSerializer
    model = models.RemoteAppPermission.users.through
    relation_query_name = 'remoteapppermission'
    permission_classes = (IsOrgAdmin,)
    filterset_fields = [
        'id', 'user', 'remoteapppermission'
    ]
    search_fields = ('user__name', 'user__username', 'remoteapppermission__name')

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(user_display=F('user__name'))
        return queryset
