Установка и запуск

Кратко

Проект: Telegram-бот для архивации/просмотра сообщений.

Требования

- Python 3.10+
- pip

Быстрая установка (Windows PowerShell)

1) Создать виртуальное окружение и активировать:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Установить зависимости:

```powershell
pip install -r requirements.txt
```
3) Создать файл конфигурации `.env` из шаблона:
```
Отредактируйте `.env` и заполните минимум:
- BOT_TOKEN — токен бота
- CHANNEL_ID — id канала (целое число)
- BOT_USERNAME — имя бота (без @)
- ADMIN_IDS — список id админов через запятую
- IOS_LINK / ANDROID_LINK — ссылки для кнопок в гиде (опционально)
- PHOTO_URL (опционально)
- CHANNEL_USERNAME (опционально)

Файл `.env.sample` присутствует в репозитории.

4) Запустить бота:

```powershell
python main.py
```

Альтернативный способ (если не активировали venv):

```powershell
.\.venv\Scripts\python.exe main.py
```

Linux / macOS (bash):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.sample .env
python main.py
```

Остановка/выход из окружения:

```powershell
deactivate
```

Удаление окружения (Windows PowerShell):

```powershell
Remove-Item -Recurse -Force .venv
```

Поддержка и баги

При покупке/установке проекта я включаю исправление багов, связанных с установкой и запуском (фикса под окружение покупателя). Если возникнут проблемы — пишите лично: @nolyktg (Telegram).
