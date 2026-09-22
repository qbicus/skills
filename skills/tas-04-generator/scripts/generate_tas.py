#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


SOURCE_SKILL = "tas-04-generator"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate TAS markdown from normalized architecture data.")
    parser.add_argument("--workspace-folder", required=True, help="Architecture workspace root.")
    parser.add_argument("--runner", required=False, help="Optional runner or reviewer name for decisions logging.")
    return parser.parse_args()


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9._-]+", "-", value.lower()).strip("-") or "entity"


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Required normalized input not found: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Required normalized input is invalid: {path}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"Required normalized input is not a JSON object: {path}")
    return data


def ensure_template(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content.rstrip() + "\n", encoding="utf-8")


class TasGenerator:
    def __init__(self, workspace_folder: Path, skill_root: Path, runner: str | None) -> None:
        self.workspace_folder = workspace_folder.resolve()
        self.skill_root = skill_root.resolve()
        self.normalized_path = self.workspace_folder / "03-normalizer" / "normalized.json"
        self.output_folder = self.workspace_folder / "04-tas"
        self.runner = runner.strip() if isinstance(runner, str) and runner.strip() else "unknown"
        self.decisions: list[str] = []
        self.project_entity_names: set[str] = set()
        self.platform_entity_names: set[str] = set()
        self.generated_platform_count = 0
        self.generated_project_count = 0

    def run(self) -> None:
        self._ensure_templates()
        normalized = load_json(self.normalized_path)
        self.output_folder.mkdir(parents=True, exist_ok=True)
        canonical_entities = self._objects(normalized.get("canonical_entities"))
        normalized_platforms = self._objects(normalized.get("normalized_platforms"))
        normalized_dependencies = self._objects(normalized.get("normalized_dependencies"))
        manual_review_queue = self._objects(normalized.get("manual_review_queue"))
        assumptions = self._strings(normalized.get("assumptions"))
        unknowns = self._strings(normalized.get("unknowns"))

        self.project_entity_names = {
            item["canonical_name"]
            for item in canonical_entities
            if item.get("entity_type") == "project" and isinstance(item.get("canonical_name"), str)
        }
        self.platform_entity_names = {
            item["canonical_name"]
            for item in canonical_entities
            if item.get("entity_type") == "platform" and isinstance(item.get("canonical_name"), str)
        }

        self._write_master_tas(canonical_entities, normalized_platforms, normalized_dependencies, manual_review_queue, unknowns)
        self._write_platform_tas(normalized_platforms, normalized_dependencies, canonical_entities, unknowns)
        self._write_project_tas(normalized_platforms, normalized_dependencies, canonical_entities, unknowns)
        self._append_decisions(assumptions, unknowns, manual_review_queue)

    @staticmethod
    def _platform_name(platform: dict) -> str:
        return str(platform.get("name") or platform.get("canonical_name") or "unknown")

    @staticmethod
    def _named_values(items: object) -> list[str]:
        if not isinstance(items, list):
            return []
        values = []
        for item in items:
            if isinstance(item, dict):
                name = str(item.get("name", "")).strip()
                if name:
                    values.append(name)
            elif isinstance(item, str) and item.strip():
                values.append(item.strip())
        return sorted(set(values), key=str.lower)

    @staticmethod
    def _object_lookup(items: object) -> dict[str, dict]:
        lookup: dict[str, dict] = {}
        if not isinstance(items, list):
            return lookup
        for item in items:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()
            if name:
                lookup[name] = item
        return lookup

    def _ensure_templates(self) -> None:
        ensure_template(
            self.skill_root / "references" / "tas" / "master-template.md",
            MASTER_TEMPLATE,
        )
        ensure_template(
            self.skill_root / "references" / "tas" / "platform-template.md",
            PLATFORM_TEMPLATE,
        )
        ensure_template(
            self.skill_root / "references" / "tas" / "project-template.md",
            PROJECT_TEMPLATE,
        )

    def _write_master_tas(
        self,
        canonical_entities: list[dict],
        normalized_platforms: list[dict],
        normalized_dependencies: list[dict],
        manual_review_queue: list[dict],
        unknowns: list[str],
    ) -> None:
        shared_services = sorted({service for platform in normalized_platforms for service in self._strings(platform.get("shared_services"))})
        platform_names = [self._platform_name(platform) for platform in normalized_platforms]
        platform_summaries = []
        risks = []
        constraints = []
        normalization_notes = []
        for platform in sorted(normalized_platforms, key=lambda item: self._platform_name(item).lower()):
            business_context = self._string(platform.get("business_context"))
            platform_type = self._string(platform.get("platform_type"))
            description = self._string(platform.get("description")) or self._string(platform.get("summary")) or "No data available"
            note_parts = []
            if business_context:
                note_parts.append(f"business context: {business_context}")
            if platform_type:
                note_parts.append(f"platform type: {platform_type}")
            if self._strings(platform.get("grouping_rationale")):
                note_parts.append(f"grouping rationale: {', '.join(self._strings(platform.get('grouping_rationale'))[:2])}")
            platform_summaries.append(
                {
                    "name": self._platform_name(platform),
                    "description": description,
                    "projects": ", ".join(self._strings(platform.get("projects"))) or "none",
                    "notes": "; ".join(note_parts) or "No data available",
                }
            )
            risks.extend(self._strings(platform.get("risks")))
            constraints.extend(self._strings(platform.get("assumptions")))
            normalization_notes.extend(self._strings(platform.get("notes")) + self._strings(platform.get("grouping_rationale")))
        lines = self._header()
        lines.extend(
            [
                "---",
                "# Technical Architecture Specification — Master Architecture Summary",
                "",
                "> Confidence note: This document may include both observed and inferred architecture facts. Review unknowns and assumptions before treating the document as authoritative.",
                ">",
                "> Source: Generated automatically from code and configuration analysis.",
                "> Review status: Not reviewed / Partially reviewed / Reviewed",
                "",
                "## 1. Overview",
                "",
                "**Purpose**  ",
                "Observed: consolidate normalized platform architecture into a single technical landscape view.",
                "",
                "**Scope**  ",
                f"Observed: {len(normalized_platforms)} normalized platform(s) and {len(self.project_entity_names)} normalized project(s) were supplied from `03-normalizer/normalized.json`.",
                "",
                "**Included Platforms**  ",
            ]
        )
        lines.extend(self._bullet_lines(platform_names, empty_text="none"))
        lines.extend(
            [
                "",
                "---",
                "",
                "## 2. Architectural Landscape",
                "",
                f"Observed: Canonical entity counts by type: {self._entity_count_summary(canonical_entities)}.",
                f"Observed: {len(platform_summaries)} platform summary record(s) were available for TAS synthesis.",
                "Inferred: This view reflects normalized technical architecture rather than complete runtime behavior.",
                "",
                "---",
                "",
                "## 3. Major Platforms",
            ]
        )
        if platform_summaries:
            for item in platform_summaries:
                lines.extend(
                    [
                        f"### {item['name']}",
                        "",
                        f"- **Description:** {item['description']}",
                        f"- **Projects:** {item['projects']}",
                        f"- **Key Notes:** {item['notes']}",
                        "",
                    ]
                )
        else:
            lines.append("No data available")
        lines.extend(
            [
                "",
                "---",
                "",
                "## 4. Shared Enterprise Services",
            ]
        )
        lines.extend(self._bullet_lines(shared_services, empty_text="none"))
        lines.extend(["", "---", "", "## 5. Cross-Platform Dependencies"])
        lines.extend(self._dependency_lines(normalized_dependencies, platform_scope=True))
        risk_items = list(risks)
        if manual_review_queue:
            risk_items.append(f"Observed: {len(manual_review_queue)} manual review item(s) remain unresolved in normalization output.")
        if not normalized_platforms:
            risk_items.append("Observed: No platforms were normalized, so cross-platform analysis is limited.")
        lines.extend(
            [
                "",
                "---",
                "",
                "## 6. Strategic Risks and Constraints",
                "",
                "### Risks",
            ]
        )
        lines.extend(self._bullet_lines(sorted(set(risk_items)), empty_text="none"))
        lines.extend(["", "### Constraints"])
        lines.extend(self._bullet_lines(sorted(set(constraints)), empty_text="none"))
        lines.extend(
            [
                "",
                "---",
                "",
                "## 7. Normalization Notes",
            ]
        )
        lines.extend(
            self._bullet_lines(
                [
                    f"Observed: {len(manual_review_queue)} manual review issue(s) and {len(unknowns)} unknown item(s) were carried from normalization.",
                    "Inferred: Canonical naming may evolve as alias mappings improve over time.",
                ]
                + sorted(set(normalization_notes)),
                empty_text="none",
            )
        )
        lines.extend(
            [
                "",
                "---",
                "",
                "## 8. Open Questions and Gaps",
            ]
        )
        lines.extend(self._bullet_lines(unknowns, empty_text="none"))
        lines.extend(
            [
                "",
                "---",
                "",
                "## 9. Reviewer Checklist",
                "",
                "- [ ] Confirm included platforms",
                "- [ ] Review the architectural landscape summary",
                "- [ ] Review major platform descriptions",
                "- [ ] Confirm shared enterprise services",
                "- [ ] Confirm cross-platform dependencies",
                "- [ ] Review strategic risks and constraints",
                "- [ ] Review normalization notes",
                "- [ ] Review open questions and gaps",
                "- [ ] Update Review status at the top of this document",
                "",
                "---",
                "",
                "## 10. Appendix",
                "",
                "### Input Sources",
                "- 03-normalizer/normalized.json",
                "",
                "### Additional Notes",
            ]
        )
        lines.extend(self._bullet_lines(sorted(set(constraints + unknowns)), empty_text="none"))
        (self.output_folder / "master-tas.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    def _write_platform_tas(
        self,
        normalized_platforms: list[dict],
        normalized_dependencies: list[dict],
        canonical_entities: list[dict],
        unknowns: list[str],
    ) -> None:
        integration_names = {
            entity["canonical_name"]
            for entity in canonical_entities
            if entity.get("entity_type") == "integration"
        }
        datastore_names = {
            entity["canonical_name"]
            for entity in canonical_entities
            if entity.get("entity_type") == "datastore"
        }
        self.generated_platform_count = len(normalized_platforms)
        for platform in sorted(normalized_platforms, key=lambda item: self._platform_name(item).lower()):
            name = self._platform_name(platform)
            projects = self._strings(platform.get("projects"))
            shared_services = self._strings(platform.get("shared_services"))
            shared_datastores = self._strings(platform.get("shared_datastores"))
            key_integrations = self._strings(platform.get("key_integrations"))
            primary_stack = self._strings(platform.get("primary_stack"))
            entry_surfaces = self._strings(platform.get("entry_surfaces"))
            deployable_units = self._strings(platform.get("deployable_units"))
            observed_facts = self._strings(platform.get("observed_facts"))
            inferred_facts = self._strings(platform.get("inferred_facts"))
            platform_unknowns = self._strings(platform.get("unknowns")) or unknowns
            platform_risks = self._strings(platform.get("risks"))
            dependencies = [
                item
                for item in normalized_dependencies
                if self._string(item.get("source_project")) in projects
            ]
            security = platform.get("security", {}) if isinstance(platform.get("security"), dict) else {}
            deployment = platform.get("deployment", {}) if isinstance(platform.get("deployment"), dict) else {}
            security_patterns = self._strings(security.get("auth_systems"))
            if not security_patterns:
                security_patterns = [service for service in shared_services if service.upper() in {"JWT", "OIDC", "OAUTH", "AUTH0"} or service in integration_names]
            operational_patterns = self._strings(deployment.get("hosting_clues")) + self._strings(deployment.get("runtime_clues")) + self._strings(deployment.get("ci_cd_clues"))
            project_notes = self._synthesize_project_roles(platform)
            lines = self._header()
            lines.extend(
                [
                    "---",
                    f"# Technical Architecture Specification — {name}",
                    "",
                    "> Confidence note: This document may include both observed and inferred architecture facts. Review unknowns and assumptions before treating the document as authoritative.",
                    ">",
                    "> Source: Generated automatically from code and configuration analysis.",
                    "> Review status: Not reviewed / Partially reviewed / Reviewed",
                    "",
                    "## 1. Overview",
                    "",
                    "**Purpose**  ",
                    f"Observed: summarize the normalized architecture for platform `{name}`.",
                    "",
                    "**Scope**  ",
                    f"Observed: {len(projects)} project(s), {len(shared_services)} shared service(s), {len(shared_datastores)} shared datastore(s), and {len(key_integrations)} key integration(s).",
                    "",
                    "**Included Projects**  ",
                ]
            )
            lines.extend(self._bullet_lines(projects, empty_text="none"))
            lines.extend(
                [
                    "",
                    "---",
                    "",
                    "## 2. Platform Architecture Summary",
                    "",
                    self._string(platform.get("summary")) or self._string(platform.get("description")) or "No data available",
                    "",
                    f"Observed: Primary stack={', '.join(primary_stack) or 'none'}; deployable units={', '.join(deployable_units) or 'none'}.",
                    "Inferred: Platform cohesion is derived from normalized grouping, shared infrastructure, and platform-level architecture signals.",
                    "",
                    "---",
                    "",
                    "## 3. Constituent Projects",
                    "",
                ]
            )
            for project_name in projects:
                lines.extend(
                    [
                        f"### {project_name}",
                        "",
                        f"- **Role:** {project_notes.get(project_name, 'Platform member')}",
                        f"- **Notes:** participates in platform `{name}` with shared stack and integration context.",
                        "",
                    ]
                )
            lines.extend(["---", "", "## 4. Shared Services", ""])
            lines.extend(self._bullet_lines(shared_services, empty_text="none"))
            lines.extend(["", "---", "", "## 5. Cross-Project Dependencies", ""])
            lines.extend(self._dependency_lines(dependencies, platform_scope=False))
            lines.extend(["", "---", "", "## 6. Data and Integration Landscape", "", "### Shared Data Stores"])
            lines.extend(self._bullet_lines(shared_datastores, empty_text="none"))
            lines.extend(["", "### Key Integrations"])
            lines.extend(self._bullet_lines(key_integrations, empty_text="none"))
            lines.extend(["", "### Data / Integration Notes"])
            integration_notes = self._strings(platform.get("notes")) + self._strings(platform.get("grouping_rationale")) + observed_facts[:5]
            if entry_surfaces:
                integration_notes.append(f"Entry surfaces: {', '.join(entry_surfaces)}")
            lines.extend(self._bullet_lines(sorted(set(integration_notes)), empty_text="none"))
            lines.extend(["", "---", "", "## 7. Security and Operational Patterns", "", "### Security Patterns"])
            lines.extend(self._bullet_lines(security_patterns + self._strings(security.get("secrets_handling")), empty_text="none"))
            lines.extend(["", "### Operational Patterns"])
            lines.extend(self._bullet_lines(sorted(set(primary_stack + operational_patterns + deployable_units)), empty_text="none"))
            risk_lines = list(platform_risks)
            if not shared_services:
                risk_lines.append("Observed: No shared services were normalized for this platform.")
            if not shared_datastores and not [item for item in projects if item in datastore_names]:
                risk_lines.append("Inferred: Data architecture may be fragmented or under-documented for this platform.")
            lines.extend(["", "---", "", "## 8. Risks and Technical Debt", ""])
            lines.extend(self._bullet_lines(sorted(set(risk_lines)), empty_text="none"))
            lines.extend(["", "---", "", "## 9. Open Questions", ""])
            lines.extend(self._bullet_lines(platform_unknowns + inferred_facts[:5], empty_text="none"))
            lines.extend(
                [
                    "",
                    "---",
                    "",
                    "## 10. Reviewer Checklist",
                    "",
                    "- [ ] Confirm included projects belong in this platform",
                    "- [ ] Review platform summary",
                    "- [ ] Review constituent project roles",
                    "- [ ] Confirm shared services are correct",
                    "- [ ] Confirm cross-project dependencies",
                    "- [ ] Review data and integration landscape",
                    "- [ ] Review security and operational patterns",
                    "- [ ] Review risks and technical debt",
                    "- [ ] Review open questions",
                    "- [ ] Update Review status at the top of this document",
                    "",
                    "---",
                    "",
                    "## 11. Appendix",
                    "",
                    "### Source Projects",
                ]
            )
            lines.extend(self._bullet_lines(projects, empty_text="none"))
            lines.extend(["", "### Notes"])
            appendix_notes = sorted(set(self._strings(platform.get("notes")) + self._strings(platform.get("grouping_rationale")) + inferred_facts[:5]))
            lines.extend(self._bullet_lines(appendix_notes, empty_text="none"))
            output_path = self.output_folder / f"platform-{slugify(name)}.md"
            output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    def _write_project_tas(
        self,
        normalized_platforms: list[dict],
        normalized_dependencies: list[dict],
        canonical_entities: list[dict],
        unknowns: list[str],
    ) -> None:
        projects_in_platforms = sorted({project for platform in normalized_platforms for project in self._strings(platform.get("projects"))})
        relevant_projects = list(projects_in_platforms)
        self.generated_project_count = len(relevant_projects)
        entity_lookup = self._entity_lookup(canonical_entities)
        platform_lookup = {
            project_name: platform
            for platform in normalized_platforms
            for project_name in self._strings(platform.get("projects"))
        }
        for project_name in relevant_projects:
            project_entity = entity_lookup.get(("project", project_name), {})
            service_entity = entity_lookup.get(("service", project_name), {})
            platform = platform_lookup.get(project_name, {})
            dependencies = [item for item in normalized_dependencies if self._string(item.get("source_project")) == project_name]
            integrations = sorted(
                {
                    self._string(item.get("target_project_or_service"))
                    for item in dependencies
                    if self._string(item.get("target_project_or_service")) not in self.project_entity_names
                }
            )
            platform_name = self._platform_name(platform) if platform else "No data available"
            platform_components = self._named_values(platform.get("components")) if platform else []
            platform_datastores = self._named_values(platform.get("datastores")) if platform else []
            platform_integrations = self._named_values(platform.get("integrations")) if platform else []
            platform_interfaces = platform.get("interfaces", {}) if isinstance(platform.get("interfaces"), dict) else {}
            platform_security = platform.get("security", {}) if isinstance(platform.get("security"), dict) else {}
            platform_deployment = platform.get("deployment", {}) if isinstance(platform.get("deployment"), dict) else {}
            project_unknowns = self._strings(platform.get("unknowns")) if platform else []
            project_risks = self._strings(platform.get("risks")) if platform else []
            project_assumptions = self._strings(platform.get("assumptions")) if platform else []
            observed = self._strings(platform.get("observed_facts")) if platform else []
            inferred = self._strings(platform.get("inferred_facts")) if platform else []
            role = self._synthesize_project_roles(platform).get(project_name, "Project") if platform else "Project"
            lines = self._header()
            lines.extend(
                [
                    "---",
                    f"# Technical Architecture Specification — {project_name}",
                    "",
                    "> Confidence note: This document may include both observed and inferred architecture facts. Review unknowns and assumptions before treating the document as authoritative.",
                    ">",
                    "> Source: Generated automatically from code and configuration analysis.",
                    "> Review status: Not reviewed / Partially reviewed / Reviewed",
                    "",
                    "## 1. Overview",
                    "",
                    "**Purpose**  ",
                    f"Observed: Project `{project_name}` appears in normalized architecture outputs.",
                    "",
                    "**Scope**  ",
                    f"Observed: project context is synthesized from normalized platform `{platform_name}` and normalized dependency data.",
                    "",
                    "**Current State Summary**  ",
                    "Inferred: This project TAS is a technical supplement generated from normalized dependencies and entity mappings.",
                    "",
                    "---",
                    "",
                    "## 2. Architecture Summary",
                    "",
                    f"Observed: {len(dependencies)} normalized dependency link(s) and platform membership in `{platform_name}`.",
                    f"Inferred: {project_name} likely serves as `{role.lower()}` within `{platform_name}`.",
                    "",
                    "---",
                    "",
                    "## 3. Core Components",
                    "",
                ]
            )
            component_lines = [f"{project_name} ({role})"]
            if self._strings(service_entity.get("aliases")) and self._strings(service_entity.get("aliases")) != [project_name]:
                component_lines.append(f"{project_name} aliases: {', '.join(self._strings(service_entity.get('aliases')))}")
            if platform_components:
                component_lines.append(f"Inherited platform component context: {', '.join(platform_components[:6])}")
            lines.extend(self._bullet_lines(component_lines, empty_text="none"))
            lines.extend(
                [
                    "",
                    "---",
                    "",
                    "## 4. Interfaces and Integrations",
                    "",
                    "### Inbound Interfaces",
                ]
            )
            lines.extend(self._bullet_lines(self._strings(platform_interfaces.get("inbound")), empty_text="none"))
            lines.extend(
                [
                    "",
                    "### Outbound Integrations",
                ]
            )
            integration_lines = []
            if integrations:
                integration_lines.append(f"Project-specific normalized dependency targets: {', '.join(integrations)}")
            if platform_integrations:
                integration_lines.append(f"Inherited platform integration context: {', '.join(platform_integrations[:12])}")
            lines.extend(self._bullet_lines(integration_lines, empty_text="none"))
            lines.extend(
                [
                    "",
                    "### Dependencies",
                ]
            )
            lines.extend(self._dependency_lines(dependencies, platform_scope=False))
            lines.extend(
                [
                    "",
                    "---",
                    "",
                    "## 5. Data Architecture",
                    "",
                    "### Data Stores",
                ]
            )
            datastore_lines = [f"Inherited platform datastores: {', '.join(platform_datastores)}"] if platform_datastores else []
            lines.extend(self._bullet_lines(datastore_lines, empty_text="none"))
            lines.extend(
                [
                    "",
                    "### Data Notes",
                ]
            )
            data_note_lines = []
            if platform_datastores:
                data_note_lines.append(
                    f"Observed: platform-level shared datastore context from {platform_name} is inherited into this project view."
                )
            data_note_lines.append(
                "Inferred: project-local persistence details may exist beyond the normalized shared platform data."
            )
            lines.extend(self._bullet_lines(data_note_lines, empty_text="none"))
            lines.extend(
                [
                    "",
                    "---",
                    "",
                    "## 6. Security and Access",
                    "",
                    "### Authentication",
                ]
            )
            auth_lines = [f"Inherited platform authentication context: {', '.join(self._strings(platform_security.get('auth_systems')))}"] if self._strings(platform_security.get("auth_systems")) else []
            lines.extend(self._bullet_lines(auth_lines, empty_text="none"))
            lines.extend(["", "### Authorization"])
            lines.extend(self._bullet_lines(["No project-specific authorization model was isolated in normalized output."], empty_text="none"))
            lines.extend(["", "### Secrets and Sensitive Configuration"])
            secret_lines = [f"Inherited platform secret handling: {', '.join(self._strings(platform_security.get('secrets_handling')))}"] if self._strings(platform_security.get("secrets_handling")) else []
            lines.extend(self._bullet_lines(secret_lines, empty_text="none"))
            lines.extend(
                [
                    "",
                    "---",
                    "",
                    "## 7. Deployment and Operations",
                    "",
                    "### Hosting / Runtime",
                ]
            )
            hosting_values = self._strings(platform_deployment.get("hosting_clues")) + self._strings(platform_deployment.get("runtime_clues"))
            hosting_lines = [f"Inherited platform runtime context: {', '.join(hosting_values)}"] if hosting_values else []
            lines.extend(self._bullet_lines(hosting_lines, empty_text="none"))
            lines.extend(["", "### CI/CD"])
            cicd_values = self._strings(platform_deployment.get("ci_cd_clues"))
            cicd_lines = [f"Inherited platform CI/CD clues: {', '.join(cicd_values)}"] if cicd_values else []
            lines.extend(self._bullet_lines(cicd_lines, empty_text="none"))
            lines.extend(["", "### Operational Notes"])
            operational_lines = [f"Inherited platform note: {note}" for note in self._strings(platform.get("notes"))] if platform else []
            lines.extend(self._bullet_lines(operational_lines, empty_text="none"))
            lines.extend(["", "---", "", "## 8. Observed Architecture Facts", ""])
            observed_lines = [f"Inherited platform fact: {fact}" for fact in observed]
            lines.extend(self._bullet_lines(observed_lines, empty_text="none"))
            lines.extend(["", "---", "", "## 9. Inferred Architecture Facts", ""])
            inferred_lines = [f"Inherited platform inference: {fact}" for fact in inferred]
            lines.extend(self._bullet_lines(inferred_lines, empty_text="none"))
            lines.extend(["", "---", "", "## 10. Risks, Constraints, and Unknowns", "", "### Risks"])
            risk_lines = list(project_risks)
            if not dependencies:
                risk_lines.append("Observed: No normalized dependencies were available for this project TAS.")
            if not integrations and not platform_integrations:
                risk_lines.append("Inferred: Project integration coverage may be incomplete after normalization.")
            lines.extend(self._bullet_lines(sorted(set(risk_lines)), empty_text="none"))
            lines.extend(["", "### Constraints"])
            lines.extend(self._bullet_lines(project_assumptions, empty_text="none"))
            lines.extend(["", "### Unknowns"])
            lines.extend(self._bullet_lines(project_unknowns or unknowns, empty_text="none"))
            lines.extend(
                [
                    "",
                    "---",
                    "",
                    "## 11. Reviewer Checklist",
                    "",
                    "- [ ] Confirm purpose and scope",
                    "- [ ] Confirm architecture summary reflects the actual system",
                    "- [ ] Review all core components",
                    "- [ ] Review inbound and outbound integrations",
                    "- [ ] Confirm dependencies",
                    "- [ ] Validate data architecture",
                    "- [ ] Validate security and access notes",
                    "- [ ] Validate deployment and operational notes",
                    "- [ ] Review observed vs inferred facts",
                    "- [ ] Review risks, constraints, and unknowns",
                    "- [ ] Update Review status at the top of this document",
                    "",
                    "---",
                    "",
                    "## 12. Evidence / References Appendix",
                ]
            )
            references = self._strings(project_entity.get("source_references")) + self._strings(service_entity.get("source_references"))
            lines.extend(self._bullet_lines(sorted(set(references)), empty_text="none"))
            output_path = self.output_folder / f"project-{slugify(project_name)}.md"
            output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    def _append_decisions(self, assumptions: list[str], unknowns: list[str], manual_review_queue: list[dict]) -> None:
        path = self.output_folder / "decisions.md"
        generated_at = datetime.now(timezone.utc).isoformat()
        lines = [
            f"## {generated_at}",
            f"- workspace folder: {self.workspace_folder}",
            f"- platforms generated: {self.generated_platform_count}",
            f"- projects processed: {self.generated_project_count}",
            f"- project tas generated: {'yes' if self.generated_project_count else 'no'}",
            f"- runner: {self.runner}",
        ]
        for assumption in assumptions:
            lines.append(f"- assumption: {assumption}")
        for unknown in unknowns:
            lines.append(f"- missing context: {unknown}")
        for issue in manual_review_queue:
            issue_type = self._string(issue.get("issue_type"))
            candidates = ", ".join(self._strings(issue.get("candidates")))
            reason = self._string(issue.get("reason"))
            lines.append(f"- missing context: {issue_type} -> {candidates} ({reason})")
        if len(lines) == 6:
            lines.append("- assumption: No additional assumptions or missing context were recorded for this run.")
        lines.append("")
        with path.open("a", encoding="utf-8") as handle:
            handle.write("\n".join(lines))

    def _header(self) -> list[str]:
        return [
            f"generated_at: {datetime.now(timezone.utc).isoformat()}",
            f"source_skill: {SOURCE_SKILL}",
            f"workspace_folder: {self.workspace_folder}",
            "",
        ]

    @staticmethod
    def _objects(value: object) -> list[dict]:
        return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []

    @staticmethod
    def _strings(value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return sorted({item.strip() for item in value if isinstance(item, str) and item.strip()})

    @staticmethod
    def _string(value: object) -> str:
        return value.strip() if isinstance(value, str) else ""

    @staticmethod
    def _bullet_lines(items: list[str], empty_text: str) -> list[str]:
        return [f"- {item}" for item in items] if items else [f"- {empty_text}"]

    def _synthesize_project_roles(self, platform: dict) -> dict[str, str]:
        projects = self._strings(platform.get("projects"))
        roles: dict[str, str] = {}
        platform_name = self._platform_name(platform)
        summary = self._string(platform.get("summary")).lower()
        for project in projects:
            lowered = project.lower()
            if "library" in lowered or lowered.endswith("lib") or lowered.endswith("shared"):
                roles[project] = f"Shared library reused within {platform_name}"
            elif "api" in lowered:
                roles[project] = f"API/service entry point within {platform_name}"
            elif "worker" in lowered or "service" in lowered or "manager" in lowered or "dispatch" in lowered:
                roles[project] = f"Background processing or integration service within {platform_name}"
            elif "display" in lowered or "pwa" in lowered or "frontend" in lowered:
                roles[project] = f"Display or frontend runtime within {platform_name}"
            elif "tool" in lowered or "bundler" in lowered or "index" in lowered:
                roles[project] = f"Utility or tooling component within {platform_name}"
            elif lowered.endswith("website") or lowered == "website" or lowered.endswith("portal") or lowered == "cms" or lowered.endswith("webapi") or "webapi" in lowered:
                roles[project] = f"Primary web or operator-facing application within {platform_name}"
            elif "helper" in lowered:
                roles[project] = f"Shared library or support component within {platform_name}"
            elif summary:
                roles[project] = f"Platform member contributing to: {summary[:120]}"
            else:
                roles[project] = f"Platform member within {platform_name}"
        return roles

    def _dependency_lines(self, dependencies: list[dict], platform_scope: bool) -> list[str]:
        if not dependencies:
            return ["- none"]
        lines = []
        for item in sorted(
            dependencies,
            key=lambda row: (
                self._string(row.get("source_project")).lower(),
                self._string(row.get("target_project_or_service")).lower(),
            ),
        ):
            source = self._string(item.get("source_project"))
            target = self._string(item.get("target_project_or_service"))
            relationship = self._string(item.get("relationship"))
            confidence = self._string(item.get("confidence")) or "low"
            evidence = ", ".join(self._strings(item.get("evidence"))) or "No data available"
            prefix = "Observed" if not platform_scope else "Observed"
            lines.append(f"- {prefix}: {source} -> {target} | {relationship} | confidence={confidence} | notes={evidence}")
        return lines

    @staticmethod
    def _entity_count_summary(canonical_entities: list[dict]) -> str:
        counts = {}
        for item in canonical_entities:
            entity_type = str(item.get("entity_type", "unknown"))
            counts[entity_type] = counts.get(entity_type, 0) + 1
        if not counts:
            return "none"
        return ", ".join(f"{key}={counts[key]}" for key in sorted(counts))

    @staticmethod
    def _entity_lookup(canonical_entities: list[dict]) -> dict[tuple[str, str], dict]:
        lookup = {}
        for item in canonical_entities:
            entity_type = str(item.get("entity_type", ""))
            canonical_name = str(item.get("canonical_name", ""))
            if entity_type and canonical_name:
                lookup[(entity_type, canonical_name)] = item
        return lookup


MASTER_TEMPLATE = """# Master TAS Template

## 1. Overview

## 2. Platforms

## 3. Architecture Landscape

## 4. Shared Services

## 5. Cross-Platform Dependencies

## 6. Risks and Technical Debt

## 7. Normalization Notes

## 8. Unknowns
"""


PLATFORM_TEMPLATE = """# Platform TAS Template

## 1. Overview

## 2. Projects

## 3. Architecture Summary

## 4. Shared Services

## 5. Dependencies

## 6. Data Landscape

## 7. Security Patterns

## 8. Risks

## 9. Unknowns
"""


PROJECT_TEMPLATE = """# Project TAS Template

## 1. Overview

## 2. Scope

## 3. Architecture Summary

## 4. Components

## 5. Integrations

## 6. Data Architecture

## 7. Security

## 8. Deployment

## 9. Risks

## 10. Unknowns
"""


def main() -> int:
    args = parse_args()
    workspace_folder = Path(args.workspace_folder)
    workspace_folder.mkdir(parents=True, exist_ok=True)
    generator = TasGenerator(workspace_folder, Path(__file__).resolve().parents[1], args.runner)
    generator.run()
    print(generator.output_folder)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
