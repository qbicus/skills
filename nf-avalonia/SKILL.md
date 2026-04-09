---
name: nf-avalonia
description: "Support the `new-feature` workflow for Avalonia desktop UI work. Use when a feature includes Avalonia, cross-platform desktop UI, XAML views, MVVM/viewmodels, desktop navigation or windowing, styling/themes, tray behavior, desktop dialogs, or platform-specific desktop integrations."
---

# NF Avalonia

Provide Avalonia-specific guidance inside the `new-feature` chain. Do not replace `nf-spec`, `nf-design`, or `nf-tasks`; strengthen them when the feature includes Avalonia UI.

Use the structure in [references/avalonia-checklist.md](references/avalonia-checklist.md) when a focused design or execution checklist is helpful.

## Integration Points

### During `nf-spec`
- Capture target platforms explicitly: Windows only, or Windows/Linux/macOS.
- Define the desktop UX surface: windows, dialogs, navigation model, tray behavior, file pickers, notifications, startup flow, and offline behavior where relevant.
- Record UI architecture expectations at a high level: MVVM, shell structure, state ownership, and whether views are reused across platforms.
- Note platform-specific capabilities or constraints such as file-system access, native integrations, packaging, auto-start, or single-instance behavior.
- Make non-functional expectations explicit: startup time, responsiveness, long-running task handling, and accessibility expectations if relevant.

### During `nf-design`
- Favor clear view/viewmodel boundaries and keep business logic out of code-behind unless there is a narrow UI-only reason.
- Define threading and dispatcher boundaries for UI updates from background work.
- Specify navigation, window lifecycle, dialog orchestration, and shared state ownership.
- Define theming/styling strategy, asset loading, and resource organization.
- Call out platform abstractions when desktop integrations differ by OS.
- Identify testing boundaries for viewmodels, UI services, and platform adapters.

### During `nf-tasks`
- Split work into shell/app bootstrap, views, viewmodels, UI services, platform adapters, styling/resources, and tests when those slices exist.
- Mark parallel-safe UI tasks carefully; avoid parallelizing work that shares the same navigation shell, resource dictionaries, or common viewmodel contracts unless dependencies are explicit.
- Include packaging or distribution tasks when desktop delivery is in scope.

### During execution
- Preserve existing Avalonia patterns in the repository before introducing new ones.
- Prefer small, testable viewmodels and thin views.
- Keep bindings explicit and predictable.
- Treat OS-specific behavior as adapter/service boundaries instead of scattering conditionals through views.

## Guardrails

- Do not invent a custom UI architecture if the repo already has an Avalonia pattern.
- Do not put domain logic into views to move faster.
- Do not ignore cross-platform behavior when the spec says the app must run on multiple OS targets.
- Do not treat packaging, native dialogs, or file-system behavior as afterthoughts when they affect the user flow.
- If a requested UI change affects user-visible behavior or scope, feed that back into `nf-spec` or `nf-design` through `new-feature` approval gates.

## Output Rules

- When this skill is active, state which Avalonia concerns were applied to the spec, design, tasks, or execution.
- Keep Avalonia advice concrete: windows, viewmodels, threading, dialogs, resources, platform adapters, testing, packaging.
- If the feature is not actually Avalonia-based, do not use this skill.
