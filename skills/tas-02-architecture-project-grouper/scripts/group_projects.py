#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


STOP_WORDS = {"api", "app", "application", "backend", "core", "frontend", "gateway", "platform", "project", "service", "system", "web", "worker"}
INTERNAL_SUFFIXES = (".internal", ".local", ".svc", ".cluster.local")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Group analyzed projects into conservative platforms.")
    parser.add_argument("--workspace-folder", required=True, help="Architecture workspace root.")
    return parser.parse_args()


def safe_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def tokenize(value: str) -> set[str]:
    tokens = {token for token in re.split(r"[^A-Za-z0-9]+", value.lower()) if token}
    return {token for token in tokens if token not in STOP_WORDS and len(token) > 2}


def dedupe(items) -> list:
    seen = set()
    result = []
    for item in items:
        marker = json.dumps(item, sort_keys=True) if isinstance(item, dict) else str(item)
        if not item or marker in seen:
            continue
        seen.add(marker)
        result.append(item)
    return result


def to_string(value: object, default: str = "") -> str:
    return value.strip() if isinstance(value, str) and value.strip() else default


def to_string_list(items: object) -> list[str]:
    if not isinstance(items, list):
        return []
    return dedupe([item.strip() for item in items if isinstance(item, str) and item.strip()])


def to_dict_list(items: object) -> list[dict]:
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def normalize_confidence(value: object) -> str:
    return value if isinstance(value, str) and value in {"high", "medium", "low"} else "low"


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
        dependencies = self._build_dependencies(projects, shared_services)
        platforms, orphans = self._build_platforms(projects, shared_services, dependencies)
        result = {
            "platforms": platforms,
            "shared_services": shared_services,
            "cross_project_dependencies": dependencies,
            "naming_collisions": self._build_naming_collisions(projects),
            "orphans": orphans,
            "unknowns": dedupe(self.unknowns),
            "assumptions": dedupe(self.assumptions),
        }
        self._write_json(result)
        self._write_markdown(result, len(projects))
        self._append_decisions(result, len(projects))

    def _load_projects(self) -> list[dict]:
        if not self.analyzer_folder.exists():
            self.unknowns.append("Analyzer folder does not exist under workspace.")
            return []
        raw = []
        for path in sorted(self.analyzer_folder.rglob("output.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                self.unknowns.append(f"Ignored invalid analyzer output: {path}")
                continue
            name = to_string(data.get("project_name"))
            if not name:
                self.unknowns.append(f"Ignored analyzer output with missing project_name: {path}")
                continue
            security = data.get("security", {}) if isinstance(data.get("security", {}), dict) else {}
            deployment = data.get("deployment", {}) if isinstance(data.get("deployment", {}), dict) else {}
            interfaces = data.get("interfaces", {}) if isinstance(data.get("interfaces", {}), dict) else {}
            raw.append(
                {
                    "project_name": name,
                    "file_path": str(path),
                    "summary": to_string(data.get("summary")),
                    "business_context": to_string(data.get("business_context"), "No data available"),
                    "project_type": to_string(data.get("project_type"), "unknown"),
                    "primary_stack": to_string_list(data.get("primary_stack", [])),
                    "entry_points": to_string_list(data.get("entry_points", [])),
                    "deployable_units": to_string_list(data.get("deployable_units", [])),
                    "components": to_dict_list(data.get("components", [])),
                    "datastores": to_dict_list(data.get("datastores", [])),
                    "integrations": to_dict_list(data.get("integrations", [])),
                    "interfaces": {
                        "inbound": to_string_list(interfaces.get("inbound", [])),
                        "outbound": to_string_list(interfaces.get("outbound", [])),
                    },
                    "security": {
                        "authentication": to_string_list(security.get("authentication", [])),
                        "authorization": to_string_list(security.get("authorization", [])),
                        "secrets_handling": to_string_list(security.get("secrets_handling", [])),
                        "confidence": normalize_confidence(security.get("confidence")),
                    },
                    "deployment": {
                        "hosting_clues": to_string_list(deployment.get("hosting_clues", [])),
                        "ci_cd_clues": to_string_list(deployment.get("ci_cd_clues", [])),
                        "runtime_clues": to_string_list(deployment.get("runtime_clues", [])),
                        "confidence": normalize_confidence(deployment.get("confidence")),
                    },
                    "observed_facts": to_string_list(data.get("observed_facts", [])),
                    "inferred_facts": to_string_list(data.get("inferred_facts", [])),
                    "unknowns": to_string_list(data.get("unknowns", [])),
                    "risks": to_string_list(data.get("risks", [])),
                    "assumptions": to_string_list(data.get("assumptions", [])),
                    "overall_confidence": normalize_confidence(data.get("overall_confidence")),
                }
            )
        if not raw:
            self.unknowns.append("No valid analyzer outputs were found under 01-analyzer.")
            return []
        alias_map = self._build_alias_map(raw)
        return [self._normalize_project(project, alias_map) for project in raw]

    def _build_alias_map(self, projects: list[dict]) -> dict[str, str]:
        aliases: dict[str, str] = {}
        for project in projects:
            for value in [project["project_name"]] + [item.get("name", "") for item in project["components"]] + project["deployable_units"]:
                for alias in self._aliases(value):
                    aliases.setdefault(alias, project["project_name"])
        return aliases

    def _normalize_project(self, project: dict, alias_map: dict[str, str]) -> dict:
        project["normalized_auth"] = self._infer_auth(project)
        project["normalized_dependencies"] = self._infer_dependencies(project, alias_map)
        return project

    def _infer_auth(self, project: dict) -> list[dict]:
        catalog = {
            "Auth0": ("auth0",),
            "Keycloak": ("keycloak",),
            "OpenID Connect": ("openid", "oidc"),
            "OAuth 2.0": ("oauth",),
            "JWT": ("jwt", "bearer"),
            "Azure AD": ("azuread", "azure ad", "entra"),
            "Identity": ("identity",),
        }
        evidence_sources = (
            project["security"]["authentication"]
            + project["security"]["authorization"]
            + [item.get("name", "") for item in project["integrations"]]
            + project["observed_facts"]
            + ([project["summary"]] if project["summary"] else [])
        )
        found = []
        for label, needles in catalog.items():
            evidence = [source for source in evidence_sources if any(needle in source.lower() for needle in needles)]
            if evidence:
                confidence = "high" if len(evidence) > 1 else "medium"
                found.append({"name": label, "evidence": dedupe(evidence)[:3], "confidence": confidence})
                self.decisions.append(f"inferred auth mapping: {project['project_name']} -> {label} ({confidence})")
        return found

    def _infer_dependencies(self, project: dict, alias_map: dict[str, str]) -> list[dict]:
        results = []
        for integration in project["integrations"]:
            name = to_string(integration.get("name"))
            if not name:
                continue
            integration_type = to_string(integration.get("type"), "unknown").lower()
            candidates = {alias_map[alias] for alias in self._aliases(name) if alias in alias_map and alias_map[alias] != project["project_name"]}
            for target in sorted(candidates):
                confidence = "high" if integration_type == "internal" or name.lower().endswith(INTERNAL_SUFFIXES) else "medium"
                results.append({"target": target, "source_name": name, "confidence": confidence})
                self.decisions.append(f"inferred internal dependency: {project['project_name']} -> {target} from '{name}' ({confidence})")
        return dedupe(results)
    def _build_shared_services(self, projects: list[dict]) -> list[dict]:
        usage: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
        project_names = {project["project_name"].lower() for project in projects}
        for project in projects:
            for integration in project["integrations"]:
                name = to_string(integration.get("name"))
                if name and name.lower() not in project_names:
                    usage[name][project["project_name"]].append(project["file_path"])
            for auth in project["normalized_auth"]:
                usage[auth["name"]][project["project_name"]].append(project["file_path"])
        result = []
        for name, used_by in sorted(usage.items()):
            if len(used_by) < 2:
                continue
            result.append(
                {
                    "name": name,
                    "used_by": sorted(used_by.keys()),
                    "evidence": [f"{project}: {', '.join(sorted(set(paths)))}" for project, paths in sorted(used_by.items())],
                    "confidence": "high" if len(used_by) >= 3 else "medium",
                }
            )
        return result

    def _build_dependencies(self, projects: list[dict], shared_services: list[dict]) -> list[dict]:
        deps = []
        for project in projects:
            for item in project["normalized_dependencies"]:
                deps.append(
                    {
                        "source_project": project["project_name"],
                        "target_project_or_service": item["target"],
                        "relationship": "Normalized internal integration matches another analyzed project or unit.",
                        "evidence": [item["source_name"], project["file_path"]],
                        "confidence": item["confidence"],
                    }
                )
            for shared_service in shared_services:
                if project["project_name"] in shared_service["used_by"]:
                    deps.append(
                        {
                            "source_project": project["project_name"],
                            "target_project_or_service": shared_service["name"],
                            "relationship": "Project shares a normalized service, integration, or auth dependency with other analyzed projects.",
                            "evidence": [project["file_path"]],
                            "confidence": "medium" if shared_service["confidence"] == "medium" else "high",
                        }
                    )
        return dedupe(deps)

    def _build_platforms(self, projects: list[dict], shared_services: list[dict], dependencies: list[dict]) -> tuple[list[dict], list[dict]]:
        adjacency: dict[str, set[str]] = defaultdict(set)
        pair_rationale: dict[tuple[str, str], list[str]] = defaultdict(list)
        pair_scores: dict[tuple[str, str], int] = defaultdict(int)
        pair_strong: dict[tuple[str, str], bool] = defaultdict(bool)
        service_map = {item["name"]: item for item in shared_services}
        for index, left in enumerate(projects):
            for right in projects[index + 1 :]:
                pair = tuple(sorted((left["project_name"], right["project_name"])))
                self._score_pair(left, right, dependencies, service_map, pair, pair_scores, pair_rationale, pair_strong)
                if pair_scores[pair] >= 3 and pair_strong[pair]:
                    adjacency[left["project_name"]].add(right["project_name"])
                    adjacency[right["project_name"]].add(left["project_name"])
                elif pair_scores[pair] > 0:
                    self.decisions.append(f"rejected grouping: {left['project_name']} <-> {right['project_name']} ({'; '.join(pair_rationale[pair])})")
        visited = set()
        platforms = []
        for project in sorted(projects, key=lambda item: item["project_name"].lower()):
            if project["project_name"] in visited or not adjacency.get(project["project_name"]):
                continue
            stack = [project["project_name"]]
            members = []
            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                members.append(current)
                stack.extend(sorted(adjacency.get(current, [])))
            if len(members) > 1:
                component_projects = [self._find_project(projects, name) for name in sorted(members)]
                platforms.append(self._build_platform(component_projects, pair_scores, pair_rationale, dependencies))
        grouped = {name for platform in platforms for name in platform["projects"]}
        orphans = []
        for project in sorted(projects, key=lambda item: item["project_name"].lower()):
            if project["project_name"] in grouped:
                continue
            orphans.append(
                {
                    "project_name": project["project_name"],
                    "summary": project["summary"] or "No data available",
                    "reasons_not_grouped": ["No peer project met the minimum score with at least one non-name signal."],
                    "observed_signals": dedupe(
                        [item.get("name", "") for item in project["datastores"][:2]]
                        + [item.get("name", "") for item in project["integrations"][:2]]
                        + [item["name"] for item in project["normalized_auth"][:2]]
                    ) or ["No strong shared signals found."],
                    "unknowns": project["unknowns"][:3] or ["No data available"],
                    "confidence": project["overall_confidence"],
                }
            )
        return platforms, orphans

    def _score_pair(self, left: dict, right: dict, dependencies: list[dict], service_map: dict[str, dict], pair: tuple[str, str], scores: dict, rationale: dict, strong: dict) -> None:
        left_ds = {item.get("name", "") for item in left["datastores"]}
        right_ds = {item.get("name", "") for item in right["datastores"]}
        shared_ds = sorted(left_ds & right_ds)
        if shared_ds:
            scores[pair] += 2
            strong[pair] = True
            rationale[pair].append(f"shared datastores: {', '.join(shared_ds)}")
        left_i = {item.get("name", "") for item in left["integrations"]}
        right_i = {item.get("name", "") for item in right["integrations"]}
        shared_i = sorted(left_i & right_i)
        if shared_i:
            scores[pair] += 2
            strong[pair] = True
            rationale[pair].append(f"shared integrations: {', '.join(shared_i)}")
        left_auth = {item["name"] for item in left["normalized_auth"]}
        right_auth = {item["name"] for item in right["normalized_auth"]}
        shared_auth = sorted(left_auth & right_auth)
        if shared_auth:
            scores[pair] += 1
            strong[pair] = True
            rationale[pair].append(f"shared auth systems: {', '.join(shared_auth)}")
        shared_stack = sorted(set(left["primary_stack"]) & set(right["primary_stack"]))
        if shared_stack:
            scores[pair] += 1
            rationale[pair].append(f"shared stack clues: {', '.join(shared_stack[:3])}")
        shared_names = sorted(tokenize(left["project_name"]) & tokenize(right["project_name"]))
        if shared_names:
            scores[pair] += 1
            rationale[pair].append(f"name similarity: {', '.join(shared_names)}")
        direct_dep = any(
            item["source_project"] in pair and item["target_project_or_service"] in pair and item["source_project"] != item["target_project_or_service"]
            for item in dependencies
        )
        if direct_dep:
            scores[pair] += 3
            strong[pair] = True
            rationale[pair].append("direct normalized cross-project dependency")
        shared_services = sorted(name for name, service in service_map.items() if left["project_name"] in service["used_by"] and right["project_name"] in service["used_by"])
        if shared_services:
            scores[pair] += 1
            strong[pair] = True
            rationale[pair].append(f"shared services: {', '.join(shared_services)}")
    def _build_platform(self, projects: list[dict], pair_scores: dict, pair_rationale: dict, dependencies: list[dict]) -> dict:
        names = [project["project_name"] for project in projects]
        shared_datastores = self._shared_named_objects(projects, "datastores")
        shared_integrations = self._shared_named_objects(projects, "integrations")
        shared_auth = self._shared_auth(projects)
        rationale = []
        max_score = 0
        for index, left in enumerate(names):
            for right in names[index + 1 :]:
                pair = tuple(sorted((left, right)))
                rationale.extend(pair_rationale.get(pair, []))
                max_score = max(max_score, pair_scores.get(pair, 0))
        platform_deps = [item for item in dependencies if item["source_project"] in names and item["target_project_or_service"] in names]
        stack_counts = defaultdict(int)
        for project in projects:
            for stack in project["primary_stack"]:
                stack_counts[stack] += 1
        primary_stack = [value for value, _ in sorted(stack_counts.items(), key=lambda item: (-item[1], item[0].lower()))]
        return {
            "name": self._platform_name(names, shared_integrations, shared_datastores),
            "summary": self._platform_summary(projects, shared_datastores, shared_integrations, primary_stack),
            "business_context": next((project["business_context"] for project in projects if project["business_context"] != "No data available"), "No data available"),
            "platform_type": f"{projects[0]['project_type']}-platform" if len({project['project_type'] for project in projects}) == 1 else "mixed-platform",
            "description": self._platform_description(names, shared_datastores, shared_integrations),
            "projects": names,
            "primary_stack": primary_stack,
            "entry_surfaces": dedupe([entry for project in projects for entry in project["interfaces"]["inbound"]][:8] + [entry for project in projects for entry in project["entry_points"]][:4]),
            "deployable_units": dedupe([unit for project in projects for unit in project["deployable_units"]]),
            "components": dedupe([item for project in projects for item in project["components"]]),
            "datastores": dedupe([item for project in projects for item in project["datastores"]]),
            "interfaces": {
                "inbound": dedupe([entry for project in projects for entry in project["interfaces"]["inbound"]]),
                "outbound": dedupe([entry for project in projects for entry in project["interfaces"]["outbound"]]),
            },
            "integrations": dedupe([item for project in projects for item in project["integrations"]]),
            "security": {
                "auth_systems": dedupe([item["name"] for project in projects for item in project["normalized_auth"]]),
                "secrets_handling": dedupe([entry for project in projects for entry in project["security"]["secrets_handling"]]),
                "confidence": "high" if any(project["security"]["confidence"] == "high" for project in projects) else "medium",
            },
            "deployment": {
                "hosting_clues": dedupe([entry for project in projects for entry in project["deployment"]["hosting_clues"]]),
                "ci_cd_clues": dedupe([entry for project in projects for entry in project["deployment"]["ci_cd_clues"]]),
                "runtime_clues": dedupe([entry for project in projects for entry in project["deployment"]["runtime_clues"]]),
                "confidence": "high" if any(project["deployment"]["confidence"] == "high" for project in projects) else "medium",
            },
            "shared_services": dedupe(shared_integrations + shared_auth),
            "shared_datastores": shared_datastores,
            "key_integrations": shared_integrations,
            "cross_project_dependencies": platform_deps,
            "observed_facts": dedupe([fact for project in projects for fact in project["observed_facts"]]),
            "inferred_facts": dedupe([fact for project in projects for fact in project["inferred_facts"]] + [f"Platform grouping inferred from {'; '.join(dedupe(rationale)[:3]) or 'repeated cross-project signals'}"]),
            "unknowns": dedupe([fact for project in projects for fact in project["unknowns"]]),
            "risks": dedupe([fact for project in projects for fact in project["risks"]]),
            "assumptions": dedupe([fact for project in projects for fact in project["assumptions"]]),
            "grouping_rationale": dedupe(rationale) or ["Conservative grouping from repeated cross-project signals."],
            "confidence": "high" if max_score >= 5 else "medium",
        }

    def _shared_named_objects(self, projects: list[dict], field: str) -> list[str]:
        shared = {item.get("name", "") for item in projects[0][field]}
        for project in projects[1:]:
            shared &= {item.get("name", "") for item in project[field]}
        return sorted(item for item in shared if item)

    def _shared_auth(self, projects: list[dict]) -> list[str]:
        shared = {item["name"] for item in projects[0]["normalized_auth"]}
        for project in projects[1:]:
            shared &= {item["name"] for item in project["normalized_auth"]}
        return sorted(shared)

    def _platform_name(self, names: list[str], shared_integrations: list[str], shared_datastores: list[str]) -> str:
        token_counts = defaultdict(int)
        for name in names:
            for token in tokenize(name):
                token_counts[token] += 1
        common = [token for token, count in token_counts.items() if count >= 2]
        if common:
            return "-".join(sorted(common)) + "-platform"
        if shared_integrations:
            return safe_slug(shared_integrations[0]) + "-platform"
        if shared_datastores:
            return safe_slug(shared_datastores[0]) + "-platform"
        return safe_slug(names[0]) + "-platform"

    def _platform_summary(self, projects: list[dict], shared_datastores: list[str], shared_integrations: list[str], primary_stack: list[str]) -> str:
        project_types = dedupe([project["project_type"] for project in projects])
        return (
            f"Platform formed from {', '.join(project['project_name'] for project in projects)}, "
            f"covering {', '.join(project_types) or 'unknown project types'}, "
            f"with stack clues {', '.join(primary_stack[:4]) or 'unknown stack'}, "
            f"{', '.join(shared_datastores[:3]) or 'no clearly shared datastore'}, and "
            f"{', '.join(shared_integrations[:3]) or 'no clearly shared integration'}."
        )

    def _platform_description(self, names: list[str], shared_datastores: list[str], shared_integrations: list[str]) -> str:
        if shared_integrations:
            return f"Groups {', '.join(names)} around shared integrations {', '.join(shared_integrations)}."
        if shared_datastores:
            return f"Groups {', '.join(names)} around shared datastores {', '.join(shared_datastores)}."
        return f"Groups {', '.join(names)} from repeated cross-project signals."

    def _build_naming_collisions(self, projects: list[dict]) -> list[dict]:
        buckets: dict[str, set[str]] = defaultdict(set)
        for project in projects:
            canonical = safe_slug(project["project_name"])
            buckets[canonical].add(project["project_name"])
            for variant in project["deployable_units"]:
                if safe_slug(variant) != canonical and tokenize(variant) & tokenize(project["project_name"]):
                    buckets[canonical].add(variant)
        result = []
        for canonical, variants in sorted(buckets.items()):
            if len(variants) > 1:
                result.append({"canonical_candidate": canonical, "variants": sorted(variants), "notes": ["Name variants share normalized tokens and may refer to the same logical capability."]})
        return result

    def _find_project(self, projects: list[dict], name: str) -> dict:
        for project in projects:
            if project["project_name"] == name:
                return project
        raise KeyError(name)

    def _aliases(self, value: str) -> list[str]:
        variants = {value.lower(), safe_slug(value)}
        variants.update(tokenize(value))
        for part in re.split(r"[./_-]+", value.lower()):
            if part:
                variants.add(part)
                variants.add(safe_slug(part))
        return [item for item in variants if item]

    def _write_json(self, result: dict) -> None:
        (self.output_folder / "grouped.json").write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    def _write_markdown(self, result: dict, project_count: int) -> None:
        lines = [
            "---",
            "document_type: architecture-grouping",
            f"generated_at: {datetime.now(timezone.utc).isoformat()}",
            "source_skill: tas-02-architecture-project-grouper",
            f"workspace_folder: {self.workspace_folder}",
            "---",
            "",
            "# Project Grouping Summary",
            "",
            "> Confidence note: This document may include both observed and inferred architecture facts. Review unknowns and assumptions before treating the document as authoritative.",
            ">",
            "> Source: Generated automatically from analyzer outputs plus conservative normalization.",
            "> Review status: Not reviewed / Partially reviewed / Reviewed",
            "",
            "## 1. Overview",
            "",
            f"Projects analyzed: {project_count}",
            f"Platforms proposed: {len(result['platforms'])}",
            f"Shared services identified: {len(result['shared_services'])}",
            f"Orphans: {len(result['orphans'])}",
            "",
            "## 2. Platform Summaries",
        ]
        if not result["platforms"]:
            lines.append("- none")
        for platform in result["platforms"]:
            lines.extend(
                [
                    f"### {platform['name']}",
                    "",
                    f"Summary: {platform['summary']}",
                    f"Business context: {platform['business_context']}",
                    f"Platform type: {platform['platform_type']}",
                    f"Projects: {', '.join(platform['projects']) or 'No data available'}",
                    f"Primary stack: {', '.join(platform['primary_stack']) or 'No data available'}",
                    f"Confidence: {platform['confidence']}",
                    "",
                ]
            )
        lines.extend(["## 3. Grouping Rationale", ""])
        lines.extend([f"- {platform['name']}: {'; '.join(platform['grouping_rationale'])}" for platform in result["platforms"]] or ["- none"])
        lines.extend(["", "## 4. Shared Services", ""])
        lines.extend(self._render_named(result["shared_services"], ["used_by", "evidence", "confidence"]))
        lines.extend(["", "## 5. Cross-Project Dependencies", ""])
        lines.extend(self._render_named([{"name": f"{item['source_project']} -> {item['target_project_or_service']}", **item} for item in result["cross_project_dependencies"]], ["relationship", "evidence", "confidence"]))
        lines.extend(["", "## 6. Architecture Overview by Platform", ""])
        for platform in result["platforms"]:
            lines.append(f"- {platform['name']}")
            lines.append(f"  - Entry Surfaces: {', '.join(platform['entry_surfaces']) or 'No data available'}")
            lines.append(f"  - Deployable Units: {', '.join(platform['deployable_units']) or 'No data available'}")
            lines.append(f"  - Shared Services: {', '.join(platform['shared_services']) or 'No data available'}")
            lines.append(f"  - Shared Datastores: {', '.join(platform['shared_datastores']) or 'No data available'}")
        if not result["platforms"]:
            lines.append("- none")
        lines.extend(["", "## 7. Data Stores", ""])
        for platform in result["platforms"]:
            lines.append(f"- {platform['name']}: {', '.join(item.get('name', '') for item in platform['datastores']) or 'No data available'}")
        if not result["platforms"]:
            lines.append("- none")
        lines.extend(["", "## 8. Interfaces & Integrations", ""])
        for platform in result["platforms"]:
            lines.append(f"- {platform['name']}")
            lines.append(f"  - Inbound: {', '.join(platform['interfaces']['inbound']) or 'No data available'}")
            lines.append(f"  - Outbound: {', '.join(platform['interfaces']['outbound']) or 'No data available'}")
            lines.append(f"  - Integrations: {', '.join(item.get('name', '') for item in platform['integrations']) or 'No data available'}")
        if not result["platforms"]:
            lines.append("- none")
        lines.extend(["", "## 9. Security", ""])
        for platform in result["platforms"]:
            lines.append(f"- {platform['name']}: auth={', '.join(platform['security']['auth_systems']) or 'No data available'}; secrets={', '.join(platform['security']['secrets_handling']) or 'No data available'}; confidence={platform['security']['confidence']}")
        if not result["platforms"]:
            lines.append("- none")
        lines.extend(["", "## 10. Deployment", ""])
        for platform in result["platforms"]:
            lines.append(f"- {platform['name']}: hosting={', '.join(platform['deployment']['hosting_clues']) or 'No data available'}; cicd={', '.join(platform['deployment']['ci_cd_clues']) or 'No data available'}; runtime={', '.join(platform['deployment']['runtime_clues']) or 'No data available'}; confidence={platform['deployment']['confidence']}")
        if not result["platforms"]:
            lines.append("- none")
        lines.extend(["", "## 11. Orphans", ""])
        for orphan in result["orphans"]:
            lines.append(f"- {orphan['project_name']}: {orphan['summary']}")
            lines.append(f"  - Reasons Not Grouped: {', '.join(orphan['reasons_not_grouped'])}")
            lines.append(f"  - Observed Signals: {', '.join(orphan['observed_signals'])}")
            lines.append(f"  - Unknowns: {', '.join(orphan['unknowns'])}")
            lines.append(f"  - Confidence: {orphan['confidence']}")
        if not result["orphans"]:
            lines.append("- none")
        lines.extend(["", "## 12. Naming Collisions", ""])
        lines.extend(self._render_named([{"name": item["canonical_candidate"], **item} for item in result["naming_collisions"]], ["variants", "notes"]))
        lines.extend(["", "## 13. Observed Facts", ""])
        for platform in result["platforms"]:
            lines.append(f"- {platform['name']}: {', '.join(platform['observed_facts'][:8]) or 'No data available'}")
        if not result["platforms"]:
            lines.append("- none")
        lines.extend(["", "## 14. Inferred Facts", ""])
        for platform in result["platforms"]:
            lines.append(f"- {platform['name']}: {', '.join(platform['inferred_facts'][:8]) or 'No data available'}")
        if not result["platforms"]:
            lines.append("- none")
        lines.extend(["", "## 15. Unknowns", ""])
        for platform in result["platforms"]:
            lines.append(f"- {platform['name']}: {', '.join(platform['unknowns'][:8]) or 'No data available'}")
        lines.extend([f"- {item}" for item in result["unknowns"]] or ["- none"])
        lines.extend(["", "## 16. Risks and Assumptions", "", "### Risks"])
        for platform in result["platforms"]:
            lines.append(f"- {platform['name']}: {', '.join(platform['risks'][:8]) or 'No data available'}")
        if not result["platforms"]:
            lines.append("- none")
        lines.extend(["", "### Assumptions"])
        for platform in result["platforms"]:
            lines.append(f"- {platform['name']}: {', '.join(platform['assumptions'][:8]) or 'No data available'}")
        lines.extend([f"- {item}" for item in result["assumptions"]] or ["- none"])
        (self.output_folder / "grouped.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    def _render_named(self, items: list[dict], fields: list[str]) -> list[str]:
        if not items:
            return ["- none"]
        lines = []
        for item in items:
            lines.append(f"- {item['name']}")
            for field in fields:
                value = item.get(field, [])
                if isinstance(value, list):
                    text = ", ".join(str(entry) for entry in value) or "No data available"
                else:
                    text = str(value) if value else "No data available"
                lines.append(f"  - {field.replace('_', ' ').title()}: {text}")
        return lines

    def _append_decisions(self, result: dict, project_count: int) -> None:
        lines = [
            f"## {datetime.now(timezone.utc).isoformat()}",
            f"- workspace folder: {self.workspace_folder}",
            f"- projects processed: {project_count}",
        ]
        lines.extend([f"- grouping assumption: {item}" for item in result["assumptions"]])
        lines.extend([f"- {item}" for item in dedupe(self.decisions)])
        if len(lines) == 3:
            lines.append("- grouping assumption: No grouping assumptions or uncertain links were recorded for this run.")
        lines.append("")
        with (self.output_folder / "decisions.md").open("a", encoding="utf-8") as handle:
            handle.write("\n".join(lines))


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
