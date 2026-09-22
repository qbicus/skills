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
    "ci": "CI",
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
    parser.add_argument("--runner", required=False, help="Optional runner or reviewer name for decisions logging.")
    return parser.parse_args()


def normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def tokenize(value: str) -> list[str]:
    return [token for token in re.split(r"[^A-Za-z0-9]+", value) if token]


def list_to_text(values: list[str], default: str = "No data available") -> str:
    return ", ".join(values) if values else default


def is_placeholder_value(value: str) -> bool:
    return normalize_key(value) in {"nodataavailable", "unknown", "none", "n/a"}


class Normalizer:
    def __init__(self, workspace_folder: Path, alias_map_path: Path | None, runner: str | None) -> None:
        self.workspace_folder = workspace_folder.resolve()
        self.analyzer_folder = self.workspace_folder / "01-analyzer"
        self.grouper_path = self.workspace_folder / "02-grouper" / "grouped.json"
        self.output_folder = self.workspace_folder / "03-normalizer"
        self.alias_map_path = alias_map_path
        self.runner = runner.strip() if isinstance(runner, str) and runner.strip() else "unknown"
        self.alias_map = self._load_alias_map()
        self.unknowns: list[str] = []
        self.assumptions: list[str] = []
        self.decisions: list[str] = []
        self.manual_review_queue: list[dict] = []
        self.analyzer_outputs_processed = 0
        self.grouped_output_present = False

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
        self.analyzer_outputs_processed = len(loaded)
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
        self.grouped_output_present = True
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
                self._add_candidate(
                    candidates,
                    "service",
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
        for _, bucket in sorted(buckets.items()):
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
        quality_notes = self._quality_review_notes(aliases, references, entity_type)
        if quality_notes:
            self.manual_review_queue.append(
                {
                    "issue_type": f"{entity_type}_low_signal_review",
                    "candidates": aliases,
                    "reason": "; ".join(quality_notes),
                }
            )
            self.decisions.append(f"manual review: {entity_type} aliases {', '.join(aliases)} flagged for low-signal evidence")
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

    def _quality_review_notes(self, aliases: list[str], references: list[str], entity_type: str) -> list[str]:
        notes: list[str] = []
        if any(is_placeholder_value(alias) for alias in aliases):
            notes.append("Placeholder-like entity name present; keep it, but require manual review.")
        non_placeholder_aliases = [alias for alias in aliases if not is_placeholder_value(alias)]
        if not non_placeholder_aliases and aliases:
            notes.append("Entity has no non-placeholder alias.")
        low_signal_aliases = [alias for alias in non_placeholder_aliases if self._is_low_signal_name(alias, entity_type)]
        if low_signal_aliases:
            notes.append(f"Low-signal entity name detected: {', '.join(low_signal_aliases)}")
        if any(is_placeholder_value(reference) for reference in references):
            notes.append("Placeholder-like source reference present.")
        return notes

    @staticmethod
    def _is_low_signal_name(name: str, entity_type: str) -> bool:
        normalized = normalize_key(name)
        if not normalized:
            return True
        if entity_type in {"integration", "service"} and normalized in {"public", "private", "internal", "external", "service"}:
            return True
        return len(normalized) <= 2

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
        token_sets = {tuple(token.lower() for token in tokenize(alias)) for alias in aliases}
        return len(token_sets) == 1

    def _build_normalized_platforms(self, grouped: dict, canonical_entities: list[dict]) -> list[dict]:
        canonical_lookup = self._canonical_lookup(canonical_entities)
        normalized_platforms: list[dict] = []
        for item in self._objects(grouped.get("platforms")):
            normalized_platforms.append(
                {
                    "name": self._canonicalize_name(self._string(item.get("name")), "platform", canonical_lookup),
                    "summary": self._string(item.get("summary")),
                    "business_context": self._string(item.get("business_context")),
                    "platform_type": self._string(item.get("platform_type")),
                    "description": self._string(item.get("description")),
                    "projects": self._normalize_string_names(item.get("projects"), "project", canonical_lookup),
                    "primary_stack": self._list(item.get("primary_stack")),
                    "entry_surfaces": self._list(item.get("entry_surfaces")),
                    "deployable_units": self._list(item.get("deployable_units")),
                    "components": self._normalize_named_objects(
                        item.get("components"),
                        "service",
                        canonical_lookup,
                        preserve_fields=("kind", "details", "evidence"),
                    ),
                    "datastores": self._normalize_named_objects(
                        item.get("datastores"),
                        "datastore",
                        canonical_lookup,
                        preserve_fields=("type", "details", "evidence"),
                    ),
                    "interfaces": self._normalize_interfaces(item.get("interfaces")),
                    "integrations": self._normalize_named_objects(
                        item.get("integrations"),
                        "integration",
                        canonical_lookup,
                        preserve_fields=("type", "details", "evidence"),
                    ),
                    "security": self._normalize_security(item.get("security"), canonical_lookup),
                    "deployment": self._normalize_deployment(item.get("deployment")),
                    "shared_services": self._normalize_string_names(item.get("shared_services"), "service", canonical_lookup),
                    "shared_datastores": self._normalize_string_names(item.get("shared_datastores"), "datastore", canonical_lookup),
                    "key_integrations": self._normalize_string_names(item.get("key_integrations"), "integration", canonical_lookup),
                    "cross_project_dependencies": self._normalize_platform_dependencies(
                        item.get("cross_project_dependencies"),
                        canonical_lookup,
                    ),
                    "observed_facts": self._list(item.get("observed_facts")),
                    "inferred_facts": self._list(item.get("inferred_facts")),
                    "unknowns": self._list(item.get("unknowns")),
                    "risks": self._list(item.get("risks")),
                    "assumptions": self._list(item.get("assumptions")),
                    "grouping_rationale": self._list(item.get("grouping_rationale")),
                    "confidence": self._confidence(item.get("confidence")),
                    "notes": self._build_platform_notes(item),
                }
            )
        return sorted(normalized_platforms, key=lambda platform: platform["name"].lower())

    def _build_platform_notes(self, item: dict) -> list[str]:
        notes = []
        summary = self._string(item.get("summary"))
        business_context = self._string(item.get("business_context"))
        description = self._string(item.get("description"))
        platform_type = self._string(item.get("platform_type"))
        if summary:
            notes.append(f"Summary: {summary}")
        if business_context:
            notes.append(f"Business context: {business_context}")
        if platform_type:
            notes.append(f"Platform type: {platform_type}")
        if description:
            notes.append(f"Description: {description}")
        return notes

    def _normalize_interfaces(self, value: object) -> dict[str, list[str]]:
        data = value if isinstance(value, dict) else {}
        return {
            "inbound": self._list(data.get("inbound")),
            "outbound": self._list(data.get("outbound")),
        }

    def _normalize_security(self, value: object, canonical_lookup: dict[str, dict[str, str]]) -> dict:
        data = value if isinstance(value, dict) else {}
        auth_values = self._list(data.get("auth_systems"))
        if not auth_values:
            auth_values = self._list(data.get("authentication")) + self._list(data.get("authorization"))
        return {
            "auth_systems": self._normalize_string_names(auth_values, "service", canonical_lookup),
            "secrets_handling": self._list(data.get("secrets_handling")),
            "confidence": self._confidence(data.get("confidence")),
        }

    def _normalize_deployment(self, value: object) -> dict:
        data = value if isinstance(value, dict) else {}
        return {
            "hosting_clues": self._list(data.get("hosting_clues")),
            "ci_cd_clues": self._list(data.get("ci_cd_clues")),
            "runtime_clues": self._list(data.get("runtime_clues")),
            "confidence": self._confidence(data.get("confidence")),
        }

    def _normalize_platform_dependencies(self, value: object, canonical_lookup: dict[str, dict[str, str]]) -> list[dict]:
        dependencies = []
        for item in self._objects(value):
            target_name = self._string(item.get("target_project_or_service"))
            target_type = self._infer_known_entity_type(target_name, canonical_lookup) or "service"
            dependencies.append(
                {
                    "source_project": self._canonicalize_name(
                        self._string(item.get("source_project")),
                        "project",
                        canonical_lookup,
                    ),
                    "target_project_or_service": self._canonicalize_name(target_name, target_type, canonical_lookup),
                    "relationship": self._string(item.get("relationship")),
                    "evidence": self._list(item.get("evidence")),
                    "confidence": self._confidence(item.get("confidence")),
                }
            )
        return self._dedupe_objects(
            sorted(
                dependencies,
                key=lambda item: (
                    item["source_project"].lower(),
                    item["target_project_or_service"].lower(),
                    item["relationship"].lower(),
                ),
            ),
            lambda item: (item["source_project"], item["target_project_or_service"], item["relationship"]),
        )

    def _normalize_named_objects(
        self,
        value: object,
        entity_type: str,
        canonical_lookup: dict[str, dict[str, str]],
        preserve_fields: tuple[str, ...],
    ) -> list[dict]:
        merged: dict[str, dict] = {}
        for item in self._objects(value):
            name = self._canonicalize_name(self._string(item.get("name")), entity_type, canonical_lookup)
            if not name:
                continue
            key = normalize_key(name)
            entry = merged.setdefault(key, {"name": name})
            for field in preserve_fields:
                field_value = item.get(field)
                if isinstance(field_value, list):
                    existing = entry.get(field, [])
                    if not isinstance(existing, list):
                        existing = [existing] if existing else []
                    entry[field] = self._dedupe(existing + self._list(field_value))
                elif isinstance(field_value, str):
                    field_text = field_value.strip()
                    if field_text:
                        existing = entry.get(field)
                        if not existing:
                            entry[field] = field_text
                        elif isinstance(existing, list):
                            entry[field] = self._dedupe(existing + [field_text])
                        elif existing != field_text:
                            entry[field] = self._dedupe([existing, field_text])
        normalized = list(merged.values())
        for entry in normalized:
            for field in preserve_fields:
                if isinstance(entry.get(field), list):
                    entry[field] = sorted(entry[field], key=str.lower)
        return sorted(normalized, key=lambda item: item["name"].lower())

    def _normalize_string_names(
        self,
        value: object,
        entity_type: str,
        canonical_lookup: dict[str, dict[str, str]],
    ) -> list[str]:
        result = []
        for item in self._list(value):
            result.append(self._canonicalize_name(item, entity_type, canonical_lookup))
        return self._dedupe(sorted(result, key=str.lower))

    def _build_normalized_dependencies(self, grouped: dict, canonical_entities: list[dict]) -> list[dict]:
        canonical_lookup = self._canonical_lookup(canonical_entities)
        dependencies: list[dict] = []
        for item in self._objects(grouped.get("cross_project_dependencies")):
            source = self._canonicalize_name(self._string(item.get("source_project")), "project", canonical_lookup)
            target_name = self._string(item.get("target_project_or_service"))
            target_type = self._infer_known_entity_type(target_name, canonical_lookup) or "service"
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

    def _infer_known_entity_type(self, name: str, lookup: dict[str, dict[str, str]]) -> str | None:
        normalized = normalize_key(name)
        for entity_type in ("project", "service", "integration", "datastore", "platform"):
            if normalized in lookup.get(entity_type, {}):
                return entity_type
        return None

    def _write_json(self, result: dict) -> None:
        path = self.output_folder / "normalized.json"
        path.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    def _write_markdown(self, result: dict) -> None:
        path = self.output_folder / "normalized.md"
        generated_at = datetime.now(timezone.utc).isoformat()
        lines = [
            "---",
            "document_type: architecture-normalization",
            f"generated_at: {generated_at}",
            "source_skill: tas-03-architecture-normalizer",
            f"workspace_folder: {self.workspace_folder}",
            "---",
            "",
            "# Architecture Normalization Summary",
            "",
            "> Confidence note: This document may include both observed and inferred architecture facts. Review unknowns and assumptions before treating the document as authoritative.",
            ">",
            "> Source: Generated automatically from code and configuration analysis.",
            "> Review status: Not reviewed / Partially reviewed / Reviewed",
            "",
            "## 1. Overview",
            "",
            "This document reconciles naming differences, aliases, duplicates, and conflicting terminology across analyzed projects and grouped platform data.",
            "",
            f"**Canonical Entities:** {len(result['canonical_entities'])}  ",
            f"**Normalized Platforms:** {len(result['normalized_platforms'])}  ",
            f"**Normalized Dependencies:** {len(result['normalized_dependencies'])}  ",
            f"**Manual Review Items:** {len(result['manual_review_queue'])}",
            "",
            "---",
            "",
            "## 2. Canonical Entities",
            "",
        ]
        lines.extend(self._render_canonical_entities(result["canonical_entities"]))
        lines.extend(["", "---", "", "## 3. Normalized Platforms", ""])
        lines.extend(self._render_normalized_platforms(result["normalized_platforms"]))
        lines.extend(["", "---", "", "## 4. Normalized Dependencies", ""])
        lines.extend(self._render_normalized_dependencies(result["normalized_dependencies"]))
        lines.extend(["", "---", "", "## 5. Manual Review Queue", ""])
        lines.extend(self._render_manual_review_queue(result["manual_review_queue"]))
        lines.extend(["", "---", "", "## 6. Unknowns", ""])
        lines.extend(self._render_strings(result["unknowns"]))
        lines.extend(["", "---", "", "## 7. Assumptions", ""])
        lines.extend(self._render_strings(result["assumptions"]))
        lines.extend(
            [
                "",
                "---",
                "",
                "## 8. Reviewer Checklist",
                "",
                "- [ ] Confirm canonical names are appropriate",
                "- [ ] Confirm aliases map to the correct canonical entities",
                "- [ ] Review all merge recommendations",
                "- [ ] Review keep_separate recommendations",
                "- [ ] Work through the manual review queue",
                "- [ ] Check normalized platforms for unintended merges",
                "- [ ] Check normalized dependencies for clarity and correctness",
                "- [ ] Review unknowns and assumptions",
                "- [ ] Update Review status at the top of this document",
            ]
        )
        path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    def _render_canonical_entities(self, entities: list[dict]) -> list[str]:
        if not entities:
            return ["No data available"]
        lines: list[str] = []
        for entity in entities:
            lines.extend(
                [
                    f"### {entity['canonical_name']}",
                    "",
                    f"- **Entity Type:** {entity['entity_type']}",
                    f"- **Merge Recommendation:** {entity['merge_recommendation']}",
                    f"- **Confidence:** {entity['confidence']}",
                    "",
                    "**Aliases**",
                ]
            )
            lines.extend(self._render_strings(entity["aliases"]))
            lines.extend(["", "**Source References**"])
            lines.extend(self._render_strings(entity["source_references"]))
            lines.extend(["", "**Rationale**"])
            lines.extend(self._render_strings(entity["rationale"]))
            lines.append("")
        return lines[:-1]

    def _render_normalized_platforms(self, platforms: list[dict]) -> list[str]:
        if not platforms:
            return ["No data available"]
        lines: list[str] = []
        for platform in platforms:
            lines.extend(
                [
                    f"### {platform['name']}",
                    "",
                    f"- **Confidence:** {platform['confidence']}",
                    f"- **Summary:** {platform['summary'] or 'No data available'}",
                    f"- **Business Context:** {platform['business_context'] or 'No data available'}",
                    f"- **Platform Type:** {platform['platform_type'] or 'No data available'}",
                    f"- **Description:** {platform['description'] or 'No data available'}",
                    "",
                    "**Projects**",
                ]
            )
            lines.extend(self._render_strings(platform["projects"]))
            lines.extend(
                [
                    "",
                    "**Primary Stack**",
                    *self._render_strings(platform["primary_stack"]),
                    "",
                    "**Entry Surfaces**",
                    *self._render_strings(platform["entry_surfaces"]),
                    "",
                    "**Deployable Units**",
                    *self._render_strings(platform["deployable_units"]),
                    "",
                    "**Components**",
                ]
            )
            lines.extend(self._render_named_list(platform["components"], ("kind",)))
            lines.extend(["", "**Datastores**"])
            lines.extend(self._render_named_list(platform["datastores"], ("type",)))
            lines.extend(
                [
                    "",
                    "**Interfaces**",
                    f"- Inbound: {list_to_text(platform['interfaces']['inbound'])}",
                    f"- Outbound: {list_to_text(platform['interfaces']['outbound'])}",
                    "",
                    "**Integrations**",
                ]
            )
            lines.extend(self._render_named_list(platform["integrations"], ("type",)))
            lines.extend(
                [
                    "",
                    "**Security**",
                    f"- Auth Systems: {list_to_text(platform['security']['auth_systems'])}",
                    f"- Secrets Handling: {list_to_text(platform['security']['secrets_handling'])}",
                    f"- Confidence: {platform['security']['confidence']}",
                    "",
                    "**Deployment**",
                    f"- Hosting Clues: {list_to_text(platform['deployment']['hosting_clues'])}",
                    f"- CI/CD Clues: {list_to_text(platform['deployment']['ci_cd_clues'])}",
                    f"- Runtime Clues: {list_to_text(platform['deployment']['runtime_clues'])}",
                    f"- Confidence: {platform['deployment']['confidence']}",
                    "",
                    "**Shared Services**",
                ]
            )
            lines.extend(self._render_strings(platform["shared_services"]))
            lines.extend(["", "**Shared Datastores**"])
            lines.extend(self._render_strings(platform["shared_datastores"]))
            lines.extend(["", "**Key Integrations**"])
            lines.extend(self._render_strings(platform["key_integrations"]))
            lines.extend(["", "**Cross-Project Dependencies**"])
            lines.extend(self._render_dependency_list(platform["cross_project_dependencies"]))
            lines.extend(["", "**Grouping Rationale**"])
            lines.extend(self._render_strings(platform["grouping_rationale"]))
            lines.extend(["", "**Observed Facts**"])
            lines.extend(self._render_strings(platform["observed_facts"]))
            lines.extend(["", "**Inferred Facts**"])
            lines.extend(self._render_strings(platform["inferred_facts"]))
            lines.extend(["", "**Unknowns**"])
            lines.extend(self._render_strings(platform["unknowns"]))
            lines.extend(["", "**Risks**"])
            lines.extend(self._render_strings(platform["risks"]))
            lines.extend(["", "**Assumptions**"])
            lines.extend(self._render_strings(platform["assumptions"]))
            lines.extend(["", "**Notes**"])
            lines.extend(self._render_strings(platform["notes"]))
            lines.append("")
        return lines[:-1]

    def _render_normalized_dependencies(self, dependencies: list[dict]) -> list[str]:
        if not dependencies:
            return ["No data available"]
        lines: list[str] = []
        for item in dependencies:
            lines.extend(
                [
                    f"### {item['source_project']} -> {item['target_project_or_service']}",
                    "",
                    f"- **Relationship:** {item['relationship'] or 'No data available'}",
                    f"- **Confidence:** {item['confidence']}",
                    "- **Evidence:**",
                ]
            )
            lines.extend(self._render_strings(item["evidence"]))
            lines.append("")
        return lines[:-1]

    def _render_manual_review_queue(self, items: list[dict]) -> list[str]:
        if not items:
            return ["No data available"]
        lines: list[str] = []
        for item in items:
            lines.extend(
                [
                    f"### {item['issue_type']}",
                    "",
                    "**Candidates**",
                ]
            )
            lines.extend(self._render_strings(item["candidates"]))
            lines.extend(["", "**Reason**", item["reason"] or "No data available", ""])
        return lines[:-1]

    def _append_decisions(self, result: dict) -> None:
        path = self.output_folder / "decisions.md"
        generated_at = datetime.now(timezone.utc).isoformat()
        lines = [
            f"## {generated_at}",
            f"- workspace folder: {self.workspace_folder}",
            f"- analyzer outputs processed: {self.analyzer_outputs_processed}",
            f"- grouped.json present: {'yes' if self.grouped_output_present else 'no'}",
            f"- runner: {self.runner}",
        ]
        for item in result["manual_review_queue"]:
            lines.append(f"- ambiguous match: {item['issue_type']} -> {', '.join(item['candidates'])} ({item['reason']})")
        for decision in self._dedupe(self.decisions):
            lines.append(f"- {decision}")
        if len(lines) == 5:
            lines.append("- conflict: No ambiguous matches or conflicts were recorded for this run.")
        lines.append("")
        with path.open("a", encoding="utf-8") as handle:
            handle.write("\n".join(lines))

    def _render_named_list(self, items: list[dict], extra_fields: tuple[str, ...]) -> list[str]:
        if not items:
            return ["No data available"]
        lines: list[str] = []
        for item in items:
            suffix_parts = []
            for field in extra_fields:
                value = item.get(field)
                if isinstance(value, str) and value:
                    suffix_parts.append(f"{field}={value}")
                elif isinstance(value, list) and value:
                    suffix_parts.append(f"{field}={list_to_text(value)}")
            suffix = f" ({'; '.join(suffix_parts)})" if suffix_parts else ""
            lines.append(f"- {item['name']}{suffix}")
        return lines

    def _render_dependency_list(self, items: list[dict]) -> list[str]:
        if not items:
            return ["No data available"]
        lines = []
        for item in items:
            relationship = item.get("relationship") or "unspecified"
            confidence = item.get("confidence") or "low"
            evidence = list_to_text(item.get("evidence", []))
            lines.append(
                f"- {item.get('source_project', 'unknown')} -> {item.get('target_project_or_service', 'unknown')} | relationship={relationship} | confidence={confidence} | evidence={evidence}"
            )
        return lines

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
    def _render_strings(items: list[str]) -> list[str]:
        return [f"- {item}" for item in items] if items else ["No data available"]

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
    normalizer = Normalizer(workspace_folder, alias_map_path, args.runner)
    normalizer.run()
    print(normalizer.output_folder)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
