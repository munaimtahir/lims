import os

with open('.env.production.example', 'r') as f:
    content = f.read()

content = content.replace('your-production-secret-key-here-change-this-immediately', 'test-secret-key')
content = content.replace('your-secure-postgres-password-change-this-immediately', 'test-db-password')
content = content.replace('ALLOWED_HOSTS=lims.alshifalab.pk', 'ALLOWED_HOSTS=localhost,127.0.0.1')
content = content.replace('CORS_ALLOWED_ORIGINS=https://lims.alshifalab.pk', 'CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000')
content = content.replace('CSRF_TRUSTED_ORIGINS=https://lims.alshifalab.pk', 'CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000')

with open('.env.production', 'w') as f:
    f.write(content)
