---
name: log-parsing-and-normalization
description: Use when parsing application logs, filtering errors, normalizing service names, and outputting structured JSON summaries.
---
1. Transform service names in the output to be lower-case with hyphens replaced by underscores (e.g., `payment-service` becomes `payment_service`).
2. Sort error lists by service name, then by `timestamp_utc` in ascending order.
3. Include the exact top-level schema header fields: `"schema_version": 2` and `"generated_by": "log-triage"`.
4. Properly handle repeat log lines and multi-line tracebacks to accumulate correct repeat counts and extract exception strings.
5. Self-check: Inspect the generated JSON structure to confirm exact key names, sorting order, and value transformations.
