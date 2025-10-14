# Security Features

This document describes the security features implemented in the Visual Product Matcher application.

## Overview

The application implements multiple layers of security to protect against common web vulnerabilities:

1. **Rate Limiting** - Prevents abuse and DoS attacks
2. **Input Validation** - Validates all user inputs
3. **SSRF Protection** - Prevents Server-Side Request Forgery
4. **File Upload Security** - Validates and sanitizes uploaded files
5. **Security Headers** - Implements secure HTTP headers
6. **CORS Configuration** - Controlled cross-origin requests

## Rate Limiting

### Configuration

Rate limiting is configured in `config.yaml`:

```yaml
security:
  rate_limit:
    enabled: true
    default: "100 per hour"        # Global rate limit
    upload: "10 per minute"        # File upload endpoint
    search: "30 per minute"        # Search endpoints
    storage_uri: "memory://"       # Use "redis://localhost:6379" for production
```

### Endpoints

- **Global**: 100 requests per hour per IP
- **File Upload** (`/api/upload`): 10 requests per minute
- **Search** (`/api/search-url`): 30 requests per minute
- **Health Check** (`/api/health`): No limit (monitoring)

### Rate Limit Headers

When rate limited, responses include:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Time when limit resets

### Production Recommendations

For production deployment:
1. Use Redis for distributed rate limiting:
   ```yaml
   storage_uri: "redis://localhost:6379"
   ```
2. Adjust limits based on expected traffic
3. Monitor rate limit violations

## File Upload Security

### Validation

All uploaded files are validated for:

1. **File Size**: Maximum 10MB (configurable)
2. **MIME Type**: Only image types allowed
   - `image/jpeg`
   - `image/jpg`
   - `image/png`
   - `image/webp`
3. **File Extension**: Blocked extensions
   - Executables: `.exe`, `.bat`, `.cmd`, `.sh`, `.ps1`
   - Scripts: `.php`, `.jsp`, `.asp`, `.js`, `.py`, `.rb`, `.pl`
4. **Path Traversal**: Prevents `../` attacks
5. **EXIF Stripping**: Removes metadata for privacy (optional)

### Configuration

```yaml
security:
  upload_safety:
    max_file_size_mb: 10
    allowed_mime_types: ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    strip_exif: true
    scan_for_malware: false  # Enable when antivirus available
```

### Example Error Response

```json
{
  "error": "Invalid file",
  "message": "File type 'application/pdf' is not allowed"
}
```

## SSRF Protection

### URL Validation

The `/api/search-url` endpoint validates URLs to prevent Server-Side Request Forgery (SSRF) attacks:

1. **Scheme Validation**: Only HTTP/HTTPS allowed
2. **Private IP Blocking**: Prevents access to:
   - Private networks (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
   - Loopback addresses (127.0.0.1, ::1)
   - Link-local addresses (169.254.0.0/16)
   - Cloud metadata endpoints
3. **URL Length**: Maximum 2048 characters
4. **Timeout**: 10-second request timeout

### Blocked Patterns

- `localhost`
- `127.0.0.1`, `::1`
- `169.254.*` (link-local)
- `metadata.google.internal`
- `*.internal` domains

### Configuration

```yaml
security:
  request_validation:
    max_url_length: 2048
    url_timeout_seconds: 10
    allowed_url_schemes: ["http", "https"]
    blocked_private_ips: true
```

### Example Error Response

```json
{
  "error": "Invalid URL",
  "message": "Access to private IP addresses is not allowed"
}
```

## Security Headers

All responses include security headers:

### Headers Applied

1. **X-Frame-Options: DENY**
   - Prevents clickjacking attacks
   - Blocks embedding in frames/iframes

2. **X-Content-Type-Options: nosniff**
   - Prevents MIME type sniffing
   - Forces browser to respect declared content type

3. **X-XSS-Protection: 1; mode=block**
   - Enables XSS filter in older browsers
   - Blocks page if XSS detected

4. **Strict-Transport-Security: max-age=31536000; includeSubDomains**
   - Enforces HTTPS connections
   - Valid for 1 year

### Configuration

```yaml
security:
  headers:
    x_frame_options: "DENY"
    x_content_type_options: "nosniff"
    x_xss_protection: "1; mode=block"
    strict_transport_security: "max-age=31536000; includeSubDomains"
```

## Authentication (Future)

### Planned Features

Authentication is not currently implemented but planned for future releases:

1. **JWT-based Authentication**
   - Token-based stateless authentication
   - Refresh token rotation

2. **API Keys**
   - Per-user rate limiting
   - Usage tracking and analytics

3. **OAuth 2.0**
   - Third-party authentication
   - Social login integration

4. **Role-Based Access Control (RBAC)**
   - Admin, User, Read-Only roles
   - Fine-grained permissions

### Preparation

When adding authentication:

1. Update `config.yaml`:
   ```yaml
   security:
     auth:
       enabled: true
       jwt_secret: "${JWT_SECRET}"
       token_expiry: 3600
       refresh_token_expiry: 604800
   ```

2. Protect endpoints:
   ```python
   @api_bp.route('/admin/rebuild-index', methods=['POST'])
   @require_auth(role='admin')
   def rebuild_index():
       # Protected admin endpoint
       pass
   ```

3. Rate limit per user instead of IP

## Best Practices

### Development

1. **Environment Variables**
   - Never commit secrets to git
   - Use `.env` file for sensitive config
   - Example:
     ```bash
     SECRET_KEY=your-secret-key-here
     JWT_SECRET=your-jwt-secret-here
     ```

2. **Testing**
   - Test rate limiting in staging
   - Validate security headers
   - Test SSRF protection with various URLs

### Production

1. **HTTPS Only**
   - Use SSL/TLS certificates
   - Redirect HTTP to HTTPS
   - Configure HSTS headers

2. **Redis for Rate Limiting**
   - Persistent rate limit storage
   - Distributed across instances
   - Better performance

3. **Monitoring**
   - Log rate limit violations
   - Monitor failed validations
   - Alert on suspicious patterns

4. **Regular Updates**
   - Keep dependencies updated
   - Monitor security advisories
   - Apply security patches promptly

## Security Checklist

Before deploying to production:

- [ ] HTTPS configured and enforced
- [ ] Rate limiting enabled with Redis
- [ ] All security headers applied
- [ ] File upload validation tested
- [ ] SSRF protection verified
- [ ] Secrets moved to environment variables
- [ ] Logging configured for security events
- [ ] Monitoring and alerting set up
- [ ] Backup and disaster recovery plan
- [ ] Security audit completed

## Incident Response

If you detect a security issue:

1. **Immediate Actions**
   - Block the attacking IP
   - Review logs for impact
   - Isolate affected systems

2. **Investigation**
   - Analyze attack pattern
   - Check for data breach
   - Assess damage

3. **Remediation**
   - Patch vulnerabilities
   - Update security rules
   - Restore from backup if needed

4. **Post-Incident**
   - Document incident
   - Update security measures
   - Conduct security review

## Contact

For security concerns or to report vulnerabilities:
- Create a security advisory on GitHub
- Email: security@your-domain.com (configure your contact)
- Use responsible disclosure practices

## License

Security features are part of the main application license.
