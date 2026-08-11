from rest_framework.routers import DefaultRouter

from .views import InvoiceViewSet, PaymentViewSet

router = DefaultRouter()
router.register("payments", PaymentViewSet, basename="payment")
router.register("", InvoiceViewSet, basename="invoice")

urlpatterns = router.urls
