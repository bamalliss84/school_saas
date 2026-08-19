# Student V1 Closure — Phase 1 Results

Baseline: `c2ebac7`.

## Review result
The backend already supports a school-configurable `ExamType` (`name`, `code`, `max_score`, `weight_percentage`) and does not contain an official grade-scale / تقدير model. Therefore V1 exposes the real exam type and does not invent Arabic grade labels from percentages.

## Changes
- Added `exam_type_id`, `exam_type_name`, `exam_type_code` to `ExamResultSerializer`.
- Flutter parses and displays the configured exam type in list/detail.
- Preserved score / total / percentage, term/subject filters, publication rules, active academic-year scope, historical read-only and scoped Drift cache.
- Added parser regression coverage for exam type metadata.

## Results acceptance demo dataset
`seed_demo_school` now creates deterministic Results V1 acceptance scenarios for `demo_student_a_01`: short quiz, monthly, midterm, term and final published results across Mathematics/Science/Arabic, including teacher feedback. It also creates one approved-but-unpublished result that must remain hidden. `demo_student_transferred` has a published historical result in its real historical School A context.

The seeder remains idempotent and its regression snapshot now includes exams/results so duplicate result creation is detected.

## Acceptance pending
Short emulator smoke: run the demo seed, verify the five published current results and filters, confirm the unpublished result is absent, then verify the transferred student's historical result and Offline cache.
