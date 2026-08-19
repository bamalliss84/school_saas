# Student V1 Closure — Phase 1 Results

Baseline: `c2ebac7`.

## Review result
The backend already supports a school-configurable `ExamType` (`name`, `code`, `max_score`, `weight_percentage`) and does not contain an official grade-scale / تقدير model. Therefore V1 exposes the real exam type and does not invent Arabic grade labels from percentages.

## Changes
- Added `exam_type_id`, `exam_type_name`, `exam_type_code` to `ExamResultSerializer`.
- Flutter parses and displays the configured exam type in list/detail.
- Preserved score / total / percentage, term/subject filters, publication rules, active academic-year scope, historical read-only and scoped Drift cache.
- Added parser regression coverage for exam type metadata.

## Acceptance pending
Short emulator smoke only: list, detail, filters, offline cache, historical context if demo data is available.
