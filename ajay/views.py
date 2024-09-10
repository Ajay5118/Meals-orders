from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_protect
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction

from ajay.models import Delivery, MealsOrders, Subscription, Meals, UserOTP, Users, Quiz, QuizResult, Options, Question
from django.db.models import F, Count, Sum, Avg, Subquery, OuterRef
from django.shortcuts import render, redirect
import datetime
from io import BytesIO
# from PIL import ImageOps
# from PIL import Image
from asgiref.sync import async_to_sync
# from channels.layers import get_channel_layer
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files.base import ContentFile
from django.db.models import Avg
from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
# from single_session.signals import remove_other_sessions, remove_all_sessions

from .serializers import PhoneTokenCreateSerializer, PhoneTokenValidateSerializer

from FirstProject import settings
from django.contrib.auth import login, authenticate, user_logged_out, user_logged_in
from rest_framework.authtoken.models import Token

from .serializers import MealsOrdersSerializer
from django.db.models import F
from django.db.models.functions import Cast, Coalesce, TruncDate
from django.db import models


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


def sum(request):
    a = 35
    b = 30
    if a > b:
        return HttpResponse(True)
    else:
        return HttpResponse(True)


@api_view(['GET'])
def boxes(request):
    boxes_received1 = Delivery.objects.annotate(Count("boxes_given"))
    print(boxes_received1)
    response_content = "\n".join([str(box) for box in boxes_received1])
    return HttpResponse(response_content)


@api_view(['GET'])
def mealsavg(request):
    avgmeals = MealsOrders.objects.values('mo_meal').annotate(avgitems=Avg('quantity')).order_by('avgitems')
    avgmeals = list(avgmeals)
    print(avgmeals)

    return JsonResponse(avgmeals, safe=False)


@api_view(['GET'])
def most_ordered_meal(request):
    most_ordered = MealsOrders.objects.select_related('mo_user').values('mo_meal', 'mo_user_id',
                                                                        'mo_user__name').annotate(
        order_count=Count('id')
    ).order_by('-order_count')[:3]

    most_ordered = list(most_ordered)

    return JsonResponse(most_ordered, safe=False)


@api_view(['POST', 'GET'])
@csrf_protect
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def Remaining_meals(request):
    user = request.user

    subscriptions = Subscription.objects.filter(sub_user=user)

    result = MealsOrders.objects.annotate(
        plan=Subquery(subscriptions.values('plan')[:1]),
        difference=Coalesce(
            Cast(F('plan'), output_field=models.IntegerField()) -
            Cast(F('quantity'), output_field=models.IntegerField()),
            0
        )
    ).values('mo_user_id', 'difference')

    return JsonResponse(list(result), safe=False)


@api_view(["GET"])
def paymentstatus(request):
    typeofpayment = MealsOrders.objects.filter(payment='cod').select_related('mo_user_id').values('mo_meal',
                                                                                                  'mo_user_id__name',
                                                                                                  'payment')

    t2 = '\n'.join(
        [f"meal : {payment['mo_meal']}, name :  {payment['mo_user_id__name']}, type : {payment['payment']}" for payment
         in typeofpayment])
    return HttpResponse(t2)


def user_detail(user, last_login):
    try:
        token = user.auth_token.key
    except:
        token = Token.objects.create(user=user)
        token = token.key
    user_json = {
        "id": user.pk,
        "last_login": last_login,
        "token": token,
        "status": status.HTTP_200_OK,

    }
    return user_json


class GenerateOTP(CreateAPIView, ):
    queryset = UserOTP.objects.all()
    serializer_class = PhoneTokenCreateSerializer

    def get(self, request):
        # Render the HTML form
        return render(request, 'phone_number.html')

    def post(self, request, format=None, **kwargs):
        # Get the patient if present or result None.
        print(request.data)
        try:
            ser = self.serializer_class(
                data=request.data,
                context={'request': request}
            )
            if ser.is_valid():
                token, new_user, name, resp = UserOTP.create_otp_for_number(request.data.get('phone_number'),
                                                                            request.data.get('first_name', ''))
                if token:
                    phone_token = self.serializer_class(
                        token, context={'request': request}
                    )
                    data = phone_token.data
                    if getattr(settings, 'PHONE_LOGIN_DEBUG', False):
                        data['debug'] = token.otp
                    data['new_user'] = new_user
                    data['name'] = name
                    print(data)
                    if new_user == False:
                        return render(request, template_name='mealsorders.html')

                    return render(request, 'otpvalidation.html', {'data': data})
                return Response({'reason': resp}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'reason': ser.errors}, status=status.HTTP_406_NOT_ACCEPTABLE)
        except Exception as e:
            e = str(e)
            return Response({'reason': e}, status=status.HTTP_400_BAD_REQUEST)


class ValidateOTP(CreateAPIView):
    queryset = UserOTP.objects.all()
    serializer_class = PhoneTokenValidateSerializer

    def get(self, request):
        # Render the HTML form
        return render(request, 'otpvalidation.html')

    #print(requests)

    def post(self, request, format=None):
        # Get the patient if present or result None.

        ser = self.serializer_class(
            data=request.data, context={'request': request}
        )
        if ser.is_valid():
            pk = request.data.get("pk")
            otp = request.data.get("otp")
            if len(str(otp)) < 3:
                otp = '0' * (3 - len(str(otp))) + str(otp)
            print(pk, otp)
            try:
                user = authenticate(request, pk=pk, otp=otp)
                print(user)
                if user:
                    last_login = user.last_login
                login(request, user)

                response = user_detail(user, last_login)
                print('hiii')
                print(response)
                # rendered_html = render_to_string('login.html', context={})
                # response['login.html'] = rendered_html

                return render(request, 'subscription.html', {'response': response})



            except ObjectDoesNotExist:
                return Response(
                    {'reason': "OTP doesn't exist"},
                    status=status.HTTP_406_NOT_ACCEPTABLE
                )

        return Response(
            {'reason': ser.errors}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(['GET', 'POST'])
@csrf_protect
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def subscribe(request):
    def get(self, request):
        return render(request, 'mealsorders.html')
        print(request)

    if request.method == 'POST':
        plan = int(request.POST.get('plan'))
        payment_method = request.POST.get('payment_method')

        user = request.user  # This should be an authenticated user
        print(user)

        if not user or isinstance(user, AnonymousUser):
            return Response({'error': 'User is not authenticated.'}, status=400)

        try:

            subscription = Subscription.objects.create(
                sub_user=user,
                plan=plan,
                payment_method=payment_method,
                amount=plan * 119
            )
            print(subscription)
            print(request)

            context = {
                'message': f'Successfully registered for {plan} with {payment_method} payment method and the amount is.',
                'subscription_user': subscription.sub_user.name,  # or any other user field
                'plan': subscription.plan,
                'payment_method': subscription.payment_method,
                'amount': subscription.amount
            }
            return render(request, 'mealsorders.html', context)


        except Exception as e:
            return Response({'error': str(e)}, status=400)


@api_view(["GET", 'POST'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def Meals_type(request):
    if request.method == 'GET':
        return render(request, 'mealsorders.html')

    if request.method == 'POST':
        quantity = request.data.get('quantity')
        meal_type_name = request.data.get('meal_type')
        payment_method = request.data.get('payment_method')

        user = request.user
        if isinstance(user, AnonymousUser):
            return Response({'error': 'User is not authenticated.'}, status=400)

        meal_type = Meals.objects.filter(meals_name=meal_type_name).first()
        if not meal_type:
            return Response({'error': 'Invalid meal type'}, status=400)

        meals_order = MealsOrders.objects.create(
            mo_user=user,
            meal_type=meal_type,
            quantity=quantity,
        )

        serializer = MealsOrdersSerializer(meals_order)

        subscription = Subscription.objects.filter(sub_user=user).first()
        if not subscription:
            return Response({'error': 'User has no active subscription'}, status=400)

        total_ordered_meals = MealsOrders.objects.filter(mo_user=user).aggregate(total_quantity=Sum('quantity'))[
                                  'total_quantity'] or 0
        remaining_meals = subscription.plan - total_ordered_meals

        if remaining_meals < 0:
            return render(request, 'subscription.html', status=400)

        subscription.meals_remaining = remaining_meals
        subscription.save()

        context = {
            'success': True,
            'order': serializer.data,
            'user': user.name,
            "plan": subscription.plan,
            "quantity": total_ordered_meals,
            "payment_method": subscription.payment_method,
            'remaining_meals': remaining_meals
        }

        return render(request, 'subscription_meals_difference.html', context)


@api_view(['GET'])
def remain_boxes(request):
    delivery_data = MealsOrders.objects.values(
        'mo_user__name',
        'meal_type',
        'quantity',
        'delivered_status'
    ).distinct()
    print(delivery_data)

    context = {'delivery_data': delivery_data}
    return render(request, 'remain_boxes.html', context)


@api_view(['GET', 'POST'])
def deliveries_view(request):
    if request.method == "POST":
        mealorder_id = request.POST.get('mealorder')
        boxes_received = request.POST.get('boxes_received')
        boxes_given = request.POST.get('boxes_given')

        # Filter meals orders where delivered_status is False and get the specific order
        mealorder = MealsOrders.objects.filter(id=mealorder_id, delivered_status=False).first()
        print(mealorder)

        if mealorder:
            Delivery.objects.create(
                mealorder=mealorder,
                boxes_received=boxes_received,
                boxes_given=boxes_given,

            )
            # meal order as delivered
            mealorder.delivered_status = True
            mealorder.save()

    # Fetch all meal orders where delivered_status is False
    mealorders = MealsOrders.objects.filter(delivered_status=False)
    deliveries = Delivery.objects.all()
    print(deliveries)

    return render(request, 'deliveries_view.html', {
        'mealorders': mealorders,
        'deliveries': deliveries
    })


@api_view(["GET"])
def delivery_data(request):
    delivery_data = MealsOrders.objects.filter(delivered_status=False).annotate(
        order_date=TruncDate('orderplacedtime')
    ).values(
        'mo_user__name',
        'order_date',

    ).annotate(total_quantity=Sum('quantity')).order_by('order_date', 'mo_user__name')

    # Update meals_Remaining
    for data in delivery_data:
        user_name = data['mo_user__name']
        total_quantity = data['total_quantity']

        user = Users.objects.get(name=user_name)
        subscription = Subscription.objects.filter(sub_user=user).order_by('-date_of_payment').first()

        if subscription:
            subscription.meals_Remaining = max(0, subscription.meals_Remaining - total_quantity)
            subscription.save()

    # Create a list of users who need to take a subscription
    need_subscription = [data['mo_user__name'] for data in delivery_data if data['total_quantity'] > 10]

    return render(request, 'delivery_data.html',
                  {'delivery_data': delivery_data, 'need_subscription': need_subscription})


@api_view(["GET"])
def delivery_information(request):
    delivery_info = MealsOrders.objects.filter(delivered_status=False).values(
        'mo_user__name',
        'meal_type',
        'quantity',
        'orderplacedtime'
    ).order_by('orderplacedtime')
    print(delivery_info)
    return render(request, 'delivery_information.html',
                  {'delivery_info': delivery_info})


@api_view(['POST', 'GET'])
def GmailLogin(request):
    email = request.data.get("email")
    user = Users.objects.filter(email=email).first()
    if not user:
        password = Users.objects.make_random_password()
        username = email
        user = Users.objects.create_user(username=username, password=password, email=email)
    if user:
        last_login = user.last_login
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    response = user_detail(user, last_login)
    print(response)

    return render(request, template_name='Gmail.html', context={response})


@api_view(['GET'])
def logout(request):
    """
    Removes the authenticated user's ID from the request and flushes their
    session data.
    """
    # Dispatch the signal before the user is logged out so the receivers have a
    # chance to find out *who* logged out.
    user = getattr(request, 'user', None)
    if hasattr(user, 'is_authenticated') and not user.is_authenticated:
        user = None

    user_logged_out.send(sender=user.__class__, request=request, user=user)
    if hasattr(request, 'user'):
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()

    return Response({'status': 'success'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def updateUser(request):
    user = request.user
    data = request.data
    user.name = data.get('first_name', '') + ' ' + data.get('last_name', '')
    user.gender = data.get('gender', 'male')
    user.save()
    return Response({'status': "ok"}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def getUserDetails(request):
    user = request.user
    return Response({"data": {'name': user.name, 'gender': user.gender, 'rating': user.rating}},
                    status=status.HTTP_200_OK)


@api_view(['POST'])
def CreateProfile(request):
    user = request.user
    if request.data.get('name', ''):
        user.name = request.data.get('name')
    if request.data.get('age', 0):
        user.age = request.data.get('age')
    if request.data.get('gender', ''):
        user.gender = request.data.get('gender')
    user.save()
    return Response({"status": "ok"}, status=status.HTTP_200_OK)


@api_view(['POST'])
def UpdateProfile(request):
    user = request.user
    if request.data.get('level', ''):
        user.level = request.data.get('level')
    user.save()
    return Response({"status": "ok"}, status=status.HTTP_200_OK)


def my_view(request):
    context = {'message': 'Hello from Django!'}  # Optional context data
    return render(request, 'my_template.html', context)


def display_ad(request):
    return render(request, 'ad.html')


@api_view(["GET", 'POST'])
def quiz_list(request):
    quizzes = Quiz.objects.all()
    return render(request, 'quiz_list.html', {'quizzes': quizzes})


@api_view(["GET", 'POST'])
def take_quiz(request, quiz_id):
    print(f"Entering take_quiz view with quiz_id: {quiz_id}")
    quiz = get_object_or_404(Quiz, pk=quiz_id)

    # Get or initialize the user's progress
    current_question_index = request.session.get(f'quiz_{quiz_id}_current_question', 0)
    attempts = request.session.get(f'quiz_{quiz_id}_attempts', 0)
    score = request.session.get(f'quiz_{quiz_id}_score', 0)

    if request.method == 'POST':
        print("POST request received")

        # Get the current question
        questions = list(quiz.questions.all())
        if current_question_index >= len(questions):
            return JsonResponse({'status': 'quiz_complete', 'score': score, 'total': len(questions)})

        current_question = questions[current_question_index]

        selected_choice_id = request.POST.get('selected_choice')
        if selected_choice_id:
            selected_choice = Options.objects.get(pk=selected_choice_id)

            if selected_choice.is_correct:
                # Correct answer
                score += 1
                current_question_index += 1
                attempts = 0
                message = "Correct! Moving to the next question."
                status = 'correct'
            else:
                # Wrong answer
                attempts += 1
                if attempts >= 2:
                    # After two attempts, show the correct answer and move to the next question
                    correct_choice = current_question.options.filter(is_correct=True).first()
                    message = f"The correct answer is: {correct_choice.text}. Moving to the next question."
                    current_question_index += 1
                    attempts = 0
                    status = 'show_correct'
                else:
                    message = "Incorrect. Try again."
                    status = 'incorrect'

            # Update session
            request.session[f'quiz_{quiz_id}_current_question'] = current_question_index
            request.session[f'quiz_{quiz_id}_attempts'] = attempts
            request.session[f'quiz_{quiz_id}_score'] = score

            # Check if quiz is complete
            if current_question_index >= len(questions):
                result = QuizResult.objects.create(
                    user=request.user,
                    quiz=quiz,
                    score=score,
                    total_questions=len(questions)
                )
                return JsonResponse({
                    'status': 'quiz_complete',
                    'score': score,
                    'total': len(questions),
                    'result_url': reverse('quiz_result', kwargs={'quiz_id': quiz.id, 'result_id': result.id})
                })

            # Prepare next question
            next_question = questions[current_question_index] if current_question_index < len(questions) else None

            return JsonResponse({
                'status': status,
                'message': message,
                'next_question': {
                    'text': next_question.text if next_question else None,
                    'options': [{'id': o.id, 'text': o.text, 'midi_note': o.midi_note} for o in
                                next_question.options.all()] if next_question else None
                } if next_question else None
            })

    # For GET requests or if no choice selected
    questions = list(quiz.questions.all())
    if current_question_index >= len(questions):
        messages.info(request, "You have already completed this quiz.")
        return redirect('quiz_list')  # Or wherever you want to redirect after quiz completion

    current_question = questions[current_question_index]

    return render(request, 'take_quiz.html', {
        'quiz': quiz,
        'question': current_question,
        'midi_enabled': True  # Flag to enable MIDI functionality in template
    })

@api_view(["GET", 'POST'])
def quiz_result(request, quiz_id, result_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    result = get_object_or_404(QuizResult, pk=result_id, user=request.user, quiz=quiz)

    # Clear session data for this quiz
    request.session.pop(f'quiz_{quiz_id}_current_question', None)
    request.session.pop(f'quiz_{quiz_id}_attempts', None)
    request.session.pop(f'quiz_{quiz_id}_score', None)

    return render(request, 'quiz_result.html', {
        'quiz': quiz,
        'result': result
    })



@api_view(["GET", 'POST'])
def check_midi_answer(request, question_id):
    if request.method == 'POST':
        midi_note = request.POST.get('midi_note')
        question = get_object_or_404(Question, pk=question_id)
        correct_choice = question.Options.filter(is_correct=True, midi_note=midi_note).exists()
        return JsonResponse({'correct': correct_choice})
# @api_view(["GET", 'POST'])
# def quiz_result(request, quiz_id):
#     quiz = get_object_or_404(Quiz, pk=quiz_id)
#     result = QuizResult.objects.filter(user=request.user, quiz=quiz).latest('completed_at')
#     return render(request, 'quiz_result.html', {'quiz': quiz, 'result': result})


