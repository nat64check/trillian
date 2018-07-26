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
