import sys
from unittest.mock import MagicMock

from intersystems_pyprod._production_definition import ServiceItem, _create_production_item


def test_special_characters_are_xml_escaped(monkeypatch):
    # Generation only needs the iris module for validation, which this test does not exercise
    monkeypatch.setitem(sys.modules, "iris", MagicMock())

    class MyProduction:
        services = [
            ServiceItem(
                "My&Service",
                "EnsLib.File.PassthroughService",
                adapter_settings={"FilePath": "/data/input&output <a> \"b\""},
                comment="x < y",
            )
        ]

    xml, _ = _create_production_item(MyProduction)

    assert 'Name="My&amp;Service"' in xml, f"unescaped item name: {xml!r}"
    assert 'Comment="x &lt; y"' in xml, f"unescaped item comment: {xml!r}"
    assert "/data/input&amp;output &lt;a&gt; &quot;b&quot;" in xml, f"unescaped setting value: {xml!r}"
