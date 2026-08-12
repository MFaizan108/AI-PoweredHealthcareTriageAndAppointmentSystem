from django.core.cache import cache
from django.test import TestCase

from .crypto import decrypt_value, encrypt_value
from .models import AIProviderSettings


class GroqKeyEncryptionTests(TestCase):
    def test_round_trip(self):
        secret = "gsk_super_secret_value_123"
        encrypted = encrypt_value(secret)
        self.assertNotEqual(encrypted, secret)
        self.assertEqual(decrypt_value(encrypted), secret)

    def test_empty_value_round_trips_to_empty(self):
        self.assertEqual(encrypt_value(""), "")
        self.assertEqual(decrypt_value(""), "")

    def test_model_property_encrypts_on_write_and_decrypts_on_read(self):
        settings_obj = AIProviderSettings.get_solo()
        settings_obj.groq_api_key = "gsk_my_key"
        settings_obj.save()

        self.assertNotIn("gsk_my_key", settings_obj.groq_api_key_encrypted)

        reloaded = AIProviderSettings.objects.get(pk=settings_obj.pk)
        self.assertEqual(reloaded.groq_api_key, "gsk_my_key")


class AIProviderSettingsCacheTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_get_solo_is_cached_after_first_call(self):
        AIProviderSettings.get_solo()
        self.assertIsNotNone(cache.get(AIProviderSettings.CACHE_KEY))

        with self.assertNumQueries(0):
            AIProviderSettings.get_solo()

    def test_saving_invalidates_the_cache(self):
        obj = AIProviderSettings.get_solo()
        self.assertIsNotNone(cache.get(AIProviderSettings.CACHE_KEY))

        obj.provider = AIProviderSettings.Provider.GROQ
        obj.save()
        self.assertIsNone(cache.get(AIProviderSettings.CACHE_KEY))

        refreshed = AIProviderSettings.get_solo()
        self.assertEqual(refreshed.provider, AIProviderSettings.Provider.GROQ)
