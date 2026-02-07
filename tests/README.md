# Testing Guide

## Overview

Comprehensive test suite for Problem Hunter covering unit tests and integration tests.

## Test Structure

```
tests/
├── __init__.py
├── run_tests.py              # Test runner
├── test_cache.py             # Cache module tests
├── test_aggregator.py        # Aggregator module tests
├── test_database.py          # Database module tests
├── test_trend_analyzer.py    # Trend analyzer tests
└── test_integration.py       # End-to-end integration tests
```

## Running Tests

### Run All Tests
```bash
cd tests
python run_tests.py
```

### Run Specific Test File
```bash
python -m unittest tests.test_cache
python -m unittest tests.test_aggregator
python -m unittest tests.test_database
python -m unittest tests.test_trend_analyzer
python -m unittest tests.test_integration
```

### Run Single Test Case
```bash
python -m unittest tests.test_cache.TestCache.test_ttl_expiration
```

## Test Coverage

### Unit Tests

#### `test_cache.py` (10 tests)
- ✅ Post cache save and get
- ✅ Cache miss handling
- ✅ TTL expiration
- ✅ Analysis caching
- ✅ Source-specific caching
- ✅ Clear source cache
- ✅ Clear expired entries
- ✅ Statistics tracking

#### `test_aggregator.py` (9 tests)
- ✅ Single source success
- ✅ Multiple sources parallel
- ✅ Graceful error handling
- ✅ Post validation
- ✅ Deduplication
- ✅ Sort posts
- ✅ Filter posts
- ✅ Statistics tracking

#### `test_database.py` (5 tests)
- ✅ Save and get post
- ✅ Save analysis
- ✅ Get statistics
- ✅ Duplicate post update

#### `test_trend_analyzer.py` (5 tests)
- ✅ Normalize problem
- ✅ Problem hash generation
- ✅ Track problem
- ✅ Emerging trends detection
- ✅ Threshold filtering

### Integration Tests

#### `test_integration.py` (3 tests)
- ✅ Complete pipeline (fetch → analyze → store → trends)
- ✅ Parallel fetching performance
- ✅ Deduplication across sources

## Test Utilities

### Mock Objects
- `MockSource` - Simulates data source for testing
- Mock AI analysis responses

### Temporary Resources
- Temporary databases (auto-cleanup)
- Temporary cache directories (auto-cleanup)

## CI/CD Integration

Add to GitHub Actions:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: cd tests && python run_tests.py
```

## Writing New Tests

### Template
```python
import unittest

class TestNewFeature(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        pass
    
    def tearDown(self):
        """Clean up after tests."""
        pass
    
    def test_feature(self):
        """Test description."""
        # Arrange
        # Act
        # Assert
        self.assertEqual(expected, actual)

if __name__ == '__main__':
    unittest.main()
```

## Known Limitations

- AI analysis tests use mocks (no real API calls)
- Source tests don't hit real APIs (use mocks)
- Performance tests are relative, not absolute

## Future Improvements

- Add coverage reporting (pytest-cov)
- Add performance benchmarks
- Add load testing
- Add UI testing (Selenium/Playwright)
