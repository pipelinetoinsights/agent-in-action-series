---
name: data-quality-runbook
description: Runs the standard pre-publish data quality checks on a table before
  promoting it to the gold layer. Use when asked to validate, QA, or
  quality-check a table, or before publishing a table to production.
---

# Data Quality Runbook

Follow this procedure whenever asked to quality-check a table before publishing.
Do not skip steps. Report results as a short summary at the end.

## Step 1: Run the automated checks

Run the bundled validation script on the target table:

```
python scripts/run_checks.py --table <table_name>
```

This checks for: row count > 0, no fully-null columns, and primary key
uniqueness. Read only the script's output — you do not need to read its code.

## Step 2: Apply schema-specific thresholds

Different schemas have different tolerances. Read `thresholds.md` and apply the
freshness and null-rate thresholds for the table's schema.

## Step 3: Decide and report

- If all checks pass: report "PASS" and confirm the table is safe to publish.
- If any check fails: report "FAIL", list the exact checks that failed, and do
  NOT recommend publishing. Suggest the engineer post in #data-incidents.

Always end with a one-line summary: PASS or FAIL plus the table name.
