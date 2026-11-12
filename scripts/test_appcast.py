import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

spec = importlib.util.spec_from_file_location("merge_appcasts", Path(__file__).with_name("merge-appcasts.py"))
appcasts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(appcasts)


def feed(*items):
    channel = ET.Element("channel")
    for version, url in items:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, f"{{{appcasts.SPARKLE}}}version").text = version
        ET.SubElement(item, "enclosure", url=url, length="123", **{f"{{{appcasts.SPARKLE}}}edSignature": "unchanged"})
    root = ET.Element("rss")
    root.append(channel)
    return ET.ElementTree(root)


class AppcastCompatibilityTests(unittest.TestCase):
    def test_merges_numerically_and_preserves_signed_enclosures(self):
        result = appcasts.merge(feed(("10", "Verelay.zip")), feed(("5", "LiveTranslateBridge.zip")))
        items = result.getroot().findall("channel/item")
        self.assertEqual([i.findtext(f"{{{appcasts.SPARKLE}}}version") for i in items], ["10", "5"])
        self.assertEqual(items[1].find("enclosure").attrib, {
            "url": "LiveTranslateBridge.zip", "length": "123",
            f"{{{appcasts.SPARKLE}}}edSignature": "unchanged",
        })

    def test_empty_new_feed_keeps_old_updates(self):
        result = appcasts.merge(feed(), feed(("5", "old.zip")))
        self.assertEqual(result.getroot().find("channel/item/enclosure").get("url"), "old.zip")

    def test_duplicate_build_prefers_new_name(self):
        result = appcasts.merge(feed(("6", "Verelay.zip")), feed(("6", "old.zip")))
        items = result.getroot().findall("channel/item")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].find("enclosure").get("url"), "Verelay.zip")
