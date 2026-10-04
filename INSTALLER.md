# AI Framework Installer — Implementation Checklist

Status: **implementation present — Windows live validation next, then Linux live validation**

The installer owns the global AI framework installation lifecycle for Codex and Claude while preserving unrelated user configuration, skills, MCP registrations, repository overrides, and project indexes.


## Implementation status snapshot — 2026-10-04

Implemented in this pass:

- shared lifecycle core: `installer/installer.py`;
- Windows bootstrap: `install.ps1`;
- Linux bootstrap: `install.sh`;
- Install / Update / Repair / Uninstall / Doctor command surfaces;
- Codex / Claude / both target selection;
- low / medium / high profile selection and persistence;
- prerequisite bootstrap for Git + `uv`;
- shared-skill linking while preserving unrelated skills;
- Codex native rendering + targeted TOML merge/restore;
- Claude native rendering + targeted JSON merge/restore;
- installer state under `~/.ai/local/installer-state.json`;
- Graphify installation/update through `uv tool install --upgrade graphifyy` plus per-client integration;
- AiIndex release download/checksum/extraction path with private Gitea token support;
- AiIndex MCP wiring for Codex and Claude where client capabilities permit;
- dry-run and non-interactive flags;
- initial Doctor/Status output;
- isolated Linux lifecycle tests and installer-core unit tests.

Still requiring real-environment validation/hardening before release:

- run the full lifecycle on the user's Windows Codex installation without losing existing config;
- verify Windows Git/uv bootstrap on a machine where either is absent;
- verify AiIndex private release asset names/API against an actual published release;
- verify Claude MCP/Graphify integration on a real Claude installation when desired;
- run the full Linux lifecycle on a real Linux machine;
- add deeper drift/hash reporting and model-availability probing to Doctor;
- decide/embed the canonical framework repository URL for one-line pipe bootstrap;
- optionally add shared-runtime purge/removal after the last client is uninstalled;
- complete platform matrix and failure-case tests below.

## 1. Supported operations

Implement four top-level operations:

- [ ] **Install**
- [ ] **Update / Repair**
- [ ] **Uninstall**
- [ ] **Doctor / Status**

`Update / Repair` is intentionally one operation: it upgrades installer-owned framework/runtime files when newer content exists and also reapplies/repairs missing, stale, or corrupted installer-owned wiring without disturbing unrelated user content.

Support both interactive and non-interactive usage.

Potential CLI shape:

```text
install --target codex|claude|both
update-repair --target codex|claude|both
uninstall --target codex|claude|both
doctor
```

Useful common options:

```text
--yes
--dry-run
--verbose
```

## 2. Platform support

- [ ] Windows x64
- [ ] Windows ARM64
- [ ] Linux x64
- [ ] Linux ARM64
- [ ] macOS x64
- [ ] macOS ARM64
- [ ] Detect OS automatically.
- [ ] Detect architecture automatically.
- [ ] Reject unsupported platforms cleanly.

## 3. Prerequisite detection

Check required prerequisites before installation.

### Git

- [ ] Detect `git`.
- [ ] Report detected version.
- [ ] If missing, offer automatic installation where supported.
- [ ] Use the platform's normal/safe installation path.
- [ ] Fail cleanly if Git cannot be installed automatically.

### uv

- [ ] Confirm whether Graphify requires `uv` in the final runtime design.
- [ ] Detect `uv`.
- [ ] Report detected version.
- [ ] If missing, offer automatic installation.
- [ ] Use the official supported `uv` installation method.
- [ ] Verify `uv` works after installation.

### Python

- [ ] Confirm whether direct Python installation is still required once `uv` is used.
- [ ] Detect Python only if required by Graphify or framework tooling.
- [ ] Avoid installing redundant runtimes unnecessarily.

### Other bootstrap dependencies

- [ ] Confirm whether `curl`, PowerShell 7, `tar`, or equivalent are required by platform.
- [ ] Prefer built-in platform tools where safe/reliable.
- [ ] Fail with a clear remediation message when a required bootstrap dependency is unavailable.

## 4. Detect client installations

### Codex

- [ ] Detect whether Codex CLI is installed.
- [ ] Detect Codex version where possible.
- [ ] Detect whether the AI framework is already wired into Codex.
- [ ] Detect whether AiIndex MCP is already registered with Codex.
- [ ] Detect whether any installer-owned Codex resources already exist.

### Claude

- [ ] Detect whether Claude Code is installed.
- [ ] Detect Claude Code version where possible.
- [ ] Detect whether the AI framework is already wired into Claude.
- [ ] Detect whether AiIndex MCP is already registered with Claude.
- [ ] Detect whether any installer-owned Claude resources already exist.

## 5. Pre-operation status summary

Before changing anything, show a concise status report:

```text
Git              installed / missing / version
uv               installed / missing / version
Codex            installed / missing / version
Claude           installed / missing / version
Shared .ai       installed / missing / version or commit
Codex wiring     present / missing
Claude wiring    present / missing
AiIndex CLI      present / missing / version
AiIndex MCP      Codex: yes/no, Claude: yes/no
Graphify         present / missing / healthy
Provider config  present / missing / valid
Skills           present / missing / drifted
```

- [ ] Show this before interactive install/update/uninstall.
- [ ] Reuse the same checks for doctor/status mode.

## 6. Target selection

For install/update/uninstall, support:

- [ ] Codex only
- [ ] Claude only
- [ ] Both

Interactive mode:

- [ ] Present only valid targets where practical.
- [ ] Warn when the selected client is not installed.
- [ ] Allow the user to cancel before changes are made.

Non-interactive mode:

```text
--target codex
--target claude
--target both
```

## 6A. Usage-profile selection

For each selected client:

- [ ] Offer `low`, `medium`, or `high`.
- [ ] Default/recommend `medium`.
- [ ] Explain `low` as quota/usage-saving and `high` as quality-first.
- [ ] Persist the installer-selected active profile in installer state and `~/.ai/local/provider-profiles.json` (or via `ai.py provider --set-profile`).
- [ ] Allow different profiles for Codex and Claude when target is `both`.
- [ ] During **Update / Repair**, allow keeping the current profile or switching profiles.
- [ ] Re-render native client wiring whenever the selected profile changes.
- [ ] Preserve repo-local generic/profile-specific overrides.

Non-interactive examples should support an explicit profile, for example:

```text
--target codex --profile medium
--target both --codex-profile low --claude-profile medium
```

## 7. Canonical global framework location

- [ ] Confirm canonical shared framework path under the user's home directory.
- [ ] Use `~/.ai` / equivalent as the shared runtime/config root.
- [ ] Ensure both Codex and Claude can reference the shared framework without duplicating the canonical source unnecessarily.
- [ ] Preserve user-owned files that are not installer-managed.

## 8. Framework installation / Update / Repair

- [ ] Clone the canonical framework/skills repository when absent.
- [ ] Update/pull the canonical repository during **Update / Repair** when already installed and installer-owned.
- [ ] Record installed commit/version.
- [ ] **Update / Repair** must re-apply missing/stale installer-owned files, regenerate client-native routing artifacts, and repair installer-owned registrations without deleting unrelated user content.
- [ ] Support a force-repair switch later if needed, without creating a separate reinstall lifecycle.
- [ ] Make **Update / Repair** idempotent and safe to run repeatedly.
- [ ] Do not duplicate skill registrations or config blocks.
- [ ] Install/update all provider usage profiles:
  - `providers/codex.yml` (medium/default)
  - `providers/codex.low.yml`
  - `providers/codex.high.yml`
  - `providers/claude.yml` (medium/default)
  - `providers/claude.low.yml`
  - `providers/claude.high.yml`
- [ ] Install/update shared skills, including `advisor`.
- [ ] Install/update helper scripts.
- [ ] Install/update `README.md` and `HELP.md`.

## 9. Codex wiring

- [ ] Configure Codex to see/use the shared skills/framework.
- [ ] Install/update only installer-owned Codex wiring.
- [ ] Wire provider routing/runtime integration.
- [ ] Register AiIndex MCP if selected/required.
- [ ] Verify AiIndex MCP registration.
- [ ] Verify expected skills are visible to Codex.
- [ ] Verify provider config is readable/valid.
- [ ] Preserve unrelated Codex settings, skills, and MCP registrations.

## 10. Claude wiring

- [ ] Configure Claude Code to see/use the shared skills/framework.
- [ ] Install/update only installer-owned Claude wiring.
- [ ] Wire provider routing/runtime integration.
- [ ] Register AiIndex MCP if selected/required.
- [ ] Verify AiIndex MCP registration.
- [ ] Configure/update required subagents/settings without replacing unrelated user content.
- [ ] Verify expected skills are visible to Claude.
- [ ] Verify provider config is readable/valid.
- [ ] Preserve unrelated Claude settings, skills, subagents, and MCP registrations.


### Generated native wiring

- [ ] Render Codex native agent/config files into `~/.ai/generated/codex/`.
- [ ] Render Claude native subagent/settings files into `~/.ai/generated/claude/`.
- [ ] Merge/reference generated files from client config without duplicating agent files where direct paths are supported.
- [ ] Preserve unrelated existing client agents/subagents/config sections.
- [ ] Re-render generated wiring during Update / Repair when provider config or framework renderer changes.

## 11. AiIndex installation

- [ ] Detect whether AiIndex CLI is already installed.
- [ ] Detect installed version.
- [ ] Resolve latest stable release by default.
- [ ] Support optional pinned version.
- [ ] Select correct OS/architecture artifact.
- [ ] Download release archive.
- [ ] Download checksum manifest.
- [ ] Verify SHA-256 before extraction.
- [ ] Abort on checksum mismatch.
- [ ] Install CLI and MCP runtime to a stable user-local path.
- [ ] Put `aiindex` on PATH or use a stable shim strategy.
- [ ] Verify `aiindex` CLI runs.
- [ ] Register `aiindex-mcp` with selected clients.
- [ ] Refresh an installer-owned MCP registration safely during update.
- [ ] Never remove or alter project `.ai-index.json`.
- [ ] Never remove or alter project `.ai-index/` data.

## 12. Graphify installation

- [ ] Confirm Graphify's exact runtime requirements.
- [ ] Detect whether Graphify is already installed/configured.
- [ ] Use `uv` for Graphify environment/dependency management where applicable.
- [ ] Install/update Graphify dependencies.
- [ ] Preserve user/repo Graphify data/config not owned by the installer.
- [ ] Verify Graphify is callable after installation.
- [ ] Add Graphify checks to doctor/status.

## 13. Provider configuration installation

- [ ] Install global provider configs under `~/.ai/providers/`.
- [ ] Preserve user changes that are explicitly designated user-owned.
- [ ] Detect locally modified installer-owned provider files.
- [ ] Back up locally modified files before replacing them.
- [ ] Never modify repository-local overrides under `<repo>/.ai/providers/`.
- [ ] Validate YAML after Install / Update / Repair.
- [ ] Treat `providers/*.yml` as routing source of truth and `generated/<provider>/` as machine-local runtime output.
- [ ] Regenerate `generated/<provider>/` instead of shipping checked-in Codex/Claude native snapshots.
- [ ] Verify all five roles are defined or resolvable via defaults/fallbacks.

## 14. Installer ownership/state manifest

Create an installer state file that records only installer-owned resources.

Suggested fields:

- [ ] installer/framework version
- [ ] installed framework commit/version
- [ ] selected clients
- [ ] installed skill names
- [ ] provider files installed
- [ ] client wiring files/settings owned by installer
- [ ] AiIndex version
- [ ] AiIndex runtime path
- [ ] Graphify installation/runtime details
- [ ] PATH/shim changes made by installer
- [ ] MCP registrations created by installer
- [ ] prerequisite changes made by installer where useful

The state file must support safe partial uninstall.

## 15. Preserve unrelated user content

This is a hard requirement.

- [ ] Never replace an entire Codex config when only one installer-owned section is needed.
- [ ] Never replace an entire Claude config when only one installer-owned section is needed.
- [ ] Never remove unrelated skills.
- [ ] Never remove unrelated subagents.
- [ ] Never remove unrelated MCP registrations.
- [ ] Never remove unrelated PATH entries.
- [ ] Never remove repo-local `.ai` overrides.
- [ ] Never modify source repositories during global uninstall.
- [ ] Never remove project AiIndex data.

## 16. Drift / local modification handling

- [ ] Detect when an installer-owned file has been modified locally.
- [ ] Before overwrite, create a backup when safe merge is not possible.
- [ ] Interactive mode should explain the conflict.
- [ ] Prefer safe merge for structured config where reliable.
- [ ] Do not silently discard user modifications.
- [ ] Record backup paths in the final operation summary.

## 17. Update / Repair behavior

- [ ] Add explicit **Update / Repair** operation.
- [ ] Update framework repository/files when newer content is available.
- [ ] Re-apply installer-owned framework files even when the same version is selected if repair is needed.
- [ ] Repair missing/corrupted installer-owned skills, provider files, generated native wiring, and helper files.
- [ ] Regenerate native Codex/Claude agent/config fragments from the effective provider configuration.
- [ ] Update provider configs safely.
- [ ] Refresh client wiring only where installer-owned state requires it.
- [ ] Update AiIndex to latest stable by default unless pinned.
- [ ] Update Graphify dependencies/runtime where applicable.
- [ ] Refresh/repair installer-owned MCP registrations safely.
- [ ] Re-check prerequisites/runtime health during Update / Repair.
- [ ] Re-run validation after Update / Repair.
- [ ] Make the operation safe when nothing has changed.
- [ ] Preserve repo overrides and unrelated user content.
- [ ] Support a force-reapply switch only if later needed; do not create a separate reinstall operation.

## 18. Uninstall behavior

### Target selection

- [ ] Codex only
- [ ] Claude only
- [ ] Both

### Partial uninstall

When one client remains installed:

- [ ] Remove only the selected client's installer-owned wiring.
- [ ] Keep shared `.ai` resources required by the remaining client.
- [ ] Keep AiIndex/Graphify if still required by the remaining client.
- [ ] Remove only the selected client's installer-owned MCP registrations.

### Full uninstall

- [ ] Remove installer-owned Codex wiring.
- [ ] Remove installer-owned Claude wiring.
- [ ] Remove installer-owned MCP registrations.
- [ ] Offer to remove the shared framework clone/runtime.
- [ ] Offer to remove AiIndex runtime.
- [ ] Offer to remove Graphify runtime/environment.
- [ ] Remove installer-created PATH/shim changes safely.
- [ ] Preserve all unrelated user content.
- [ ] Preserve all repository overrides.
- [ ] Preserve all project AiIndex indexes/configuration.

## 19. Doctor / status mode

Implement a non-destructive diagnostic operation.

Example output:

```text
Git             OK       2.x
uv              OK       0.x
Codex           OK       installed
Claude          OK       installed
Shared .ai      OK       <version/commit>
Codex wiring    OK
Claude wiring   OK
AiIndex CLI     OK       <version>
AiIndex MCP     Codex OK / Claude OK
Graphify        OK
Provider config OK
Model routing   OK / warnings (when safely detectable)
Skills          OK
```

Doctor should also detect:

- [ ] missing prerequisite
- [ ] invalid provider YAML
- [ ] missing role mapping
- [ ] broken client wiring
- [ ] missing MCP registration
- [ ] missing AiIndex binary
- [ ] Graphify environment problem
- [ ] modified/drifted installer-owned files
- [ ] stale framework version/update available where detectable
- [ ] configured model availability/unsupported model where the client exposes a safe probe
- [ ] role repeatedly falling back because the preferred model is unavailable or usage-limited where detectable

Doctor must not change anything unless the user explicitly invokes a repair operation in the future.

## 20. Dry-run support

- [ ] `--dry-run` for install.
- [ ] `--dry-run` for Update / Repair.
- [ ] `--dry-run` for uninstall.
- [ ] Show files/settings/registrations that would change.
- [ ] Do not modify filesystem, PATH, MCP registrations, or configs.

## 21. Non-interactive / automation support

- [ ] `--target codex|claude|both`
- [ ] `--yes`
- [ ] `--dry-run`
- [ ] optional pinned AiIndex version
- [ ] stable exit codes
- [ ] useful stdout/stderr output
- [ ] no interactive prompt when all required arguments are supplied

## 22. Logging and diagnostics

- [ ] Add `--verbose`.
- [ ] Print concise default output.
- [ ] Log actionable errors.
- [ ] Avoid logging secrets/tokens.
- [ ] Report exact failed step on installation failure.
- [ ] Report rollback/backup state where applicable.

## 23. Failure handling / rollback

- [ ] Validate prerequisites before destructive changes.
- [ ] Prefer staged writes for config files.
- [ ] Back up files before replacement when required.
- [ ] Abort safely on checksum failure.
- [ ] Abort safely on invalid downloaded archive.
- [ ] Avoid leaving partially written client config.
- [ ] Record incomplete state so rerun/update can recover safely.
- [ ] Make rerunning after a failed install safe.

## 24. Security

- [ ] Verify downloaded AiIndex release checksums.
- [ ] Use HTTPS sources only.
- [ ] Do not weaken TLS/certificate verification.
- [ ] Do not install elevated/system-wide unless actually required.
- [ ] Prefer user-local installation paths.
- [ ] Do not collect or expose user secrets.
- [ ] Keep installer-owned config changes minimal.

## 25. Documentation

Once implemented:

- [ ] Replace README installation placeholder.
- [ ] Document Windows install.
- [ ] Document Linux install.
- [ ] Document macOS install.
- [ ] Document Codex-only install.
- [ ] Document Claude-only install.
- [ ] Document both-clients install.
- [ ] Document Update / Repair.
- [ ] Document uninstall.
- [ ] Document doctor/status.
- [ ] Document dry-run.
- [ ] Document non-interactive examples.
- [ ] Document prerequisite behavior.
- [ ] Document provider config ownership/overrides.
- [ ] Document preservation guarantees.
- [ ] Add troubleshooting for Git, uv, AiIndex, Graphify, MCP, and client wiring.

## 26. Installer tests

### Fresh install

- [ ] Windows: Codex only
- [ ] Windows: Claude only
- [ ] Windows: both
- [ ] Linux: Codex only
- [ ] Linux: Claude only
- [ ] Linux: both
- [ ] macOS: Codex only
- [ ] macOS: Claude only
- [ ] macOS: both

### Existing installation

- [ ] Re-run install over current version.
- [ ] Update / Repair to newer framework version.
- [ ] Update / Repair AiIndex version.
- [ ] Preserve repo overrides.
- [ ] Preserve unrelated skills/config/MCP registrations.
- [ ] Handle modified installer-owned files safely.

### Missing prerequisites

- [ ] Git missing.
- [ ] uv missing.
- [ ] Codex missing when selected.
- [ ] Claude missing when selected.
- [ ] unsupported OS/architecture.

### Failure cases

- [ ] bad checksum
- [ ] interrupted download
- [ ] invalid provider YAML
- [ ] failed MCP registration
- [ ] permission failure
- [ ] partial previous installation

### Uninstall

- [ ] Codex-only uninstall while Claude remains.
- [ ] Claude-only uninstall while Codex remains.
- [ ] Full uninstall.
- [ ] Shared resources retained when still needed.
- [ ] Unrelated user content retained.
- [ ] Project `.ai` overrides retained.
- [ ] Project `.ai-index` data retained.

### Doctor

- [ ] Healthy install reports healthy.
- [ ] Missing dependency detected.
- [ ] Broken MCP registration detected.
- [ ] Invalid provider config detected.
- [ ] Drifted file detected.

## Done criteria

- [ ] Installer can install for Codex, Claude, or both.
- [ ] Installer can Update / Repair an existing installation safely, including reapplying missing/corrupted installer-owned state.
- [ ] Installer can uninstall Codex, Claude, or both independently.
- [ ] Git and required `uv`/Graphify prerequisites are detected and installable where supported.
- [ ] Existing Codex/Claude installation and framework wiring are detected correctly.
- [ ] AiIndex CLI/MCP are installed, verified, and registered correctly.
- [ ] Graphify is installed/configured and verified.
- [ ] Provider configs and routing files are installed correctly.
- [ ] Re-running Install or Update / Repair is idempotent.
- [ ] Unrelated configs, skills, subagents, MCP registrations, and PATH entries are preserved.
- [ ] Repo-local `.ai` overrides are never modified by global lifecycle operations.
- [ ] Project `.ai-index.json` and `.ai-index/` are never removed.
- [ ] Doctor/status accurately reports installation health.
- [ ] Dry-run accurately shows intended changes without modifying the system.
- [ ] Documentation matches the implemented lifecycle.


## Prerequisite lifecycle clarification

- Python is a framework runtime prerequisite, not just an installer implementation detail.
- Accept existing Python 3.11+ without forcing an upgrade.
- Fresh Windows bootstrap installs the highest stable Python 3.x package currently available through winget.
- Fresh Linux bootstrap installs the distribution's current Python package and verifies it is 3.11+.
- The bootstrap records whether Git/Python/uv were pre-existing or installed by the framework.
- Uninstall must never uninstall Python, Git, or uv.


Doctor and uninstall are intentionally non-mutating with respect to system prerequisites: they require an existing compatible Python runtime and never install Git, Python, or uv.
