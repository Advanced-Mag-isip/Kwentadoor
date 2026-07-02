from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from audit.models import AuditLog
from .serializers import UserSerializer, RegisterSerializer, LoginSerializer

User = get_user_model()

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')
    return request.META.get('REMOTE_ADDR')

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        
        AuditLog.objects.create(
            user=user,
            action='CREATE',
            model_name='User',
            object_id=str(user.id),
            description="User registered a new account.",
            ip_address=get_client_ip(request)
        )

        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "token": token.key
        }, status=status.HTTP_201_CREATED)

class LoginView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)

        AuditLog.objects.create(
            user=user,
            action='LOGIN',
            model_name='User',
            object_id=str(user.id),
            description="User logged in successfully.",
            ip_address=get_client_ip(request)
        )

        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "token": token.key
        })

class LogoutView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        try:
            AuditLog.objects.create(
                user=request.user,
                action='LOGOUT',
                model_name='User',
                object_id=str(request.user.id),
                description="User logged out successfully.",
                ip_address=get_client_ip(request)
            )
            
            Token.objects.filter(user=request.user).delete()
            return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user