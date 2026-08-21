# Results UI Closure patch

Scope: Flutter-only patch on top of Homework Attachments bbed125.

- Dynamic ExamType ChoiceChips; only types present in cached/current result data are shown.
- Known types are ordered Quiz, Monthly, Midterm, Term, Final; unknown school-defined types remain dynamic and follow them.
- Term + Subject + ExamType filters combine in ResultsReady.visible.
- Exam type is rendered as a compact badge on result cards.
- Score labels use Arabic-safe `score من max` in list/detail; Homework already uses the same form.
- Selected term/subject rendering avoids ellipsis in the closed field while dropdown items retain their full labels.
- No backend, migration, repository/cache schema, or Homework attachment behavior changed.
- Historical/context switching remains out of scope.
