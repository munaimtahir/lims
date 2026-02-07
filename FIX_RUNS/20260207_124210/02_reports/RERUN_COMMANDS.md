# Test Rerun Commands

## Full Test Suite
```bash
cd /home/munaim/srv/apps/lims/lims-backend && \
source .venv/bin/activate && \
pytest -q
```

## Only Failing Tests (7 tests)
```bash
cd /home/munaim/srv/apps/lims/lims-backend && \
source .venv/bin/activate && \
pytest -q \
  apps/laboratory/tests/test_parameter_validation.py::TestExcelImportParameterValidation::test_import_invalid_parameter_id_format \
  apps/laboratory/tests/test_parameter_validation.py::TestExcelImportParameterValidation::test_import_mapping_with_missing_parameter_id \
  apps/laboratory/tests/test_parameter_validation.py::TestExcelImportParameterValidation::test_import_mapping_with_invalid_parameter_id_format \
  apps/results/tests/test_results.py::TestTestResultViewSet::test_verify_result \
  apps/samples/tests/test_samples.py::TestSampleViewSet::test_create_sample \
  apps/samples/tests/test_services.py::SampleGenerationTestCase::test_ensure_samples_wrapper_function \
  apps/samples/tests/test_services.py::SampleGenerationTestCase::test_idempotency_no_duplicate_samples
```

## By Category

### Parameter Import Tests (3 failures)
```bash
cd /home/munaim/srv/apps/lims/lims-backend && \
source .venv/bin/activate && \
pytest -q -k "parameter" apps/laboratory/tests/test_parameter_validation.py
```

### Results Tests (1 failure)
```bash
cd /home/munaim/srv/apps/lims/lims-backend && \
source .venv/bin/activate && \
pytest -q apps/results/tests/test_results.py::TestTestResultViewSet::test_verify_result
```

### Sample Tests (3 failures)
```bash
cd /home/munaim/srv/apps/lims/lims-backend && \
source .venv/bin/activate && \
pytest -q \
  apps/samples/tests/test_samples.py::TestSampleViewSet::test_create_sample \
  apps/samples/tests/test_services.py::SampleGenerationTestCase::test_ensure_samples_wrapper_function \
  apps/samples/tests/test_services.py::SampleGenerationTestCase::test_idempotency_no_duplicate_samples
```

## Verbose Output (for debugging)

### Full suite with verbose output:
```bash
cd /home/munaim/srv/apps/lims/lims-backend && \
source .venv/bin/activate && \
pytest -v
```

### Specific test with full output:
```bash
cd /home/munaim/srv/apps/lims/lims-backend && \
source .venv/bin/activate && \
pytest -vv -s apps/results/tests/test_results.py::TestTestResultViewSet::test_verify_result
```

## Coverage Report

### Run tests with coverage:
```bash
cd /home/munaim/srv/apps/lims/lims-backend && \
source .venv/bin/activate && \
pytest --cov=apps --cov-report=html --cov-report=term
```

### View coverage report:
```bash
open /home/munaim/srv/apps/lims/lims-backend/htmlcov/index.html
```

## Continuous Testing

### Watch mode (requires pytest-watch):
```bash
cd /home/munaim/srv/apps/lims/lims-backend && \
source .venv/bin/activate && \
ptw -- -q
```

### Run only changed tests:
```bash
cd /home/munaim/srv/apps/lims/lims-backend && \
source .venv/bin/activate && \
pytest --lf -q  # Last failed
```

```bash
cd /home/munaim/srv/apps/lims/lims-backend && \
source .venv/bin/activate && \
pytest --ff -q  # Failed first
```

## Performance Profiling

### Show slowest tests:
```bash
cd /home/munaim/srv/apps/lims/lims-backend && \
source .venv/bin/activate && \
pytest --durations=10
```

### Profile test execution:
```bash
cd /home/munaim/srv/apps/lims/lims-backend && \
source .venv/bin/activate && \
pytest --profile
```

## Output to File

### Save test results:
```bash
cd /home/munaim/srv/apps/lims/lims-backend && \
source .venv/bin/activate && \
pytest -q 2>&1 | tee test_results_$(date +%Y%m%d_%H%M%S).txt
```

### Save only failures:
```bash
cd /home/munaim/srv/apps/lims/lims-backend && \
source .venv/bin/activate && \
pytest -q --tb=short 2>&1 | grep -A 20 "FAILED" > failures.txt
```

## CI/CD Integration

### Run in CI mode (no color, machine-readable):
```bash
cd /home/munaim/srv/apps/lims/lims-backend && \
source .venv/bin/activate && \
pytest --color=no --tb=short --junitxml=test-results.xml
```

### Generate JSON report:
```bash
cd /home/munaim/srv/apps/lims/lims-backend && \
source .venv/bin/activate && \
pytest --json-report --json-report-file=test-report.json
```
