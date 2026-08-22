#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse


REQUIRED_LISTING_FIELDS = (
    "name",
    "subtitle",
    "description",
    "category",
    "developerName",
    "websiteURL",
    "customerSupportURL",
    "privacyPolicyURL",
    "termsOfServiceURL",
    "version",
    "packageName",
    "capabilities",
)
URL_FIELDS = ("websiteURL", "customerSupportURL", "privacyPolicyURL", "termsOfServiceURL")


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
    try:
        parsed = urlparse(value)
    except Exception:
        return False
    return parsed.scheme == "https" and bool(parsed.netloc)


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
        "starterPrompts": override.get("starterPrompts", interface.get("defaultPrompt", [])),
    }

    branding = {
        "manifestLogo": interface.get("logo"),
        "composerIcon": interface.get("composerIcon"),
        "lightLogo": asset_ref(root, "assets/logo-light.svg"),
        "darkLogo": asset_ref(root, "assets/logo-dark.svg"),
        "brandColor": interface.get("brandColor"),
    }

    missing = [key for key in REQUIRED_LISTING_FIELDS if not nonempty(listing.get(key))]
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

    subtitle = listing.get("subtitle")
    if isinstance(subtitle, str) and len(subtitle) > 30:
        errors.append(f"subtitle exceeds 30 characters: {len(subtitle)}")

    description = listing.get("description")
    if isinstance(description, str) and len(description) > 4000:
        errors.append(f"description exceeds 4000 characters: {len(description)}")

    capabilities = listing.get("capabilities")
    if capabilities is not None and not isinstance(capabilities, list):
        errors.append("capabilities must be a list")
    elif isinstance(capabilities, list):
        if len(capabilities) > 20:
            errors.append(f"capabilities exceeds 20 items: {len(capabilities)}")
        for index, capability in enumerate(capabilities):
            if not isinstance(capability, str) or not capability.strip():
                errors.append(f"capabilities[{index}] must be a non-empty string")
            elif len(capability) > 120:
                errors.append(f"capabilities[{index}] exceeds 120 characters")

    prompts = listing.get("starterPrompts")
    if prompts is not None and not isinstance(prompts, list):
        errors.append("starterPrompts must be a list")
    elif isinstance(prompts, list):
        normalized = [item.strip() for item in prompts if isinstance(item, str)]
        if len(normalized) != len(prompts):
            errors.append("starterPrompts must contain strings only")
        if len(set(normalized)) != len(normalized):
            errors.append("starterPrompts must be unique")

    for key in URL_FIELDS:
        value = listing.get(key)
        if isinstance(value, str) and value.strip() and not https_url(value.strip()):
            errors.append(f"{key} must be a public HTTPS URL")

    developer = listing.get("developerName")
    if developer:
        warnings.append("Confirm developerName matches the verified OpenAI developer/business identity; this cannot be proven from package metadata alone.")

    report = {
        "ok": not missing and not errors,
        "schemaVersion": 1,
        "source": {
            "pluginRoot": str(root),
            "manifest": ".codex-plugin/plugin.json",
            "listingOverride": str(listing_source) if listing_source else None,
        },
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
