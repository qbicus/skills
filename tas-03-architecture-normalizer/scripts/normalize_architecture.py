#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ENTITY_TYPES = ("project", "service", "datastore", "integration", "platform")
VALID_CONFIDENCE = {"high", "medium", "low"}
ABBREVIATIONS = {
    "api": "API",
    "db": "DB",
    "id": "ID",
    "jwt": "JWT",
    "oidc": "OIDC",
    "sql": "SQL",
    "ui": "UI",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize architecture entities from analyzer and grouper outputs.")
    parser.add_argument("--workspace-folder", required=True, help="Architecture workspace root.")
    parser.add_argument("--alias-map", required=False, help="Optional alias mapping JSON file.")
    return parser.parse_args()


def normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def tokenize(value: str) -> list[str]:
    return [token for token in re.split(r"[^A-Za-z0-9]+", value) if token]


def titleize(value: str) -> str:
    parts = []
    for token in tokenize(value):
        lowered = token.lower()
        parts.append(ABBREVIATIONS.get(lowered, token[:1].upper() + token[1:].lower()))
    return " ".join(parts) if parts else value


class Normalizer:
    def __init__(self, workspace_folder: Path, alias_map_path: Path | None) -> None:
        self.workspace_folder = workspace_folder.resolve()
        self.analyzer_folder = self.workspace_folder / "01-analyzer"
        self.grouper_path = self.workspace_folder / "02-grouper" / "grouped.json"
        self.output_folder = self.workspace_folder / "03-normalizer"
        self.alias_map_path = alias_map_path
        self.alias_map = self._load_alias_map()
        self.unknowns: list[str] = []
        self.assumptions: list[str] = []
        self.decisions: list[str] = []
        self.manual_review_queue: list[dict] = []

    def run(self) -> None:
        self.output_folder.mkdir(parents=True, exist_ok=True)
        analyzer_projects = self._load_analyzer_outputs()
        grouped = self._load_grouped_output()
        canonical_entities = self._build_canonical_entities(analyzer_projects, grouped)
        normalized_platforms = self._build_normalized_platforms(grouped, canonical_entities)
        normalized_dependencies = self._build_normalized_dependencies(grouped, canonical_entities)
        result = {
            "canonical_entities": canonical_entities,
            "normalized_platforms": normalized_platforms,
            "normalized_dependencies": normalized_dependencies,
            "manual_review_queue": self._dedupe_objects(
                self.manual_review_queue,
                lambda item: (item["issue_type"], tuple(item["candidates"]), item["reason"]),
            ),
            "assumptions": self._dedupe(self.assumptions),
            "unknowns": self._dedupe(self.unknowns),
        }
        self._write_json(result)
        self._write_markdown(result)
        self._append_decisions(result)

    def _load_alias_map(self) -> dict[str, dict[str, str]]:
        default = {entity_type: {} for entity_type in ENTITY_TYPES}
        if not self.alias_map_path:
            self.assumptions.append("No alias map path was provided; heuristic normalization only.")
            return default
        try:
            data = json.loads(self.alias_map_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            self.unknowns.append(f"Alias mapping file not found: {self.alias_map_path}")
            return default
        except (OSError, json.JSONDecodeError):
            self.unknowns.append(f"Alias mapping file is invalid and was ignored: {self.alias_map_path}")
            return default
        if not isinstance(data, dict):
            self.unknowns.append(f"Alias mapping file is not a JSON object and was ignored: {self.alias_map_path}")
            return default
        merged = default.copy()
        for entity_type in ENTITY_TYPES:
            section = data.get(entity_type, {})
            if not isinstance(section, dict):
                continue
            merged[entity_type] = {normalize_key(str(key)): str(value) for key, value in section.items()}
        return merged

    def _load_analyzer_outputs(self) -> list[dict]:
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
            loaded.append(data)
        if not loaded:
            self.unknowns.append("No valid analyzer outputs were found for normalization.")
        return loaded

    def _load_grouped_output(self) -> dict:
        try:
            data = json.loads(self.grouper_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            self.unknowns.append("Grouped output not found under 02-grouper/grouped.json.")
            return {}
        except (OSError, json.JSONDecodeError):
            self.unknowns.append("Grouped output is invalid and was ignored.")
            return {}
        if not isinstance(data, dict):
            self.unknowns.append("Grouped output is not a JSON object and was ignored.")
            return {}
        return data

    def _build_canonical_entities(self, analyzer_projects: list[dict], grouped: dict) -> list[dict]:
        candidates: dict[str, list[dict]] = defaultdict(list)
        for project in analyzer_projects:
            project_name = self._string(project.get("project_name"))
            if project_name:
                self._add_candidate(candidates, "project", project_name, [self._ref(project)])
            for datastore in self._objects(project.get("datastores")):
                self._add_candidate(
                    candidates,
                    "datastore",
                    self._string(datastore.get("name")),
                    self._list(datastore.get("evidence")) + [self._ref(project)],
                )
            for integration in self._objects(project.get("integrations")):
                self._add_candidate(
                    candidates,
                    "integration",
                    self._string(integration.get("name")),
                    self._list(integration.get("evidence")) + [self._ref(project)],
                )
            for component in self._objects(project.get("components")):
                kind = self._string(component.get("kind"))
                entity_type = "service" if kind not in {"deployable-unit", ""} else "service"
                self._add_candidate(
                    candidates,
                    entity_type,
                    self._string(component.get("name")),
                    self._list(component.get("evidence")) + [self._ref(project)],
                )
        for platform in self._objects(grouped.get("platforms")):
            self._add_candidate(
                candidates,
                "platform",
                self._string(platform.get("name")),
                self._list(platform.get("projects")) + ["02-grouper/grouped.json"],
            )
            for service_name in self._list(platform.get("shared_services")):
                self._add_candidate(candidates, "service", service_name, ["02-grouper/grouped.json"])
            for datastore_name in self._list(platform.get("shared_datastores")):
                self._add_candidate(candidates, "datastore", datastore_name, ["02-grouper/grouped.json"])
            for integration_name in self._list(platform.get("key_integrations")):
                self._add_candidate(candidates, "integration", integration_name, ["02-grouper/grouped.json"])

        canonical_entities: list[dict] = []
        for entity_type in ENTITY_TYPES:
            grouped_candidates = self._group_candidates(candidates.get(entity_type, []), entity_type)
            for group in grouped_candidates:
                canonical_entities.append(self._canonical_entity_from_group(group, entity_type))
        return sorted(canonical_entities, key=lambda item: (item["entity_type"], item["canonical_name"].lower()))

    def _add_candidate(self, candidates: dict[str, list[dict]], entity_type: str, name: str, refs: list[str]) -> None:
        if entity_type not in ENTITY_TYPES or not name:
            return
        candidates[entity_type].append(
            {
                "name": name,
                "normalized": normalize_key(name),
                "references": sorted(set(ref for ref in refs if ref)),
            }
        )

    def _group_candidates(self, candidates: list[dict], entity_type: str) -> list[list[dict]]:
        by_explicit: dict[str, list[dict]] = defaultdict(list)
        for candidate in candidates:
            canonical = self.alias_map.get(entity_type, {}).get(candidate["normalized"])
            if canonical:
                by_explicit[canonical].append(candidate)

        consumed_ids = {id(candidate) for members in by_explicit.values() for candidate in members}
        remaining = [candidate for candidate in candidates if id(candidate) not in consumed_ids]
        buckets: dict[str, list[dict]] = defaultdict(list)
        for candidate in remaining:
            buckets[candidate["normalized"]].append(candidate)

        groups: list[list[dict]] = list(by_explicit.values())
        for normalized_key, bucket in sorted(buckets.items()):
            if len(bucket) == 1:
                groups.append(bucket)
                continue
            original_names = sorted({item["name"] for item in bucket})
            if self._strong_alias_match(original_names):
                groups.append(bucket)
            else:
                self.manual_review_queue.append(
                    {
                        "issue_type": f"{entity_type}_alias_conflict",
                        "candidates": original_names,
                        "reason": "Names share a normalized key but differ materially; review before merging.",
                    }
                )
                self.decisions.append(
                    f"ambiguous match: {entity_type} candidates {', '.join(original_names)} require manual review"
                )
                for candidate in bucket:
                    groups.append([candidate])
        return groups

    def _canonical_entity_from_group(self, group: list[dict], entity_type: str) -> dict:
        aliases = sorted({item["name"] for item in group})
        references = sorted({ref for item in group for ref in item["references"]})
        canonical_name = self._choose_canonical_name(aliases, entity_type)
        merge_recommendation, rationale, confidence = self._classify_group(aliases, entity_type)
        if merge_recommendation == "manual_review":
            self.manual_review_queue.append(
                {
                    "issue_type": f"{entity_type}_manual_review",
                    "candidates": aliases,
                    "reason": "; ".join(rationale),
                }
            )
            self.decisions.append(f"conflict: {entity_type} aliases {', '.join(aliases)} need manual review")
        return {
            "canonical_name": canonical_name,
            "entity_type": entity_type,
            "aliases": aliases,
            "source_references": references,
            "merge_recommendation": merge_recommendation,
            "rationale": rationale,
            "confidence": confidence,
        }

    def _choose_canonical_name(self, aliases: list[str], entity_type: str) -> str:
        explicit_matches = []
        for alias in aliases:
            mapped = self.alias_map.get(entity_type, {}).get(normalize_key(alias))
            if mapped:
                explicit_matches.append(mapped)
        if explicit_matches:
            return sorted(explicit_matches, key=lambda item: (len(item), item.lower()))[0]
        return sorted(aliases, key=lambda item: (len(item), item.lower()))[0]

    def _classify_group(self, aliases: list[str], entity_type: str) -> tuple[str, list[str], str]:
        if len(aliases) == 1:
            return "keep_separate", ["Only one observed name for this entity."], "high"
        normalized = {normalize_key(alias) for alias in aliases}
        alias_map_hit = all(self.alias_map.get(entity_type, {}).get(key) for key in normalized)
        if alias_map_hit:
            return "merge", ["Explicit alias mapping resolved all observed aliases."], "high"
        if self._strong_alias_match(aliases):
            return "merge", ["Aliases differ only by casing, punctuation, or known abbreviation patterns."], "medium"
        return "manual_review", ["Aliases are similar but not strong enough for automatic merge."], "low"

    @staticmethod
    def _strong_alias_match(aliases: list[str]) -> bool:
        normalized = {normalize_key(alias) for alias in aliases}
        if len(normalized) == 1:
            return True
        base_tokens = {tuple(token.lower() for token in tokenize(alias)) for alias in aliases}
        return len(base_tokens) == 1

    def _build_normalized_platforms(self, grouped: dict, canonical_entities: list[dict]) -> list[dict]:
        canonical_lookup = self._canonical_lookup(canonical_entities)
        platforms: list[dict] = []
        for item in self._objects(grouped.get("platforms")):
            name = self._canonicalize_name(self._string(item.get("name")), "platform", canonical_lookup)
            platforms.append(
                {
                    "canonical_name": name,
                    "projects": [self._canonicalize_name(project, "project", canonical_lookup) for project in self._list(item.get("projects"))],
                    "shared_services": [
                        self._canonicalize_name(service, "service", canonical_lookup)
                        for service in self._list(item.get("shared_services"))
                    ],
                    "shared_datastores": [
                        self._canonicalize_name(datastore, "datastore", canonical_lookup)
                        for datastore in self._list(item.get("shared_datastores"))
                    ],
                    "key_integrations": [
                        self._canonicalize_name(integration, "integration", canonical_lookup)
                        for integration in self._list(item.get("key_integrations"))
                    ],
                    "confidence": self._confidence(item.get("confidence")),
                }
            )
        return sorted(platforms, key=lambda item: item["canonical_name"].lower())

    def _build_normalized_dependencies(self, grouped: dict, canonical_entities: list[dict]) -> list[dict]:
        canonical_lookup = self._canonical_lookup(canonical_entities)
        dependencies: list[dict] = []
        for item in self._objects(grouped.get("cross_project_dependencies")):
            source = self._canonicalize_name(self._string(item.get("source_project")), "project", canonical_lookup)
            target_name = self._string(item.get("target_project_or_service"))
            target_type = self._infer_dependency_target_type(target_name, canonical_entities)
            target = self._canonicalize_name(target_name, target_type, canonical_lookup)
            dependencies.append(
                {
                    "source_project": source,
                    "target_project_or_service": target,
                    "relationship": self._string(item.get("relationship")),
                    "evidence": sorted(self._list(item.get("evidence"))),
                    "confidence": self._confidence(item.get("confidence")),
                }
            )
        return sorted(
            self._dedupe_objects(
                dependencies,
                lambda item: (
                    item["source_project"],
                    item["target_project_or_service"],
                    item["relationship"],
                ),
            ),
            key=lambda item: (item["source_project"].lower(), item["target_project_or_service"].lower(), item["relationship"].lower()),
        )

    def _canonical_lookup(self, canonical_entities: list[dict]) -> dict[str, dict[str, str]]:
        lookup = {entity_type: {} for entity_type in ENTITY_TYPES}
        for entity in canonical_entities:
            entity_type = entity["entity_type"]
            for alias in entity["aliases"]:
                lookup[entity_type][normalize_key(alias)] = entity["canonical_name"]
        return lookup

    def _canonicalize_name(self, name: str, entity_type: str, lookup: dict[str, dict[str, str]]) -> str:
        if not name:
            return name
        return lookup.get(entity_type, {}).get(normalize_key(name), name)

    def _infer_dependency_target_type(self, name: str, canonical_entities: list[dict]) -> str:
        normalized = normalize_key(name)
        for entity_type in ("project", "service", "integration", "datastore", "platform"):
            for entity in canonical_entities:
                if entity["entity_type"] != entity_type:
                    continue
                if any(normalize_key(alias) == normalized for alias in entity["aliases"]):
                    return entity_type
        return "service"

    def _write_json(self, result: dict) -> None:
        path = self.output_folder / "normalized.json"
        path.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    def _write_markdown(self, result: dict) -> None:
        path = self.output_folder / "normalized.md"
        generated_at = datetime.now(timezone.utc).isoformat()
        alias_lines = []
        for entity in result["canonical_entities"]:
            if entity["aliases"]:
                alias_lines.append(f"- {entity['canonical_name']}: {', '.join(entity['aliases'])}")
        merge_lines = []
        for entity in result["canonical_entities"]:
            merge_lines.append(
                f"- {entity['canonical_name']} ({entity['entity_type']}): {entity['merge_recommendation']} | confidence={entity['confidence']} | rationale={'; '.join(entity['rationale'])}"
            )
        lines = [
            f"generated_at: {generated_at}",
            "source_skill: architecture-normalizer",
            f"workspace_folder: {self.workspace_folder}",
            "",
            "# 1. Canonical Entities",
        ]
        lines.extend(
            self._render_named_objects(
                [
                    {
                        "name": entity["canonical_name"],
                        "entity_type": entity["entity_type"],
                        "aliases": entity["aliases"],
                        "source_references": entity["source_references"],
                        "merge_recommendation": entity["merge_recommendation"],
                        "confidence": entity["confidence"],
                    }
                    for entity in result["canonical_entities"]
                ],
                ["entity_type", "aliases", "source_references", "merge_recommendation", "confidence"],
            )
        )
        lines.extend(["", "# 2. Alias Mapping"])
        lines.extend(alias_lines or ["- none"])
        lines.extend(["", "# 3. Merge Decisions"])
        lines.extend(merge_lines or ["- none"])
        lines.extend(["", "# 4. Manual Review Queue"])
        lines.extend(
            self._render_named_objects(
                [
                    {
                        "name": item["issue_type"],
                        "candidates": item["candidates"],
                        "reason": item["reason"],
                    }
                    for item in result["manual_review_queue"]
                ],
                ["candidates", "reason"],
            )
        )
        lines.extend(["", "# 5. Unknowns"])
        lines.extend(self._render_strings(result["unknowns"]))
        lines.extend(["", "# 6. Assumptions"])
        lines.extend(self._render_strings(result["assumptions"]))
        path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    def _append_decisions(self, result: dict) -> None:
        path = self.output_folder / "decisions.md"
        generated_at = datetime.now(timezone.utc).isoformat()
        lines = [f"## {generated_at}"]
        for item in result["manual_review_queue"]:
            lines.append(f"- ambiguous match: {item['issue_type']} -> {', '.join(item['candidates'])} ({item['reason']})")
        for decision in self._dedupe(self.decisions):
            lines.append(f"- {decision}")
        if len(lines) == 1:
            lines.append("- conflict: No ambiguous matches or conflicts were recorded for this run.")
        lines.append("")
        with path.open("a", encoding="utf-8") as handle:
            handle.write("\n".join(lines))

    @staticmethod
    def _ref(project: dict) -> str:
        return str(project.get("workspace_output_folder", "")) or str(project.get("source_project_folder", ""))

    @staticmethod
    def _string(value: object) -> str:
        return value.strip() if isinstance(value, str) else ""

    @staticmethod
    def _objects(value: object) -> list[dict]:
        return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []

    @staticmethod
    def _list(value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return sorted({item.strip() for item in value if isinstance(item, str) and item.strip()})

    @staticmethod
    def _confidence(value: object) -> str:
        if isinstance(value, str) and value in VALID_CONFIDENCE:
            return value
        return "low"

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
    alias_map_path = Path(args.alias_map).resolve() if args.alias_map else None
    normalizer = Normalizer(workspace_folder, alias_map_path)
    normalizer.run()
    print(normalizer.output_folder)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
