---
name: post-schema-normalizer-and-migrator
description: Use when converting older Halting Problems posts or event profiles to the current threat-post schema and validating feed compatibility.
---

# Post Schema Normalizer And Migrator

## Mission

Normalize older posts and machine-readable profiles to the current feed contract.

## Tasks

- Convert old Format B arrays to current event profile object.
- Normalize field names.
- Preserve raw IOCs only in machine-readable JSON.
- Defang prose and YAML network IOCs.
- Validate frontmatter and sourceCount.
- Add missing remediation gates and detection hunt recipe placeholders when evidence supports them.

## Required Output

```yaml
migration_report:
  input_file: ""
  output_file: ""
  detected_format: ""
  changes_made: []
  warnings: []
  validation_status: "pass|fail|needs_review"
```
