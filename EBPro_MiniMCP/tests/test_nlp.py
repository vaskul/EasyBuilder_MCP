"""Юніт-тести для модуля nlp."""
from __future__ import annotations

import pytest

from ..nlp import NLPError, parse_instruction


def test_open_project_parses_path():
    action, params = parse_instruction('Відкрий проєкт "D:/HMI/demo.emtp"')
    assert action == "open_project"
    assert params["path"] == "D:/HMI/demo.emtp"


def test_build_command():
    action, params = parse_instruction("Зібрати проект у exob")
    assert action == "build_exob"
    assert params == {}


def test_offline_simulation():
    action, _ = parse_instruction("Запусти офлайн симуляцію негайно")
    assert action == "run_offline_sim"


def test_screenshot_requires_out():
    with pytest.raises(NLPError):
        parse_instruction("Зроби скріншот")

    action, params = parse_instruction(
        'Зроби скріншот "D:/shots/sim.png"',
        args={"out": "D:/shots/override.png"},
    )
    assert action == "take_screenshot"
    assert params["out"] == "D:/shots/override.png"


def test_pack_ecmp():
    action, params = parse_instruction(
        "Будь ласка, запакуй проект у ecmp",
        args={"out": "D:/export/project.ecmp"},
    )
    assert action == "pack_ecmp"
    assert params["out"] == "D:/export/project.ecmp"


def test_unknown_command():
    with pytest.raises(NLPError):
        parse_instruction("Покажи мені статистику")
