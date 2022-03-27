# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from django.db import IntegrityError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from .models import User
from .serializers import UserSerializerWithToken, UserSerializer


class MyUserAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializerWithToken(user, many=False)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        data = request.data

        email = data["email"]

        user.email = email
        user.save()

        return Response(
            "User saved successfully",
            status=status.HTTP_200_OK,
        )

    def delete(self, request):
        user = request.user
        user.delete()
        return Response(
            "User deleted successfully",
            status=status.HTTP_200_OK,
        )


class UserAPI(APIView):
    def get(self, request, pk):
        user = User.objects.get(id=pk)
        serializer = UserSerializer(user, many=False)
        return Response(serializer.data)

    def post(self, request):
        data = request.data

        try:
            user = User.objects.create_user(
                email=data["email"],
                password=data["password"],
            )
        except IntegrityError:
            return Response(
                "Email not available",
                status=status.HTTP_409_CONFLICT,
            )
        except:
            return Response(
                "There was an error crrating the user",
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = UserSerializer(user, many=False)
        return Response(serializer.data)
