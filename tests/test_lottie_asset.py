"""Tests for the locally bundled SALESCAST Lottie animation."""

import json
from pathlib import Path


def test_salescast_lottie_asset_has_animated_shapes_and_canvas():
    asset_path = Path(__file__).resolve().parents[1] / "assets" / "salescast-lottie.json"
    animation = json.loads(asset_path.read_text(encoding="utf-8"))

    assert animation["nm"] == "SALESCAST signal"
    assert animation["op"] > animation["ip"]
    groups = animation["layers"][0]["shapes"]
    assert len(groups) == 5
    assert [group["nm"] for group in groups[:4]] == [
        "Bar one", "Bar two", "Bar three", "Bar four"
    ]
    assert groups[-1]["nm"] == "Navy canvas"
    assert all(group["it"][-1]["s"]["a"] == 1 for group in groups[:4])
