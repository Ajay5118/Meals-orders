import datetime
import os
import hashlib

from django.contrib.auth.models import AbstractUser

from django.core.validators import RegexValidator
from django.db import models
from django.db.models import CharField
from django.utils import timezone
from FirstProject import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Create your models here.
"""
# Users:
    * name: <string>
    * phone: <number/string>
    * alt phone: 
    * location 1: <string, url>
    * location 2: <string, url>
# Boxes:
    * name
    * Cost
# Meal:
    * name
    * cost
    * Boxes <many-many relation>
# Subscription:
    * user <foreign key>
    * Date of payment
    * meals remaining
# MealOrders
    * User <foreign key users>
    * meal <foreign key Meal>
    * Quantity <int>
    * Payment <choices==> subscription, prepaid, COD>
    * Order placed Time <date time>
# Delivery
    * MealOrders (foreign key)
    * time of delivery
    * Order delivered time <date time>
    * Boxes received <int>
    * location
"""


class Users(AbstractUser):
    name = models.CharField(max_length=100)
    phone_number = models.PositiveBigIntegerField(
        validators=[RegexValidator(r'^\d{10}$', 'Phone Number must have 10 digits', 'Invalid number')], null=True)
    gender = models.CharField(max_length=128, default='unknown')
    email = models.CharField(default='-', max_length=512)
    date_created = models.DateTimeField(default=timezone.now)
    age = models.FloatField(default=0)
    location_1 = models.CharField(max_length=200)
    location_2 = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class UserOTP(models.Model):
    phone_number = models.PositiveBigIntegerField(
        validators=[RegexValidator(r'^\d{10}$', 'Phone Number must have 10 digits', 'Invalid number')])
    first_name = models.CharField(max_length=250, null=True, blank=True)
    otp = models.CharField(max_length=6, null=False, blank=False)
    timestamp = models.DateTimeField(default=timezone.now, editable=False)
    attempts = models.IntegerField(default=0)
    used = models.BooleanField(default=False)

    class Meta:
        verbose_name = "OTP Token"
        verbose_name_plural = "OTP Tokens"

    def __str__(self):
        return "%s[%s]" % (self.phone_number, str(self.otp), str(self.first_name))

    @classmethod
    def create_otp_for_number(cls, number, name):
        today_min = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
        today_max = datetime.datetime.combine(datetime.date.today(), datetime.time.max)
        otps = cls.objects.filter(phone_number=number, first_name=name, timestamp__range=(today_min, today_max))
        new_user = False
        if len(Users.objects.filter(phone_number=number)) <= 0:
            user, object_ = Users.objects.get_or_create(phone_number=number, first_name=name,
                                                        defaults={
                                                            'username': name.lower().replace(" ", "") + str(
                                                                cls.generate_otp(length=3)),
                                                            'name': name,
                                                            'gender': '-'
                                                        }, )
            if object_:
                new_user = True
        # if otps.count() <= getattr(settings, 'PHONE_LOGIN_ATTEMPTS', 10):
        if len(otps) <= 10:
            otp = cls.generate_otp(length=getattr(settings, 'PHONE_LOGIN_OTP_LENGTH', 3))
            phone_token = UserOTP(phone_number=number, otp=otp, first_name=name)
            phone_token.save()

            # Sending OTP to phone via sms.
            # message = "Your One Time Password for Lylo is %s Thank you." % otp
            # send_sms_by_2factor(to_=str(number), message=message)
            return phone_token, new_user, name, "Success"
        else:
            return False, new_user, "you can not have more than {n} attempts per day, please try again tomorrow".format(
                n=getattr(settings, 'PHONE_LOGIN_ATTEMPTS', 10))

    @classmethod
    def generate_otp(cls, length=3):
        hash_algorithm = getattr(settings, 'PHONE_LOGIN_OTP_HASH_ALGORITHM', 'sha256')
        m = getattr(hashlib, hash_algorithm)()
        m.update(getattr(settings, 'SECRET_KEY', None).encode('utf-8'))
        m.update(os.urandom(16))
        otp = str(int(m.hexdigest(), 16))[-length:]
        return otp


class Boxes(models.Model):
    box_name = models.CharField(max_length=200)
    cost = models.IntegerField()


class Subscription(models.Model):
    sub_user = models.ForeignKey(Users, related_name='subscription_users', on_delete=models.CASCADE)
    plan = models.IntegerField(default=0)
    payment_method = models.CharField(max_length=100, default='cod')
    date_of_payment = models.DateTimeField(default=timezone.now)
    meals_Remaining = models.IntegerField(default=0)
    amount = models.IntegerField(default=0)


class Meals(models.Model):
    meals_name = models.CharField(max_length=100)
    meals_cost = models.IntegerField()
    meals_boxes = models.ManyToManyField(Boxes, related_name='meals_boxs')

    def __str__(self):
        return self.meals_name


class MealsOrders(models.Model):
    PAYMENT_CHOICES = [
        ('subscription', 'Subscription'),
        ('prepaid', 'Prepaid'),
        ('cod', 'Cash on Delivery'),
    ]

    # meals_orders = mo
    mo_user = models.ForeignKey(Users, related_name="MealsOrders_user", on_delete=models.CASCADE)
    meal_type = models.ForeignKey(Meals, related_name="meals_type", on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    payment = models.CharField(max_length=100, choices=PAYMENT_CHOICES)
    orderplacedtime = models.DateTimeField(default=timezone.now)
    delivered_status = models.BooleanField(default=False)


class Delivery(models.Model):
    mealorder = models.ForeignKey(MealsOrders, related_name='orderdeliverd', on_delete=models.CASCADE)
    time_of_delivery = models.TimeField(default=timezone.now)
    boxes_received = models.IntegerField()
    boxes_given = models.IntegerField()
    location_of_delivery = models.CharField(max_length=200)


class Quiz(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    audio = models.FileField(upload_to='question_audio/', null=True, blank=True)

    def __str__(self):
        return self.text


class Options(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)
    midi_note = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.text


class QuizResult(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.IntegerField()
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} - Score: {self.score}"



