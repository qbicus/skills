#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


SOURCE_SKILL = "tas-generator"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate TAS markdown from normalized architecture data.")
    parser.add_argument("--workspace-folder", required=True, help="Architecture workspace root.")
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
    def __init__(self, workspace_folder: Path, skill_root: Path) -> None:
        self.workspace_folder = workspace_folder.resolve()
        self.skill_root = skill_root.resolve()
        self.normalized_path = self.workspace_folder / "03-normalizer" / "normalized.json"
        self.output_folder = self.workspace_folder / "04-tas"
        self.decisions: list[str] = []
        self.project_entity_names: set[str] = set()
        self.platform_entity_names: set[str] = set()

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
        shared_services = sorted(
            {
                entity["canonical_name"]
                for entity in canonical_entities
                if entity.get("entity_type") == "service"
            }
        )
        lines = self._header()
        lines.extend(
            [
                "# 1. Overview",
                f"Observed: {len(normalized_platforms)} normalized platform(s) and {len(self.project_entity_names)} normalized project(s) were supplied from `03-normalizer/normalized.json`.",
                "Inferred: This document reflects only technical relationships present in normalized architecture data.",
                f"Confidence note: {'medium' if normalized_platforms else 'low'}",
                "",
                "# 2. Platforms",
            ]
        )
        if normalized_platforms:
            for platform in sorted(normalized_platforms, key=lambda item: item.get("canonical_name", "").lower()):
                lines.append(
                    f"- {platform.get('canonical_name', 'unknown')}: projects={', '.join(self._strings(platform.get('projects'))) or 'none'} | confidence={platform.get('confidence', 'low')}"
                )
        else:
            lines.append("- none")
        lines.extend(
            [
                "",
                "# 3. Architecture Landscape",
                f"Observed: Canonical entity counts by type: {self._entity_count_summary(canonical_entities)}.",
                "Inferred: Platform and dependency views represent the current normalized technical landscape rather than full runtime behavior.",
                "",
                "# 4. Shared Services",
            ]
        )
        lines.extend(self._bullet_lines(shared_services, empty_text="none"))
        lines.extend(
            [
                "",
                "# 5. Cross-Platform Dependencies",
            ]
        )
        lines.extend(self._dependency_lines(normalized_dependencies, platform_scope=True))
        risk_items = []
        if manual_review_queue:
            risk_items.append(f"Observed: {len(manual_review_queue)} manual review item(s) remain unresolved in normalization output.")
        if not normalized_platforms:
            risk_items.append("Observed: No platforms were normalized, so cross-platform analysis is limited.")
        lines.extend(
            [
                "",
                "# 6. Risks and Technical Debt",
            ]
        )
        lines.extend(risk_items or ["- none"])
        lines.extend(
            [
                "",
                "# 7. Normalization Notes",
                f"Observed: {len(manual_review_queue)} manual review issue(s) and {len(unknowns)} unknown item(s) were carried from normalization.",
                "Inferred: Canonical naming may evolve as alias mappings improve over time.",
                "",
                "# 8. Unknowns",
            ]
        )
        lines.extend(self._bullet_lines(unknowns, empty_text="none"))
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
        for platform in sorted(normalized_platforms, key=lambda item: item.get("canonical_name", "").lower()):
            name = str(platform.get("canonical_name", "unknown"))
            projects = self._strings(platform.get("projects"))
            shared_services = self._strings(platform.get("shared_services"))
            shared_datastores = self._strings(platform.get("shared_datastores"))
            key_integrations = self._strings(platform.get("key_integrations"))
            dependencies = [
                item
                for item in normalized_dependencies
                if self._string(item.get("source_project")) in projects
            ]
            security_patterns = [service for service in shared_services if service.upper() in {"JWT", "OIDC", "OAUTH", "AUTH0"} or service in integration_names]
            lines = self._header()
            lines.extend(
                [
                    "# 1. Overview",
                    f"Observed: Platform `{name}` contains {len(projects)} project(s).",
                    "Inferred: Platform summary is generated from normalized platform membership and dependency data.",
                    f"Confidence note: {platform.get('confidence', 'low')}",
                    "",
                    "# 2. Projects",
                ]
            )
            lines.extend(self._bullet_lines(projects, empty_text="none"))
            lines.extend(
                [
                    "",
                    "# 3. Architecture Summary",
                    f"Observed: Shared services={', '.join(shared_services) or 'none'}; shared datastores={', '.join(shared_datastores) or 'none'}; key integrations={', '.join(key_integrations) or 'none'}.",
                    "Inferred: Shared services and dependencies indicate the main technical cohesion within the platform.",
                    "",
                    "# 4. Shared Services",
                ]
            )
            lines.extend(self._bullet_lines(shared_services, empty_text="none"))
            lines.extend(
                [
                    "",
                    "# 5. Dependencies",
                ]
            )
            lines.extend(self._dependency_lines(dependencies, platform_scope=False))
            lines.extend(
                [
                    "",
                    "# 6. Data Landscape",
                    f"Observed: Shared datastores={', '.join(shared_datastores) or 'none'}.",
                    f"Inferred: Platform data landscape may also involve project-local stores not elevated to platform level." if shared_datastores else "Inferred: No shared platform datastore was normalized.",
                    "",
                    "# 7. Security Patterns",
                ]
            )
            lines.extend(self._bullet_lines(security_patterns, empty_text="none"))
            risk_lines = []
            if not shared_services:
                risk_lines.append("Observed: No shared services were normalized for this platform.")
            if not shared_datastores and not [item for item in projects if item in datastore_names]:
                risk_lines.append("Inferred: Data architecture may be fragmented or under-documented for this platform.")
            lines.extend(
                [
                    "",
                    "# 8. Risks",
                ]
            )
            lines.extend(risk_lines or ["- none"])
            lines.extend(
                [
                    "",
                    "# 9. Unknowns",
                ]
            )
            lines.extend(self._bullet_lines(unknowns, empty_text="none"))
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
        relevant_projects = []
        for project_name in projects_in_platforms:
            dep_count = len([item for item in normalized_dependencies if self._string(item.get("source_project")) == project_name])
            if dep_count > 0 or len(projects_in_platforms) == 1:
                relevant_projects.append(project_name)
        entity_lookup = self._entity_lookup(canonical_entities)
        for project_name in relevant_projects:
            project_entity = entity_lookup.get(("project", project_name), {})
            service_entity = entity_lookup.get(("service", project_name), {})
            dependencies = [item for item in normalized_dependencies if self._string(item.get("source_project")) == project_name]
            integrations = sorted(
                {
                    self._string(item.get("target_project_or_service"))
                    for item in dependencies
                    if self._string(item.get("target_project_or_service")) not in self.project_entity_names
                }
            )
            lines = self._header()
            lines.extend(
                [
                    "# 1. Overview",
                    f"Observed: Project `{project_name}` appears in normalized architecture outputs.",
                    "Inferred: This project TAS is a technical supplement generated from normalized dependencies and entity mappings.",
                    f"Confidence note: {project_entity.get('confidence', 'low')}",
                    "",
                    "# 2. Scope",
                    "Observed: Scope is limited to technical architecture data available after normalization.",
                    "Inferred: Business scope is intentionally omitted because it was not present in the source data.",
                    "",
                    "# 3. Architecture Summary",
                    f"Observed: {len(dependencies)} normalized dependency link(s) were found for this project.",
                    "Inferred: The project likely participates in a larger platform architecture if platform membership exists.",
                    "",
                    "# 4. Components",
                ]
            )
            component_lines = [project_name]
            if self._strings(service_entity.get("aliases")) and self._strings(service_entity.get("aliases")) != [project_name]:
                component_lines.append(f"{project_name} aliases: {', '.join(self._strings(service_entity.get('aliases')))}")
            lines.extend(self._bullet_lines(component_lines, empty_text="none"))
            lines.extend(
                [
                    "",
                    "# 5. Integrations",
                ]
            )
            lines.extend(self._bullet_lines(integrations, empty_text="none"))
            lines.extend(
                [
                    "",
                    "# 6. Data Architecture",
                    "Observed: Project-level datastore details are not preserved separately in normalized output.",
                    "Inferred: Refer back to analyzer outputs if datastore detail is required for this project.",
                    "",
                    "# 7. Security",
                    "Observed: Security details are only represented indirectly through normalized services and dependencies.",
                    "Inferred: Authentication and authorization specifics may require analyzer-level review.",
                    "",
                    "# 8. Deployment",
                    "Observed: Deployment details are not reproduced in normalized output.",
                    "Inferred: Deployment specifics should be traced back to project analyzer artifacts.",
                    "",
                    "# 9. Risks",
                ]
            )
            risk_lines = []
            if not dependencies:
                risk_lines.append("Observed: No normalized dependencies were available for this project TAS.")
            if not integrations:
                risk_lines.append("Inferred: Project integration coverage may be incomplete after normalization.")
            lines.extend(risk_lines or ["- none"])
            lines.extend(
                [
                    "",
                    "# 10. Unknowns",
                ]
            )
            lines.extend(self._bullet_lines(unknowns, empty_text="none"))
            output_path = self.output_folder / f"project-{slugify(project_name)}.md"
            output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    def _append_decisions(self, assumptions: list[str], unknowns: list[str], manual_review_queue: list[dict]) -> None:
        path = self.output_folder / "decisions.md"
        generated_at = datetime.now(timezone.utc).isoformat()
        lines = [f"## {generated_at}"]
        for assumption in assumptions:
            lines.append(f"- assumption: {assumption}")
        for unknown in unknowns:
            lines.append(f"- missing context: {unknown}")
        for issue in manual_review_queue:
            issue_type = self._string(issue.get("issue_type"))
            candidates = ", ".join(self._strings(issue.get("candidates")))
            reason = self._string(issue.get("reason"))
            lines.append(f"- missing context: {issue_type} -> {candidates} ({reason})")
        if len(lines) == 1:
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
            prefix = "Observed" if not platform_scope else "Observed"
            lines.append(f"- {prefix}: {source} -> {target} | {relationship} | confidence={confidence}")
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
    generator = TasGenerator(workspace_folder, Path(__file__).resolve().parents[1])
    generator.run()
    print(generator.output_folder)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
