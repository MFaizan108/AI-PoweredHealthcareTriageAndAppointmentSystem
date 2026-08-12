import secrets

from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone

from .models import TwoFactorRecoveryCode

RECOVERY_CODE_COUNT = 8


def generate_recovery_codes(user):
    """Replaces any existing codes with a fresh batch and returns the plaintext codes — the only
    time they're ever available in plaintext. Only the hash is persisted."""
    TwoFactorRecoveryCode.objects.filter(user=user).delete()
    plaintext_codes = []
    for _ in range(RECOVERY_CODE_COUNT):
        code = f"{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"
        plaintext_codes.append(code)
        TwoFactorRecoveryCode.objects.create(user=user, code_hash=make_password(code))
    return plaintext_codes


def consume_recovery_code(user, code):
    """Checks `code` against the user's unused recovery codes; marks it used (single-use) and
    returns True on a match, False otherwise."""
    if not code:
        return False
    for recovery_code in TwoFactorRecoveryCode.objects.filter(user=user, used_at__isnull=True):
        if check_password(code, recovery_code.code_hash):
            recovery_code.used_at = timezone.now()
            recovery_code.save(update_fields=["used_at"])
            return True
    return False
