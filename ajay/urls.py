import django.urls
from django.conf import settings
from django.conf.urls.static import static

from ajay import views
from ajay.views import GenerateOTP

urlpatterns = [
    django.urls.path("boxes", views.boxes),
    django.urls.path("sum", views.sum, name='sum'),
    django.urls.path("remainders", views.remain_boxes),
    django.urls.path("mealsavg", views.mealsavg),
    django.urls.path("most_ordered_meal", views.most_ordered_meal),
    django.urls.path("subcribe", views.subscribe, name='subcribe'),
    django.urls.path("paymenttype", views.paymentstatus),
    django.urls.path("GmailLogin", views.GmailLogin),
    django.urls.path("CreateProfile", views.CreateProfile),
    django.urls.path("my_view", views.my_view),
    django.urls.path("user_detail", views.user_detail),
    django.urls.path('generate-otp/', GenerateOTP.as_view(), name='generate-otp'),
    django.urls.path('get_meals_orders/', views.Meals_type, name='get_meals_orders'),
    django.urls.path("validateotp", views.ValidateOTP.as_view(), name='validateotp'),
    django.urls.path('Remaining_meals', views.Remaining_meals),
    django.urls.path('delivery_data', views.delivery_data),
    django.urls.path('delivery_info', views.delivery_information),
    django.urls.path('deliveries_view', views.deliveries_view, name='deliveries_view'),
    django.urls.path('ad/', views.display_ad, name='display_ad'),
    django.urls.path('quiz_list', views.quiz_list, name='quiz_list'),
    django.urls.path('<int:quiz_id>/', views.take_quiz, name='take_quiz'),
    django.urls.path('api/ajay/<int:quiz_id>/result/<int:result_id>/', views.quiz_result, name='quiz_result'),
    django.urls.path('check_midi/<int:question_id>/', views.check_midi_answer, name='check_midi_answer'),
    django.urls.path('quiz_completed', views.quiz_completed, name='quiz_completed')
]
