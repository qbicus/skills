# AI Framework — Remaining Work

Status: **Codex runtime/E2E verified, profile-aware routing added — deferred Claude E2E + installer pending**


> 2026-10-04 update: provider routing, native Codex/Claude agent generation, strict runtime fallback orchestration, substantial-work advisor checkpoints, bounded workers, and plan-controlled parallel execution are implemented. Live Codex validation now covers native role invocation, model fallback, substantial `new-feature`, researcher/executor delegation, advisor plan/completion checkpoints, and explicit parallel execution. Claude implementation remains statically validated but live E2E is intentionally deferred to avoid company-limit usage. Installation/update lifecycle remains owned by `INSTALLER.md`.

This checklist tracks the remaining work after the provider-neutral role model, advisor skill, substantial-work marker, bounded workers, plan-controlled parallel execution, provider config files, README/help updates, and initial skill standardization were added.

## 1. Runtime provider routing

- [x] Implement runtime loading of Codex `low` / `medium` / `high` provider profiles.
- [x] Implement runtime loading of Claude `low` / `medium` / `high` provider profiles.
- [x] Keep `medium` as the default/recommended profile (`codex.yml` / `claude.yml`).
- [x] Support temporary profile selection with `--profile` / `AI_PROFILE` and persistent per-provider selection with `--set-profile`.
- [x] Detect the active provider automatically where possible.
- [x] Support an explicit provider override for testing/debugging.
- [x] Resolve provider/profile configuration in this order:
  1. selected global profile (`<provider>.yml` for medium, `<provider>.low.yml` / `<provider>.high.yml`)
  2. generic repository override: `<repo>/.ai/providers/<provider>.yml`
  3. profile-specific repository override: `<repo>/.ai/providers/<provider>.<profile>.yml`
- [x] Allow repo overrides to change both model mappings and orchestration settings.
- [x] Validate provider config schema and report invalid values clearly.

## 2. Role resolution

Support all shared provider-neutral roles:

- [x] `primary`
- [x] `executor`
- [x] `researcher`
- [x] `advisor`
- [x] `fast`

For each role:

- [x] Resolve configured model.
- [x] Resolve configured reasoning/effort level where supported.
- [x] Resolve role-specific runtime/subagent behavior.
- [x] Resolve allowed capabilities/tool restrictions where supported.
- [x] Implement provider-level fallback/default routing when the preferred model/role is unavailable.
- [x] Log/report when a fallback is used.

## 3. Codex runtime integration

- [x] Verify the current Codex mechanism for model selection/delegation/subagents.
- [x] Map `primary` to the selected high-reasoning Codex model.
- [x] Map `executor` to the selected implementation model.
- [x] Map `researcher` to the selected research model.
- [x] Map `advisor` to the selected independent review model.
- [x] Map `fast` to the selected low-latency/low-cost model.
- [x] Ensure role selection is driven by provider config rather than hard-coded skill text.
- [x] Ensure role fallbacks work when a configured Codex model is unavailable. *(Verified live: failed `ai-fast` candidate retried fallback agents in order; primary did not silently take over.)*
- [x] Confirm whether per-role tool restrictions are enforceable in Codex.
- [x] Document any Codex-specific limitations.

## 4. Claude runtime integration

- [x] Verify the current Claude Code mechanism for model selection, subagents, effort, and advisor usage.
- [x] Map `primary` to the selected Claude high-reasoning model.
- [x] Map `executor` to the selected Claude implementation model.
- [x] Map `researcher` to the selected Claude research model.
- [x] Map `advisor` to the selected advisor/reviewer model.
- [x] Map `fast` to the selected low-latency/low-cost model.
- [x] Keep the framework `advisor` skill portable even when Claude native advisor support is used.
- [ ] Ensure role fallbacks work when a configured Claude model is unavailable.
- [x] Confirm whether per-subagent tool restrictions are enforceable in Claude.
- [x] Document any Claude-specific limitations.

## 5. Advisor runtime behavior

- [x] Wire `advisor:plan` into substantial planning workflows.
- [x] Wire `advisor:stuck` into repeated-failure handling.
- [x] Wire `advisor:complete` into substantial completion checks.
- [x] Keep advisor context compact and purpose-specific.
- [x] Do not stream the full session into the advisor by default.
- [x] Enforce `repeatedFailureThreshold` from provider/repo config.
- [x] Default repeated-failure threshold to `2`.
- [x] Allow manual invocation of the advisor skill.
- [x] Ensure advisor remains read/review oriented and does not silently take over implementation.

## 6. Substantial-work behavior

- [x] Ensure `new-feature` always emits `substantial: true|false`.
- [x] Define/document default substantial classifications:
  - feature work → substantial
  - migration → substantial
  - modernization → substantial
  - architecture changes → substantial
  - significant debugging → substantial
  - small/local changes → normally not substantial
- [x] Allow parent skills to override the default classification explicitly.
- [x] Run `advisor:complete` only when the task is substantial.
- [x] Ensure non-substantial work does not pay unnecessary advisor cost.

## 7. Worker/executor contract

- [x] Enforce bounded worker scope.
- [x] Permit closely related files needed to complete the assigned task.
- [x] Require workers to report material scope expansion.
- [x] Escalate architectural/design expansion instead of deciding locally.
- [x] Standardize worker outcomes:
  - `COMPLETE`
  - `BLOCKED`
  - `NEEDS_DECISION`
  - `NEEDS_RESEARCH`
- [x] Route `NEEDS_DECISION` to `primary`.
- [x] Route `NEEDS_RESEARCH` to `researcher`.
- [x] Define what information must accompany `BLOCKED`.
- [x] Ensure worker completion includes tests/validation performed.

## 8. Parallel execution

- [x] Keep parallel execution **plan-controlled only**.
- [x] Do not automatically fan out merely because tasks appear independent.
- [x] Ensure plans explicitly mark tasks as parallel-safe before dispatch.
- [x] Ensure `nf-tasks` and modernization task planning preserve dependency ordering.
- [x] Ensure `parallel-exec` respects configured concurrency limits if introduced.
- [x] Add/confirm merge checkpoints for parallel worker output.
- [x] Ensure conflicting file ownership is detected before parallel dispatch.

## 9. Research role

- [x] Define when a task should escalate to `researcher`.
- [x] Keep external research separate from implementation where practical.
- [x] Return concise findings to `primary`/`executor` rather than dumping raw research context.
- [x] Document provider-specific web/docs capabilities and limitations.

## 10. Fast role

- [x] Define the class of decisions safe for `fast`.
- [x] Restrict `fast` to low-risk, reversible, local routing decisions.
- [x] Prevent architectural or user-impacting decisions from being delegated to `fast`.
- [x] Add fallback to `executor` or `primary` when the task is not safely classifiable as trivial.

## 11. Provider configuration schema

- [x] Finalize the exact YAML schema for roles.
- [x] Finalize fallback syntax.
- [x] Finalize effort/reasoning syntax per provider.
- [x] Finalize capability/tool restriction syntax.
- [x] Finalize advisor settings.
- [x] Finalize parallel-execution settings.
- [x] Add schema examples to README/HELP.
- [x] Add repo override examples.
- [x] Add invalid-config examples/troubleshooting.

Example target shape:

```yaml
roles:
  primary:
    model: ...
    effort: high

  executor:
    model: ...
    effort: medium

  researcher:
    model: ...
    effort: medium

  advisor:
    model: ...
    effort: medium
    fallback:
      - executor
      - primary

  fast:
    model: ...
    effort: low

advisor:
  repeatedFailureThreshold: 2
  completionCheck:
    substantialOnly: true

execution:
  parallel:
    mode: plan-only
```

## 12. Global vs repository overrides

- [x] Confirm global provider config location under `~/.ai/providers/`.
- [x] Confirm repo override location under `<repo>/.ai/providers/`.
- [x] Ensure repository overrides are never modified by global install/update/uninstall.
- [x] Implement deep/partial merge behavior.
- [x] Document precedence rules clearly.
- [x] Add a command/help output that shows the effective merged provider config.

## 13. Help / diagnostics commands

- [x] Extend the helper CLI to show active provider.
- [x] Show effective role mapping.
- [x] Show which config files contributed to the final merged configuration.
- [x] Show fallback chains.
- [x] Add a validation command for provider config.
- [x] Add a runtime diagnostics mode for routing decisions.
- [x] Make diagnostics useful without exposing secrets or unrelated user config.

Potential commands:

```text
ai.py provider
ai.py provider --effective
ai.py provider --validate
ai.py provider --diagnose
ai.py provider --get behavior.advisor.repeatedFailureThreshold
ai.py skills
ai.py help
```

## 14. README / HELP finalization

- [ ] Replace installation placeholder once installer work is complete.
- [x] Document runtime role routing after native Codex/Claude integration exists.
- [x] Document provider detection and explicit override.
- [x] Document low/medium/high usage profiles.
- [x] Document `AI_PROFILE` / `--profile` / `--set-profile` selection and profile-specific repo overrides.
- [x] Document fallbacks.
- [x] Document repo overrides.
- [x] Document manual advisor invocation.
- [x] Document substantial vs non-substantial behavior.
- [x] Document bounded worker escalation outcomes.
- [x] Document plan-controlled parallel execution.
- [ ] Add/refresh complete end-to-end examples from verified behavior:
  - [x] `new-feature` *(Codex substantial flow verified; document the real flow)*
  - [ ] `debug`
  - [ ] `modernize-eval` / `modernize-plan`
  - [x] `parallel-exec` *(Codex plan-controlled parallel flow verified; document it)*  
  - [ ] `code-review`
  - [x] `advisor` checkpoints through `new-feature`
  - [x] `advisor` manual invocation
  - [x] repo-level provider override
  - [x] fallback behavior within the real `new-feature` run
- [x] Ensure all available skills are listed in both README and HELP.
- [x] Ensure command examples match the actual helper/installer commands.

## 15. End-to-end validation

### Codex

> Live substantial-feature acceptance run completed on 2026-10-04: 69 tests passed in two host timezones, production build/typecheck passed, advisor plan/completion checkpoints ran, researcher/executors were delegated, model fallback was exercised, and the only approved parallel batch remained bounded and conflict-free.


- [x] Start a small non-substantial task and verify no completion advisor runs.
- [x] Start a substantial `new-feature` task and verify advisor plan/completion checkpoints. *(Verified live with Date & Time Dashboard; plan + completion checkpoints both ran.)*
- [x] Verify `executor` routing. *(Verified live; bounded executor work plus configured fallback after a usage-limit failure.)*
- [x] Verify `researcher` routing. *(Verified live during toolchain compatibility research.)*
- [x] Verify `fast` routing on an appropriate low-risk fork.
- [x] Verify repeated failure threshold triggers `advisor:stuck` at `2`. *(Verified live in DateDashboard controlled fail-fast debug run.)*
- [x] Verify repo override changes the effective role mapping. *(Verified live: repo override changed only `fast.effort` while inherited model/other roles remained intact.)*
- [x] Verify manual advisor invocation in a small standalone review. *(Verified live; advisor returned `OK` in read-only review.)*
- [x] Verify fallback model is used when the preferred model is unavailable.
- [x] Verify parallel execution occurs only when the plan explicitly permits it. *(Verified live: only the approved T002/T003 batch ran in parallel; remaining implementation stayed sequential.)*

### Claude

> Deferred by choice for now to avoid consuming company Claude limits. Claude provider config/native subagent rendering remains implemented and statically validated. Reuse the same Codex acceptance matrix when live Claude validation is scheduled.

- [ ] Repeat the same scenarios under Claude Code.
- [ ] Verify Claude-specific subagents/advisor integration.
- [ ] Verify repo override behavior.
- [ ] Verify fallback behavior.
- [ ] Verify no framework behavior depends on Claude-only features.

## 16. Cross-provider review

- [ ] Have Codex review the Claude integration for missed assumptions/inconsistencies. *(Can be done without spending Claude usage.)*
- [ ] Have Claude review the Codex integration for missed assumptions/inconsistencies. *(Deferred with Claude E2E.)*
- [ ] Resolve validated findings only.
- [ ] Run a final framework-level review after fixes/installer wiring.

## 17. Distribution / release integration *(installer-owned)*

- [ ] Ensure provider configs are included in the distributed framework.
- [ ] Ensure the advisor skill is included in the distributed skill set.
- [ ] Ensure HELP/README ship with the framework.
- [ ] Ensure installers place/update provider files correctly.
- [ ] Ensure Update / Repair preserves repo overrides and unrelated user content.
- [ ] Ensure uninstall removes only installer-owned resources.

See `INSTALLER.md` for the installer-specific checklist.

## Done criteria

### Framework/Codex acceptance before installer

- [x] Skills reference roles, never provider-specific model names.
- [x] All five roles resolve correctly at runtime.
- [x] Global and repo provider configs deep-merge correctly in runtime tests.
- [x] Codex fallback orchestration works when a preferred model is unavailable or usage-limited.
- [x] Advisor plan/completion checkpoints work in a substantial Codex `new-feature` flow.
- [x] Repeated-failure threshold is configurable and defaults to `2`.
- [x] Workers are bounded and escalate through the standardized outcomes.
- [x] Parallel execution occurs only when explicitly permitted by the approved plan.
- [x] Codex substantial `new-feature`, executor, researcher, fallback, and parallel paths have live E2E evidence.
- [x] Codex non-substantial flow confirms unnecessary advisor checkpoints are skipped.
- [x] Codex repeated implementation failure triggers `advisor:stuck` at threshold `2`.
- [ ] Codex repo-local provider override is verified live.
- [ ] Manual advisor invocation is verified live.
- [ ] README/HELP are refreshed with final verified examples.

### Deferred / release-level acceptance

- [ ] Same shared skills are live-E2E verified under Claude as well as Codex. *(Claude live E2E intentionally deferred for now.)*
- [ ] Claude fallback behavior is live verified.
- [ ] Cross-provider review is completed.
- [ ] Installer **Install / Update / Repair / Uninstall / Doctor** lifecycle passes for selected clients.
- [ ] README installation placeholder is replaced with the implemented installer instructions.
