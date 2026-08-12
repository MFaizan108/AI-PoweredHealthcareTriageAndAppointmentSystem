def blacklist_all_outstanding_tokens(user):
    """Invalidates every refresh token ever issued to this user that hasn't expired/been blacklisted
    yet — used for "log out everywhere" and automatically after a password reset. Note: this can't
    revoke an already-issued *access* token (JWTs are stateless), so a stolen access token stays
    valid for up to its own lifetime (30 minutes) regardless — this bounds, rather than eliminates,
    that exposure window, which is the standard accepted trade-off for stateless JWT auth."""
    from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

    tokens = list(OutstandingToken.objects.filter(user=user))
    for token in tokens:
        BlacklistedToken.objects.get_or_create(token=token)
    return len(tokens)
