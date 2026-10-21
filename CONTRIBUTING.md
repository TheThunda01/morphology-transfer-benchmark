# Contributing

Keep changes reproducible and make the biological boundary easy to understand. Describe the question, the source data and the expected result in a pull request; include the commands you ran.

Run `python -m unittest discover -s tests -v`, produce a fresh output with `python -m morphology --output reproduced-results`, and run `python scripts/check_reproduction.py reproduced-results`. Tests check scientific boundaries such as control-only fitting, compound separation and ineligible retrieval queries, as well as exact input integrity. Reproduction compares numeric values with tolerance; figure bytes need not match across platforms.

Do not replace pinned data or configuration silently. A new extract needs a source version, object hashes, retained license, updated data dictionary and visible inclusion/exclusion counts. Preserve the existing benchmark as a versioned reference if model choices are informed by its test scores. Keep same-identity grouping, training-only transforms and explicit missing/unsupported outcomes intact.

Support biological claims with inspected primary literature, distinguish a measured phenotype from a mechanistic interpretation, and record uncertainty or conflicting metadata. Please do not include patient records, credentials, or claims of clinical validation.
