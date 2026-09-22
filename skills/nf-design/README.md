# NF Design

Purpose: create the design-stage artifact for `new-feature`.

Use it when you want:
- file-by-file implementation design
- architecture, observability, rollout, and risk planning
- technical design from an approved spec

Default behavior:
- requires approved spec input
- produces a concrete implementation design

Example prompts:
- `Use $nf-design with the approved spec in _localnotes/customer-import/specs.md and create the design.`
- `Use $nf-design to revise _localnotes/customer-import/design.md using the review comments and keep the same approved spec.`
- `Use $nf-design for customer-import. The spec is already approved; resume design work from the existing specs.md file.`
