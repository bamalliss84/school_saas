# AGENT_OPERATING_MODEL.md
# How Codex and Antigravity must work

## Start-of-task instruction

Instead of pasting a long prompt every time, tell the agent:

### Codex
`Read SCHOOL_SAAS_MASTER_EXECUTION_PLAN.md and PROJECT_EXECUTION_BOARD.md. Execute only the task marked 🟢 ACTIVE for Codex. Follow all gates and stop with the required handoff report.`

### Antigravity
`Read SCHOOL_SAAS_MASTER_EXECUTION_PLAN.md and PROJECT_EXECUTION_BOARD.md. Execute only the task marked 🟢 ACTIVE for Antigravity. Follow all gates and stop with the required handoff report.`

The agent must not choose the next task itself.

## Task completion
Agent returns:
- summary
- exact changed files
- API/backend changes
- migrations
- tests
- runtime evidence
- screenshots/video where required
- git commit hash if worktrees are active
- remaining gaps

The Supervisor:
1. reviews evidence;
2. asks for fixes if needed;
3. marks DONE only after acceptance;
4. changes the next row to 🟢 ACTIVE.

## Cross-track dependency
If an agent needs a Backend contract not yet integrated:
- stop that specific path;
- create a Backend change request;
- continue only unrelated work;
- do not invent endpoint behavior.

## No invisible coordination
Codex must not assume what Antigravity changed.
Antigravity must not assume what Codex changed.
`main` after Supervisor integration is the shared truth.
