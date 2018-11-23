# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  Copyright (c) 2018, S.J.M. Steffann. This software is licensed under the BSD
#  3-Clause License. Please see the LICENSE file in the project root directory.
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••

import django_filters
from django.contrib.auth import get_user_model

user_model = get_user_model()


class UserFilter(django_filters.FilterSet):
    class Meta:
        model = user_model
        fields = {
            'username': ['exact'],
        }


class UserAdminFilter(django_filters.FilterSet):
    class Meta:
        model = user_model
        fields = {
            'username': ['exact', 'icontains'],
            'email': ['exact', 'icontains'],
            'first_name': ['exact', 'icontains'],
            'last_name': ['exact', 'icontains'],
            'is_active': ['exact'],
            'is_staff': ['exact'],
        }
