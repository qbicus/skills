#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


VALID_CONFIDENCE = {"high", "medium", "low"}
STOP_WORDS = {
    "api",
    "app",
    "application",
    "backend",
    "core",
    "frontend",
    "gateway",
    "platform",
    "project",
    "service",
    "system",
    "web",
    "worker",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Group analyzed projects into conservative platforms.")
    parser.add_argument("--workspace-folder", required=True, help="Architecture workspace root.")
    return parser.parse_args()


def safe_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def tokenize(value: str) -> set[str]:
    tokens = {token for token in re.split(r"[^A-Za-z0-9]+", value.lower()) if token}
    return {token for token in tokens if token not in STOP_WORDS and len(token) > 2}


class Grouper:
    def __init__(self, workspace_folder: Path) -> None:
        self.workspace_folder = workspace_folder.resolve()
        self.analyzer_folder = self.workspace_folder / "01-analyzer"
        self.output_folder = self.workspace_folder / "02-grouper"
        self.unknowns: list[str] = []
        self.assumptions: list[str] = []
        self.decisions: list[str] = []

    def run(self) -> None:
        self.output_folder.mkdir(parents=True, exist_ok=True)
        projects = self._load_projects()
        shared_services = self._build_shared_services(projects)
        dependencies = self._build_cross_project_dependencies(projects, shared_services)
        platforms, orphans = self._build_platforms(projects, shared_services, dependencies)
        naming_collisions = self._build_naming_collisions(projects)
        result = {
            "platforms": platforms,
            "shared_services": shared_services,
            "cross_project_dependencies": dependencies,
            "naming_collisions": naming_collisions,
            "orphans": orphans,
            "unknowns": self._dedupe(self.unknowns),
            "assumptions": self._dedupe(self.assumptions),
        }
        self._write_json(result)
        self._write_markdown(result)
        self._append_decisions(result)

    def _load_projects(self) -> list[dict]:
        if not self.analyzer_folder.exists():
            self.unknowns.append("Analyzer folder does not exist under workspace.")
            return []
        loaded: list[dict] = []
        for path in sorted(self.analyzer_folder.rglob("output.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                self.unknowns.append(f"Ignored invalid analyzer output: {path}")
                continue
            if not isinstance(data, dict):
                self.unknowns.append(f"Ignored non-object analyzer output: {path}")
                continue
            project_name = data.get("project_name")
            if not isinstance(project_name, str) or not project_name.strip():
                self.unknowns.append(f"Ignored analyzer output with missing project_name: {path}")
                continue
            loaded.append(
                {
                    "project_name": project_name.strip(),
                    "file_path": str(path),
                    "summary": data.get("summary", ""),
                    "project_type": data.get("project_type", "unknown"),
                    "datastores": self._extract_names(data.get("datastores", []), "name"),
                    "integrations": self._extract_names(data.get("integrations", []), "name"),
                    "auth": self._extract_security_names(data.get("security", {})),
                    "deployable_units": self._to_string_list(data.get("deployable_units", [])),
                    "components": self._extract_names(data.get("components", []), "name"),
                    "evidence": self._collect_evidence(data),
                    "confidence": data.get("overall_confidence", "low"),
                }
            )
        if not loaded:
            self.unknowns.append("No valid analyzer outputs were found under 01-analyzer.")
        return loaded

    def _build_shared_services(self, projects: list[dict]) -> list[dict]:
        usage: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
        known_project_names = {project["project_name"].lower() for project in projects}
        for project in projects:
            project_name = project["project_name"]
            for integration in project["integrations"]:
                normalized = integration.strip()
                if not normalized or normalized.lower() in known_project_names:
                    continue
                usage[normalized][project_name].append(project["file_path"])
            for auth_name in project["auth"]:
                usage[auth_name][project_name].append(project["file_path"])
        shared: list[dict] = []
        for name, used_by in sorted(usage.items()):
            if len(used_by) < 2:
                continue
            evidence = [f"{project}: {', '.join(sorted(set(paths)))}" for project, paths in sorted(used_by.items())]
            confidence = "high" if len(used_by) >= 3 else "medium"
            shared.append(
                {
                    "name": name,
                    "used_by": sorted(used_by.keys()),
                    "evidence": evidence,
                    "confidence": confidence,
                }
            )
        return shared

    def _build_cross_project_dependencies(self, projects: list[dict], shared_services: list[dict]) -> list[dict]:
        project_names = {project["project_name"]: project for project in projects}
        alias_map: dict[str, str] = {}
        for project in projects:
            alias_map[project["project_name"].lower()] = project["project_name"]
            for variant in project["deployable_units"] + project["components"]:
                alias_map[variant.lower()] = project["project_name"]
        dependencies: list[dict] = []
        for project in projects:
            project_name = project["project_name"]
            for integration in project["integrations"]:
                target_project = alias_map.get(integration.lower())
                if target_project and target_project != project_name:
                    dependencies.append(
                        {
                            "source_project": project_name,
                            "target_project_or_service": target_project,
                            "relationship": "Integration name matches another analyzed project or unit.",
                            "evidence": [project["file_path"]],
                            "confidence": "high",
                        }
                    )
            for shared_service in shared_services:
                if project_name not in shared_service["used_by"]:
                    continue
                dependencies.append(
                    {
                        "source_project": project_name,
                        "target_project_or_service": shared_service["name"],
                        "relationship": "Project shares a service or auth dependency with other analyzed projects.",
                        "evidence": [project["file_path"]],
                        "confidence": "medium" if shared_service["confidence"] == "medium" else "high",
                    }
                )
        deduped = self._dedupe_objects(
            dependencies,
            lambda item: (
                item["source_project"],
                item["target_project_or_service"],
                item["relationship"],
            ),
        )
        for item in deduped:
            if item["confidence"] == "medium":
                self.decisions.append(
                    f"uncertain link: {item['source_project']} -> {item['target_project_or_service']} ({item['relationship']})"
                )
        return deduped

    def _build_platforms(
        self,
        projects: list[dict],
        shared_services: list[dict],
        dependencies: list[dict],
    ) -> tuple[list[dict], list[str]]:
        shared_service_map = {item["name"]: item for item in shared_services}
        adjacency: dict[str, set[str]] = defaultdict(set)
        pair_rationale: dict[tuple[str, str], list[str]] = defaultdict(list)
        pair_scores: dict[tuple[str, str], int] = defaultdict(int)
        for i, left in enumerate(projects):
            for right in projects[i + 1 :]:
                pair = tuple(sorted((left["project_name"], right["project_name"])))
                self._score_pair(left, right, dependencies, shared_service_map, pair_scores, pair_rationale, pair)
                if pair_scores[pair] >= 3:
                    adjacency[left["project_name"]].add(right["project_name"])
                    adjacency[right["project_name"]].add(left["project_name"])
                elif pair_scores[pair] > 0:
                    self.decisions.append(
                        f"uncertain grouping: {left['project_name']} <-> {right['project_name']} ({'; '.join(pair_rationale[pair])})"
                    )

        visited: set[str] = set()
        platforms: list[dict] = []
        for project in sorted(projects, key=lambda item: item["project_name"].lower()):
            name = project["project_name"]
            if name in visited or not adjacency.get(name):
                continue
            stack = [name]
            component: list[str] = []
            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                component.append(current)
                stack.extend(sorted(adjacency.get(current, [])))
            if len(component) < 2:
                continue
            component_projects = [self._project_by_name(projects, item) for item in sorted(component)]
            platforms.append(self._build_platform(component_projects, pair_rationale, pair_scores))

        grouped_projects = {project for platform in platforms for project in platform["projects"]}
        orphans = sorted(project["project_name"] for project in projects if project["project_name"] not in grouped_projects)
        return platforms, orphans

    def _score_pair(
        self,
        left: dict,
        right: dict,
        dependencies: list[dict],
        shared_service_map: dict[str, dict],
        pair_scores: dict[tuple[str, str], int],
        pair_rationale: dict[tuple[str, str], list[str]],
        pair: tuple[str, str],
    ) -> None:
        shared_datastores = sorted(set(left["datastores"]) & set(right["datastores"]))
        if shared_datastores:
            pair_scores[pair] += 2
            pair_rationale[pair].append(f"shared datastores: {', '.join(shared_datastores)}")

        shared_integrations = sorted(set(left["integrations"]) & set(right["integrations"]))
        if shared_integrations:
            pair_scores[pair] += 2
            pair_rationale[pair].append(f"shared integrations: {', '.join(shared_integrations)}")

        shared_auth = sorted(set(left["auth"]) & set(right["auth"]))
        if shared_auth:
            pair_scores[pair] += 1
            pair_rationale[pair].append(f"shared auth systems: {', '.join(shared_auth)}")

        shared_tokens = sorted(tokenize(left["project_name"]) & tokenize(right["project_name"]))
        if shared_tokens:
            pair_scores[pair] += 1
            pair_rationale[pair].append(f"name similarity: {', '.join(shared_tokens)}")

        left_to_right = any(
            item["source_project"] == left["project_name"] and item["target_project_or_service"] == right["project_name"]
            for item in dependencies
        )
        right_to_left = any(
            item["source_project"] == right["project_name"] and item["target_project_or_service"] == left["project_name"]
            for item in dependencies
        )
        if left_to_right or right_to_left:
            pair_scores[pair] += 3
            pair_rationale[pair].append("direct cross-project dependency")

        shared_service_links = sorted(
            service["name"]
            for service in shared_service_map.values()
            if left["project_name"] in service["used_by"] and right["project_name"] in service["used_by"]
        )
        if shared_service_links:
            pair_scores[pair] += 1
            pair_rationale[pair].append(f"shared services: {', '.join(shared_service_links)}")

    def _build_platform(
        self,
        projects: list[dict],
        pair_rationale: dict[tuple[str, str], list[str]],
        pair_scores: dict[tuple[str, str], int],
    ) -> dict:
        project_names = [project["project_name"] for project in projects]
        shared_datastores = self._shared_across_projects(projects, "datastores")
        shared_integrations = self._shared_across_projects(projects, "integrations")
        shared_auth = self._shared_across_projects(projects, "auth")
        rationale: list[str] = []
        max_score = 0
        for i, left in enumerate(project_names):
            for right in project_names[i + 1 :]:
                pair = tuple(sorted((left, right)))
                rationale.extend(pair_rationale.get(pair, []))
                max_score = max(max_score, pair_scores.get(pair, 0))
        if shared_auth:
            rationale.append(f"shared auth systems across grouped projects: {', '.join(shared_auth)}")
        name = self._platform_name(project_names, shared_integrations, shared_datastores)
        description_parts = [
            f"Groups {', '.join(project_names)}",
        ]
        if shared_integrations:
            description_parts.append(f"around shared integrations {', '.join(shared_integrations)}")
        elif shared_datastores:
            description_parts.append(f"around shared datastores {', '.join(shared_datastores)}")
        else:
            description_parts.append("based on repeated dependency and naming clues")
        confidence = "high" if max_score >= 5 else "medium"
        return {
            "name": name,
            "description": " ".join(description_parts) + ".",
            "projects": project_names,
            "shared_services": self._dedupe(shared_integrations + shared_auth),
            "shared_datastores": shared_datastores,
            "key_integrations": shared_integrations,
            "grouping_rationale": self._dedupe(rationale) or ["Conservative grouping from repeated cross-project signals."],
            "confidence": confidence,
        }

    def _build_naming_collisions(self, projects: list[dict]) -> list[dict]:
        buckets: dict[str, set[str]] = defaultdict(set)
        for project in projects:
            canonical = safe_slug(project["project_name"])
            if canonical:
                buckets[canonical].add(project["project_name"])
            for variant in project["deployable_units"]:
                if safe_slug(variant) == canonical:
                    continue
                if tokenize(variant) & tokenize(project["project_name"]):
                    buckets[canonical].add(variant)
        collisions: list[dict] = []
        for canonical, variants in sorted(buckets.items()):
            if len(variants) < 2:
                continue
            sorted_variants = sorted(variants)
            collisions.append(
                {
                    "canonical_candidate": canonical,
                    "variants": sorted_variants,
                    "notes": ["Name variants share normalized tokens and may refer to the same logical capability."],
                }
            )
        return collisions

    def _write_json(self, result: dict) -> None:
        output_path = self.output_folder / "grouped.json"
        output_path.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    def _write_markdown(self, result: dict) -> None:
        output_path = self.output_folder / "grouped.md"
        generated_at = datetime.now(timezone.utc).isoformat()
        lines = [
            f"generated_at: {generated_at}",
            "source_skill: tas-02-architecture-project-grouper",
            f"workspace_folder: {self.workspace_folder}",
            "",
            "# 1. Platforms",
        ]
        lines.extend(self._render_platforms(result["platforms"]))
        lines.extend(["", "# 2. Shared Services"])
        lines.extend(self._render_named_objects(result["shared_services"], ["used_by", "evidence", "confidence"]))
        lines.extend(["", "# 3. Dependencies"])
        lines.extend(
            self._render_named_objects(
                [
                    {
                        "name": f"{item['source_project']} -> {item['target_project_or_service']}",
                        "relationship": item["relationship"],
                        "evidence": item["evidence"],
                        "confidence": item["confidence"],
                    }
                    for item in result["cross_project_dependencies"]
                ],
                ["relationship", "evidence", "confidence"],
            )
        )
        lines.extend(["", "# 4. Orphans"])
        lines.extend(self._render_strings(result["orphans"]))
        lines.extend(["", "# 5. Naming Collisions"])
        lines.extend(
            self._render_named_objects(
                [
                    {
                        "name": item["canonical_candidate"],
                        "variants": item["variants"],
                        "notes": item["notes"],
                    }
                    for item in result["naming_collisions"]
                ],
                ["variants", "notes"],
            )
        )
        lines.extend(["", "# 6. Unknowns"])
        lines.extend(self._render_strings(result["unknowns"]))
        lines.extend(["", "# 7. Assumptions"])
        lines.extend(self._render_strings(result["assumptions"]))
        output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    def _append_decisions(self, result: dict) -> None:
        output_path = self.output_folder / "decisions.md"
        generated_at = datetime.now(timezone.utc).isoformat()
        lines = [f"## {generated_at}"]
        for assumption in result["assumptions"]:
            lines.append(f"- grouping assumption: {assumption}")
        for decision in self._dedupe(self.decisions):
            lines.append(f"- {decision}")
        if len(lines) == 1:
            lines.append("- grouping assumption: No grouping assumptions or uncertain links were recorded for this run.")
        lines.append("")
        with output_path.open("a", encoding="utf-8") as handle:
            handle.write("\n".join(lines))

    @staticmethod
    def _extract_names(items: object, key: str) -> list[str]:
        if not isinstance(items, list):
            return []
        names: list[str] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                names.append(value.strip())
        return Grouper._dedupe(names)

    @staticmethod
    def _to_string_list(items: object) -> list[str]:
        if not isinstance(items, list):
            return []
        return Grouper._dedupe([item.strip() for item in items if isinstance(item, str) and item.strip()])

    @staticmethod
    def _extract_security_names(security: object) -> list[str]:
        if not isinstance(security, dict):
            return []
        values: list[str] = []
        for key in ("authentication", "authorization"):
            values.extend(Grouper._to_string_list(security.get(key, [])))
        normalized: list[str] = []
        for value in values:
            lowered = value.lower()
            if "jwt" in lowered:
                normalized.append("JWT")
            elif "openid" in lowered or "oidc" in lowered:
                normalized.append("OpenID Connect")
            elif "identity" in lowered:
                normalized.append("Identity")
            elif "auth0" in lowered:
                normalized.append("Auth0")
            elif "azuread" in lowered or "azure ad" in lowered:
                normalized.append("Azure AD")
        return Grouper._dedupe(normalized)

    @staticmethod
    def _collect_evidence(data: dict) -> list[str]:
        evidence: list[str] = []
        for collection_name in ("components", "datastores", "integrations"):
            collection = data.get(collection_name, [])
            if not isinstance(collection, list):
                continue
            for item in collection:
                if not isinstance(item, dict):
                    continue
                evidence.extend(Grouper._to_string_list(item.get("evidence", [])))
        return Grouper._dedupe(evidence)

    @staticmethod
    def _shared_across_projects(projects: list[dict], field: str) -> list[str]:
        if len(projects) < 2:
            return []
        shared = set(projects[0].get(field, []))
        for project in projects[1:]:
            shared &= set(project.get(field, []))
        return sorted(shared)

    @staticmethod
    def _platform_name(project_names: list[str], shared_integrations: list[str], shared_datastores: list[str]) -> str:
        token_counts: dict[str, int] = defaultdict(int)
        for name in project_names:
            for token in tokenize(name):
                token_counts[token] += 1
        common_tokens = [token for token, count in token_counts.items() if count >= 2]
        if common_tokens:
            return "-".join(sorted(common_tokens)) + "-platform"
        if shared_integrations:
            return safe_slug(shared_integrations[0]) + "-platform"
        if shared_datastores:
            return safe_slug(shared_datastores[0]) + "-platform"
        return safe_slug(project_names[0]) + "-platform"

    @staticmethod
    def _project_by_name(projects: list[dict], name: str) -> dict:
        for project in projects:
            if project["project_name"] == name:
                return project
        raise KeyError(name)

    @staticmethod
    def _render_platforms(platforms: list[dict]) -> list[str]:
        if not platforms:
            return ["- none"]
        lines: list[str] = []
        for item in platforms:
            lines.append(f"- {item['name']}")
            lines.append(f"  - Description: {item['description']}")
            lines.append(f"  - Projects: {', '.join(item['projects']) or 'none'}")
            lines.append(f"  - Shared Services: {', '.join(item['shared_services']) or 'none'}")
            lines.append(f"  - Shared Datastores: {', '.join(item['shared_datastores']) or 'none'}")
            lines.append(f"  - Key Integrations: {', '.join(item['key_integrations']) or 'none'}")
            lines.append(f"  - Grouping Rationale: {'; '.join(item['grouping_rationale']) or 'none'}")
            lines.append(f"  - Confidence: {item['confidence']}")
        return lines

    @staticmethod
    def _render_named_objects(items: list[dict], fields: list[str]) -> list[str]:
        if not items:
            return ["- none"]
        lines: list[str] = []
        for item in items:
            lines.append(f"- {item['name']}")
            for field in fields:
                value = item.get(field, [])
                if isinstance(value, list):
                    value_text = ", ".join(value) if value else "none"
                else:
                    value_text = value or "none"
                lines.append(f"  - {field.replace('_', ' ').title()}: {value_text}")
        return lines

    @staticmethod
    def _render_strings(items: list[str]) -> list[str]:
        return [f"- {item}" for item in items] if items else ["- none"]

    @staticmethod
    def _dedupe(items: Iterable[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            if not item or item in seen:
                continue
            seen.add(item)
            result.append(item)
        return result

    @staticmethod
    def _dedupe_objects(items: list[dict], key_func) -> list[dict]:
        seen = set()
        result: list[dict] = []
        for item in items:
            key = key_func(item)
            if key in seen:
                continue
            seen.add(key)
            result.append(item)
        return result


def main() -> int:
    args = parse_args()
    workspace_folder = Path(args.workspace_folder)
    workspace_folder.mkdir(parents=True, exist_ok=True)
    grouper = Grouper(workspace_folder)
    grouper.run()
    print(grouper.output_folder)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
