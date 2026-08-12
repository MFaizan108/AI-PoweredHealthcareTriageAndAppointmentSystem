from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User

from .models import Notification


class NotificationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="notif_user", email="notif_user@example.com", password="x", role=User.Role.PATIENT
        )
        self.other_user = User.objects.create_user(
            username="notif_other", email="notif_other@example.com", password="x", role=User.Role.PATIENT
        )

        self.n1 = Notification.objects.create(
            recipient=self.user, title="Appointment booked", notification_type=Notification.NotificationType.APPOINTMENT_BOOKED
        )
        self.n2 = Notification.objects.create(
            recipient=self.user,
            title="Reminder",
            notification_type=Notification.NotificationType.APPOINTMENT_REMINDER,
            is_read=True,
        )
        Notification.objects.create(recipient=self.other_user, title="Not yours")

    def test_user_only_sees_own_notifications(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get("/api/notifications/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 2)

    def test_unread_filter(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get("/api/notifications/?unread=1")
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["id"], self.n1.id)

    def test_mark_read(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(f"/api/notifications/{self.n1.id}/mark-read/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.n1.refresh_from_db()
        self.assertTrue(self.n1.is_read)

    def test_cannot_mark_another_users_notification_read(self):
        self.client.force_authenticate(self.other_user)
        resp = self.client.post(f"/api/notifications/{self.n1.id}/mark-read/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_mark_all_read(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post("/api/notifications/mark-all-read/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["marked_read"], 1)  # n2 was already read
        self.assertEqual(Notification.objects.filter(recipient=self.user, is_read=False).count(), 0)
