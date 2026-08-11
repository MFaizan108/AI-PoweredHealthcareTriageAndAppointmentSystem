# 11. Security

Healthcare application mein security important hai.

Implement:

- JWT authentication
- Session authentication
- Role-based access control
- Object-level permissions
- Password hashing
- Email verification
- Password reset
- 2FA
- Rate limiting
- Audit logs
- Login history by device name
- Secure file uploads
- Encryption for sensitive fields where appropriate
- HTTPS in production
- CSRF protection
- Security headers

Example access rules:

```
Patient        → Only own medical records
Doctor         → Assigned/authorized patient records
Receptionist   → Appointment-related information
Lab Staff      → Lab-related information
Admin          → System management
```
