# Security & Optimization Guide

This guide covers all security, optimization, and error handling improvements for the trading system.

---

## 🚨 CRITICAL SECURITY ISSUES FOUND & FIXED

### 1. **Hardcoded Passwords** (CRITICAL)

**Issue Found:**
```yaml
# docker-compose.yml - Line 36
POSTGRES_PASSWORD: trading123  # ❌ EXPOSED IN GIT!
```

**Fix Applied:**
```yaml
# docker-compose.secure.yml
POSTGRES_PASSWORD: ${TIMESCALE_PASSWORD}  # ✅ From .env file
```

**Action Required:**
1. Copy `.env.template` to `.env`
2. Generate strong password: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
3. Update `TIMESCALE_PASSWORD` in `.env`
4. Use `docker-compose.secure.yml` instead of `docker-compose.yml`

---

### 2. **Bare Except Clauses** (HIGH)

**Issue Found:**
```python
# 10 instances of bare except:
try:
    risky_operation()
except:  # ❌ Catches ALL exceptions, even KeyboardInterrupt!
    pass
```

**Fix:**
```python
# ✅ Specific exception handling
try:
    risky_operation()
except ValueError as e:
    logger.error(f"Validation error: {e}")
except ConnectionError as e:
    logger.error(f"Connection failed: {e}")
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
```

**Files to Fix:**
- `src/dashboard/utils/data_loader_real.py` (4 instances)
- `src/dashboard/utils/formatters.py` (6 instances)

---

### 3. **Print Statements Instead of Logging** (MEDIUM)

**Issue Found:**
- 88 `print()` statements in production code

**Fix:**
```python
# ❌ Bad
print("[ERROR] Failed to connect")

# ✅ Good
from src.utils import get_logger
logger = get_logger(__name__)
logger.error("Failed to connect to database", exc_info=True)
```

**Why?**
- Print goes to stdout (lost in production)
- Logger supports levels, rotation, formatting
- Can be centralized and monitored

---

### 4. **No Input Validation** (MEDIUM)

**Fix Applied:**
```python
from src.security import InputValidator, validate_trade_input

# Validate symbol
valid, msg = InputValidator.validate_symbol("RELIANCE.NS")
if not valid:
    raise ValueError(msg)

# Validate complete trade
valid, errors = validate_trade_input(
    symbol="RELIANCE.NS",
    quantity=100,
    price=2500.0
)
```

**Prevents:**
- SQL injection
- XSS attacks
- Invalid data causing crashes
- Buffer overflows

---

### 5. **No Rate Limiting** (MEDIUM)

**Fix Applied:**
```python
from src.security import rate_limit

# Limit API calls
@rate_limit(max_requests=10, time_window=60)
def fetch_market_data(symbol):
    # Only 10 calls per minute allowed
    pass
```

**Prevents:**
- API quota exhaustion
- DDoS attacks
- Accidental infinite loops
- Broker bans

---

### 6. **Secrets in Logs** (MEDIUM)

**Fix Applied:**
```python
from src.security import SecretsManager

# ❌ Bad - exposes API key in logs
logger.info(f"Using API key: {api_key}")

# ✅ Good - masks secret
masked = SecretsManager.mask_secret(api_key)
logger.info(f"Using API key: {masked}")  # "sk-***abc"
```

---

## 🛡️ SECURITY BEST PRACTICES

### Environment Variables

**Setup:**
```bash
# 1. Copy template
cp .env.template .env

# 2. Generate strong passwords
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. Fill in .env
nano .env

# 4. Never commit .env
# (Already in .gitignore)
```

**Required Variables:**
```bash
TIMESCALE_PASSWORD=your-strong-password-here
SENDER_PASSWORD=your-email-app-password
SESSION_SECRET_KEY=generated-secret-key
```

---

### Docker Security

**Use Secure Compose:**
```bash
# ✅ Use secure version
docker-compose -f docker-compose.secure.yml up

# ❌ Don't use original (has hardcoded passwords)
docker-compose up
```

**Security Features:**
- ✅ No hardcoded secrets
- ✅ Resource limits (CPU, memory)
- ✅ Read-only filesystems where possible
- ✅ Dropped unnecessary capabilities
- ✅ Network encryption enabled
- ✅ Password-protected Redis

---

### API Security

**1. Rate Limiting:**
```python
from src.security import rate_limit

@rate_limit(max_requests=100, time_window=60)
def call_external_api():
    pass
```

**2. Input Validation:**
```python
from src.security import InputValidator

# Validate before using
valid, msg = InputValidator.validate_symbol(user_input)
if not valid:
    raise ValueError(msg)
```

**3. SQL Injection Prevention:**
```python
# ✅ Good - parameterized queries
cursor.execute("SELECT * FROM trades WHERE symbol = %s", (symbol,))

# ❌ Bad - string concatenation
cursor.execute(f"SELECT * FROM trades WHERE symbol = '{symbol}'")
```

---

### Password Security

**Hashing:**
```python
from src.security import SecretsManager

# Hash password
hashed = SecretsManager.hash_password("my_password")

# Verify password
is_valid = SecretsManager.verify_password("my_password", hashed)
```

**Best Practices:**
- Use PBKDF2 with 100,000 iterations
- Always use salt
- Never store plain text passwords
- Use app-specific passwords for email

---

### Logging Security

**Safe Logging:**
```python
from src.security import SecretsManager
from src.utils import get_logger

logger = get_logger(__name__)

# ✅ Mask secrets
api_key_masked = SecretsManager.mask_secret(api_key)
logger.info(f"Using API key: {api_key_masked}")

# ✅ Don't log passwords ever
logger.info("User logged in")  # Don't include password

# ✅ Use exc_info for full tracebacks
try:
    risky_operation()
except Exception as e:
    logger.exception("Operation failed")  # Includes traceback
```

---

## 🚀 OPTIMIZATION BEST PRACTICES

### Database Optimization

**Connection Pooling:**
```python
# Use connection pool (already in db_connector.py)
from src.database import DatabaseConnector

db = DatabaseConnector()
# Reuses connections automatically
```

**Query Optimization:**
```python
# ✅ Good - use indexes
CREATE INDEX idx_trades_symbol ON trades(symbol);

# ✅ Good - limit results
SELECT * FROM trades WHERE symbol = %s ORDER BY timestamp DESC LIMIT 100;

# ❌ Bad - full table scan
SELECT * FROM trades WHERE LOWER(symbol) = 'reliance.ns';
```

---

### Cache Optimization

**Redis Caching:**
```python
from src.cache import get_cache

cache = get_cache()

# Cache expensive queries
def get_portfolio_value():
    cached = cache.get('portfolio_value')
    if cached:
        return cached

    # Expensive calculation
    value = calculate_portfolio_value()

    # Cache for 5 minutes
    cache.set('portfolio_value', value, ttl=300)
    return value
```

**When to Cache:**
- ✅ Market data (1-5 min TTL)
- ✅ Indicator calculations (1 min TTL)
- ✅ Portfolio stats (30 sec TTL)
- ❌ Trade execution (never cache)
- ❌ Real-time prices (never cache)

---

### Error Handling Best Practices

**Specific Exceptions:**
```python
# ✅ Good - specific exceptions
try:
    data = fetch_market_data(symbol)
except requests.Timeout:
    logger.warning("API timeout, retrying...")
    retry_with_backoff()
except requests.HTTPError as e:
    if e.response.status_code == 429:
        logger.error("Rate limited")
    else:
        logger.error(f"HTTP error: {e}")
except Exception as e:
    logger.exception("Unexpected error")
    raise
```

**Retry Logic:**
```python
import time

def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt  # Exponential backoff
            logger.warning(f"Retry {attempt + 1}/{max_retries} after {wait_time}s")
            time.sleep(wait_time)
```

---

## 🔒 PRODUCTION CHECKLIST

Before deploying to production:

### Required:
- [ ] Copy `.env.template` to `.env`
- [ ] Set strong passwords (20+ characters)
- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Set `DEBUG_MODE=false` in `.env`
- [ ] Use `docker-compose.secure.yml`
- [ ] Enable HTTPS/SSL for database
- [ ] Enable Redis password
- [ ] Configure firewall rules
- [ ] Set up log rotation
- [ ] Configure backup strategy

### Recommended:
- [ ] Enable email notifications
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure alerting (PagerDuty/Discord)
- [ ] Enable 2FA for critical services
- [ ] Set up VPN for remote access
- [ ] Regular security audits
- [ ] Penetration testing
- [ ] DDOS protection (Cloudflare)

### Optional (Advanced):
- [ ] Set up reverse proxy (Nginx)
- [ ] Enable Kafka authentication
- [ ] Use encrypted volumes
- [ ] Set up intrusion detection (Fail2Ban)
- [ ] Regular backup testing
- [ ] Disaster recovery plan

---

## 🌐 API EXPOSURE & NGROK

### When to Use Ngrok

**Use Cases:**
- ✅ Webhook callbacks (broker, payment gateways)
- ✅ Remote dashboard access (temporarily)
- ✅ Demo to clients
- ✅ Mobile app testing

**Setup:**
```bash
# 1. Install ngrok
brew install ngrok  # macOS

# 2. Expose dashboard
ngrok http 8501

# 3. Use HTTPS URL provided
# https://abc123.ngrok.io
```

**Security with Ngrok:**
```bash
# Add authentication
ngrok http 8501 --auth="username:password"

# Whitelist IPs
ngrok http 8501 --allow-cidr="1.2.3.4/32"
```

**⚠️ Warning:**
- Don't expose production databases via ngrok
- Use ngrok for temporary access only
- Always use ngrok auth
- Monitor ngrok sessions

---

### API Gateway Pattern

For production API exposure:

```
Internet → Nginx (SSL) → Rate Limiter → API Gateway → Your Services
```

**Benefits:**
- SSL termination
- Rate limiting
- Authentication
- Request logging
- DDoS protection

**Example Nginx Config:**
```nginx
server {
    listen 443 ssl;
    server_name api.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    location /api/ {
        limit_req zone=api burst=20 nodelay;

        proxy_pass http://localhost:8000;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## 📊 SECURITY MONITORING

### Log Analysis

**Important Logs to Monitor:**
```python
from src.security import SecurityAudit

# Authentication attempts
SecurityAudit.log_auth_attempt(success=True, user="admin", ip="1.2.3.4")

# Suspicious activity
SecurityAudit.log_suspicious_activity(
    "Multiple failed login attempts",
    {"ip": "1.2.3.4", "count": 5}
)

# Data access
SecurityAudit.log_data_access(user="admin", resource="trades", action="READ")
```

**Monitoring Tools:**
- **Grafana**: Dashboards for metrics
- **ELK Stack**: Log aggregation
- **Prometheus**: Time-series metrics
- **AlertManager**: Alert routing

---

## 🐛 COMMON SECURITY MISTAKES TO AVOID

### ❌ DON'T:
1. Hardcode secrets in code
2. Commit `.env` file to git
3. Use `except:` without specifying exception
4. Log sensitive data (passwords, API keys)
5. Disable SSL verification
6. Use outdated dependencies
7. Run services as root
8. Expose databases to internet
9. Use weak passwords
10. Skip input validation

### ✅ DO:
1. Use environment variables
2. Add `.env` to `.gitignore`
3. Handle specific exceptions
4. Mask secrets in logs
5. Always verify SSL
6. Keep dependencies updated
7. Use non-root users in Docker
8. Use VPN for database access
9. Use 20+ character random passwords
10. Validate all user input

---

## 📚 Additional Resources

**Security:**
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [Docker Security](https://docs.docker.com/engine/security/)

**Performance:**
- [PostgreSQL Performance](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Redis Best Practices](https://redis.io/docs/manual/patterns/)
- [Python Performance Tips](https://wiki.python.org/moin/PythonSpeed/PerformanceTips)

---

## 🆘 Security Incident Response

If you detect a security breach:

1. **Immediately:**
   - Disconnect affected systems from network
   - Change all passwords and API keys
   - Enable 2FA on all accounts

2. **Investigation:**
   - Review logs for unauthorized access
   - Identify what data was accessed
   - Document timeline of events

3. **Recovery:**
   - Patch vulnerabilities
   - Restore from clean backups
   - Monitor for continued attacks

4. **Post-Incident:**
   - Security audit of entire system
   - Update security policies
   - Train team on new procedures

---

**Remember: Security is not a feature, it's a process!**

Regular audits, updates, and monitoring are essential for maintaining security.
