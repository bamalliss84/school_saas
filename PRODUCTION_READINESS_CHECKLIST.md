# Production Readiness Checklist

## Verified in acceptance

- [x] PostgreSQL migrations applied through core 0023.
- [x] Django check passes.
- [x] Core tests pass and coverage is at least 93%.
- [x] Ruff and OpenAPI validation pass.
- [x] Health, documentation, protected API, and Admin smoke behavior verified.
- [x] No remaining runserver process or generated coverage artifact.
- [x] Tenant, role, membership, IDOR, historical-write, workflow, attachment, and after-commit behaviors covered by tests.

## Deployment-specific work

- [ ] Set a strong production `SECRET_KEY`.
- [ ] Enable HTTPS redirect and appropriate HSTS after TLS/proxy validation.
- [ ] Configure allowed hosts, trusted origins, database backups, monitoring, log retention, static/media storage, and provider credentials through secrets management.
- [ ] Run deployment smoke tests with the real proxy, storage, and delivery providers.
