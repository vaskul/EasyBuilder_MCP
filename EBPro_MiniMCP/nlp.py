"""Простий парсер україномовних завдань для EBPro Mini-MCP."""
from __future__ import annotations

import re
from typing import Any, Dict, Tuple


class NLPError(Exception):
    """Помилка розбору інструкції користувача."""


# Регексп для шляху у лапках (подвійні або одинарні лапки).
PATH_REGEX = re.compile(r"['\"]([^'\"]+)['\"]")


def _extract_path(text: str) -> str | None:
    """Повертає шлях до файлу/теки, знайдений у лапках, якщо він існує."""

    match = PATH_REGEX.search(text)
    if match:
        return match.group(1)
    return None


def parse_instruction(text: str, args: Dict[str, Any] | None = None) -> Tuple[str, Dict[str, Any]]:
    """Розпізнає дію та аргументи з україномовного тексту.

    Parameters
    ----------
    text: str
        Сирий текст від користувача (українською/змішаною мовою).
    args: Dict[str, Any] | None
        Додаткові аргументи з HTTP-запиту, мають пріоритет над текстом.

    Returns
    -------
    Tuple[str, Dict[str, Any]]
        Пара (назва дії, словник параметрів).

    Raises
    ------
    NLPError
        Якщо інструкцію не вдалося розпізнати.
    """

    if not text or not text.strip():
        raise NLPError("Надайте текст інструкції українською мовою.")

    lowered = text.lower()
    args = dict(args or {})

    # Визначення дії "відкрити проєкт".
    if re.search(r"(відкри(й|ти)|open).*(проєкт|проект)", lowered):
        path = args.get("path") or _extract_path(text)
        if not path:
            raise NLPError(
                "Не вдалося знайти шлях до проєкту. Додайте його у лапках або в полі args.path."
            )
        args["path"] = path
        return "open_project", args

    # Дія "збірка EXOB".
    if re.search(r"(зібра(ти|й)|компілювати|build|експортуй).*", lowered):
        return "build_exob", args

    # Дія "офлайн симуляція".
    if re.search(r"(офлайн|offline).*(симуляц(ію|ія)|simulation)", lowered):
        return "run_offline_sim", args

    # Дія "зробити скріншот".
    if re.search(r"(скрін|скріншот|screenshot)", lowered):
        out_path = args.get("out") or _extract_path(text)
        if not out_path:
            raise NLPError(
                "Для скріншота вкажіть шлях збереження у лапках або у полі args.out."
            )
        args["out"] = out_path
        return "take_screenshot", args

    # Дія "запакувати у ECMP".
    if re.search(r"(запакуй|упакуй|compress|ecmp)", lowered):
        out_path = args.get("out") or _extract_path(text)
        if not out_path:
            raise NLPError(
                "Для пакування в ECMP вкажіть шлях збереження у лапках або у полі args.out."
            )
        args["out"] = out_path
        return "pack_ecmp", args

    raise NLPError(
        "Не вдалося визначити дію. Використайте ключові слова: відкрий, зібрати, офлайн симуляція, скріншот, запакуй."
    )


__all__ = ["parse_instruction", "NLPError"]
