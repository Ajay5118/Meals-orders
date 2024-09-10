from django.contrib import admin

from ajay.models import Users, Boxes, Meals, Subscription, MealsOrders, Delivery, UserOTP, Quiz, Question, QuizResult, Options


class UsersAdmin(admin.ModelAdmin):
    list_display = ('name', 'age', 'phone_number', 'email', 'gender', 'date_created', 'location_1', 'location_2')


class BoxesAdmin(admin.ModelAdmin):
    list_display = ('box_name', 'cost')


class MealsAdmin(admin.ModelAdmin):
    def meals_name(self, obj):
        return obj.meals_name.name

    list_display = ('meals_name', 'meals_cost',)


class SubscriptionAdmin(admin.ModelAdmin):
    def sub_user(self, obj):
        return obj.sub_user.name

    list_display = ('sub_user', 'plan', 'payment_method', "date_of_payment", 'meals_Remaining', 'amount')


class MealOrdersAdmin(admin.ModelAdmin):
    def user(self, obj):
        return obj.mo_user.name

    list_display = ('id', 'user', 'quantity', 'payment', 'orderplacedtime', 'meal_type')

    list_filter = ('payment',)


class DeliveryAdmin(admin.ModelAdmin):
    def user_name(self, obj):
        return obj.mealorder.mo_user.name

    list_display = ('user_name', 'time_of_delivery', 'boxes_given', 'boxes_received', 'location_of_delivery')


class UserOTPAdmin(admin.ModelAdmin):
    list_display = ('id', 'phone_number', 'otp', 'timestamp', 'attempts', 'used')


admin.site.register(UserOTP, UserOTPAdmin)
admin.site.register(Users, UsersAdmin)
admin.site.register(Boxes, BoxesAdmin)
admin.site.register(Meals, MealsAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(MealsOrders, MealOrdersAdmin)
admin.site.register(Delivery, DeliveryAdmin)
admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Options)
admin.site.register(QuizResult)
