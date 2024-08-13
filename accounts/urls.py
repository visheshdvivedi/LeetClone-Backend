from django.urls import path

from rest_framework.routers import DefaultRouter
from .views import AccountViewSet, LogoutView, GoogleLoginView

router = DefaultRouter()
router.register(r'account', AccountViewSet, basename='account')
urlpatterns = router.urls

urlpatterns.extend([
    path("logout/", LogoutView.as_view(), name="logout_view"),
    path("login/google/", GoogleLoginView.as_view(), name="google_login")
])