# Module 10 — Test Report

## 1. Testing Objective

Verify that the Stock Movement Context Dashboard follows the business rules defined in `BUILD_SPEC.md`.

## 2. Tests Performed

The project contains **13 automated tests**, including 11 existing tests and 2 new tests added for Module 10.

### Test 1: Period Filtering

- **Business Rule:** Changing the selected period must not recalculate existing flags.
- **Test Data:** Three AAPL trading dates across 2024 and 2025.
- **Expected Result:** Only the flagged date (2025-01-02) is returned when filtering for 2025.
- **Actual Result:** PASS

### Test 2: News Date Window

- **Business Rule:** News must fall within D-7 through D, inclusive. Future news must be excluded.
- **Test Data:** Four AAPL news records dated January 1, 2, 9, and 10, 2025.
- **Expected Result:** January 2 and January 9 are included for the selected date January 9, 2025.
- **Actual Result:** PASS

## 3. Test Execution

**Command:**

```bash
PYTHONPATH=src python -m pytest -q --tb=short
```

**Results:**

| Metric | Result |
|---|---|
| Total Tests | 13 |
| Passed | 13 |
| Failed | 0 |
| Execution Time | 1.33 seconds |

## 4. Additional Existing Test Coverage

The existing test suite checks:

- Adjusted prices for indexed performance and summaries
- Flag preservation and cross-stock flag counts
- News and filing context
- Validation of inconsistent or duplicate data
- Missing files and empty datasets
- Full-range period selection
- Ticker consistency

## 5. Limitations

- Passing unit tests does not guarantee that every dashboard interaction works correctly.
- The two new tests use small synthetic datasets rather than the complete production dataset.
- Full end-to-end browser interaction testing was not performed.

## 6. Conclusion

All **13 automated tests passed**.

The tested business rules behaved as expected for the supplied test cases. Additional end-to-end testing would provide further confidence in the dashboard.
