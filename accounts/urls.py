from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from accounts.views import SignupView, setup_view
from accounts.logout import LogoutView
from accounts.login_auth import CustomTokenObtainPairView 


urlpatterns = [
    path('register/', SignupView.as_view(), name='user-register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='user-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('setup/', setup_view),

]
