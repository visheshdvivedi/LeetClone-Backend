from .views import ProblemViewSet, LanguageViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'problem', ProblemViewSet, basename='problem')
router.register(r'language', LanguageViewSet, basename='language')
urlpatterns = router.urls