$ErrorActionPreference = "Stop"

Write-Host "Running SDK release checks..." -ForegroundColor Cyan

Write-Host "`n1. Running tests..."
python -m pytest -q

Write-Host "`n2. Checking formatting..."
python -m ruff format --check .

Write-Host "`n3. Checking lint..."
python -m ruff check .

Write-Host "`n4. Building package..."
python -m build

Write-Host "`n5. Validating package..."
python -m twine check dist/*

Write-Host "`nAll release checks passed!" -ForegroundColor Green
