# Approval Protocol

## Gate semantics

Use three distinct gates:

1. Requirements approval permits design work.
2. Design approval permits task planning.
3. Task-plan approval permits implementation through `$execute-task-waves`.

At each gate:

- Summarize the artifact and validation result.
- List blocking open questions and material assumptions.
- Ask for explicit approval or edits.
- Stop. Do not interpret silence, praise, continued discussion, or approval of a different artifact as approval.

Accept unambiguous language such as:

- “Approve REQUIREMENTS.md.”
- “Requirements approved; proceed to design.”
- “Approve DESIGN.md.”
- “Design approved; create the tasks.”
- “Approve TASKS.md.”
- “Task plan approved; begin execution.”

On approval, update front matter when present:

```yaml
status: approved
approved_at: YYYY-MM-DD
```

Do not invent `approved_by`. Add it only when the user provides a stable identity to record.

## Material changes

Return the affected artifact to draft when a change alters scope, intended use, requirement behavior, safety controls, architecture, data boundaries, task dependencies, or release gates. Revalidate downstream artifacts and request renewed approval in order.

Editorial corrections that do not change meaning may retain approval, but report them.
