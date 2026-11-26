---
name: nf-executive-summary
description: "Create a stakeholder-facing executive summary from an approved new-feature spec and design before task decomposition. Always write the Markdown summary, then ask whether a PDF is needed. When generating PDF, use an existing project/global reference PDF only as a visual branding reference, cache extracted style data with SHA-256 invalidation, and fall back to the skill's built-in standard style when no reference exists."
---

# NF Executive Summary

Create a concise, management-ready summary from the approved feature artifacts. This skill sits after design approval and before `nf-tasks` in the `new-feature` workflow.

The Markdown artifact is mandatory. PDF is optional and must be explicitly offered after the Markdown file is created.

## Audience

Write primarily for:

- project managers;
- product owners;
- delivery stakeholders;
- non-implementation technical stakeholders;
- leadership that needs scope, impact, risk, and rollout context without a file-by-file engineering plan.

## Source of truth

Use the approved artifacts as authoritative inputs:

- `<projectFolder>/_localnotes/<featureShortName>/specs.md`;
- `<projectFolder>/_localnotes/<featureShortName>/design.md`;
- `<projectFolder>/_localnotes/<featureShortName>/decisions.md` when relevant.

Do not introduce new scope, requirements, architecture decisions, dates, commitments, or estimates that are not supported by those sources. Clearly label unresolved items.

`executive-summary.md` is a communication artifact, not an implementation source of truth. `nf-tasks` must continue to derive task decomposition from the approved design/spec, not from this summary.

## Workflow

1. Confirm inputs
- Require an approved design and its approved spec.
- Capture `projectFolder` and `featureShortName`.
- Read relevant material decisions when they materially affect scope, risk, rollout, dependencies, or stakeholder expectations.
- If approval status is unclear, do not present a final executive summary as approved-state documentation.

2. Draft the stakeholder summary
- Translate technical language into concise stakeholder-facing language.
- Preserve exact product/business behavior, constraints, risks, dependencies, and rollout implications from the approved artifacts.
- Avoid task IDs, file-by-file implementation details, class names, low-level storage details, and internal mechanics unless they materially affect scope, risk, delivery, compliance, operations, or stakeholder expectations.
- Scale depth to the feature: small/local changes may be approximately half a page; substantial features may need several pages.

3. Write Markdown
- Default output: `<projectFolder>/_localnotes/<featureShortName>/executive-summary.md`.
- Markdown is always the primary artifact and must be created even when PDF is requested.
- Do not add an approval gate for the executive summary unless the user explicitly requests one.

4. Ask about PDF
- After the Markdown file has been written, ask whether a PDF version is needed unless the invoking parent workflow already has an explicit PDF preference for this feature.
- Reuse a known prior preference when regenerating after an upstream change: regenerate the PDF automatically if it was previously requested; do not repeatedly ask if it was previously declined unless the user changes that preference.
- If the user declines, return control to the parent workflow so `nf-tasks` can continue.
- If the user accepts, generate `<projectFolder>/_localnotes/<featureShortName>/executive-summary.pdf` from the same summary content. Do not independently rewrite the content for PDF.

5. Resolve PDF branding
Use the first available source in this order:

1. an explicit reference PDF path supplied by the user for this run;
2. project override: `<repo>/.ai/templates/executive-summary/reference.pdf`;
3. global override: `~/.ai/templates/executive-summary/reference.pdf`;
4. built-in skill style: `assets/standard-style.json`.

A reference PDF is a visual reference only. Never edit, overwrite, fill, stamp, or otherwise write into the reference PDF.

6. Reference-PDF analysis and cache
- Render/inspect the reference PDF before deriving branding from it.
- Extract only reusable visual characteristics such as page size, margins, dominant/accent colors, logo/mark imagery when reusable, heading/body hierarchy, header/footer treatment, rules, tables/callouts, and spacing.
- Never extract, copy, or redistribute embedded font binaries.
- Cache derived project branding under `<repo>/.ai/cache/executive-summary/`.
- Cache derived global branding under `~/.ai/cache/executive-summary/`.
- The cache must include `style-cache.json` and may include derived reusable image assets such as `assets/logo.png`.
- Store the SHA-256 of the source reference PDF in the cache along with the cache schema version.
- Before every reuse, recompute the reference PDF SHA-256. Rebuild the cache if the hash differs, the cache schema version differs, required cached assets are missing, or the source PDF is no longer the same resolved reference.
- Do not use a stale cache when the reference PDF is missing; continue down the branding precedence chain instead.

7. Font handling
- Record font family names/style characteristics only when detectable.
- Use the matching locally available font when legally and technically available.
- Otherwise use a safe substitute defined by the built-in style rules while preserving relative hierarchy, weight, size, and spacing.
- Record substitutions in the style cache where useful.
- Never extract or share font files from the reference PDF.

8. Generate and verify PDF
- Create a new PDF; do not modify the reference PDF.
- Prefer the available document/PDF generation path that produces a stable text-heavy business document.
- Preserve Markdown content semantics, heading order, tables, lists, and callouts.
- Render the generated PDF to images and visually verify that there is no clipping, overlap, missing glyphs, broken logo rendering, unreadable contrast, or malformed pagination.
- If branded PDF generation cannot be completed reliably, keep the Markdown artifact, explain the blocker, and do not fabricate a successful PDF result.

## Required Markdown Sections

Use these sections in this order unless the user explicitly requests a different stakeholder format:

1. Executive Overview
2. Why We Are Doing This
3. What Will Change
4. User / Business Impact
5. In Scope
6. Out of Scope
7. Delivery Approach
8. Dependencies and Assumptions
9. Risks and Mitigations
10. Testing and Acceptance
11. Rollout / Operational Impact
12. Open Decisions or Questions

Omit empty boilerplate. When a section genuinely has nothing material to report, use a short `None identified` / `Not applicable` statement rather than inventing content.

## Output Convention

Primary:

```text
<projectFolder>/_localnotes/<featureShortName>/executive-summary.md
```

Optional PDF:

```text
<projectFolder>/_localnotes/<featureShortName>/executive-summary.pdf
```

Project branding override:

```text
<repo>/.ai/templates/executive-summary/reference.pdf
```

Global branding override:

```text
~/.ai/templates/executive-summary/reference.pdf
```

Derived project cache:

```text
<repo>/.ai/cache/executive-summary/style-cache.json
<repo>/.ai/cache/executive-summary/assets/*
```

Built-in fallback:

```text
skills/nf-executive-summary/assets/standard-style.json
```

## Quality Gate

Before returning the Markdown artifact, verify:

- content is traceable to the approved spec/design/decisions;
- no new requirements or commitments were invented;
- scope and out-of-scope statements match approved artifacts;
- risks/dependencies/rollout implications are understandable without implementation-level context;
- unresolved decisions are clearly called out;
- low-level technical detail is included only when stakeholder-relevant;
- the Markdown file exists at the reported path;
- the user is asked whether a PDF is needed.

Before returning a PDF, additionally verify:

- branding precedence was resolved correctly;
- a reference PDF, when used, was treated only as a visual source;
- cache validity was checked using SHA-256 plus cache schema version;
- no embedded font binary was extracted/reused;
- generated PDF was rendered and visually checked;
- PDF content matches the Markdown source.
