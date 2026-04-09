#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from dataclasses import dataclass


TEXT_EXTENSIONS = {
    ".cs",
    ".csproj",
    ".fs",
    ".fsproj",
    ".json",
    ".jsonc",
    ".md",
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".java",
    ".kt",
    ".kts",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".env",
    ".sql",
    ".sh",
    ".ps1",
    ".tf",
    ".hcl",
    ".xml",
    ".properties",
}

INTERESTING_FILENAMES = {
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
    "jenkinsfile",
    "readme",
    "readme.md",
    "global.json",
    "package.json",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "requirements.txt",
    "pyproject.toml",
    "pipfile",
    "go.mod",
    "cargo.toml",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "settings.gradle",
    "settings.gradle.kts",
    "azure-pipelines.yml",
    ".gitlab-ci.yml",
}

IGNORE_DIRS = {
    ".git",
    ".idea",
    ".vs",
    ".vscode",
    "bin",
    "obj",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "target",
    ".terraform",
    ".next",
    ".nuxt",
    "__pycache__",
}
IGNORE_TOP_LEVEL_DIRS = {
    "_localnotes",
    "skills",
}

MAX_FILE_SIZE = 512 * 1024
MAX_TEXT_CHARS = 200_000


@dataclass
class RepoFile:
    path: Path
    relative_path: str
    content: str


class Analyzer:
    def __init__(self, project_folder: Path, workspace_folder: Path) -> None:
        self.project_folder = project_folder.resolve()
        self.workspace_folder = workspace_folder.resolve()
        self.project_name = self._sanitize_project_name(self.project_folder.name)
        self.output_folder = self.workspace_folder / "01-analyzer" / self.project_name
        self.files: list[RepoFile] = []
        self.observed_facts: list[str] = []
        self.inferred_facts: list[str] = []
        self.unknowns: list[str] = []
        self.risks: list[str] = []
        self.assumptions: list[str] = []
        self.decisions: list[str] = []

    @staticmethod
    def _sanitize_project_name(name: str) -> str:
        sanitized = "".join(ch for ch in name.replace(" ", "") if ch.isalnum() or ch in "._")
        return sanitized or "project"

    def run(self) -> None:
        self.output_folder.mkdir(parents=True, exist_ok=True)
        self.files = self._collect_files()
        report = self._build_report()
        self._write_output_json(report)
        self._write_output_md(report)
        self._append_decisions(report)

    def _collect_files(self) -> list[RepoFile]:
        collected: list[RepoFile] = []
        for path in self.project_folder.rglob("*"):
            if not path.is_file():
                continue
            relative_parts = path.relative_to(self.project_folder).parts
            if any(part in IGNORE_DIRS for part in path.parts):
                continue
            if relative_parts and relative_parts[0] in IGNORE_TOP_LEVEL_DIRS:
                continue
            if path.stat().st_size > MAX_FILE_SIZE:
                continue
            lower_name = path.name.lower()
            if path.suffix.lower() not in TEXT_EXTENSIONS and lower_name not in INTERESTING_FILENAMES:
                continue
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")[:MAX_TEXT_CHARS]
            except OSError:
                continue
            collected.append(
                RepoFile(
                    path=path,
                    relative_path=path.relative_to(self.project_folder).as_posix(),
                    content=content,
                )
            )
        return collected

    def _build_report(self) -> dict:
        frameworks = self._detect_frameworks()
        entry_points = self._detect_entry_points()
        deployable_units = self._detect_deployable_units(entry_points)
        components = self._detect_components(entry_points, deployable_units)
        datastores = self._detect_datastores()
        interfaces = self._detect_interfaces()
        integrations = self._detect_integrations()
        security = self._detect_security()
        deployment = self._detect_deployment()
        project_type = self._infer_project_type(frameworks, interfaces, entry_points)
        summary = self._build_summary(project_type, frameworks, deployable_units, datastores, integrations)
        overall_confidence = self._derive_overall_confidence(
            frameworks, entry_points, deployable_units, datastores, interfaces, integrations, security, deployment
        )
        if not self.unknowns:
            self.unknowns.append("No major architecture unknowns detected from scanned repository artifacts.")

        return {
            "project_name": self.project_name,
            "source_project_folder": str(self.project_folder),
            "workspace_output_folder": str(self.output_folder),
            "summary": summary,
            "project_type": project_type,
            "primary_stack": frameworks,
            "entry_points": entry_points,
            "deployable_units": deployable_units,
            "components": components,
            "datastores": datastores,
            "interfaces": interfaces,
            "integrations": integrations,
            "security": security,
            "deployment": deployment,
            "observed_facts": self._dedupe(self.observed_facts),
            "inferred_facts": self._dedupe(self.inferred_facts),
            "unknowns": self._dedupe(self.unknowns),
            "risks": self._dedupe(self.risks),
            "assumptions": self._dedupe(self.assumptions),
            "overall_confidence": overall_confidence,
        }

    def _detect_frameworks(self) -> list[str]:
        frameworks: list[str] = []
        for repo_file in self.files:
            content_lower = repo_file.content.lower()
            name = repo_file.relative_path.lower()
            if repo_file.path.suffix == ".csproj":
                frameworks.append(".NET")
                self.observed_facts.append(f".NET project file detected at {repo_file.relative_path}.")
                if "microsoft.aspnetcore" in content_lower or "web sdk" in content_lower:
                    frameworks.append("ASP.NET Core")
                    self.observed_facts.append(f"ASP.NET Core dependency or SDK detected in {repo_file.relative_path}.")
                if "microsoft.extensions.hosting" in content_lower:
                    frameworks.append(".NET Generic Host")
            if name == "global.json":
                frameworks.append(".NET SDK pinning")
            if name == "package.json":
                frameworks.append("Node.js")
                package_data = self._safe_json(repo_file.content)
                deps = {
                    **package_data.get("dependencies", {}),
                    **package_data.get("devDependencies", {}),
                }
                for dep, label in {
                    "express": "Express",
                    "next": "Next.js",
                    "react": "React",
                    "nestjs": "NestJS",
                    "fastify": "Fastify",
                    "vue": "Vue",
                    "@angular/core": "Angular",
                }.items():
                    if dep in deps:
                        frameworks.append(label)
                        self.observed_facts.append(f"{label} dependency detected in {repo_file.relative_path}.")
            if name == "pyproject.toml" or name == "requirements.txt":
                frameworks.append("Python")
                for needle, label in {
                    "fastapi": "FastAPI",
                    "django": "Django",
                    "flask": "Flask",
                    "celery": "Celery",
                    "sqlalchemy": "SQLAlchemy",
                }.items():
                    if needle in content_lower:
                        frameworks.append(label)
            if name == "pom.xml":
                frameworks.append("Java")
                if "spring-boot" in content_lower:
                    frameworks.append("Spring Boot")
            if name in {"build.gradle", "build.gradle.kts"}:
                frameworks.append("Gradle")
            if name == "go.mod":
                frameworks.append("Go")
            if name == "cargo.toml":
                frameworks.append("Rust")
            if name == "dockerfile":
                frameworks.append("Docker")
        if not frameworks:
            self.unknowns.append("Primary framework stack could not be identified from recognized manifests.")
        return self._dedupe(frameworks)

    def _detect_entry_points(self) -> list[str]:
        entry_points: list[str] = []
        for repo_file in self.files:
            path = repo_file.relative_path
            content = repo_file.content
            lower = content.lower()
            if path.endswith("Program.cs"):
                entry_points.append(path)
                self.observed_facts.append(f"Runtime entry point detected at {path}.")
            elif path.endswith("main.py") or path.endswith("__main__.py"):
                entry_points.append(path)
            elif path.endswith("main.go") and "func main()" in content:
                entry_points.append(path)
            elif path.endswith("src/main") or re.search(r"\bpublic static void main\s*\(", content):
                entry_points.append(path)
            elif path.endswith("package.json"):
                package_data = self._safe_json(content)
                scripts = package_data.get("scripts", {})
                if isinstance(scripts, dict):
                    for key in ("start", "dev", "serve"):
                        if key in scripts:
                            entry_points.append(f"{path}#scripts.{key}")
                            self.observed_facts.append(f"Node runtime script '{key}' declared in {path}.")
        if not entry_points:
            self.unknowns.append("Runtime entry points were not clearly identified.")
        return self._dedupe(entry_points)

    def _detect_deployable_units(self, entry_points: list[str]) -> list[str]:
        units: list[str] = []
        csproj_files = [f for f in self.files if f.path.suffix == ".csproj"]
        for repo_file in csproj_files:
            name = repo_file.path.stem
            if "test" in name.lower():
                continue
            units.append(name)
            self.observed_facts.append(f"Deployable or buildable .NET project candidate found: {name} ({repo_file.relative_path}).")
        for repo_file in self.files:
            lower_name = repo_file.path.name.lower()
            if lower_name == "dockerfile":
                unit_name = repo_file.path.parent.name or self.project_name
                units.append(f"{unit_name} container")
                self.observed_facts.append(f"Docker build unit detected in {repo_file.relative_path}.")
            if lower_name in {"docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"}:
                compose_services = re.findall(r"^\s{2}([A-Za-z0-9._-]+):\s*$", repo_file.content, re.MULTILINE)
                for service in compose_services:
                    units.append(f"{service} service")
        if not units and entry_points:
            units.extend(Path(item.split("#", 1)[0]).parent.name or self.project_name for item in entry_points)
            self.inferred_facts.append("Deployable units inferred from located entry points.")
        if not units:
            self.unknowns.append("Deployable units were not confirmed from project or container manifests.")
        return self._dedupe(units)

    def _detect_components(self, entry_points: list[str], deployable_units: list[str]) -> list[dict]:
        components: list[dict] = []
        for unit in deployable_units:
            evidence = [f.relative_path for f in self.files if f.path.stem == unit or f.path.parent.name == unit.replace(" container", "")]
            if not evidence and entry_points:
                evidence = [item for item in entry_points if Path(item.split("#", 1)[0]).parent.name == unit]
            components.append(
                {
                    "name": unit,
                    "kind": "deployable-unit",
                    "description": f"Deployable application unit identified from project or container artifacts.",
                    "evidence": self._dedupe(evidence),
                    "confidence": "high" if evidence else "medium",
                }
            )
        folder_patterns = {
            "Controllers": "api-layer",
            "Services": "service-layer",
            "BackgroundServices": "background-worker",
            "Workers": "background-worker",
            "Jobs": "background-worker",
            "Consumers": "message-consumer",
        }
        for folder_name, kind in folder_patterns.items():
            matches = [f for f in self.files if f"/{folder_name}/" in f"/{f.relative_path}/"]
            if not matches:
                continue
            component_name = folder_name
            components.append(
                {
                    "name": component_name,
                    "kind": kind,
                    "description": f"{folder_name} folder suggests a dedicated {kind.replace('-', ' ')} component.",
                    "evidence": self._dedupe([f.relative_path for f in matches[:8]]),
                    "confidence": "medium",
                }
            )
            self.inferred_facts.append(f"{kind.replace('-', ' ').capitalize()} inferred from {folder_name} folder structure.")
        if not components:
            components.append(
                {
                    "name": self.project_name,
                    "kind": "unknown",
                    "description": "Repository-level component placeholder because no concrete internal component boundaries were found.",
                    "evidence": [],
                    "confidence": "low",
                }
            )
            self.unknowns.append("Internal component boundaries are unclear from the scanned repository layout.")
        return self._dedupe_objects(components, "name")

    def _detect_datastores(self) -> list[dict]:
        patterns = {
            "PostgreSQL": [r"npgsql", r"postgres"],
            "SQL Server": [r"sqlserver", r"server=.*database=", r"useSqlServer"],
            "MySQL": [r"mysql", r"mariadb"],
            "SQLite": [r"sqlite"],
            "MongoDB": [r"mongodb", r"mongo"],
            "Redis": [r"redis"],
            "RabbitMQ": [r"rabbitmq"],
            "Kafka": [r"kafka"],
            "Azure Blob Storage": [r"azurewebjobsstorage", r"blobserviceclient", r"azure.storage.blobs"],
            "Amazon S3": [r"aws-sdk-s3", r"amazons3", r"\bs3\b"],
        }
        findings: dict[str, set[str]] = defaultdict(set)
        for repo_file in self.files:
            for datastore, needles in patterns.items():
                if any(re.search(needle, repo_file.content, re.IGNORECASE) for needle in needles):
                    findings[datastore].add(repo_file.relative_path)
        datastores: list[dict] = []
        type_map = {
            "PostgreSQL": "relational",
            "SQL Server": "relational",
            "MySQL": "relational",
            "SQLite": "relational",
            "MongoDB": "document",
            "Redis": "cache",
            "RabbitMQ": "message-broker",
            "Kafka": "event-stream",
            "Azure Blob Storage": "object-storage",
            "Amazon S3": "object-storage",
        }
        for name, evidence in findings.items():
            datastores.append(
                {
                    "name": name,
                    "type": type_map.get(name, "unknown"),
                    "usage": f"Referenced in code or configuration as {type_map.get(name, 'unknown')} infrastructure.",
                    "evidence": sorted(evidence),
                    "confidence": "high" if len(evidence) > 1 else "medium",
                }
            )
            self.observed_facts.append(f"{name} usage clue detected in {', '.join(sorted(evidence)[:3])}.")
        if not datastores:
            self.unknowns.append("Datastores were not identified from configuration, dependencies, or code references.")
        return sorted(datastores, key=lambda item: item["name"])

    def _detect_interfaces(self) -> dict:
        inbound: list[str] = []
        outbound: list[str] = []
        for repo_file in self.files:
            content = repo_file.content
            lower = content.lower()
            path = repo_file.relative_path
            if any(token in content for token in ["MapGet(", "MapPost(", "[HttpGet", "[HttpPost", "app.Map", "@app.get(", "@router.get("]):
                inbound.append(f"HTTP API endpoints defined in {path}")
                self.observed_facts.append(f"Inbound HTTP interface detected in {path}.")
            if "grpc" in lower:
                inbound.append(f"gRPC-related interface clues in {path}")
            if any(token in lower for token in ["backgroundservice", "ihostedservice", "celery", "@scheduled", "hangfire", "quartz"]):
                inbound.append(f"Background or scheduled execution in {path}")
            if any(token in lower for token in ["httpclient", "axios", "fetch(", "requests.", "resttemplate", "grpcchannel", "smtplib"]):
                outbound.append(f"Outbound network calls from {path}")
            if any(token in lower for token in ["publish(", "sendasync(", "producer", "queueclient", "servicebusclient"]):
                outbound.append(f"Messaging or queue interaction from {path}")
        if not inbound:
            self.unknowns.append("Inbound interfaces were not clearly identified.")
        if not outbound:
            self.unknowns.append("Outbound interfaces were not clearly identified.")
        return {
            "inbound": self._dedupe(inbound),
            "outbound": self._dedupe(outbound),
        }

    def _detect_integrations(self) -> list[dict]:
        integration_map: dict[str, dict] = {}
        url_pattern = re.compile(r"https?://([A-Za-z0-9._-]+)")
        for repo_file in self.files:
            matches = url_pattern.findall(repo_file.content)
            for host in matches:
                if host.startswith(("localhost", "127.", "0.0.0.0")):
                    continue
                if host in {"aka.ms", "github.com", "learn.microsoft.com", "docs.microsoft.com"}:
                    continue
                integration_type = "external"
                if host.endswith((".local", ".internal", ".svc")):
                    integration_type = "internal"
                entry = integration_map.setdefault(
                    host,
                    {
                        "name": host,
                        "type": integration_type,
                        "interaction": "Referenced via URL or endpoint configuration.",
                        "evidence": set(),
                        "confidence": "medium",
                    },
                )
                entry["evidence"].add(repo_file.relative_path)
        package_clues = {
            "sendgrid": "SendGrid",
            "stripe": "Stripe",
            "twilio": "Twilio",
            "slack": "Slack",
            "azure.storage": "Azure Storage",
            "aws-sdk": "AWS SDK",
            "google.cloud": "Google Cloud",
            "serilog.sinks.seq": "Seq",
        }
        for repo_file in self.files:
            lower = repo_file.content.lower()
            for needle, name in package_clues.items():
                if needle in lower:
                    entry = integration_map.setdefault(
                        name,
                        {
                            "name": name,
                            "type": "external",
                            "interaction": "SDK or package reference detected.",
                            "evidence": set(),
                            "confidence": "medium",
                        },
                    )
                    entry["evidence"].add(repo_file.relative_path)
        integrations: list[dict] = []
        for integration in integration_map.values():
            evidence = sorted(integration["evidence"])
            integrations.append(
                {
                    "name": integration["name"],
                    "type": integration["type"],
                    "interaction": integration["interaction"],
                    "evidence": evidence,
                    "confidence": "high" if len(evidence) > 1 else integration["confidence"],
                }
            )
            self.observed_facts.append(f"Integration clue for {integration['name']} detected in {', '.join(evidence[:3])}.")
        if not integrations:
            self.unknowns.append("No external or internal service integrations were confirmed from scanned files.")
        return sorted(integrations, key=lambda item: item["name"].lower())

    def _detect_security(self) -> dict:
        authentication: list[str] = []
        authorization: list[str] = []
        secrets_handling: list[str] = []
        confidence = "low"
        for repo_file in self.files:
            content = repo_file.content
            lower = content.lower()
            path = repo_file.relative_path
            if any(token in content for token in ["AddAuthentication", "JwtBearer", "OpenIdConnect", "AddIdentity"]) or any(
                token in lower for token in ["oauth", "oidc", "auth0", "keycloak", "azuread"]
            ):
                authentication.append(f"Authentication configuration in {path}")
                confidence = "medium"
            if any(token in content for token in ["[Authorize]", "RequireAuthorization", "AddAuthorization"]) or "authorization" in lower:
                authorization.append(f"Authorization clue in {path}")
                confidence = "medium"
            if any(token in lower for token in ["environment.getenvironmentvariable", "__", "dotnet user-secrets", "usersecretsid", "key vault", "vault", ".env", "secretsmanager", "configuration[\""]):
                secrets_handling.append(f"Secret or configuration indirection in {path}")
                confidence = "medium"
            if re.search(r"(password|apikey|secret|token)\s*[:=]\s*[\"'][^\"']+[\"']", content, re.IGNORECASE):
                self.risks.append(f"Potential hard-coded secret found in {path}.")
        if not authentication:
            self.unknowns.append("Authentication mechanism was not confirmed.")
        if not authorization:
            self.unknowns.append("Authorization model was not confirmed.")
        if not secrets_handling:
            self.unknowns.append("Secret management approach was not confirmed.")
        if authentication and authorization and secrets_handling:
            confidence = "high"
        return {
            "authentication": self._dedupe(authentication),
            "authorization": self._dedupe(authorization),
            "secrets_handling": self._dedupe(secrets_handling),
            "confidence": confidence,
        }

    def _detect_deployment(self) -> dict:
        hosting_clues: list[str] = []
        ci_cd_clues: list[str] = []
        runtime_clues: list[str] = []
        confidence = "low"
        for repo_file in self.files:
            path = repo_file.relative_path
            lower_name = repo_file.path.name.lower()
            lower = repo_file.content.lower()
            if lower_name == "dockerfile":
                hosting_clues.append(f"Container build definition in {path}")
                confidence = "medium"
                image_match = re.search(r"^from\s+([^\s]+)", repo_file.content, re.IGNORECASE | re.MULTILINE)
                if image_match:
                    runtime_clues.append(f"Container runtime base image {image_match.group(1)} in {path}")
            if lower_name in {"docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"}:
                hosting_clues.append(f"Compose orchestration file in {path}")
                confidence = "medium"
            if ".github/workflows/" in path or lower_name in {"azure-pipelines.yml", ".gitlab-ci.yml", "jenkinsfile"}:
                ci_cd_clues.append(f"CI/CD pipeline definition in {path}")
                confidence = "medium"
            if repo_file.path.suffix == ".tf":
                hosting_clues.append(f"Terraform infrastructure definition in {path}")
                confidence = "medium"
            if re.search(r"\bkubernetes\b|\bhelm\b|apiVersion:\s*apps/", repo_file.content, re.IGNORECASE):
                hosting_clues.append(f"Kubernetes or Helm clue in {path}")
                confidence = "medium"
            if lower_name == "global.json":
                runtime_clues.append(f".NET SDK version pinning in {path}")
            if lower_name == ".nvmrc":
                runtime_clues.append(f"Node runtime version pinning in {path}")
        if not hosting_clues:
            self.unknowns.append("Hosting environment clues were not found.")
        if not ci_cd_clues:
            self.risks.append("No CI/CD pipeline definitions were detected in the scanned repository.")
        return {
            "hosting_clues": self._dedupe(hosting_clues),
            "ci_cd_clues": self._dedupe(ci_cd_clues),
            "runtime_clues": self._dedupe(runtime_clues),
            "confidence": "high" if hosting_clues and ci_cd_clues else confidence,
        }

    def _infer_project_type(self, frameworks: list[str], interfaces: dict, entry_points: list[str]) -> str:
        joined = " ".join(frameworks + interfaces["inbound"] + entry_points).lower()
        if "react" in joined or "next.js" in joined or "vue" in joined or "angular" in joined:
            if any("http api" in item.lower() for item in interfaces["inbound"]):
                return "web-application"
            return "frontend-application"
        if any("http api" in item.lower() for item in interfaces["inbound"]) or "asp.net core" in joined or "spring boot" in joined or "fastapi" in joined:
            return "web-api"
        if any("background" in item.lower() for item in interfaces["inbound"]) or ".net generic host" in joined or "celery" in joined:
            return "background-service"
        if frameworks and not interfaces["inbound"]:
            return "application"
        return "unknown"

    def _build_summary(
        self,
        project_type: str,
        frameworks: list[str],
        deployable_units: list[str],
        datastores: list[dict],
        integrations: list[dict],
    ) -> str:
        stack_text = ", ".join(frameworks[:4]) if frameworks else "unknown stack"
        unit_text = f"{len(deployable_units)} deployable unit(s)" if deployable_units else "an unknown number of deployable units"
        datastore_text = ", ".join(item["name"] for item in datastores[:3]) if datastores else "no confirmed datastore"
        integration_text = ", ".join(item["name"] for item in integrations[:3]) if integrations else "no confirmed integrations"
        return (
            f"{self.project_name} appears to be a {project_type} built on {stack_text}, "
            f"with {unit_text}, {datastore_text}, and {integration_text} based on scanned repository artifacts."
        )

    def _derive_overall_confidence(
        self,
        frameworks: list[str],
        entry_points: list[str],
        deployable_units: list[str],
        datastores: list[dict],
        interfaces: dict,
        integrations: list[dict],
        security: dict,
        deployment: dict,
    ) -> str:
        score = 0
        if frameworks:
            score += 2
        if entry_points:
            score += 2
        if deployable_units:
            score += 2
        if datastores:
            score += 1
        if interfaces["inbound"] or interfaces["outbound"]:
            score += 1
        if integrations:
            score += 1
        if security["confidence"] in {"medium", "high"}:
            score += 1
        if deployment["confidence"] in {"medium", "high"}:
            score += 1
        if score >= 8:
            return "high"
        if score >= 5:
            return "medium"
        return "low"

    def _write_output_json(self, report: dict) -> None:
        output_path = self.output_folder / "output.json"
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    def _write_output_md(self, report: dict) -> None:
        output_path = self.output_folder / "output.md"
        generated_at = datetime.now(timezone.utc).isoformat()
        markdown = [
            f"generated_at: {generated_at}",
            "source_skill: tas-01-project-architecture-analyzer",
            f"project_folder: {report['source_project_folder']}",
            f"workspace_folder: {report['workspace_output_folder']}",
            f"confidence_summary: {report['overall_confidence']}",
            "",
            "# 1. Overview",
            f"- Project: {report['project_name']}",
            f"- Type: {report['project_type']}",
            f"- Primary stack: {', '.join(report['primary_stack']) or 'unknown'}",
            f"- Entry points: {', '.join(report['entry_points']) or 'unknown'}",
            "",
            "# 2. Architecture Summary",
            report["summary"],
            "",
            "# 3. Components",
        ]
        markdown.extend(self._render_named_objects(report["components"], ["kind", "description", "confidence", "evidence"]))
        markdown.extend(["", "# 4. Data Stores"])
        markdown.extend(self._render_named_objects(report["datastores"], ["type", "usage", "confidence", "evidence"]))
        markdown.extend(["", "# 5. Interfaces"])
        markdown.append("## Inbound")
        markdown.extend(self._render_string_list(report["interfaces"]["inbound"]))
        markdown.append("")
        markdown.append("## Outbound")
        markdown.extend(self._render_string_list(report["interfaces"]["outbound"]))
        markdown.extend(["", "# 6. Integrations"])
        markdown.extend(self._render_named_objects(report["integrations"], ["type", "interaction", "confidence", "evidence"]))
        markdown.extend(["", "# 7. Security"])
        markdown.append(f"- Confidence: {report['security']['confidence']}")
        markdown.append("- Authentication")
        markdown.extend(self._render_string_list(report["security"]["authentication"]))
        markdown.append("- Authorization")
        markdown.extend(self._render_string_list(report["security"]["authorization"]))
        markdown.append("- Secrets Handling")
        markdown.extend(self._render_string_list(report["security"]["secrets_handling"]))
        markdown.extend(["", "# 8. Deployment"])
        markdown.append(f"- Confidence: {report['deployment']['confidence']}")
        markdown.append("- Hosting Clues")
        markdown.extend(self._render_string_list(report["deployment"]["hosting_clues"]))
        markdown.append("- CI/CD Clues")
        markdown.extend(self._render_string_list(report["deployment"]["ci_cd_clues"]))
        markdown.append("- Runtime Clues")
        markdown.extend(self._render_string_list(report["deployment"]["runtime_clues"]))
        markdown.extend(["", "# 9. Observed Facts"])
        markdown.extend(self._render_string_list(report["observed_facts"]))
        markdown.extend(["", "# 10. Inferred Facts"])
        markdown.extend(self._render_string_list(report["inferred_facts"]))
        markdown.extend(["", "# 11. Unknowns"])
        markdown.extend(self._render_string_list(report["unknowns"]))
        markdown.extend(["", "# 12. Risks and Assumptions"])
        markdown.append("## Risks")
        markdown.extend(self._render_string_list(report["risks"]))
        markdown.append("")
        markdown.append("## Assumptions")
        markdown.extend(self._render_string_list(report["assumptions"]))
        output_path.write_text("\n".join(markdown).rstrip() + "\n", encoding="utf-8")

    def _append_decisions(self, report: dict) -> None:
        decisions_path = self.output_folder / "decisions.md"
        generated_at = datetime.now(timezone.utc).isoformat()
        items: list[str] = []
        for assumption in report["assumptions"]:
            items.append(f"- assumption: {assumption}")
        for unknown in report["unknowns"]:
            items.append(f"- unclear component: {unknown}")
        for integration in report["integrations"]:
            if integration["confidence"] != "high":
                items.append(f"- guessed integration: {integration['name']} ({integration['interaction']})")
        if not items:
            items.append("- assumption: No extra assumptions or guessed integrations were recorded for this run.")
        block = [f"## {generated_at}"] + items + [""]
        with decisions_path.open("a", encoding="utf-8") as handle:
            handle.write("\n".join(block))

    @staticmethod
    def _render_named_objects(items: list[dict], field_order: list[str]) -> list[str]:
        if not items:
            return ["- none"]
        lines: list[str] = []
        for item in items:
            lines.append(f"- {item.get('name', 'unknown')}")
            for field in field_order:
                value = item.get(field, [])
                if isinstance(value, list):
                    value_text = ", ".join(value) if value else "none"
                else:
                    value_text = value or "none"
                lines.append(f"  - {field.replace('_', ' ').title()}: {value_text}")
        return lines

    @staticmethod
    def _render_string_list(items: list[str]) -> list[str]:
        return [f"- {item}" for item in items] if items else ["- none"]

    @staticmethod
    def _safe_json(content: str) -> dict:
        try:
            parsed = json.loads(content)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}

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
    def _dedupe_objects(items: list[dict], key: str) -> list[dict]:
        seen: set[str] = set()
        result: list[dict] = []
        for item in items:
            marker = str(item.get(key, ""))
            if marker in seen:
                continue
            seen.add(marker)
            result.append(item)
        return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze a repository and generate a Project Architecture Profile.")
    parser.add_argument("--project-folder", required=True, help="Path to the source repository.")
    parser.add_argument("--workspace-folder", required=True, help="Root output folder for analyzer artifacts.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_folder = Path(args.project_folder)
    workspace_folder = Path(args.workspace_folder)
    if not project_folder.exists() or not project_folder.is_dir():
        raise SystemExit(f"Project folder does not exist or is not a directory: {project_folder}")
    workspace_folder.mkdir(parents=True, exist_ok=True)
    analyzer = Analyzer(project_folder=project_folder, workspace_folder=workspace_folder)
    analyzer.run()
    print(analyzer.output_folder)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
