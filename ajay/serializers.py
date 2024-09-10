from django.core.validators import RegexValidator
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from .models import Meals, UserOTP, MealsOrders


class MealsOrdersSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealsOrders
        fields = ['mo_user', 'meal_type', 'quantity']


class PhoneTokenCreateSerializer(ModelSerializer):
    phone_number = serializers.CharField(
        validators=[RegexValidator(r'^\d{10}$', 'Phone Number must have 10 digits', 'Invalid number')])
    first_name = serializers.CharField(max_length=250)

    class Meta:
        model = UserOTP
        fields = ('pk', 'phone_number', 'first_name')


class PhoneTokenValidateSerializer(ModelSerializer):
    pk = serializers.IntegerField()
    otp = serializers.CharField(max_length=40)

    class Meta:
        model = UserOTP
        fields = ('pk', 'otp')
