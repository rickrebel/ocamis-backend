# -*- coding: utf-8 -*-
from . import serializers
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework import permissions, views, status


class UserRegistrationAPIView(views.APIView):
    permission_classes = (permissions.AllowAny, )
    serializer_class = serializers.UserRegistrationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={
                'request': request})
        if not serializer.is_valid(raise_exception=True):
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.data.get('username')
        email = serializer.data.get('email')
        password = serializer.data.get('password')
        name = serializer.data.get('name')
        #checkCondiction = serializer.data.get('checkCondiction')
        #invitation_key = serializer.data.get('key', False)

        # if not checkCondiction:
        #     return Response(
        #         {"errors": [u"no acepto los términos y condiciones"]},
        #         status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.create_user(
                username=username or email,
                email=email,
                password=password,
                first_name=name)
        except Exception as e:
            return Response(
                {"errors": ["El username/email no es valido", u"%s" % e]},
                status=status.HTTP_400_BAD_REQUEST)

        data = serializers.UserDataSerializer(
            user, context={'request': request}).data

        return Response(data, status=status.HTTP_201_CREATED)


class UserLoginAPIView(views.APIView):
    permission_classes = (permissions.AllowAny, )
    serializer_class = serializers.UserLoginSerializer

    def post(self, request):
        from rest_framework.exceptions import ParseError
        from rest_framework.authtoken.models import Token
        #from circles.views import activate_invitation, invitation_search
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)

        email = serializer.data.get('email', None)
        username = serializer.data.get('username', None)
        password = serializer.data.get('password', None)
        #invitation_key = serializer.data.get('key', False)

        if email:
            user_query = User.objects.filter(email=email)
        elif username:
            user_query = User.objects.filter(username=username)
        else:
            raise ParseError(
                detail=u"Please enter username or email to login.")

        if user_query.count() == 1:
            user_obj = user_query.first()
        else:
            raise ParseError(detail=u"This username/email is not valid.")
        if not user_obj.check_password(password):
            raise ParseError(detail=u"Invalid credentials.")
        if not user_obj.is_active:
            raise ParseError(detail=u"User not active.")

        auth_token = getattr(user_obj, "auth_token", None)
        if not auth_token:
            user_obj.auth_token, is_created = Token.objects\
                .get_or_create(user=user_obj)

        get_serializer = serializers.UserDataSerializer
        data = get_serializer(user_obj, context={'request': request}).data

        return Response(data, status=status.HTTP_200_OK)

    def get(self, request):
        user = request.user
        if user.is_authenticated:
            serializer = serializers.UserDataSerializer(
                user, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response()
