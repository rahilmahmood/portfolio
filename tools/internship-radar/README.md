# Internship Radar source cache

This is the machine-readable source layer for the six canary employers in Rahil's engineering internship tracker.

It fetches public career inventories directly from Tesla Careers, Greenhouse, Blue Origin Workday, and Apple Jobs every six hours. Each source must reconcile its provider-reported count to a unique stable-ID set before the snapshot is accepted. A failed source preserves the previous last-good inventory, records a source error, and suppresses removal deltas rather than turning a fetch failure into zero openings.

Generated state lives in `internship-radar-state/`:

- `status.json`: compact source health, counts, and fingerprints.
- `delta.json`: board, internship, and cohort ID-set changes since the prior state.
- `latest.json`: normalized last-good inventories plus source status.

The source layer stores only public job-board data and no credentials or personal tracker data.
