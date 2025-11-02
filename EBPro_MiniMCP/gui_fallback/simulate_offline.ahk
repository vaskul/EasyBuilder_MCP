; Скрипт AutoHotkey для запуску офлайн-симуляції EBPro
; Налаштуйте гарячі клавіші під свою версію інтерфейсу.
; Приклад: Alt+T, потім O (Tools -> Offline Simulation)

#NoEnv
SendMode Input
SetTitleMatchMode, 2  ; частковий збіг заголовку

IfWinExist, EasyBuilder Pro
{
    WinActivate
    Sleep, 500
    ; Відкриваємо меню Tools через Alt+T
    Send, !t
    Sleep, 300
    ; Запускаємо Offline Simulation (O)
    Send, o
}
else
{
    MsgBox, 48, EBPro Mini-MCP, Не знайдено вікно EasyBuilder Pro. Перевірте назву вікна у config.json.
}
