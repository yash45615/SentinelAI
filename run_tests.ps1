$ErrorActionPreference = "Stop"

Write-Host "====================================="
Write-Host "       SentinelAI Test Suite"
Write-Host "====================================="

Write-Host ""
Write-Host "[1/4] Running complete test suite..."

pytest -q

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "TEST SUITE FAILED."
    exit 1
}

Write-Host ""
Write-Host "[2/4] Running RCA tests..."

pytest -q tests/unit/test_rca_engine.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "RCA tests failed."
    exit 1
}

Write-Host ""
Write-Host "[3/4] Running reliability tests..."

pytest -q tests/unit/test_recovery_verifier.py tests/unit/test_chaos_engine.py tests/unit/test_slo_engine.py tests/unit/test_load_test_engine.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Reliability tests failed."
    exit 1
}

Write-Host ""
Write-Host "[4/4] Running security tests..."

pytest -q tests/unit/test_security.py tests/unit/test_security_middleware.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Security tests failed."
    exit 1
}

Write-Host ""
Write-Host "====================================="
Write-Host " SentinelAI CI GATE PASSED"
Write-Host "====================================="