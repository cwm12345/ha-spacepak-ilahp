#!/usr/bin/env python3
# Written by Claude, guided by Chris.
"""Rebuild custom_components/spacepak_ilahp from the core-shaped integration.

The integration is written once, in Home Assistant core's layout under core/
(homeassistant/components/spacepak_ilahp + tests/components/spacepak_ilahp),
against the published spacepak-modbus library. This script turns that into the
custom integration shipped here: the library is copied in (vendored) under
custom_components/spacepak_ilahp/spacepak_modbus, imports are pointed at the
copy, the manifest gets a version and drops the core-only keys, strings.json is
resolved into translations/en.json, and the tests are rewritten onto
pytest-homeassistant-custom-component.

Usage:
    python scripts/vendor.py --library ../spacepak-modbus --version 0.2.0

Needs `homeassistant` importable, for the shared strings translations point at.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any

DOMAIN = "spacepak_ilahp"
REPO = Path(__file__).resolve().parent.parent
REPO_URL = "https://github.com/cwm12345/ha-spacepak-ilahp"

_TEST_REWRITES = [
    (f"homeassistant.components.{DOMAIN}", f"custom_components.{DOMAIN}"),
    (
        "from tests.common import",
        "from pytest_homeassistant_custom_component.common import",
    ),
    (
        "from tests.components.diagnostics import",
        "from pytest_homeassistant_custom_component.components.diagnostics import",
    ),
    (
        "from tests.typing import",
        "from pytest_homeassistant_custom_component.typing import",
    ),
]

_CUSTOM_CONFTEST_FIXTURE = '''

@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Load the custom integration in every test."""
'''


def _resolve(node: Any, common: dict[str, Any]) -> Any:
    """Replace "[%key:a::b%]" references with the text they point at."""
    if isinstance(node, dict):
        return {key: _resolve(value, common) for key, value in node.items()}
    if isinstance(node, str) and node.startswith("[%key:") and node.endswith("%]"):
        target: Any = common
        for part in node[len("[%key:") : -len("%]")].split("::"):
            target = target[part]
        return target
    return node


def _source_revision(path: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "--short", "HEAD"], text=True
        ).strip()
    except OSError, subprocess.CalledProcessError:
        return "unknown"


def build(library: Path, core: Path, version: str) -> None:
    """Regenerate the custom integration and its tests."""
    import homeassistant

    target = REPO / "custom_components" / DOMAIN
    shutil.rmtree(target, ignore_errors=True)
    shutil.copytree(
        core / "homeassistant" / "components" / DOMAIN,
        target,
        ignore=shutil.ignore_patterns(
            "quality_scale.yaml", "translations", "__pycache__"
        ),
    )

    for path in target.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        text = re.sub(
            r"^from spacepak_modbus", "from .spacepak_modbus", text, flags=re.MULTILINE
        )
        path.write_text(text, encoding="utf-8")

    vendored = target / "spacepak_modbus"
    shutil.copytree(
        library / "src" / "spacepak_modbus",
        vendored,
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    (vendored / "VENDORED.md").write_text(
        "Copied unchanged from spacepak-modbus "
        f"(https://github.com/cwm12345/spacepak-modbus, revision "
        f"{_source_revision(library)}) by scripts/vendor.py. Edit the library, "
        "not this copy.\n",
        encoding="utf-8",
    )

    manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    manifest.pop("quality_scale", None)
    manifest.update(
        documentation=REPO_URL,
        issue_tracker=f"{REPO_URL}/issues",
        requirements=["modbus-connection[tmodbus]>=4.12.1"],
        version=version,
    )
    ordered = {"domain": manifest.pop("domain"), "name": manifest.pop("name")}
    ordered.update(sorted(manifest.items()))
    (target / "manifest.json").write_text(
        json.dumps(ordered, indent=2) + "\n", encoding="utf-8"
    )

    common = json.loads(
        (Path(homeassistant.__file__).parent / "strings.json").read_text(
            encoding="utf-8"
        )
    )
    strings = json.loads((target / "strings.json").read_text(encoding="utf-8"))
    (target / "translations").mkdir()
    (target / "translations" / "en.json").write_text(
        json.dumps(_resolve(strings, common), indent=2) + "\n", encoding="utf-8"
    )

    tests = REPO / "tests"
    shutil.rmtree(tests, ignore_errors=True)
    shutil.copytree(
        core / "tests" / "components" / DOMAIN,
        tests,
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    for path in tests.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for old, new in _TEST_REWRITES:
            text = text.replace(old, new)
        if path.name == "conftest.py":
            text += _CUSTOM_CONFTEST_FIXTURE
        path.write_text(text, encoding="utf-8")


def main() -> None:
    """Parse arguments and build."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--core", type=Path, default=REPO / "core")
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    build(args.library.resolve(), args.core.resolve(), args.version)


if __name__ == "__main__":
    main()
