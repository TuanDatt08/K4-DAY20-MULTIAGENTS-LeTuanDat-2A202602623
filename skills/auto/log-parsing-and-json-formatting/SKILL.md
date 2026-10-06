---
name: log-parsing-and-json-formatting
description: Use when parsing log files, extracting structured errors, and formatting JSON outputs.
---
1. Format all service names in the output strictly as lower-case with hyphens replaced by underscores (e.g., `payment-service` becomes `payment_service`).
2. Sort the `errors` array in the output object by `service`, then by `timestamp_utc`, ascending.
3. Ensure the top-level JSON object contains exact schema keys: `"schema_version": 2` and `"generated_by": "log-triage"`.
4. Handle multi-line tracebacks and repeat lines (`-- last message repeated N times --`) correctly by accumulating repeat counts.
5. Self-check: Read back generated JSON files to verify sort order, key naming, and schema conformance.
