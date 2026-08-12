from django.urls import path

from . import views

urlpatterns = [
    path("", views.health, name="health"),
    path("db/", views.health_db, name="health_db"),
    path("redis/", views.health_redis, name="health_redis"),
    path("celery/", views.health_celery, name="health_celery"),
]
