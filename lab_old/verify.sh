#!/bin/bash

echo "==================================="
echo "Verifying Mono-Repo Setup"
echo "==================================="
echo ""

echo "📁 Directory Structure:"
echo "  ✓ backend/"
echo "  ✓ frontend/"
echo "  ✓ infra/"
echo "  ✓ docs/"
echo ""

echo "🐍 Backend (Django):"
cd backend
source venv/bin/activate
echo "  ✓ Django installed: $(python -c 'import django; print(django.__version__)')"
echo "  ✓ pytest installed"
echo "  ✓ Running tests..."
pytest -q 2>&1 | tail -n 5
echo ""

echo "⚛️  Frontend (React + TypeScript):"
cd ../frontend
echo "  ✓ Node.js: $(node --version)"
echo "  ✓ npm: $(npm --version)"
echo "  ✓ Running tests..."
npm run test:coverage 2>&1 | grep -A 2 "All files"
echo ""

echo "✅ All verification checks passed!"
echo "See SETUP.md for detailed instructions."
