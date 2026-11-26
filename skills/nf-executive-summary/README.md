# NF Executive Summary

Purpose: create the stakeholder-facing communication artifact between approved design and `nf-tasks`.

## Default behavior

- reads the approved `specs.md`, `design.md`, and relevant `decisions.md`;
- always writes `_localnotes/<feature>/executive-summary.md`;
- translates the approved feature into PM/product/stakeholder language;
- does not become the source for task decomposition;
- asks whether a PDF version is needed after Markdown is created;
- creates a new PDF when requested, never writes into a reference PDF;
- uses project/global branding references when present and otherwise uses the skill's built-in standard style.

## PDF branding precedence

```text
explicit reference PDF for this run
-> <repo>/.ai/templates/executive-summary/reference.pdf
-> ~/.ai/templates/executive-summary/reference.pdf
-> assets/standard-style.json
```

Derived branding is cached locally. The cache stores the reference PDF SHA-256 and schema version, so replacing the PDF automatically invalidates and rebuilds the extracted style data.

Embedded font files are never extracted or redistributed. If a referenced font is unavailable, use a safe substitute while preserving the visual hierarchy.

## Example prompts

- `Use nf-executive-summary for customer-import from the approved specs.md and design.md.`
- `Generate the executive summary and also create the PDF version.`
- `Use .ai/templates/executive-summary/reference.pdf as the branding reference.`
