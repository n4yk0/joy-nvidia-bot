from __future__ import annotations

import json

from joy_bot.state import StateTracker


def test_first_seen_in_stock_is_transition(tmp_path):
    state = StateTracker(tmp_path / "s.json")
    assert state.transitioned_to_in_stock("SKU", True) is True


def test_repeat_in_stock_is_not_transition(tmp_path):
    state = StateTracker(tmp_path / "s.json")
    state.update("SKU", True)
    assert state.transitioned_to_in_stock("SKU", True) is False


def test_back_in_stock_after_out_is_transition(tmp_path):
    state = StateTracker(tmp_path / "s.json")
    state.update("SKU", True)
    state.update("SKU", False)
    assert state.transitioned_to_in_stock("SKU", True) is True


def test_persists_across_instances(tmp_path):
    path = tmp_path / "s.json"
    a = StateTracker(path)
    a.update("SKU", True)
    a.flush()

    b = StateTracker(path)
    assert b.transitioned_to_in_stock("SKU", True) is False


def test_recovers_from_corrupt_file(tmp_path):
    path = tmp_path / "s.json"
    path.write_text("not-json{")
    state = StateTracker(path)
    assert state.transitioned_to_in_stock("SKU", True) is True


def test_flush_creates_parent_dir(tmp_path):
    path = tmp_path / "nested" / "dir" / "s.json"
    state = StateTracker(path)
    state.update("SKU", True)
    state.flush()
    assert json.loads(path.read_text()) == {"SKU": True}
