"""Keep signed updates published under both product names in one Sparkle feed."""

from pathlib import Path
import sys
import xml.etree.ElementTree as ET

SPARKLE = "http://www.andymatuschak.org/xml-namespaces/sparkle"
ET.register_namespace("sparkle", SPARKLE)


def merge(current: ET.ElementTree, legacy: ET.ElementTree) -> ET.ElementTree:
    channel = current.getroot().find("channel")
    legacy_channel = legacy.getroot().find("channel")
    if channel is None or legacy_channel is None:
        raise ValueError("Both appcasts must have an RSS channel")
    versions = {}
    # Prefer the new product's item if both feeds contain the same build.
    for item in [*channel.findall("item"), *legacy_channel.findall("item")]:
        version = item.findtext(f"{{{SPARKLE}}}version")
        if not version:
            raise ValueError("Update item has no Sparkle build version")
        versions.setdefault(version, item)
    for item in channel.findall("item"):
        channel.remove(item)
    for version in sorted(versions, key=lambda v: tuple(int(n) for n in v.split(".")), reverse=True)[:10]:
        channel.append(versions[version])
    return current


if __name__ == "__main__":
    output, legacy = map(Path, sys.argv[1:])
    merged = merge(ET.parse(output), ET.parse(legacy))
    merged.write(output, encoding="utf-8", xml_declaration=True)
