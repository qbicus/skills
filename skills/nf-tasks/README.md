# NF Tasks

Purpose: create the task-planning artifact for `new-feature`.

Use it when you want:
- ordered implementation tasks from an approved design
- sequential vs parallel-safe task planning
- quality checklist and verification planning

Default behavior:
- breaks work into small tasks
- marks dependencies, execution mode, and agent slots when parallel work is approved
- keeps `dev-todos.md` as a live tracker with task status updates during execution

Example prompts:
- `Use $nf-tasks with the approved design in _localnotes/customer-import/design.md and generate the task plan.`
- `Use $nf-tasks to revise _localnotes/customer-import/dev-todos.md based on these approval comments.`
- `Use $nf-tasks for customer-import. The design is already approved; resume task planning from the existing design.md file.`
