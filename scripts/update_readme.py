#!/usr/bin/env python3
"""Dynamically update readme file in CI"""

import re
from pathlib import Path

from pyhive.src._generated_versions import SUPPORTED_API_VERSIONS

if __name__ == "__main__":
    # Read current README
    readme_file = Path("README.md")
    readme_text = readme_file.read_text(encoding="UTF-8")

    # Create the replacement block
    BLOCK = (
        "<!-- SUPPORTED_API_VERSIONS_START -->\n"
        + "\n".join(f"- `{v}`" for v in SUPPORTED_API_VERSIONS)
        + "\n<!-- SUPPORTED_API_VERSIONS_END -->"
    )

    # Replace the block between markers
    PATTERN = (
        r"<!-- SUPPORTED_API_VERSIONS_START -->(.*?)<!-- SUPPORTED_API_VERSIONS_END -->"
    )
    updated_text = re.sub(PATTERN, BLOCK, readme_text, flags=re.DOTALL)

    # Write back if changed
    if updated_text != readme_text:
        readme_file.write_text(updated_text, encoding="UTF-8")
        print("✅ README updated with supported API versions")
    else:
        print("ℹ️ README already up-to-date")
