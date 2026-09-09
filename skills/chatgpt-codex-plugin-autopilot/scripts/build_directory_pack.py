#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

CATEGORIES = {
    "Productivity", "Creativity", "Developer Tools", "Business & Operations",
    "Data & Analytics", "Communication", "Education & Research", "Security",
    "Finance", "Healthcare", "Travel", "Entertainment", "Other",
}
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
PLUGIN_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
APP_MENTION = re.compile(r"(?<![A-Za-z0-9._%+-])@[A-Za-z0-9_-]+")

BASE_REQUIRED_LISTING_FIELDS = (
    "name",
    "subtitle",
    "description",
    "category",
    "developerName",
    "version",
    "packageName",
    "capabilities",
)
MCP_REQUIRED_URL_FIELDS = (
    "websiteURL",
    "customerSupportURL",
    "privacyPolicyURL",
    "termsOfServiceURL",
)
ALL_URL_FIELDS = MCP_REQUIRED_URL_FIELDS


def is_mcp_backed(manifest: dict) -> bool:
    for key in ("mcpServers", "apps"):
        val = manifest.get(key)
        if isinstance(val, str) and val.strip():
            return True
        if isinstance(val, (dict, list)) and bool(val):
            return True
        if val is True:
            return True
    return False


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object in {path}")
    return value


def nonempty(value) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return bool(value)
    return value is not None


def https_url(value: str) -> bool:
    if not isinstance(value, str) or not value.strip() or len(value) > 1024:
        return False
    try:
        parsed = urlparse(value.strip())
    except Exception:
        return False
    return (
        parsed.scheme.lower() == "https"
        and bool(parsed.netloc)
        and not parsed.username
        and not parsed.password
    )


def validate_url(url: object, key: str, errors: list[str]) -> None:
    if url is None or (isinstance(url, str) and not url.strip()):
        return
    if not isinstance(url, str):
        errors.append(f"{key} must be an HTTPS URL string")
        return
    trimmed = url.strip()
    if len(trimmed) > 1024:
        errors.append(f"{key} exceeds final directory limit of 1024 characters: {len(trimmed)}")
    try:
        parsed = urlparse(trimmed)
    except Exception:
        errors.append(f"{key} is an unparseable URL")
        return
    if parsed.scheme.lower() != "https" or not parsed.netloc:
        errors.append(f"{key} must be a public HTTPS URL")
    elif parsed.username or parsed.password:
        errors.append(f"{key} must not contain embedded credentials")


def pick(override: dict, interface: dict, output_key: str, *manifest_keys: str):
    if output_key in override:
        return override[output_key]
    for key in manifest_keys:
        if key in interface:
            return interface[key]
    return None


def asset_ref(root: Path, relative: str) -> str | None:
    path = root / relative
    return f"./{relative}" if path.is_file() else None


def build(root: Path, listing_path: Path | None = None) -> dict:
    root = root.expanduser().resolve()
    manifest_path = root / ".codex-plugin" / "plugin.json"
    manifest = load_json(manifest_path)
    interface = manifest.get("interface")
    if not isinstance(interface, dict):
        interface = {}

    if listing_path is None:
        default_listing = root / "submission" / "listing.json"
        override = load_json(default_listing) if default_listing.is_file() else {}
        listing_source = default_listing if default_listing.is_file() else None
    else:
        listing_path = listing_path.expanduser().resolve()
        override = load_json(listing_path)
        listing_source = listing_path

    has_mcp = is_mcp_backed(manifest)
    has_skills = "skills" in manifest or (root / "skills").is_dir()
    architecture = "hybrid" if has_mcp and has_skills else "MCP-backed" if has_mcp else "skills-only"

    raw_prompts = override.get("starterPrompts") if "starterPrompts" in override else interface.get("defaultPrompt", [])
    if isinstance(raw_prompts, str):
        prompts = [raw_prompts]
    elif isinstance(raw_prompts, list):
        prompts = list(raw_prompts)
    else:
        prompts = raw_prompts

    listing = {
        "name": pick(override, interface, "name", "displayName"),
        "subtitle": pick(override, interface, "subtitle", "shortDescription"),
        "description": pick(override, interface, "description", "longDescription"),
        "category": pick(override, interface, "category", "category"),
        "developerName": pick(override, interface, "developerName", "developerName"),
        "websiteURL": pick(override, interface, "websiteURL", "websiteURL"),
        "customerSupportURL": pick(override, interface, "customerSupportURL", "supportURL", "customerSupportURL"),
        "privacyPolicyURL": pick(override, interface, "privacyPolicyURL", "privacyPolicyURL"),
        "termsOfServiceURL": pick(override, interface, "termsOfServiceURL", "termsOfServiceURL"),
        "version": override.get("version", manifest.get("version")),
        "packageName": override.get("packageName", manifest.get("name")),
        "capabilities": override.get("capabilities", interface.get("capabilities")),
        "starterPrompts": prompts,
    }

    branding = {
        "manifestLogo": interface.get("logo"),
        "composerIcon": interface.get("composerIcon"),
        "lightLogo": asset_ref(root, "assets/logo-light.svg"),
        "darkLogo": asset_ref(root, "assets/logo-dark.svg"),
        "brandColor": interface.get("brandColor"),
    }

    has_mcp = is_mcp_backed(manifest)
    required_fields = list(BASE_REQUIRED_LISTING_FIELDS)
    if has_mcp:
        required_fields.extend(MCP_REQUIRED_URL_FIELDS)

    missing = [key for key in required_fields if not nonempty(listing.get(key))]
    if not branding["manifestLogo"]:
        missing.append("branding.manifestLogo")
    if not branding["composerIcon"]:
        missing.append("branding.composerIcon")
    if not branding["lightLogo"]:
        missing.append("branding.lightLogo")
    if not branding["darkLogo"]:
        missing.append("branding.darkLogo")

    errors: list[str] = []
    warnings: list[str] = []

    name = listing.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("name is required and must be a non-empty string")
    else:
        if len(name) > 30:
            errors.append(f"name exceeds 30 characters: {len(name)}")
        if "\n" in name or "\r" in name:
            errors.append("name must fit on one line")

    package_name = listing.get("packageName")
    if not isinstance(package_name, str) or not package_name:
        errors.append("packageName is required and must be a non-empty string")
    elif len(package_name) > 64 or not PLUGIN_NAME.fullmatch(package_name):
        errors.append("packageName must be 1..64 characters using supported ASCII letters, digits, _ or -")

    version = listing.get("version")
    if not isinstance(version, str) or not version:
        errors.append("version is required and must be a non-empty string")
    elif len(version) > 64 or not SEMVER.fullmatch(version):
        errors.append("version must be strict semver and <=64 characters")

    subtitle = listing.get("subtitle")
    if isinstance(subtitle, str):
        if not subtitle.strip():
            errors.append("subtitle must be a non-empty string")
        if len(subtitle) > 30:
            errors.append(f"subtitle exceeds 30 characters: {len(subtitle)}")
        if "\n" in subtitle or "\r" in subtitle:
            errors.append("subtitle must fit on one line")
    elif subtitle is not None:
        errors.append("subtitle must be a string")

    description = listing.get("description")
    if isinstance(description, str):
        if not description.strip():
            errors.append("description must be a non-empty string")
        if len(description) > 4000:
            errors.append(f"description exceeds 4000 characters: {len(description)}")
    elif description is not None:
        errors.append("description must be a string")

    developer = listing.get("developerName")
    if isinstance(developer, str):
        if not developer.strip():
            errors.append("developerName must be a non-empty string")
        if len(developer) > 80:
            errors.append(f"developerName exceeds 80 characters: {len(developer)}")
        if "\n" in developer or "\r" in developer:
            errors.append("developerName must fit on one line")
    elif developer is not None:
        errors.append("developerName must be a string")

    category = listing.get("category")
    if isinstance(category, str):
        if category not in CATEGORIES:
            errors.append(f"category is unsupported: {category}")
    elif category is not None:
        errors.append("category must be a string")

    capabilities = listing.get("capabilities")
    if capabilities is not None:
        if not isinstance(capabilities, list):
            errors.append("capabilities must be a list")
        else:
            if len(capabilities) > 20:
                errors.append(f"capabilities exceeds 20 items: {len(capabilities)}")
            for index, capability in enumerate(capabilities):
                if not isinstance(capability, str) or not capability.strip():
                    errors.append(f"capabilities[{index}] must be a non-empty string")
                else:
                    if len(capability) > 120:
                        errors.append(f"capabilities[{index}] exceeds 120 characters")
                    if "\n" in capability or "\r" in capability:
                        errors.append(f"capabilities[{index}] must fit on one line")

    prompts = listing.get("starterPrompts")
    if prompts is not None:
        if not isinstance(prompts, list):
            errors.append("starterPrompts must be a list")
        else:
            if len(prompts) > 3:
                errors.append(f"starterPrompts must contain at most 3 prompts: {len(prompts)}")
            normalized_prompts: set[str] = set()
            for index, prompt in enumerate(prompts):
                if not isinstance(prompt, str) or not prompt.strip():
                    errors.append(f"starterPrompts[{index}] must be a non-empty string")
                    continue
                if len(prompt) > 128:
                    errors.append(f"starterPrompts[{index}] exceeds 128 characters: {len(prompt)}")
                if "\n" in prompt or "\r" in prompt:
                    errors.append(f"starterPrompts[{index}] must fit on one line")
                if APP_MENTION.search(prompt):
                    errors.append(f"starterPrompts[{index}] must not contain an app @mention")
                norm = " ".join(unicodedata.normalize("NFKC", prompt).split()).casefold()
                if norm in normalized_prompts:
                    errors.append(f"starterPrompts entries must be unique after normalization: '{prompt}'")
                normalized_prompts.add(norm)

    for key in ALL_URL_FIELDS:
        value = listing.get(key)
        validate_url(value, key, errors)

    if developer:
        warnings.append(
            "Confirm developerName matches the verified OpenAI developer/business identity; "
            "this cannot be proven from package metadata alone."
        )

    report = {
        "ok": not missing and not errors,
        "schemaVersion": 1,
        "source": {
            "pluginRoot": str(root),
            "manifest": ".codex-plugin/plugin.json",
            "listingOverride": str(listing_source) if listing_source else None,
        },
        "targetArchitecture": "mcp" if has_mcp else "skills",
        "listing": listing,
        "branding": branding,
        "readiness": {
            "missing": sorted(set(missing)),
            "errors": errors,
            "warnings": warnings,
            "status": "listing_ready" if not missing and not errors else "not_ready",
        },
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a repository-maintained Plugin Directory evidence pack.")
    parser.add_argument("plugin_root", nargs="?", default=".")
    parser.add_argument("--listing", help="Optional submission/listing.json override path")
    parser.add_argument("--out", help="Write the report to this JSON file")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        report = build(Path(args.plugin_root), Path(args.listing) if args.listing else None)
    except Exception as exc:
        report = {"ok": False, "readiness": {"missing": [], "errors": [str(exc)], "warnings": [], "status": "not_ready"}}

    if args.out:
        out = Path(args.out).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        status = report.get("readiness", {}).get("status", "not_ready")
        print(f"directory pack: {status}")
        for item in report.get("readiness", {}).get("missing", []):
            print(f"missing: {item}")
        for item in report.get("readiness", {}).get("errors", []):
            print(f"error: {item}")
        for item in report.get("readiness", {}).get("warnings", []):
            print(f"warning: {item}")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
