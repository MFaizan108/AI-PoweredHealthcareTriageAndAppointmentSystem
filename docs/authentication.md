# Authentication

The API uses **JWT (JSON Web Tokens)** via `djangorestframework-simplejwt`, with an optional **TOTP-based
2FA** step on top of username/password login.

## 1. Register

```
POST /api/accounts/register/          (public — always creates a `patient` account)
POST /api/accounts/staff/create/      (admin-only — creates doctor/receptionist/lab_staff/admin accounts)
POST /api/accounts/register/patient/  (admin/receptionist — walk-in patient registration)
```
A verification email is sent on registration (see [Email verification](#3-email-verification) below).
`email_verified` is informational — it does not currently block login.

## 2. Login

```
POST /api/accounts/login/
{ "username": "...", "password": "..." }
```
Returns:
```json
{ "access": "<jwt>", "refresh": "<jwt>" }
```
- **Rate limited**: 5 attempts / minute per client (`login` throttle scope). A 6th attempt in the same
  window returns `429 Too Many Requests`.
- **Access token lifetime**: 30 minutes. **Refresh token lifetime**: 7 days.
- **Rotation**: every refresh issues a new refresh token and blacklists the old one
  (`ROTATE_REFRESH_TOKENS` + `BLACKLIST_AFTER_ROTATION`), so a stolen refresh token can only be replayed once
  before rotation invalidates it.

If the account has 2FA enabled, the initial login call must also include a valid TOTP code:
```json
{ "username": "...", "password": "...", "otp_code": "123456" }
```
Omitting it (or sending an expired code) when 2FA is on returns `400 Bad Request`.

Use the access token on every subsequent request:
```
Authorization: Bearer <access>
```

## 3. Refresh

```
POST /api/accounts/login/refresh/
{ "refresh": "<jwt>" }
```
Returns a new `access` (and, since rotation is on, a new `refresh` — the old refresh token is blacklisted).

## 4. Logout

```
POST /api/accounts/logout/     (requires Authorization header)
{ "refresh": "<jwt>" }
```
Blacklists the given refresh token immediately. Returns `205 Reset Content`. An already-blacklisted or
malformed token returns `400 Bad Request`.

```
POST /api/accounts/logout-all/   (requires Authorization header, no body)
```
Blacklists **every** outstanding refresh token for the account — use for "log out of all devices" after
a lost/stolen device. An already-issued access token stays valid for up to its own 30-minute lifetime
regardless (JWTs are stateless — this stops it being renewed, it can't retroactively revoke it). A
successful `password-reset/confirm/` also triggers this automatically.

## 5. Two-Factor Authentication (TOTP) + recovery codes

```
POST /api/accounts/2fa/setup/     -> { secret, provisioning_uri }   (scan into an authenticator app)
POST /api/accounts/2fa/enable/    { "otp_code": "..." }             (confirms setup, turns 2FA on)
POST /api/accounts/2fa/disable/   { "password": "..." }             (turns 2FA off)
POST /api/accounts/2fa/recovery-codes/regenerate/   (requires 2FA already enabled)
```
`2fa/setup/` can be called again to regenerate the secret before it's enabled.

`2fa/enable/` and the regenerate endpoint both return `recovery_codes`: 8 single-use backup codes,
shown **only in that response** (only the hash is stored). If the authenticator device is lost, log in
with `recovery_code` instead of `otp_code`:
```json
{ "username": "...", "password": "...", "recovery_code": "A1B2C3D4-E5F6A7B8" }
```
Each code works once; regenerating invalidates every previously-issued code. Disabling 2FA deletes all
outstanding recovery codes too.

## 6. Email verification

```
POST /api/accounts/verify-email/resend/    (requires Authorization header)
POST /api/accounts/verify-email/confirm/   { "token": "..." }   (public)
```
Tokens are signed with `django.core.signing` (not stored in the DB), salted, and expire after 24 hours.

## 7. Password reset

```
POST /api/accounts/password-reset/request/   { "email": "..." }   (public — always returns 200)
POST /api/accounts/password-reset/confirm/   { "uid": "...", "token": "...", "new_password": "..." }
```
`password-reset/request/` intentionally returns the same `200` response whether or not the email exists,
to prevent account enumeration. It uses Django's own signed-token machinery
(`default_token_generator` + `urlsafe_base64_encode`), which already expires tokens once the password
changes or after Django's configured timeout.

## 8. "Who am I"

```
GET /api/accounts/me/                (current user's own profile)
GET /api/accounts/login-history/     (current user's own successful-login history: IP, device, time)
```

## Session invalidation

There are no server-side sessions for API auth (JWT is stateless). See `POST /api/accounts/logout-all/`
above — it blacklists every outstanding refresh token for the account, and runs automatically after a
password reset.
