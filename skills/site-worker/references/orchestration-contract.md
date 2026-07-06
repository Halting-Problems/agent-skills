# Site Worker Orchestration Contract

## Inputs

At least one of:

- candidate source URL list
- research packet markdown
- event profile JSON
- existing post markdown
- source inventory table
- artifact identifiers

## Outputs

- work order JSON
- subagent task list
- merged evidence summary
- validation report
- final artifact paths

## State Machine

```text
candidate_intake
  -> dedupe_decision
  -> research_packet
  -> artifact_and_provenance_verification
  -> enrichment_and_audits
  -> detection_and_ioc_exports
  -> writing
  -> schema_normalization
  -> validation
  -> publish_decision
```

## Blocking Conditions

- no direct or primary source for affected artifact
- no affected package/version/digest/workflow identity
- `publication_state: reject`
- invalid machine-readable JSON
- unsupported actor attribution
- unresolvable critical source conflict
