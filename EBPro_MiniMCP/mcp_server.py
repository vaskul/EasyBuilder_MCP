"""FastAPI-сервіс EBPro Mini-MCP."""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .ebpro_actions import (
    FriendlyError,
    build_exob,
    load_config,
    open_project,
    pack_ecmp,
    run_offline_sim,
    take_screenshot,
)
from .nlp import NLPError, parse_instruction

APP_VERSION = "0.1.0"
BUILD_DATE = datetime.utcnow().strftime("%Y-%m-%d")
SUPPORTED_ACTIONS = [
    "open_project",
    "build_exob",
    "run_offline_sim",
    "take_screenshot",
    "pack_ecmp",
]

# Налаштування логування: консоль + файл.
LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "ebpro_mcp.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
LOGGER = logging.getLogger("ebpro.server")

app = FastAPI(title="EBPro Mini-MCP", version=APP_VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    """Схема запиту для виконання україномовного завдання."""

    text: str
    args: Optional[Dict[str, Any]] = None
    token: Optional[str] = None


class RunResponse(BaseModel):
    """Стандартна відповідь сервісу."""

    ok: bool
    action: str
    file: Optional[str] = None
    notes: Optional[str] = None


class ErrorResponse(BaseModel):
    """Опис помилки з дружньою підказкою."""

    code: str
    message: str
    hint: str


def _ensure_token(token: Optional[str]) -> None:
    """Перевіряє токен API, якщо він налаштований."""

    config = load_config()
    if config.API_TOKEN and token != config.API_TOKEN:
        LOGGER.warning("Отримано некоректний токен доступу.")
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse(
                code="unauthorized",
                message="Потрібен коректний API token.",
                hint="Встановіть правильний token у config.json або у полі запиту.",
            ).dict(),
        )


@app.get("/health")
async def health() -> Dict[str, str]:
    """Швидка перевірка стану сервісу."""

    return {"status": "ok"}


@app.get("/version")
async def version() -> Dict[str, Any]:
    """Повертає інформацію про версію та підтримувані команди."""

    return {
        "version": APP_VERSION,
        "build_date": BUILD_DATE,
        "commands": SUPPORTED_ACTIONS,
    }


@app.post("/run", response_model=RunResponse)
async def run_command(request: RunRequest) -> RunResponse:
    """Приймає україномовне завдання та виконує відповідну дію у EBPro."""

    _ensure_token(request.token)

    try:
        action, params = parse_instruction(request.text, request.args or {})
    except NLPError as exc:
        LOGGER.error("Помилка NLP: %s", exc)
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                code="invalid_instruction",
                message=str(exc),
                hint="Використайте ключові слова відкрий/зібрати/симуляція/скріншот/запакуй.",
            ).dict(),
        )

    try:
        file_path: Optional[str] = None
        if action == "open_project":
            open_project(params["path"])
        elif action == "build_exob":
            build_exob()
        elif action == "run_offline_sim":
            run_offline_sim()
        elif action == "take_screenshot":
            file_path = take_screenshot(params["out"])
        elif action == "pack_ecmp":
            file_path = pack_ecmp(params["out"])
        else:
            raise FriendlyError(
                f"Дія {action} ще не реалізована.",
                "Оновіть Mini-MCP або зверніться до розробника для додавання функціоналу.",
            )
    except KeyError as exc:
        LOGGER.error("Відсутній необхідний параметр: %s", exc)
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                code="missing_argument",
                message=f"Не вистачає параметра {exc}.",
                hint="Передайте значення у полі args або в тексті запиту.",
            ).dict(),
        )
    except FriendlyError as exc:
        LOGGER.error("Помилка бізнес-логіки: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                code="action_failed",
                message=str(exc),
                hint=exc.hint,
            ).dict(),
        )
    except Exception as exc:  # pragma: no cover - непередбачувані помилки
        LOGGER.exception("Непередбачена помилка виконання дії")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                code="internal_error",
                message="Сталася непередбачена помилка.",
                hint="Перевірте логи ebpro_mcp.log для детальної інформації.",
            ).dict(),
        ) from exc

    notes = "Дію виконано успішно."
    if action == "run_offline_sim":
        notes = "Симуляцію запущено. Перевірте вікно EasySimulator."

    return RunResponse(ok=True, action=action, file=file_path, notes=notes)


__all__ = ["app"]
