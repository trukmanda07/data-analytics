# Security & Compliance V2

**Version:** 2.0
**Created:** 2025-11-09

---

## Authentication

**Method:** JWT-based authentication

```python
# infrastructure/security/jwt_auth.py

class AuthService:
    def authenticate(self, username: str, password: str) -> Optional[AuthToken]:
        # Verify credentials
        user = self.user_repo.get_by_username(username)
        if not user or not bcrypt.verify(password, user.password_hash):
            return None

        # Generate JWT
        payload = {
            'user_id': str(user.user_id),
            'roles': [r.name for r in user.roles],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }

        token = jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')
        return AuthToken(token=token, expires_at=payload['exp'])
```

---

## Authorization (RBAC)

```python
class Permission(Enum):
    READ_CUSTOMERS = "read:customers"
    WRITE_CUSTOMERS = "write:customers"
    READ_ORDERS = "read:orders"
    MANAGE_USERS = "manage:users"

ROLE_PERMISSIONS = {
    Role.ADMIN: [Permission.MANAGE_USERS, ...],  # All
    Role.DATA_ENGINEER: [Permission.WRITE_CUSTOMERS, Permission.WRITE_ORDERS],
    Role.ANALYST: [Permission.READ_CUSTOMERS, Permission.READ_ORDERS],
    Role.VIEWER: [Permission.READ_ORDERS]
}
```

**Row-Level Security:**
```sql
ALTER TABLE core.customers ENABLE ROW LEVEL SECURITY;

CREATE POLICY analyst_region_policy ON core.customers
    FOR SELECT TO analyst_role
    USING (customer_state = current_setting('app.user_region'));
```

---

## Encryption

**At Rest:** PostgreSQL TDE + AES-256 for PII
**In Transit:** TLS 1.3 for all connections
**Application-Level:** Fernet encryption for emails/addresses

---

## LGPD Compliance (Brazilian GDPR)

**PII Fields:** email, address
**Right to Erasure:** `Customer.anonymize()` method
**Consent Management:** `customer_consents` table
**Data Retention:** Anonymize after 2 years inactive

---

## Audit Logging

```sql
CREATE TABLE audit.access_logs (
    log_id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    user_id UUID NOT NULL,
    action VARCHAR(20) NOT NULL,  -- 'read', 'write', 'delete'
    resource VARCHAR(50) NOT NULL,  -- 'customer', 'order'
    resource_id VARCHAR(100) NOT NULL,
    success BOOLEAN NOT NULL,
    ip_address INET
);

-- Append-only (no updates/deletes allowed)
REVOKE UPDATE, DELETE ON audit.access_logs FROM ALL;
```
