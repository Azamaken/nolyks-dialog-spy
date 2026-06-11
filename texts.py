from html import escape
from os import getenv
from typing import Optional

from emoji import BACK_EMOJI, CATEGORY_EMOJI, CHANGE_EMOJI, CHANNEL_EMOJI, CLICK_EMOJI, COLOR_EMOJI, COMAND_EMOJI, CROSS_EMOJI, DOCUMENT_EMOJI, ERROR_EMOJI, GIF_EMOJI, GOLOS_EMOJI, ID_EMOJI, INFO_EMOJI, PEN_EMOJI, PHOTO_EMOJI, PLUS_EMOJI, PROFILE_EMOJI, QUESTION_EMOJI, RENAME_EMOJI, ROUND_EMOJI, SECRET_EMOJI, STICK_EMOJI, STATISTICS_EMOJI, TICK_EMOJI, TIME_EMOJI, TRASH_EMOJI, USER_EMOJI, VIDEO_EMOJI

BOT_USERNAME = getenv("BOT_USERNAME") or "@"
SUPPORT = getenv("SUPPORT") or "https://t.me/nolyktg"

BUTTON_LABELS = {
    "guide": " Как подключить",
    "help": " Команды",
    "features": " Возможности",
    "check_business": " Проверить подключение",
    "copy_username": " Скопировать юз",
    "back": " Назад",
    "admin_stats": f" Статистика",
    "admin_logs": f" Логи",
    "admin_accounts": f" Аккаунты",
    "admin_deleted": f" Удалённые",
    "admin_search": f"{QUESTION_EMOJI} Поиск",
    "admin_cleanup": f" Очистка",
    "admin_export": f" Экспорт",
    "admin_orphaned": f" Брошенные",
    "admin_errors": f" Ошибки",
    "admin_broadcast": f" Рассылка",
    "admin_manage": f" Управление",
    "back_to_admin": "Назад",
    "check_sub": f"{TICK_EMOJI} Проверить",
    "subscribe": f"{CHANNEL_EMOJI} Подписаться", 
}

START_TEXT = (
    f"<b><tg-emoji emoji-id='6077657514462158077'>🛡️</tg-emoji> @nolyk s-dialog-spy - <i>Ваш архив удалённых сообщений.</i></b>\n\n"
    f"<b>Автоматически сохраняет удалённые сообщения, фото, видео и другие файлы.</b>\n\n"
    f"{COMAND_EMOJI} <b>Выберите интересующий раздел ниже.</b>\n"
    f"{INFO_EMOJI} <i>Для быстрого старта откройте раздел «Как подключить».</i>"
)


SUBSCRIBE_PROMPT_TEXT = "❌ <b>Подпишитесь на канал, чтобы использовать бота</b>"
NOT_CONNECTED_BUSINESS_TEXT = "❌ Вы не подключили Business аккаунт."
NOT_SUBSCRIBED_ALERT = "❌ Вы не подписаны"
SUBSCRIPTION_CONFIRMED_TEXT = "✅ Подписка подтверждена"
SUBSCRIPTION_CONFIRMED_EDIT_TEXT = (
    "<tg-emoji emoji-id='5980930633298350051'>✅</tg-emoji> <b>Подписка подтверждена.</b>\n\n"
    "<i>Главное меню отправлено ниже.</i>"
)

BUSINESS_CONNECTED_TEXT = (
    "☑️ Business аккаунт успешно подключен!\n\n"
    "Права проверены:\n"
    "• Сохранение медиа\n"
    "• Уведомления об удалении\n"
    "• Уведомления об изменении"
)

BUSINESS_CONNECT_UNAVAILABLE_TEXT = (
    "<tg-emoji emoji-id='5260342697075416641'>❌</tg-emoji> "
    "<b><i>Бот отключён от аккаунта</i></b>\n\n"
    f"<blockquote><b>└ Если у вас возникли вопросы напишите тех.поддержке: <a href='{SUPPORT}'>Поддержка</a></b></blockquote>"
)

BUSINESS_CONNECTED_NOTIFICATION_TEXT = (
    "<tg-emoji emoji-id='5776375003280838798'>✅</tg-emoji> "
    "<b><i>Вы успешно подключили бота</i></b>\n\n"
    "<blockquote><b>└ Чтобы продолжить пропишите /start</b></blockquote>"
)

BUSINESS_DISCONNECTED_NOTIFICATION_TEXT = (
    "<tg-emoji emoji-id='5260342697075416641'>❌</tg-emoji> "
    "<b><i>Бот отключён от аккаунта</i></b>\n\n"
    f"<blockquote><b>└ Если у вас возникли вопросы напишите тех.поддержке: <a href='{SUPPORT}'>Поддержка</a></b></blockquote>"
)


GUIDE_TEXT = (
    f"<b>{QUESTION_EMOJI} Как подключить</b>\n\n"
    "<i>Выберите нужный вам раздел,</i>"
)

FEATURES_TEXT = (
    f"<b>{PEN_EMOJI} Все возможности</b>\n\n"
    f"• {TICK_EMOJI} <b>Фото, видео, сообщения и голосовые</b> сохраняются автоматически\n"
    f"• {TICK_EMOJI} <b>Одноразовые фото видео и тд,</b> сохрняются командой \n"
    f"• {TICK_EMOJI} <b>Лог редактирования текста</b> с новой и старой версией\n"
    f"• {TICK_EMOJI} <b>Уведомления об удалении</b> с краткой информацией\n"
)

BACK_TO_MENU_TEXT = START_TEXT
MESSAGE_NOT_FOUND_TEXT = "❌ Сообщение не найдено"
MEDIA_NOT_FOUND_TEXT = "❌ Медиа не найдено"
MEDIA_SENT_CONFIRMATION_TEXT = "✅ Медиа отправлено"

ADMIN_PANEL_TEXT = f"<b>{CATEGORY_EMOJI} Админ панель</b>\n\n<i>Выберите раздел:</i>"
ADMIN_STATS_HEADER = f"<b>{STATISTICS_EMOJI} Статистика</b>\n\n"
ADMIN_LOGS_HEADER = f"<b>{PEN_EMOJI} Последние 10 логов:</b>\n\n"

WARNING_SUBSCRIPTION_CHECK_TEXT = "Ошибка при проверке подписки: "
WARNING_CONNECTION_CHECK_TEXT = "❌ Ошибка при проверке подключения: "
UNKNOWN_ERROR_TEXT = "Неизвестная ошибка"

VOICE_MESSAGE_CONTENT = f"Голосовое сообщение"
STICKER_CONTENT = f"Стикер"
VIDEO_NOTE_CONTENT = f"Кружок"
DOCUMENT_CONTENT = f"Документ"
AUDIO_CONTENT = f"Аудиофайл"
ANIMATION_CONTENT = f"GIF"
UNKNOWN_USER_DISPLAY = "Неизвестно"

SPOILER_TEXT = " [Спойлер]"
ONE_TIME_VIEW_TEXT = " [Одноразовый просмотр]"
ONE_TIME_TEXT = " [Одноразовый]"

ADMIN_STATS_MESSAGES_TEMPLATE = f"{USER_EMOJI} <b>В общем:</b> {{count}}\n"
ADMIN_STATS_FILES_TEMPLATE = f"{DOCUMENT_EMOJI} <b>Все файлы:</b> {{count}}\n"
ADMIN_STATS_USERS_TEMPLATE = f"{PROFILE_EMOJI} <b>Пользователей:</b> {{count}}\n"
ADMIN_STATS_BUSINESS_CONNECTED_TEMPLATE = f"{TICK_EMOJI} <b>Подключенных:</b> {{count}}\n"
ADMIN_STATS_BUSINESS_DISCONNECTED_TEMPLATE = f"{CROSS_EMOJI} <b>Не подключенных:</b> {{count}}\n"
ADMIN_STATS_TYPES_HEADER = "\n<b>Типы сообщений:</b>\n"
ADMIN_STATS_TEXT_TEMPLATE = f"{PEN_EMOJI} <b>Текстов:</b> {{count}}\n"
ADMIN_STATS_PHOTO_TEMPLATE = f"{PHOTO_EMOJI} <b>Фото:</b> {{count}}\n"
ADMIN_STATS_VIDEO_TEMPLATE = f"{VIDEO_EMOJI} <b>Видео:</b> {{count}}\n"
ADMIN_STATS_ROUND_TEMPLATE = f"{ROUND_EMOJI} <b>Кружков:</b> {{count}}\n"
ADMIN_STATS_VOICE_TEMPLATE = f"{GOLOS_EMOJI} <b>Голосовых:</b> {{count}}\n"
ADMIN_STATS_AUDIO_TEMPLATE = f"{COLOR_EMOJI} <b>Аудио:</b> {{count}}\n"
ADMIN_STATS_STICKER_TEMPLATE = f"{STICK_EMOJI} <b>Стикеров:</b> {{count}}\n"
ADMIN_STATS_DOCUMENT_TEMPLATE = f"{DOCUMENT_EMOJI} <b>Документов:</b> {{count}}\n"
ADMIN_STATS_ANIMATION_TEMPLATE = f"{GIF_EMOJI} <b>GIF:</b> {{count}}"

ALBUM_PHOTO_LABEL = "Альбом фото"
TEXT_LABEL = "Текст"
PHOTO_LABEL = "Фото"
VIDEO_LABEL = "Видео"
VOICE_LABEL = "Голос"
AUDIO_LABEL = "Аудио"
STICKER_LABEL = "Стикер"
VIDEO_NOTE_LABEL = "Кружок"
ANIMATION_LABEL = "GIF"
DOCUMENT_LABEL = "Документ"

LOG_MESSAGE_NOT_FOUND = "Нет текста"


TYPE_LABELS = {
    "text": TEXT_LABEL,
    "photos": PHOTO_LABEL,
    "photo": PHOTO_LABEL,
    "video": VIDEO_LABEL,
    "voice": VOICE_LABEL,
    "audio": AUDIO_LABEL,
    "sticker": STICKER_LABEL,
    "video_note": VIDEO_NOTE_LABEL,
    "animation": ANIMATION_LABEL,
    "document": DOCUMENT_LABEL,
}


def format_admin_log_entry(log, index):
    author = log.from_username or log.first_name or "unknown"
    display_name = f"@{author}" if log.from_username else author
    content = escape(log.content or TYPE_LABELS.get(log.type, log.type.capitalize()))
    msg_type = TYPE_LABELS.get(log.type, log.type.capitalize())
    return (
        f"{index}{USER_EMOJI} <b>{display_name}</b> · <code>{log.user_id}</code>\n"
        f"• <b>{DOCUMENT_EMOJI} Сообщение:</b> <i>{content}</i>\n"
        f"• <b>{CATEGORY_EMOJI} Тип:</b> <i>{msg_type}</i>\n"
        f"• <b>{TIME_EMOJI} Время:</b> <code>{log.created_at}</code>\n\n"
    )


def build_delete_log(msg, msg_type):
    content = escape(msg.content or LOG_MESSAGE_NOT_FOUND)

    return (
        f"– [{PEN_EMOJI}] <b>{msg.first_name or 'unknown'} (@{msg.from_username or 'unknown'}) удалил сообщение которое было получено в {msg.created_at}:</b>\n\n"
        f"• <b>{TRASH_EMOJI} Сообщение:</b>\n<blockquote><b>{content}</b></blockquote>\n\n"
        f" <b>{USER_EMOJI} Username: @{msg.from_username or 'unknown'}</b>\n"
        f"• <b>{ID_EMOJI} ID пользователя:</b> <code>{msg.user_id}</code>\n"
        f"• <b>{TIME_EMOJI} Время изменения:</b> <code>{msg.created_at}</code>\n\n"
        f"{INFO_EMOJI} <b>{BOT_USERNAME}</b>"
    )

def build_edit_log(msg, old_content, new_content):
    old_text = escape(old_content or LOG_MESSAGE_NOT_FOUND)
    new_text = escape(new_content or LOG_MESSAGE_NOT_FOUND)

    return (
        f"– [{PEN_EMOJI}] <b>{msg.first_name or 'unknown'} (@{msg.from_username or 'unknown'}) изменил сообщение которое было получено в {msg.created_at}:</b>\n\n"
        f"• <b>{RENAME_EMOJI} Было:</b>\n<blockquote><b>{old_text}</b></blockquote>\n\n"
        f"• <b>{CHANGE_EMOJI} Стало:</b>\n<blockquote><b>{new_text}</b></blockquote>\n\n"
        f"• <b>{USER_EMOJI} Username: @{msg.from_username or 'unknown'}</b>\n"
        f"• <b>{ID_EMOJI} ID пользователя:</b> <code>{msg.user_id}</code>\n"
        f"• <b>{TIME_EMOJI} Время изменения:</b> <code>{msg.created_at}</code>\n\n"
        f"{INFO_EMOJI} <b>{BOT_USERNAME}</b>"
    )

def build_delete_photo(msg, msg_type):
    return (
        f"– [{PEN_EMOJI}] <b>{msg.first_name or 'unknown'} (@{msg.from_username or 'unknown'}) удалил фото которое было получено в {msg.created_at}:</b>\n\n"
        f"• <b>{USER_EMOJI} Username: @{msg.from_username or 'unknown'}</b>\n"
        f"• <b>{ID_EMOJI} ID пользователя:</b> <code>{msg.user_id}</code>\n"
        f"• <b>{TIME_EMOJI} Время изменения:</b> <code>{msg.created_at}</code>\n\n"
        f"{INFO_EMOJI} <b>{BOT_USERNAME}</b>"
    )

def build_delete_voice(msg, msg_type):
    return (
        f"– [{PEN_EMOJI}] <b>{msg.first_name or 'unknown'} (@{msg.from_username or 'unknown'}) удалил голосовое сообщение которое было получено в {msg.created_at}:</b>\n\n"
        f"• <b>{USER_EMOJI} Username: @{msg.from_username or 'unknown'}</b>\n"
        f"• <b>{ID_EMOJI} ID пользователя:</b> <code>{msg.user_id}</code>\n"
        f"• <b>{TIME_EMOJI} Время изменения:</b> <code>{msg.created_at}</code>\n\n"
        f"{INFO_EMOJI} <b>{BOT_USERNAME}</b>"
    )

def build_delete_audio(msg, msg_type):
    return (
        f"– [{PEN_EMOJI}] <b>{msg.first_name or 'unknown'} (@{msg.from_username or 'unknown'}) удалил аудио сообщение которое было получено в {msg.created_at}:</b>\n\n"
        f"• <b>{USER_EMOJI} Username: @{msg.from_username or 'unknown'}</b>\n"
        f"• <b>{ID_EMOJI} ID пользователя:</b> <code>{msg.user_id}</code>\n"
        f"• <b>{TIME_EMOJI} Время изменения:</b> <code>{msg.created_at}</code>\n\n"
        f"{INFO_EMOJI} <b>{BOT_USERNAME}</b>"
    )

def build_delete_animation(msg, msg_type):
    return (
        f"– [{PEN_EMOJI}] <b>{msg.first_name or 'unknown'} (@{msg.from_username or 'unknown'}) удалил гиф которая была получена в {msg.created_at}:</b>\n\n"
        f"• <b>{USER_EMOJI} Username: @{msg.from_username or 'unknown'}</b>\n"
        f"• <b>{ID_EMOJI} ID пользователя:</b> <code>{msg.user_id}</code>\n"
        f"• <b>{TIME_EMOJI} Время изменения:</b> <code>{msg.created_at}</code>\n\n"
        f"{INFO_EMOJI} <b>{BOT_USERNAME}</b>"
    )

def build_delete_sticker(msg, msg_type):
    return (
        f"– [{PEN_EMOJI}] <b>{msg.first_name or 'unknown'} (@{msg.from_username or 'unknown'}) удалил стикер который был получен в {msg.created_at}:</b>\n\n"
        f"• <b>{USER_EMOJI} Username: @{msg.from_username or 'unknown'}</b>\n"
        f"• <b>{ID_EMOJI} ID пользователя:</b> <code>{msg.user_id}</code>\n"
        f"• <b>{TIME_EMOJI} Время изменения:</b> <code>{msg.created_at}</code>\n\n"
        f"{INFO_EMOJI} <b>{BOT_USERNAME}</b>"
    )

def build_delete_round(msg, msg_type):
    return (
        f"– [{PEN_EMOJI}] <b>{msg.first_name or 'unknown'} (@{msg.from_username or 'unknown'}) удалил кружок которое было получено в {msg.created_at}:</b>\n\n"
        f"• <b>{USER_EMOJI} Username: @{msg.from_username or 'unknown'}</b>\n"
        f"• <b>{ID_EMOJI} ID пользователя:</b> <code>{msg.user_id}</code>\n"
        f"• <b>{TIME_EMOJI} Время изменения:</b> <code>{msg.created_at}</code>\n\n"
        f"{INFO_EMOJI} <b>{BOT_USERNAME}</b>"
    )

def build_delete_document(msg, msg_type):
    return (
        f"– [{PEN_EMOJI}] <b>{msg.first_name or 'unknown'} (@{msg.from_username or 'unknown'}) удалил документ который был получен в {msg.created_at}:</b>\n\n"
        f"• <b>{USER_EMOJI} Username: @{msg.from_username or 'unknown'}</b>\n"
        f"• <b>{ID_EMOJI} ID пользователя:</b> <code>{msg.user_id}</code>\n"
        f"• <b>{TIME_EMOJI} Время изменения:</b> <code>{msg.created_at}</code>\n\n"
        f"{INFO_EMOJI} <b>{BOT_USERNAME}</b>"
    )

ADMIN_DELETED_HEADER = f"<b>{TRASH_EMOJI} Статистика удалённых сообщений</b>\n\n"
ADMIN_DELETED_TEMPLATE = (
    f"{STATISTICS_EMOJI} <b>Всего удалено:</b> {{total}}\n"
    f"{TIME_EMOJI} <b>На этой неделе:</b> {{week}}\n"
    f"{TIME_EMOJI} <b>На этом месяце:</b> {{month}}"
)

ADMIN_ACCOUNTS_HEADER = f"<b>{PROFILE_EMOJI} Бизнес аккаунты</b>\n\n"
ADMIN_ACCOUNTS_EMPTY = "<i>Нет активных подключений</i>"
ADMIN_ACCOUNTS_CONNECTED = f"{TICK_EMOJI} Активен: {{count}}"
ADMIN_ACCOUNTS_DISCONNECTED = f"{CROSS_EMOJI} Отключен: {{count}}"

ADMIN_CLEANUP_PROMPT = (
    f"<b>{TRASH_EMOJI} Очистка архива</b>\n\n"
    "<i>Удалить записи старше X дней.</i>\n\n"
    "<code>Введите количество дней:</code>\n"
    "(например: <b>30</b> - удалит записи старше 30 дней)"
)
ADMIN_CLEANUP_CONFIRM = (
    f"<b>{ERROR_EMOJI} Подтверждение удаления</b>\n\n"
    "Будет удалено: <b>{count}</b> записей\n"
    "Старше: <b>{days}</b> дней\n\n"
    "Это действие нельзя отменить!"
)
ADMIN_CLEANUP_SUCCESS = f"{TICK_EMOJI} Удалено <b>{{count}}</b> записей"

ADMIN_EXPORT_PROMPT = (
    f"<b>{DOCUMENT_EMOJI} Экспорт архива</b>\n\n"
    "Выберите формат:\n"
    "(нажмите кнопку ниже)"
)
ADMIN_EXPORT_SUCCESS = f"{TICK_EMOJI} Экспорт готов!\n\nФайл сейчас отправляется..."
ADMIN_EXPORT_INVALID = f"{CROSS_EMOJI} Неверный формат"

ADMIN_ORPHANED_HEADER = f"<b>{DOCUMENT_EMOJI} Брошенные файлы</b>\n\n"
ADMIN_ORPHANED_TEXT = (
    f"{DOCUMENT_EMOJI} <b>Всего в папке:</b> {{total}}\n"
    f"{CLICK_EMOJI} <b>Привязано к БД:</b> {{linked}}\n"
    f"{SECRET_EMOJI} <b>Брошено (не привязано):</b> {{orphaned}}\n\n"
    "<i>Нажмите удалить брошенные файлы</i>"
)
ADMIN_ORPHANED_DELETED = f"{TICK_EMOJI} Удалено <b>{{count}}</b> файлов"

ADMIN_ERRORS_HEADER = f"<b>{ERROR_EMOJI} Последние ошибки</b>\n\n"
ADMIN_ERRORS_EMPTY = "<i>Ошибок не найдено</i>"

ADMIN_BROADCAST_PROMPT = (
    f"<b>{CHANNEL_EMOJI} Рассылка сообщений</b>\n\n"
    "<i>Настройка рассылки за пару кликов.</i>\n\n"
    "• <b>Текст</b> рассылки\n"
    "• <b>Фото</b> для отправки\n"
    "• <b>Кнопка</b> с ссылкой\n\n"
    "<b>Выберите действие ниже</b>"
)
ADMIN_BROADCAST_TEXT_PROMPT = (
    f"<b>{PEN_EMOJI} Введите текст рассылки</b>\n\n"
    "<i>HTML-разметка, эмодзи и жирный текст поддерживаются.</i>\n"
    "<code>Отправьте ваш текст:</code>"
)
ADMIN_BROADCAST_PHOTO_PROMPT = (
    f"<b>{PHOTO_EMOJI} Прикрепите фото</b>\n\n"
    "<i>Загрузите изображение для рассылки или нажмите «Без фото».</i>"
)
ADMIN_BROADCAST_BUTTON_TEXT_PROMPT = (
    f"<b>{PLUS_EMOJI} Текст кнопки</b>\n\n"
    "<i>Например: Перейти на канал</i>"
)
ADMIN_BROADCAST_BUTTON_URL_PROMPT = (
    f"<b>{INFO_EMOJI} Укажите ссылку для кнопки</b>\n\n"
    "<i>Ссылка должна начинаться с https://</i>\n"
    "<code>Пример: https://example.com</code>"
)
ADMIN_BROADCAST_BUTTON_STYLE_PROMPT = (
    f"<b>{CHANGE_EMOJI} Выберите стиль кнопки</b>\n\n"
    "<i>Цвет влияет на кликабельность.</i>"
)
ADMIN_BROADCAST_PREVIEW = f"<b>{CHANNEL_EMOJI} Текущая рассылка</b>\n\n{{preview}}"
ADMIN_BROADCAST_SUCCESS = f"{TICK_EMOJI} Рассылка отправлена <b>{{count}}</b> пользователям"
ADMIN_BROADCAST_FAILED = f"{CROSS_EMOJI} Ошибка при рассылке"

ADMIN_MANAGE_PROMPT = (
    f"<b>{CATEGORY_EMOJI} Управление администраторами</b>\n\n"
    "<i>Выберите действие:</i>"
)
ADMIN_MANAGE_ADD_PROMPT = "<code>Введите ID пользователя:</code>"
ADMIN_MANAGE_SUCCESS = f"{TICK_EMOJI} Администратор добавлен"
ADMIN_MANAGE_REMOVE = f"{TICK_EMOJI} Администратор удалён"
ADMIN_MANAGE_ERROR = f"{CROSS_EMOJI} Ошибка при управлении"

BUTTON_STYLE_DEFAULT = "default"
BUTTON_STYLE_PRIMARY = "primary"
BUTTON_STYLE_SUCCESS = "success"
BUTTON_STYLE_DANGER = "danger"


def format_deleted_stats(total, week, month, by_type_dict):
    by_type_str = ""
    for msg_type, count in by_type_dict.items():
        by_type_str += f"  • {msg_type}: {count}\n"
    
    return ADMIN_DELETED_TEMPLATE.format(
        total=total,
        week=week,
        month=month,
        by_type=by_type_str or "  (нет данных)"
    )


def format_broadcast_message(text, has_photo=False):
    preview = f"<b>{CHANNEL_EMOJI} Предпросмотр рассылки</b>\n\n{text}"
    if has_photo:
        preview += f"\n\n{PHOTO_EMOJI} <i>С фотографией</i>"
    return preview
