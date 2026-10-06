---
name: strict-schema-output-compliance
description: Use when processing datasets or log files to generate structured JSON outputs, CSV exports, or summary files with strict naming, formatting, and unit conventions.
---
<body>
1. Read the instructions, dataset dictionaries, and rule requirements completely before writing code or output files.
2. Apply all data transformations precisely (e.g., handling missing values, standardising date/time to UTC, normalizing region or service names by replacing hyphens or capitalization as requested).
3. Ensure numeric representations use the correct units (e.g., converting floating-point currency values to integer cents).
4. Include all required metadata blocks and schema headers with exact keys and types in the output JSON/files.
5. Verify output file paths and headers against the specification.
6. Self-check: Do all field names, formats, casing rules, metadata keys, and values match the required schema rules 100%?
