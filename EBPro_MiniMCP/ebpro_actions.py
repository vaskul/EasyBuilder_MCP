"""Набір обгорток для автоматизації дій у EasyBuilder Pro."""
from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

try:
    from pywinauto import Desktop
    from pywinauto.application import Application
    from pywinauto.findwindows import ElementNotFoundError
except Exception:  # pragma: no cover - середовище Linux під час тестів
    Desktop = None  # type: ignore
    Application = None  # type: ignore
    ElementNotFoundError = Exception  # type: ignore

try:
    from PIL import ImageGrab
except Exception:  # pragma: no cover - Pillow може не мати ImageGrab на Linux
    ImageGrab = None  # type: ignore

LOGGER = logging.getLogger("ebpro.actions")
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"


class FriendlyError(RuntimeError):
    """Спеціальний виняток з дружнім підказуванням для користувача."""

    def __init__(self, message: str, hint: Optional[str] = None):
        super().__init__(message)
        self.hint = hint or "Перевірте налаштування у config.json та README_UA.md."


@dataclass
class EBProConfig:
    """Структура конфігурації EBPro Mini-MCP."""

    EBPRO_DIR: str
    EBPRO_EXE: str
    UTILITY_MANAGER_EXE: str
    SIMULATOR_WINDOW_TITLE: str
    EBPRO_WINDOW_TITLE: str
    API_TOKEN: str
    AUTOHOTKEY_EXE: str

    @property
    def ebpro_path(self) -> Path:
        """Повний шлях до EBPro.exe."""

        return Path(self.EBPRO_DIR) / self.EBPRO_EXE


_CONFIG_CACHE: Optional[EBProConfig] = None


def load_config() -> EBProConfig:
    """Завантажує конфігурацію з файлу та накладає змінні середовища."""

    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    with CONFIG_PATH.open("r", encoding="utf-8") as fp:
        data = json.load(fp)

    # Змінні середовища мають пріоритет (EBPRO_MCP_<KEY> або просто <KEY>).
    for key in list(data.keys()):
        env_key = f"EBPRO_MCP_{key}"
        if env_key in os.environ:
            data[key] = os.environ[env_key]
            continue
        if key in os.environ:
            data[key] = os.environ[key]

    _CONFIG_CACHE = EBProConfig(**data)
    return _CONFIG_CACHE


def _ensure_windows_environment() -> None:
    """Перевіряє, що код виконується у Windows з доступною pywinauto."""

    if sys.platform != "win32":
        raise FriendlyError(
            "Керування вікнами доступне лише на Windows.",
            "Запустіть сервіс на Windows 10/11 з встановленою EasyBuilder Pro.",
        )
    if Application is None or Desktop is None:
        raise FriendlyError(
            "pywinauto недоступна у середовищі.",
            "Переконайтеся, що пакети pywinauto та залежності встановлені у Windows.",
        )


def _connect_to_ebpro_window(title: str):
    """Повертає вікно EBPro за частиною заголовка."""

    _ensure_windows_environment()
    try:
        desktop = Desktop(backend="uia")
        window = desktop.window(title_re=rf".*{title}.*")
        window.wait("ready", timeout=10)
        window.set_focus()
        return window
    except ElementNotFoundError as exc:  # type: ignore[arg-type]
        raise FriendlyError(
            f"Не знайдено вікно з назвою, що містить '{title}'.",
            "Змініть SIMULATOR_WINDOW_TITLE/EBPRO_WINDOW_TITLE у config.json під свою локалізацію.",
        ) from exc


def run_ebpro(timeout: float = 20.0) -> None:
    """Стартує EBPro.exe, якщо ще не запущено."""

    config = load_config()
    _ensure_windows_environment()

    ebpro_path = config.ebpro_path
    if not ebpro_path.exists():
        raise FriendlyError(
            f"Файл {ebpro_path} не знайдено.",
            "Укажіть правильний шлях EBPRO_DIR/EBPRO_EXE у config.json.",
        )

    try:
        app = Application(backend="uia")  # type: ignore[call-arg]
        app.connect(path=str(ebpro_path))
        LOGGER.info("EBPro вже запущено, підключаємося до процесу.")
        return
    except Exception:
        LOGGER.info("EBPro не знайдено серед процесів, запускаємо новий екземпляр.")

    try:
        app = Application(backend="uia")  # type: ignore[call-arg]
        app.start(str(ebpro_path))
        app.wait_cpu_usage_lower(threshold=5.0, timeout=timeout)
        LOGGER.info("EBPro успішно запущено.")
    except Exception as exc:  # pragma: no cover - залежить від Windows
        raise FriendlyError(
            "Не вдалося стартувати EasyBuilder Pro.",
            "Запустіть EBPro вручну та повторіть запит, або перевірте права доступу.",
        ) from exc


def focus_window(title_contains: str):
    """Фокусується на вікні з вказаним фрагментом заголовку."""

    config = load_config()
    if title_contains == "EBPRO":
        title_contains = config.EBPRO_WINDOW_TITLE
    elif title_contains == "SIMULATOR":
        title_contains = config.SIMULATOR_WINDOW_TITLE
    return _connect_to_ebpro_window(title_contains)


def click_menu(path: Iterable[str]) -> None:
    """Натискає пункт меню за шляхом типу ["File", "Open..."] у EBPro."""

    config = load_config()
    window = _connect_to_ebpro_window(config.EBPRO_WINDOW_TITLE)

    try:
        menu_path = "->".join(path)
        LOGGER.info("Виконуємо вибір меню: %s", menu_path)
        window.menu_select(menu_path)
    except Exception as exc:
        raise FriendlyError(
            "Не вдалося натиснути пункт меню.",
            "Для стрічкового інтерфейсу налаштуйте кліки в ebpro_actions.click_menu або використайте AHK.",
        ) from exc


def open_project(path: str) -> None:
    """Відкриває файл проєкту *.emtp або *.ecmp у EBPro."""

    run_ebpro()
    normalized_path = Path(path)
    if not normalized_path.exists():
        raise FriendlyError(
            f"Файл {normalized_path} не знайдено.",
            "Перевірте шлях до проєкту або права доступу.",
        )

    click_menu(["File", "Open..."])

    try:
        app = Application(backend="uia")  # type: ignore[call-arg]
        dialog = app.window(title_re=r".*(Open|Відкрити).*")
        dialog.wait("ready", timeout=10)
        edit = dialog.child_window(control_type="Edit")
        edit.set_edit_text(str(normalized_path))
        open_button = dialog.child_window(title_re=r"(Open|Відкрити)", control_type="Button")
        open_button.click()
        LOGGER.info("Проєкт відкрито: %s", normalized_path)
    except Exception as exc:
        raise FriendlyError(
            "Не вдалося взаємодіяти з діалогом відкриття файлу.",
            "Перевірте локалізацію кнопок у open_project та налаштуйте селектори.",
        ) from exc


def build_exob() -> None:
    """Запускає збірку EXOB/CXOB через меню EBPro."""

    run_ebpro()
    try:
        click_menu(["Build", "Build"])
        LOGGER.info("Команда збірки EXOB виконана.")
    except FriendlyError:
        raise
    except Exception as exc:
        raise FriendlyError(
            "Не вдалося запустити збірку через меню.",
            "Змініть шлях меню у build_exob або використайте гарячі клавіші через AHK.",
        ) from exc


def _invoke_autohotkey(script_name: str) -> None:
    """Запускає скрипт AutoHotkey як fallback."""

    config = load_config()
    ahk_exe = Path(config.AUTOHOTKEY_EXE)
    script_path = BASE_DIR / "gui_fallback" / script_name

    if not ahk_exe.exists():
        raise FriendlyError(
            "AutoHotkey не знайдено.",
            "Встановіть AutoHotkey та оновіть AUTOHOTKEY_EXE у config.json.",
        )
    if not script_path.exists():
        raise FriendlyError(
            f"AHK-скрипт {script_path} не знайдено.",
            "Переконайтеся, що файли збережено разом із сервісом.",
        )

    LOGGER.info("Запускаємо AHK fallback: %s", script_path)
    try:
        subprocess.run([str(ahk_exe), str(script_path)], check=True)
    except subprocess.CalledProcessError as exc:
        raise FriendlyError(
            "AHK-скрипт завершився з помилкою.",
            "Перевірте гарячі клавіші у simulate_offline.ahk.",
        ) from exc


def run_offline_sim(timeout: float = 5.0) -> None:
    """Запускає Offline Simulation через меню або AHK."""

    run_ebpro()
    try:
        click_menu(["Tools", "Offline Simulation"])
        LOGGER.info("Офлайн-симуляцію запущено через меню.")
        time.sleep(timeout)
    except FriendlyError as menu_error:
        LOGGER.warning("Не вдалося запустити симуляцію через меню: %s", menu_error)
        LOGGER.info("Пробуємо fallback з AutoHotkey.")
        _invoke_autohotkey("simulate_offline.ahk")


def take_screenshot(out_path: str) -> str:
    """Зберігає знімок екрана або активного вікна симулятора."""

    if ImageGrab is None:
        raise FriendlyError(
            "Модуль ImageGrab недоступний.",
            "Запустіть сервіс на Windows з Pillow та увімкніть Desktop experience.",
        )

    focus_window("SIMULATOR")
    output = Path(out_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        image = ImageGrab.grab()
        image.save(output)
        LOGGER.info("Скріншот збережено у %s", output)
        return str(output)
    except Exception as exc:
        raise FriendlyError(
            "Не вдалося зняти скріншот.",
            "Перевірте права на запис та працездатність Pillow.",
        ) from exc


def pack_ecmp(out_path: str) -> str:
    """Запускає процес Compress Project для створення *.ecmp."""

    run_ebpro()
    click_menu(["File", "Compress"])

    output = Path(out_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        app = Application(backend="uia")  # type: ignore[call-arg]
        dialog = app.window(title_re=r".*(Save As|Зберегти як).*")
        dialog.wait("ready", timeout=10)
        edit = dialog.child_window(control_type="Edit")
        edit.set_edit_text(str(output))
        save_button = dialog.child_window(title_re=r"(Save|Зберегти)", control_type="Button")
        save_button.click()
        LOGGER.info("Проєкт запаковано у ECMP: %s", output)
        return str(output)
    except Exception as exc:
        raise FriendlyError(
            "Не вдалося завершити пакування у ECMP.",
            "Перевірте локалізацію діалогу 'Save As' та підлаштуйте селектори.",
        ) from exc


__all__ = [
    "FriendlyError",
    "EBProConfig",
    "load_config",
    "run_ebpro",
    "focus_window",
    "click_menu",
    "open_project",
    "build_exob",
    "run_offline_sim",
    "take_screenshot",
    "pack_ecmp",
]
