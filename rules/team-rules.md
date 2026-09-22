# Team AI Rules

## Working style

- Work incrementally.
- Prefer clear plans before large changes.
- Keep changes focused on the requested task.
- Ask for confirmation only when required by risk or ambiguity; otherwise make a reasonable best effort.
- When changing architecture, record the decision using the `decision` skill.
- When ending meaningful work, run `session-close`.

## Output expectations

For coding tasks, summarize:

- what changed;
- files touched;
- risks;
- tests run or tests to run;
- follow-up tasks.

## Safety rules

- Do not store secrets in generated docs.
- Do not commit local machine paths unless they are examples or templates.
- Do not include private credentials in project memory.
