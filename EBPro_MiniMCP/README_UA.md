# EBPro Mini-MCP

Локальний HTTP-агент для автоматизації настільної **EasyBuilder Pro**. Сервіс приймає україномовні інструкції та виконує дії в GUI за допомогою `pywinauto` (з fallback на AutoHotkey).

## Можливості

- Відкриття проєктів *.emtp / *.ecmp.
- Збірка EXOB/CXOB.
- Запуск Offline Simulation.
- Знімки екрана симулятора.
- Пакування проєкту у *.ecmp.

## Вимоги

- Windows 10 або Windows 11.
- Встановлений Python 3.11+.
- Встановлена EasyBuilder Pro (версія з підтримкою меню File/Tools).
- Доступ до AutoHotkey (опційно для fallback).

## Встановлення

```powershell
cd EBPro_MiniMCP
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Налаштування `config.json`

1. Вкажіть каталог і назву виконуваного файлу EBPro (`EBPRO_DIR`, `EBPRO_EXE`).
2. Задайте заголовки вікон для основної програми та симулятора (`EBPRO_WINDOW_TITLE`, `SIMULATOR_WINDOW_TITLE`).
3. За потреби встановіть `API_TOKEN` — токен безпеки для `/run`.
4. Якщо плануєте fallback через AutoHotkey, відредагуйте `AUTOHOTKEY_EXE`.

Параметри можна перекривати змінними середовища, наприклад:

```powershell
set EBPRO_MCP_API_TOKEN=MySecret
```

## Запуск сервера

> **Примітка:** Команду запуску виконуйте з кореня репозиторію, де знаходиться папка `EBPro_MiniMCP`.

```powershell
python -m uvicorn EBPro_MiniMCP.mcp_server:app --reload --host 0.0.0.0 --port 8000
```

або скористайтесь скриптом:

```batch
run_server.bat
```

### Перевірка стану

- `GET http://localhost:8000/health` → `{ "status": "ok" }`
- `GET http://localhost:8000/version` → версія та перелік команд.

## Приклади HTTP-запитів

```http
POST http://localhost:8000/run
Content-Type: application/json

{"text":"Відкрий проєкт \"D:\\HMI\\pump.emtp\""}
```

```http
POST http://localhost:8000/run
Content-Type: application/json

{"text":"Зібрати проєкт у exob"}
```

```http
POST http://localhost:8000/run
Content-Type: application/json

{"text":"Запусти офлайн симуляцію"}
```

```http
POST http://localhost:8000/run
Content-Type: application/json

{"text":"Зроби скріншот","args":{"out":"D:\\HMI\\shots\\sim.png"}}
```

```http
POST http://localhost:8000/run
Content-Type: application/json

{"text":"Запакуй проект у ecmp","args":{"out":"D:\\HMI\\export\\project.ecmp"}}
```

## Налаштування гарячих клавіш / селекторів

Різні версії EBPro можуть відрізнятися меню. Якщо `pywinauto` не знаходить пункт меню:

1. Відредагуйте функцію `click_menu` в `ebpro_actions.py` (можна замінити на клік по елементах стрічки).
2. Налаштуйте `gui_fallback/simulate_offline.ahk` для своїх гарячих клавіш.
3. Змініть назви вікон у `config.json` на актуальні для вашої локалізації.

## Запуск як сервіс Windows (через NSSM)

У папці `tools/` є скрипт `service_install.ps1` з інструкцією установки агента як Windows-сервісу за допомогою [NSSM](https://nssm.cc/). Ознайомтеся з коментарями у файлі й відредагуйте шляхи під своє середовище.

## Логування

Логи сервісу зберігаються у `logs/ebpro_mcp.log` та дублюються у консоль. У разі помилок у відповіді повертається дружня підказка з рекомендаціями, що змінити в налаштуваннях.

## Поради

- Запускайте EBPro під тим самим користувачем, що й агент.
- Якщо система працює у середовищі з UAC, надайте прав адміністратора для автоматизації.
- Для точніших взаємодій налаштовуйте селектори `pywinauto` під свою версію програми.
