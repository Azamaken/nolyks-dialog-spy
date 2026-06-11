import asyncio
import logging
import sys
import json
import csv
import os
import time
from os import getenv
from pathlib import Path
from hashlib import sha1
from urllib.parse import quote_plus, unquote_plus
from uuid import uuid4
from datetime import datetime, timedelta
from html import escape
import base64
from typing import Any, Dict, Optional

import aiohttp
from dotenv import load_dotenv

from aiogram import BaseMiddleware, Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,  
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile,
    InputMediaPhoto,
    LabeledPrice,
    PreCheckoutQuery,
    BusinessMessagesDeleted,
    BusinessConnection,
    CopyTextButton
)

from commands import other_commands, load_custom_commands, save_custom_commands, build_help_keyboard, get_help_caption
from emoji import AUDIO_EMOJI, CATEGORY_EMOJI, CATEGORY_EMOJI_ID, CLICK_EMOJI, COLOR_EMOJI, COMAND_EMOJI, COMAND_EMOJI_ID, CROSS_EMOJI, CRYPTOBOT_EMOJI, CRYPTOBOT_EMOJI_ID, DOCUMENT_EMOJI, DOCUMENT_EMOJI, GIF_EMOJI, GEM_EMOJI, GEM_EMOJI_ID, GOLOS_EMOJI, ID_EMOJI, INFO_EMOJI, PEN_EMOJI, PHOTO_EMOJI, PHOTO_EMOJI_ID, PLUS_EMOJI, RENAME_EMOJI_ID, SEND_EMOJI, STARS_EMOJI, STARS_EMOJI_ID, STATISTICS_EMOJI, TICK_EMOJI, TIME_EMOJI, TRASH_EMOJI, BACK_EMOJI_ID, PLUS_EMOJI_ID, TRASH_EMOJI_ID, RENAME_EMOJI, PROFILE_EMOJI, PROFILE_EMOJI_ID, USER_EMOJI, USER_EMOJI_ID, VIDEO_EMOJI

from business_store import (
    is_connected as biz_is_connected,
    load_connections,
    get_connection_id,
    add_connection as add_business_connection,
    remove_connection as remove_business_connection,
)
from texts import (
    ADMIN_LOGS_HEADER,
    ADMIN_PANEL_TEXT,
    ADMIN_STATS_HEADER,
    ADMIN_STATS_USERS_TEMPLATE,
    ADMIN_STATS_BUSINESS_CONNECTED_TEMPLATE,
    ADMIN_STATS_BUSINESS_DISCONNECTED_TEMPLATE,
    ADMIN_STATS_TYPES_HEADER,
    ADMIN_STATS_TEXT_TEMPLATE,
    ADMIN_STATS_PHOTO_TEMPLATE,
    ADMIN_STATS_VIDEO_TEMPLATE,
    ADMIN_STATS_ROUND_TEMPLATE,
    ADMIN_STATS_VOICE_TEMPLATE,
    ADMIN_STATS_AUDIO_TEMPLATE,
    ADMIN_STATS_STICKER_TEMPLATE,
    ADMIN_STATS_DOCUMENT_TEMPLATE,
    ADMIN_STATS_ANIMATION_TEMPLATE,
    ADMIN_ACCOUNTS_HEADER,
    ADMIN_ACCOUNTS_EMPTY,
    ADMIN_DELETED_HEADER,
    ADMIN_ERRORS_HEADER,
    ADMIN_ERRORS_EMPTY,
    ADMIN_BROADCAST_PROMPT,
    ADMIN_BROADCAST_TEXT_PROMPT,
    ADMIN_BROADCAST_PHOTO_PROMPT,
    ADMIN_BROADCAST_BUTTON_URL_PROMPT,
    ADMIN_BROADCAST_BUTTON_STYLE_PROMPT,
    ADMIN_BROADCAST_BUTTON_TEXT_PROMPT,
    ADMIN_BROADCAST_PREVIEW,
    ADMIN_BROADCAST_SUCCESS,
    ADMIN_MANAGE_PROMPT,
    ADMIN_MANAGE_ADD_PROMPT,
    ADMIN_MANAGE_SUCCESS,
    ADMIN_MANAGE_REMOVE,
    BACK_TO_MENU_TEXT,
    BUTTON_LABELS,
    BUSINESS_CONNECTED_NOTIFICATION_TEXT,
    BUSINESS_CONNECTED_TEXT,
    BUSINESS_DISCONNECTED_NOTIFICATION_TEXT,
    BUSINESS_CONNECT_UNAVAILABLE_TEXT,
    FEATURES_TEXT,
    GUIDE_TEXT,
    MEDIA_NOT_FOUND_TEXT,
    MEDIA_SENT_CONFIRMATION_TEXT,
    MESSAGE_NOT_FOUND_TEXT,
    NOT_CONNECTED_BUSINESS_TEXT,
    NOT_SUBSCRIBED_ALERT,
    START_TEXT,
    SUBSCRIBE_PROMPT_TEXT,
    SUBSCRIPTION_CONFIRMED_EDIT_TEXT,
    SUBSCRIPTION_CONFIRMED_TEXT,
    UNKNOWN_ERROR_TEXT,
    WARNING_CONNECTION_CHECK_TEXT,
    WARNING_SUBSCRIPTION_CHECK_TEXT,
    VOICE_MESSAGE_CONTENT,
    STICKER_CONTENT,
    VIDEO_NOTE_CONTENT,
    DOCUMENT_CONTENT,
    AUDIO_CONTENT,
    ANIMATION_CONTENT,
    UNKNOWN_USER_DISPLAY,
    SPOILER_TEXT,
    ONE_TIME_VIEW_TEXT,
    ONE_TIME_TEXT,
    ADMIN_STATS_MESSAGES_TEMPLATE,
    ADMIN_STATS_FILES_TEMPLATE,
    ALBUM_PHOTO_LABEL,
    TEXT_LABEL,
    PHOTO_LABEL,
    VIDEO_LABEL,
    VOICE_LABEL,
    AUDIO_LABEL,
    STICKER_LABEL,
    VIDEO_NOTE_LABEL,
    ANIMATION_LABEL,
    DOCUMENT_LABEL,
    TYPE_LABELS,
    build_delete_animation,
    build_delete_audio,
    build_delete_document,
    build_delete_log,
    build_delete_photo,
    build_delete_round,
    build_delete_sticker,
    build_delete_voice,
    build_edit_log,
    format_admin_log_entry,
    format_deleted_stats,
    LOG_MESSAGE_NOT_FOUND,
)

from sqlalchemy import Column, String, text
from sqlmodel import SQLModel, Field, create_engine, Session, select
from typing import Optional

load_dotenv(dotenv_path=Path(__file__).with_name(".env"), encoding="utf-8-sig")


TOKEN = getenv("BOT_TOKEN")
CHANNEL_ID = int(getenv("CHANNEL_ID"))
BOT_USERNAME = getenv("BOT_USERNAME")
PHOTO_URL = getenv("PHOTO_URL")
ADMIN_URL = getenv("ADMIN_URL")
ADMIN_IDS = [int(x) for x in getenv("ADMIN_IDS", "").split(",") if x]
CRYPTOBOT_TOKEN = (getenv("CRYPTOBOT_TOKEN") or "").strip().strip('"').strip("'") or None
CRYPTOBOT_NETWORK = (getenv("CRYPTOBOT_NETWORK") or "mainnet").strip().lower()
FREE_DAILY_COMMAND_LIMIT = int(getenv("FREE_DAILY_COMMAND_LIMIT", "5"))
FREE_DAILY_SAVE_LIMIT = int(getenv("FREE_DAILY_SAVE_LIMIT", "30"))

CHANNEL_USERNAME = getenv("CHANNEL_USERNAME")
if CHANNEL_USERNAME:
    CHANNEL_URL = f"https://t.me/{CHANNEL_USERNAME}"
else:
    CHANNEL_URL = f"https://t.me/c/{str(CHANNEL_ID)[4:]}/"

DELETED_HTML_MAP: Dict[str, str] = {}

# Platform-specific links (fallback to channel url)
IOS_LINK = getenv("IOS_LINK") or CHANNEL_URL
ANDROID_LINK = getenv("ANDROID_LINK") or CHANNEL_URL


def _ensure_dir(path: str):
    Path(path).mkdir(parents=True, exist_ok=True)


async def _download_user_avatar(bot: Bot, user_id: int) -> Optional[Path]:
    try:
        photos = await bot.get_user_profile_photos(
            user_id=user_id,
            limit=1
        )
        if not photos.total_count:
            return None
        best_photo = photos.photos[0][-1]
        file = await bot.get_file(best_photo.file_id)
        avatar_dir = MEDIA_PATH / "avatars"
        _ensure_dir(avatar_dir)
        avatar_path = avatar_dir / f"{user_id}.jpg"
        await bot.download_file(
            file.file_path,
            destination=avatar_path
        )
        return avatar_path
    except Exception as e:
        print(f"Avatar error {user_id}: {e}")
        return None

async def generate_deleted_html(session: Session, bot: Bot, messages: list, out_dir: str) -> str:
    _ensure_dir(out_dir)
    page_id = uuid4().hex
    filename = f"deleted_log_{page_id}.html"
    out_path = os.path.join(out_dir, filename)

    bot_link = f"tg://resolve?domain={BOT_USERNAME}" if BOT_USERNAME else "https://t.me/" + (BOT_USERNAME or "")
    css = """
@import url('https://fonts.googleapis.com/css2?family=Archivo+Black&display=swap');
:root{
    --bg:#000;
    --surface:#0f0f0f;
    --surface-2:#151515;
    --border:#262626;
    --text:#ffffff;
    --muted:#8d8d8d;
}
*{
    box-sizing:border-box;
}
html{
    scroll-behavior:smooth;
}
body{
    margin:0;
    background:var(--bg);
    color:var(--text);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
}
.container{
    max-width:760px;
    margin:auto;
    padding:28px 18px 80px;
}
.header{
    position:relative;
    display:flex;
    justify-content:space-between;
    align-items:center;
    padding:22px 24px;
    margin-bottom:20px;
    border-radius:28px;
    backdrop-filter:blur(30px);
    -webkit-backdrop-filter:blur(30px);
    background:rgba(15,15,15,.7);
    border:1px solid rgba(255,255,255,.08);
    box-shadow:
        0 15px 40px rgba(0,0,0,.35);
}
.brand{
    display:flex;
    align-items:center;
    gap:14px;
}
.badge{
    margin-left:6px;
    font-size:11px;
    color:#888;
    background:#111;
    border:1px solid #222;
    padding:3px 8px;
    border-radius:999px;
}
.logo{
    width:46px;
    height:46px;
    border-radius:14px;
    background:#fff;
    color:#000;
    display:flex;
    align-items:center;
    justify-content:center;
    font-family:"Archivo Black",sans-serif;
    font-size:16px;
}
.brand-text{
    display:flex;
    flex-direction:column;
}
.brand-title{
    font-family:"Archivo Black",sans-serif;
    font-size:20px;
    color:#fff;
}
.brand-sub{
    font-size:13px;
    color:var(--muted);
}
.open-bot{
    color:#fff;
    text-decoration:none;
    border:1px solid var(--border);
    background:transparent;
    padding:10px 14px;
    border-radius:12px;
    transition:.2s ease;
}
.open-bot:hover{
    background:#fff;
    color:#000;
}  
.chat{
    display:flex;
    flex-direction:column;
    gap:22px;
}

.message{
    display:flex;
    align-items:flex-start;
    gap:14px;
}

.message-content{
    flex:1;
    min-width:0;
}

.message-top{
    display:flex;
    align-items:center;
    gap:10px;
    margin-bottom:6px;
}
.bubble-row{
    display:flex;
    align-items:center;
    gap:12px;
}
.avatar{
    width:52px;
    height:52px;
    min-width:52px;
    min-height:52px;
    border-radius:50%;
    overflow:hidden;
    display:flex;
    align-items:center;
    justify-content:center;
    flex-shrink:0;
    background:#111;
    border:1px solid #222;
}

.avatar img{
    width:100%;
    height:100%;
    display:block;
    object-fit:cover;
    object-position:center;
}
.card{
    flex:1;
    max-width:none;
    background:#0f0f0f;
    border:1px solid #1d1d1d;
    border-radius:22px;
    padding:16px 18px;
    transition:.2s ease;
}

.card:hover{
    transform:translateY(-2px);
    border-color:#323232;
    box-shadow:
        0 10px 30px rgba(0,0,0,.3);
}
.name-row{
    display:flex;
    justify-content:space-between;
    align-items:center;
    gap:12px;
    margin-bottom:8px;
}
.name{
    color:#fff;
    font-weight:700;
    text-decoration:none;
}
.name:hover{
    opacity:.8;
}
.time{
    color:#666;
    font-size:12px;
}

.message-text{
    color:#f5f5f5;
    font-size:15px;
    line-height:1.65;
    word-break:break-word;
}
.meta{
    color:var(--muted);
    font-size:12px;
    white-space:nowrap;
}
.text{
    color:#fff;
    font-size:15px;
    line-height:1.65;
    white-space:pre-wrap;
    word-break:break-word;
}
.badge{
    display:inline-flex;
    align-items:center;
    margin-left:8px;
    padding:4px 10px;
    border-radius:999px;
    background:#181818;
    border:1px solid #2a2a2a;
    color:#bdbdbd;
    font-size:12px;
}
.preview{
    margin-top:10px;
    max-width:420px;
    border-radius:18px;
    overflow:hidden;
    border:1px solid #1d1d1d;
}
.preview img{
    display:block;
    width:100%;
}
.stats-card{
    margin-bottom:20px;
    padding:24px;
    border-radius:24px;
    backdrop-filter:blur(30px);
    -webkit-backdrop-filter:blur(30px);
    background:rgba(15,15,15,.7);
    border:1px solid rgba(255,255,255,.08);
}
.stats-label{
    color:#777;
    font-size:13px;
    margin-bottom:8px;
}
.stats-value{
    font-family:"Archivo Black",sans-serif;
    font-size:52px;
    line-height:1;
    color:#fff;
}
.filters{
    display:flex;
    flex-wrap:wrap;
    gap:10px;
    margin-bottom:24px;
}
.filter-btn{
    background:#0f0f0f;
    color:#888;
    border:1px solid #222;
    border-radius:999px;
    padding:10px 16px;
    cursor:pointer;
    transition:.2s ease;
}
.filter-btn:hover{
    border-color:#444;
    color:#fff;
}
.filter-btn.active{
    background:#fff;
    color:#000;
    border-color:#fff;
}
.date-divider{
    display:flex;
    align-items:center;
    gap:12px;
    margin:28px 0 18px;
}
.date-divider::before,
.date-divider::after{
    content:"";
    flex:1;
    height:1px;
    background:#1f1f1f;
}
.date-divider span{
    color:#666;
    font-size:13px;
    letter-spacing:.4px;
}
.footer{
    margin-top:50px;
    padding:30px 20px;
    text-align:center;
    border-top:1px solid rgba(255,255,255,.06);
}
.footer-title{
    color:#999;
    font-size:14px;
    margin-bottom:6px;
}
.footer-time{
    color:#555;
    font-size:12px;
}
@media (max-width:700px){

    .container{
        padding:12px;
    }

    .header{
        flex-direction:column;
        align-items:flex-start;
        gap:12px;
        padding:14px 16px;
    }

    .logo{
        width:42px;
        height:42px;
        font-size:15px;
    }

    .brand-title{
        font-size:18px;
    }

    .brand-sub{
        font-size:12px;
    }

    .open-bot{
        padding:8px 12px;
        font-size:14px;
    }

    .filters{
        display:flex;
        flex-wrap:wrap;
        justify-content:center;
        gap:10px;
        width:100%;
        margin:18px 0 24px;
    }

    .filter-btn{
        min-width:90px;
    }

    .bubble-row{
        width:100%;
        align-items:flex-start;
        gap:10px;
    }

    .avatar{
        width:52px;
        height:52px;
        min-width:52px;
        margin-top:10px;
    }

    .card{
        flex:1;
        width:auto;
        max-width:none;
        padding:14px;
    }

    .name-row{
        flex-wrap:wrap;
        gap:8px;
    }

    .name{
        font-size:15px;
    }

    .meta{
        font-size:11px;
    }

    .text{
        font-size:14px;
        line-height:1.5;
    }

    .preview{
        max-width:100%;
    }

    .stats-card{
        padding:18px;
    }

    .stats-value{
        font-size:40px;
    }

    .footer{
        padding:24px 12px;
        text-align:center;
    }
}
.bg{
    position:fixed;
    inset:0;
    overflow:hidden;
    pointer-events:none;
    z-index:-1;
}
.orb{
    position:absolute;
    border-radius:50%;
    filter:blur(120px);
}
.orb1{
    width:500px;
    height:500px;
    background:#ffffff;
    opacity:.04;
    top:-150px;
    left:-150px;
    animation:float1 18s ease-in-out infinite;
}
.orb2{
    width:700px;
    height:700px;
    background:#ffffff;
    opacity:.02;
    bottom:-300px;
    right:-300px;
    animation:float2 24s ease-in-out infinite;
}
@keyframes float1{
    0%,100%{
        transform:translate(0,0);
    }
    50%{
        transform:translate(80px,60px);
    }
}
@keyframes float2{
    0%,100%{
        transform:translate(0,0);
    }
    50%{
        transform:translate(-100px,-80px);
    }
}
.noise{
    position:absolute;
    inset:0;
    opacity:.025;
    background-image:
    radial-gradient(circle at 20% 20%, white 1px, transparent 1px),
    radial-gradient(circle at 70% 60%, white 1px, transparent 1px),
    radial-gradient(circle at 40% 90%, white 1px, transparent 1px);
    background-size:180px 180px;
    animation:noiseMove 20s linear infinite;
}
@keyframes noiseMove{
    from{
        transform:translateY(0);
    }
    to{
        transform:translateY(-180px);
    }
}
.header{
    backdrop-filter:blur(24px);
    background:rgba(15,15,15,.85);
    border:1px solid rgba(255,255,255,.06);
    box-shadow:
        0 10px 40px rgba(0,0,0,.45);
    transition:.25s ease;
}
.header:hover{
    border-color:rgba(255,255,255,.12);
}
@keyframes messageAppear{
    from{
        opacity:0;
        transform:translateY(12px);
    }
    to{
        opacity:1;
        transform:translateY(0);
    }
}
.avatar{
    transition:.25s ease;
}
.avatar:hover{
    transform:scale(1.05);
}
.name{
    letter-spacing:.2px;
}
.name:hover{
    opacity:.75;
}
.preview{
    overflow:hidden;
}
.preview img{
    transition:
        transform .35s ease,
        opacity .35s ease;
}
.preview:hover img{
    transform:scale(1.02);
}
.footer-row{
    display:flex;
    justify-content:space-between;
    align-items:center;
    margin-top:12px;
    padding-top:10px;
    border-top:1px solid #1f1f1f;
}
::-webkit-scrollbar{
    width:10px;
}
::-webkit-scrollbar-track{
    background:#050505;
}
::-webkit-scrollbar-thumb{
    background:#242424;
    border-radius:999px;
}
::-webkit-scrollbar-thumb:hover{
    background:#343434;
}
}
"""
    parts = [
    '<!doctype html>',
    '<html lang="ru">',
    '<head>',
    '<meta charset="utf-8">',
    '<meta name="viewport" content="width=device-width,initial-scale=1">',
    '<link rel="preconnect" href="https://fonts.googleapis.com">',
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
    '<link href="https://fonts.googleapis.com/css2?family=Archivo+Black&display=swap" rel="stylesheet">',
    '<meta name="theme-color" content="#050505">',
    '<meta name="color-scheme" content="dark">',
    '<title>Shell Save — Удаленные сообщения</title>',
    f'<style>{css}</style>',
    '</head>',
    '<body>',

    '<div class="bg">'
        '<div class="orb orb1"></div>'
        '<div class="orb orb2"></div>'
        '<div class="noise"></div>'
    '</div>',

    '<div class="container">',

        '<div class="header">'
            '<div class="brand">'
                '<div class="logo">🛡</div>'
                '<div class="brand-text">'
                    '<div class="brand-title">Shell Save</div>'
                    '<div class="brand-sub">Архив удаленных сообщений</div>'
                '</div>'
            '</div>'

            f'''
            <a class="open-bot" href="{escape(bot_link)}">
                Открыть бота
            </a>
            '''
        '</div>',

        f'''
        <div class="stats-card">
            <div class="stats-label">
                Удалено всего сообщений
            </div>

            <div class="stats-value">
                {len(messages)}
            </div>
        </div>
        ''',

        '''
        <div class="filters">
            <button class="filter-btn active" data-filter="all">Все</button>
            <button class="filter-btn" data-filter="text">Текст</button>
            <button class="filter-btn" data-filter="photo">Фото</button>
            <button class="filter-btn" data-filter="video">Видео</button>
            <button class="filter-btn" data-filter="document">Документы</button>
        </div>
        ''',

        '<div class="chat">'
]

    for msg in sorted(messages, key=lambda m: m.id):

        name = escape(getattr(msg, 'first_name', UNKNOWN_USER_DISPLAY))
        username = getattr(msg, 'from_username', None)
        user_id = getattr(msg, 'user_id', None)
        time_str = escape(str(getattr(msg, 'created_at', '')))
        user_link = f"tg://user?id={user_id}" if user_id else '#'
        profile_link = f'<a class="name" href="{escape(user_link)}">{escape(name)}</a>'
        if username and username != UNKNOWN_USER_DISPLAY:
            profile_link += f' <span class="badge">@{escape(username)}</span>'

        content_text = escape(msg.content or '')
        if not content_text:
            content_text = f"[{escape(TYPE_LABELS.get(msg.type, msg.type.capitalize()))}]"

        avatar_path = await _download_user_avatar(bot, user_id) if user_id else None
        avatar_html = f'<div class="avatar">{escape(name[:1])}</div>'
        if avatar_path and avatar_path.exists():
            try:
                with open(avatar_path, 'rb') as f:
                    data = base64.b64encode(f.read()).decode('ascii')
                    avatar_html = f'<div class="avatar"><img src="data:image/png;base64,{data}" alt="avatar" style="width:100%;height:100%;border-radius:50%;object-fit:cover"/></div>'
            except Exception:
                avatar_html = f'<div class="avatar">{escape(name[:1])}</div>'

        img_html = ''
        if msg.type in ('photos', 'photo', 'animation'):
            try:
                file_rows = session.exec(select(File).where(File.message_id == msg.id)).all()
                for file in file_rows:
                    path = await ensure_file_downloaded(bot, session, file, 'jpg')
                    if path and path.exists():
                        with open(path, 'rb') as f:
                            data = base64.b64encode(f.read()).decode('ascii')
                            img_html = f'<div class="preview"><img src="data:image/jpeg;base64,{data}" alt="media"/></div>'
                            break
            except Exception:
                img_html = ''

        id_line = f'<span class="meta">ID: {escape(str(user_id))}</span>' if user_id else ''
        msg_type = msg.type
        if msg_type in ("photo", "photos", "animation"):
            html_type = "photo"
        elif msg_type in ("video", "videos"):
            html_type = "video"
        elif msg_type in ("document", "documents"):
            html_type = "document"
        else:
            html_type = "text"
        parts.append(
             f'<div class="bubble-row" data-type="{html_type}">'
            f'{avatar_html}'
            '<div class="card">'
            '<div class="name-row">'
            f'{profile_link}'
            f'<span class="meta">{time_str}</span>'
            '</div>'
            f'<div class="text">{content_text}</div>'
            f'{img_html}'
            f'{id_line}'
            '</div>'
            '</div>'
        )
            
    parts.extend([
            '</div>', 
            f'''
            <div class="footer">
                <div class="footer-title">
                    Архив создан через Shell Save
                </div>
                <div class="footer-time">
                    {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}
                </div>
            </div>
            ''',
            '</div>', 
            '''
            <script>
            const buttons = document.querySelectorAll(".filter-btn");
            buttons.forEach(btn => {
                btn.addEventListener("click", () => {
                    buttons.forEach(b => {
                        b.classList.remove("active");
                    });
                    btn.classList.add("active");
                    const filter = btn.dataset.filter;
                    document.querySelectorAll("[data-type]").forEach(msg => {
                        if (filter === "all") {
                            msg.style.display = "";
                            return;
                        }
                        msg.style.display =
                            msg.dataset.type === filter
                                ? ""
                                : "none";
                    });
                });
            });
            </script>
            ''',

            '</body>',
            '</html>'
    ])
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(parts))
    return out_path


class AdminBroadcastState(StatesGroup):
    selecting = State()
    waiting_for_text = State()
    waiting_for_photo = State()
    waiting_for_button_choice = State()
    waiting_for_button_url = State()
    waiting_for_button_style = State()
    confirming = State()


class AdminCommandState(StatesGroup):
    viewing_categories = State()
    selecting_category = State()
    viewing_commands_in_category = State()
    waiting_for_new_category = State()
    waiting_for_command_name = State()
    waiting_for_command_description = State()
    editing_command = State()
    editing_category_name = State()


class AdminCleanupState(StatesGroup):
    waiting_for_days = State()
    confirming = State()


class AdminManageState(StatesGroup):
    waiting_for_action = State()
    waiting_for_id = State()
    waiting_for_edit_category_name = State()


class UserPromoState(StatesGroup):
    waiting_for_code = State()


class ProfileCustomState(StatesGroup):
    waiting_for_title = State()


class AdminProState(StatesGroup):
    waiting_for_ban = State()
    waiting_for_unban = State()
    waiting_for_limits = State()
    waiting_for_promo = State()
    waiting_for_promo_delete = State()
    waiting_for_issue_promo = State()
    waiting_for_ref_days = State()


class AdminGiftState(StatesGroup):
    waiting_for_target = State()
    waiting_for_text = State()


class SubscriptionAdminState(StatesGroup):
    waiting_for_plan = State()
    waiting_for_edit_plan = State()
    waiting_for_grant = State()
    waiting_for_revoke = State()
    waiting_for_extend_all = State()


engine = create_engine("sqlite:///database.db")


class DBMessage(SQLModel, table=True):
    id: int = Field(primary_key=True)

    chat_id: int
    user_id: int
    owner_id: Optional[int] = None

    from_username: str
    first_name: str

    type: str
    content: Optional[str] = None
    media_group_id: Optional[str] = None

    created_at: str


class BotUser(SQLModel, table=True):
    user_id: int = Field(primary_key=True)
    username: Optional[str] = None
    first_name: Optional[str] = None
    registered_at: str


class SubscriptionPlan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    days: int
    price_usd: float = 0
    stars: int = 0
    is_active: bool = True
    created_at: str


class UserSubscription(SQLModel, table=True):
    user_id: int = Field(primary_key=True)
    plan_title: str = "Free"
    expires_at: Optional[str] = None
    source: str = "free"
    updated_at: str


class SubscriptionPayment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    plan_id: int
    provider: str
    invoice_id: Optional[str] = None
    payload: str
    amount: float = 0
    status: str = "pending"
    created_at: str
    paid_at: Optional[str] = None


class SubscriptionUsage(SQLModel, table=True):
    id: str = Field(primary_key=True)
    user_id: int
    action: str
    day: str
    count: int = 0


class UserBan(SQLModel, table=True):
    user_id: int = Field(primary_key=True)
    reason: Optional[str] = None
    banned_at: str
    banned_by: int


class UserLimitOverride(SQLModel, table=True):
    user_id: int = Field(primary_key=True)
    command_limit: Optional[int] = None
    save_limit: Optional[int] = None
    updated_at: str
    updated_by: int


class PromoCode(SQLModel, table=True):
    code: str = Field(primary_key=True)
    days: int = 0
    discount_percent: int = 0
    max_uses: int = 1
    used_count: int = 0
    is_active: bool = True
    expires_at: Optional[str] = None
    created_at: str
    created_by: int


class PromoRedemption(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str
    user_id: int
    redeemed_at: str


class UserDiscount(SQLModel, table=True):
    user_id: int = Field(primary_key=True)
    discount_percent: int
    code: str
    created_at: str
    used_at: Optional[str] = None


class Referral(SQLModel, table=True):
    referred_id: int = Field(primary_key=True)
    referrer_id: int
    created_at: str
    rewarded_at: Optional[str] = None
    reward_days: int = 0


class FavoriteMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int
    db_message_id: int
    created_at: str


class UserProfileSettings(SQLModel, table=True):
    user_id: int = Field(primary_key=True)
    card_title: Optional[str] = None
    updated_at: str


class UserNotificationState(SQLModel, table=True):
    id: str = Field(primary_key=True)
    user_id: int
    kind: str
    sent_at: str


class BotSetting(SQLModel, table=True):
    key: str = Field(primary_key=True)
    value: str


class AdminActionLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    admin_id: int
    action: str
    target_id: Optional[int] = None
    details: Optional[str] = None
    created_at: str


class AdminGiftOrder(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    admin_id: int
    target_user_id: int
    gift_id: str
    gift_label: str
    star_count: int
    text: Optional[str] = None
    payment_mode: str
    payload: Optional[str] = None
    status: str = "created"
    error: Optional[str] = None
    created_at: str
    paid_at: Optional[str] = None
    sent_at: Optional[str] = None


class File(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    file_name: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))
    file_id: Optional[str] = None
    folder: str
    message_id: int


class DeletedLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    db_message_id: int
    owner_id: int
    deleted_at: str


class EditedLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    db_message_id: int
    owner_id: int
    edited_at: str
    old_content: Optional[str] = None
    new_content: Optional[str] = None


SQLModel.metadata.create_all(engine)


def migrate_database():
    with engine.connect() as connection:
        result = connection.execute(text("PRAGMA table_info(file)"))
        columns = [row[1] for row in result]
        if "file_id" not in columns:
            connection.execute(text("ALTER TABLE file ADD COLUMN file_id TEXT"))

        dbmessage_columns = [row[1] for row in connection.execute(text("PRAGMA table_info(dbmessage)"))]
        if "media_group_id" not in dbmessage_columns:
            connection.execute(text("ALTER TABLE dbmessage ADD COLUMN media_group_id TEXT"))
        if "owner_id" not in dbmessage_columns:
            connection.execute(text("ALTER TABLE dbmessage ADD COLUMN owner_id INTEGER"))

        result = connection.execute(text("PRAGMA table_info(file)"))
        columns_info = [row for row in result]
        for row in columns_info:
            if row[1] == "file_name" and row[3] == 1:
                connection.execute(text("DROP TABLE IF EXISTS file_old"))
                connection.execute(text("ALTER TABLE file RENAME TO file_old"))
                connection.execute(text(
                    "CREATE TABLE file ("
                    "id INTEGER PRIMARY KEY, "
                    "file_name VARCHAR, "
                    "file_id TEXT, "
                    "folder VARCHAR NOT NULL, "
                    "message_id INTEGER NOT NULL)"
                ))
                connection.execute(text(
                    "INSERT INTO file (id, file_name, file_id, folder, message_id) "
                    "SELECT id, file_name, file_id, folder, message_id FROM file_old"
                ))
                connection.execute(text("DROP TABLE file_old"))
                break
        edited_info = [row[1] for row in connection.execute(text("PRAGMA table_info(editedlog)"))]
        if not edited_info:
            connection.execute(text(
                "CREATE TABLE IF NOT EXISTS editedlog ("
                "id INTEGER PRIMARY KEY, "
                "db_message_id INTEGER, "
                "owner_id INTEGER, "
                "edited_at TEXT, "
                "old_content TEXT, "
                "new_content TEXT)"
            ))

migrate_database()

MEDIA_PATH = Path("media")
MEDIA_PATH.mkdir(exist_ok=True)

folders = [
    "photos",
    "videos",
    "voices",
    "stickers",
    "documents",
    "animations",
    "video_notes",
    "audios",
    "profile_cards",
    "avatars"
]

for folder in folders:
    MEDIA_PATH.joinpath(folder).mkdir(exist_ok=True)

PROFILE_CARD_TEMPLATE = Path("assets") / "profile_card_template.png"
PROFILE_CARD_WIDTH = 1920
PROFILE_CARD_HEIGHT = 1080

dp = Dispatcher()

router = other_commands()

dp.include_router(router)

def btn(text: str, callback: str = None, style: str = None, emoji_id: str = None, **kwargs) -> InlineKeyboardButton:

    params = {}
    if callback:
        params["callback_data"] = callback
    if emoji_id:
        params["icon_custom_emoji_id"] = emoji_id
    params.update(kwargs)
    return InlineKeyboardButton(text=text, **params)


def main_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [btn(BUTTON_LABELS["guide"], "guide", emoji_id="5220053623211305785")],
        [
            btn("Профиль", "profile", emoji_id=PROFILE_EMOJI_ID),
            btn(BUTTON_LABELS["help"], "commands_menu", emoji_id=COMAND_EMOJI_ID)
        ],
        [btn(" Premium", "subscription", emoji_id=GEM_EMOJI_ID)],
        [
            btn("Рефералка", "referral", emoji_id=GEM_EMOJI_ID),
            btn("Промокод", "promo_enter", emoji_id=STARS_EMOJI_ID),
        ],
        [
            btn(BUTTON_LABELS["features"], "features", emoji_id="5222108309795908493"),
            btn(BUTTON_LABELS["check_business"], "check_business", emoji_id="5429571366384842791")
        ],
    ]
    
    if BOT_USERNAME:
        keyboard.append([
            InlineKeyboardButton(
                text=BUTTON_LABELS["copy_username"],
                icon_custom_emoji_id="5327904946413121515",
                copy_text=CopyTextButton(text=f"@{BOT_USERNAME}")
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


main_kb = main_keyboard()

async def edit_message_inline(message, text, reply_markup):
    try:
        await message.edit_caption(caption=text, reply_markup=reply_markup, parse_mode="HTML")
        return True
    except Exception:
        try:
            await message.edit_text(text=text, reply_markup=reply_markup, parse_mode="HTML")
            return True
        except Exception:
            return False


def short_id(value: str) -> str:
    return sha1(value.encode("utf-8")).hexdigest()[:10]


def resolve_category_key(key: str) -> Optional[str]:
    categories = load_custom_commands()
    for category in categories.keys():
        if short_id(category) == key:
            return category
    return None


def resolve_command_key(category: str, command_key: str) -> Optional[str]:
    commands = load_custom_commands().get(category, [])
    for cmd in commands:
        name = cmd.get("name", "")
        if short_id(name) == command_key:
            return name
    return None


def parse_timestamp(value: str) -> datetime:
    if not value:
        return datetime.min
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        pass

    formats = [
        "%d.%m %H:%M:%S",
        "%d.%m.%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            parsed = datetime.strptime(value, fmt)
            if "%Y" not in fmt:
                parsed = parsed.replace(year=datetime.now().year)
            return parsed
        except ValueError:
            continue

    raise ValueError(f"Unsupported timestamp format: {value}")


def iso_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def today_key() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def parse_datetime_safe(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return parse_timestamp(value)
    except Exception:
        return None


def ensure_default_subscription_plans():
    with Session(engine) as session:
        plans = session.exec(select(SubscriptionPlan)).all()
        if plans:
            return

        session.add(SubscriptionPlan(
            title="Premium 7",
            days=7,
            price_usd=2.0,
            stars=100,
            is_active=True,
            created_at=iso_now(),
        ))
        session.add(SubscriptionPlan(
            title="Premium 30",
            days=30,
            price_usd=5.0,
            stars=250,
            is_active=True,
            created_at=iso_now(),
        ))
        session.commit()


def get_setting(session: Session, key: str, default: str) -> str:
    setting = session.get(BotSetting, key)
    return setting.value if setting else default


def set_setting(session: Session, key: str, value: str) -> None:
    setting = session.get(BotSetting, key)
    if not setting:
        setting = BotSetting(key=key, value=value)
    else:
        setting.value = value
    session.add(setting)
    session.commit()


def log_admin_action(admin_id: int, action: str, target_id: Optional[int] = None, details: Optional[str] = None) -> None:
    with Session(engine) as session:
        session.add(AdminActionLog(
            admin_id=admin_id,
            action=action,
            target_id=target_id,
            details=details,
            created_at=iso_now(),
        ))
        session.commit()


def is_user_banned(user_id: int) -> bool:
    if user_id in ADMIN_IDS:
        return False
    with Session(engine) as session:
        return session.get(UserBan, user_id) is not None


def ban_user(admin_id: int, user_id: int, reason: str = "") -> None:
    with Session(engine) as session:
        session.add(UserBan(
            user_id=user_id,
            reason=reason or None,
            banned_at=iso_now(),
            banned_by=admin_id,
        ))
        session.commit()
    log_admin_action(admin_id, "ban_user", user_id, reason or None)


def unban_user(admin_id: int, user_id: int) -> None:
    with Session(engine) as session:
        record = session.get(UserBan, user_id)
        if record:
            session.delete(record)
            session.commit()
    log_admin_action(admin_id, "unban_user", user_id)


def get_limit_override(session: Session, user_id: int, action: str) -> Optional[int]:
    override = session.get(UserLimitOverride, user_id)
    if not override:
        return None
    return override.command_limit if action == "command_view" else override.save_limit


def get_effective_limit(session: Session, user_id: int, action: str, default_limit: int) -> int:
    if user_id in ADMIN_IDS or is_subscription_active_record(session.get(UserSubscription, user_id)):
        return -1
    override = get_limit_override(session, user_id, action)
    return default_limit if override is None else override


def format_limit_value(limit: int) -> str:
    return "безлимит" if limit < 0 else str(limit)


def consume_user_limit(user_id: int, action: str, default_limit: int) -> tuple[bool, int, int, bool]:
    with Session(engine) as session:
        limit = get_effective_limit(session, user_id, action, default_limit)
        if limit < 0:
            return True, 0, limit, False

        key = f"{user_id}:{action}:{today_key()}"
        usage = session.get(SubscriptionUsage, key)
        used = usage.count if usage else 0
        if used >= limit:
            return False, used, limit, False

        if not usage:
            usage = SubscriptionUsage(
                id=key,
                user_id=user_id,
                action=action,
                day=today_key(),
                count=0,
            )

        usage.count += 1
        session.add(usage)
        session.commit()
        almost = limit > 1 and usage.count == limit - 1
        return True, usage.count, limit, almost


def get_active_discount(session: Session, user_id: int) -> Optional[UserDiscount]:
    discount = session.get(UserDiscount, user_id)
    if discount and not discount.used_at and discount.discount_percent > 0:
        return discount
    return None


def apply_discount_amount(amount: float, discount_percent: int) -> float:
    if discount_percent <= 0:
        return amount
    return max(0, round(amount * (100 - discount_percent) / 100, 2))


def apply_discount_stars(amount: int, discount_percent: int) -> int:
    if discount_percent <= 0:
        return amount
    return max(1, int(round(amount * (100 - discount_percent) / 100)))


def use_active_discount(session: Session, user_id: int) -> Optional[UserDiscount]:
    discount = get_active_discount(session, user_id)
    if discount:
        discount.used_at = iso_now()
        session.add(discount)
        session.commit()
    return discount


def create_referral_if_needed(referrer_id: Optional[int], referred_id: int) -> bool:
    if not referrer_id or referrer_id == referred_id or referred_id in ADMIN_IDS:
        return False
    with Session(engine) as session:
        if session.get(Referral, referred_id):
            return False
        session.add(Referral(
            referred_id=referred_id,
            referrer_id=referrer_id,
            created_at=iso_now(),
        ))
        session.commit()
        return True


def apply_referral_reward(session: Session, referred_id: int) -> Optional[tuple[int, int]]:
    referral = session.get(Referral, referred_id)
    if not referral or referral.rewarded_at:
        return None

    reward_days = int(get_setting(session, "referral_reward_days", "3"))
    if reward_days <= 0:
        return None

    extend_user_subscription(session, referral.referrer_id, reward_days, "Referral Bonus", "referral")
    referral.reward_days = reward_days
    referral.rewarded_at = iso_now()
    session.add(referral)
    session.commit()
    return referral.referrer_id, reward_days


def redeem_promo_code(session: Session, user_id: int, raw_code: str) -> tuple[bool, str]:
    raw_value = (raw_code or "").strip()
    code_value = raw_value.upper()
    if not code_value:
        return False, "Введите промокод."

    promo = session.get(PromoCode, code_value)
    if not promo:
        promos = session.exec(select(PromoCode)).all()
        promo = next((item for item in promos if item.code.casefold() == raw_value.casefold()), None)
    if not promo or not promo.is_active:
        return False, "Промокод не найден или отключен."

    expires_at = parse_datetime_safe(promo.expires_at)
    if expires_at and expires_at < datetime.now():
        return False, "Срок действия промокода истек."

    if promo.max_uses > 0 and promo.used_count >= promo.max_uses:
        return False, "Лимит использований промокода исчерпан."

    already = session.exec(
        select(PromoRedemption).where(
            (PromoRedemption.code == promo.code) & (PromoRedemption.user_id == user_id)
        )
    ).first()
    if already:
        return False, "Вы уже использовали этот промокод."

    promo.used_count += 1
    session.add(PromoRedemption(code=promo.code, user_id=user_id, redeemed_at=iso_now()))
    session.add(promo)

    result_lines = [f"{GEM_EMOJI} <b>Промокод активирован:</b> <code>{escape(promo.code)}</code>"]
    if promo.days > 0:
        sub = extend_user_subscription(session, user_id, promo.days, f"Promo {promo.code}", "promo")
        result_lines.append(f"<b>Premium:</b> +{promo.days} дн.")
        result_lines.append(f"<b>Действует до:</b> <code>{escape(format_subscription_expires(sub.expires_at))}</code>")

    if promo.discount_percent > 0:
        discount = session.get(UserDiscount, user_id)
        if not discount or discount.used_at:
            discount = UserDiscount(
                user_id=user_id,
                discount_percent=promo.discount_percent,
                code=promo.code,
                created_at=iso_now(),
                used_at=None,
            )
        else:
            discount.discount_percent = max(discount.discount_percent, promo.discount_percent)
            discount.code = promo.code
            discount.created_at = iso_now()
            discount.used_at = None
        session.add(discount)
        result_lines.append(f"<b>Скидка:</b> {promo.discount_percent}% на следующую покупку.")

    session.commit()
    return True, "\n".join(result_lines)


def user_stats_text(user_id: int) -> str:
    with Session(engine) as session:
        messages = session.exec(
            select(DBMessage).where((DBMessage.owner_id == user_id) | (DBMessage.user_id == user_id))
        ).all()
        favorites = session.exec(select(FavoriteMessage).where(FavoriteMessage.owner_id == user_id)).all()
        type_counts: dict[str, int] = {}
        for msg in messages:
            type_counts[msg.type] = type_counts.get(msg.type, 0) + 1

        command_used = get_usage_count(session, user_id, "command_view")
        save_used = get_usage_count(session, user_id, "business_save")
        command_limit = get_effective_limit(session, user_id, "command_view", FREE_DAILY_COMMAND_LIMIT)
        save_limit = get_effective_limit(session, user_id, "business_save", FREE_DAILY_SAVE_LIMIT)

    top_types = sorted(type_counts.items(), key=lambda item: item[1], reverse=True)[:8]
    types_text = "\n".join(f"• <b>{escape(kind)}:</b> {count}" for kind, count in top_types) or "• Пока нет сохранений"
    return (
        f"<b>{STATISTICS_EMOJI} Моя статистика</b>\n\n"
        f"<b>Всего сохранений:</b> {len(messages)}\n"
        f"<b>В избранном:</b> {len(favorites)}\n"
        f"<b>Команды сегодня:</b> {command_used}/{format_limit_value(command_limit)}\n"
        f"<b>Сохранения сегодня:</b> {save_used}/{format_limit_value(save_limit)}\n\n"
        f"<b>Типы медиа:</b>\n{types_text}"
    )


def get_user_subscription(session: Session, user_id: int) -> UserSubscription:
    record = session.get(UserSubscription, user_id)
    if record:
        return record

    record = UserSubscription(
        user_id=user_id,
        plan_title="Free",
        expires_at=None,
        source="free",
        updated_at=iso_now(),
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def is_subscription_active_record(record: Optional[UserSubscription]) -> bool:
    if not record or not record.expires_at:
        return False

    expires_at = parse_datetime_safe(record.expires_at)
    return bool(expires_at and expires_at > datetime.now())


def is_premium_user(user_id: int) -> bool:
    if user_id in ADMIN_IDS:
        return True

    with Session(engine) as session:
        return is_subscription_active_record(session.get(UserSubscription, user_id))


def profile_status_text(user_id: int) -> str:
    if user_id in ADMIN_IDS:
        return "Администратор"
    if is_premium_user(user_id):
        return "Premium"
    return "Пользователь"


def get_profile_settings(session: Session, user_id: int) -> UserProfileSettings:
    settings = session.get(UserProfileSettings, user_id)
    if settings:
        return settings
    settings = UserProfileSettings(user_id=user_id, card_title=None, updated_at=iso_now())
    session.add(settings)
    session.commit()
    session.refresh(settings)
    return settings


def profile_card_bottom_text(user_id: int) -> str:
    with Session(engine) as session:
        settings = session.get(UserProfileSettings, user_id)
        if settings and settings.card_title:
            return settings.card_title
    return f"СТАТУС: {profile_status_text(user_id).upper()}"


def format_subscription_expires(expires_at: Optional[str]) -> str:
    parsed = parse_datetime_safe(expires_at)
    if not parsed:
        return "не активна"
    return parsed.strftime("%d.%m.%Y %H:%M")


def extend_user_subscription(session: Session, user_id: int, days: int, plan_title: str, source: str) -> UserSubscription:
    record = get_user_subscription(session, user_id)
    now = datetime.now()
    current_expires = parse_datetime_safe(record.expires_at)
    start_from = current_expires if current_expires and current_expires > now else now
    record.plan_title = plan_title
    record.expires_at = (start_from + timedelta(days=days)).isoformat(timespec="seconds")
    record.source = source
    record.updated_at = iso_now()
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def revoke_user_subscription(session: Session, user_id: int) -> UserSubscription:
    record = get_user_subscription(session, user_id)
    record.plan_title = "Free"
    record.expires_at = None
    record.source = "admin_revoke"
    record.updated_at = iso_now()
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def get_known_subscription_user_ids(session: Session) -> list[int]:
    ids = set()
    ids.update(session.exec(select(BotUser.user_id)).all())
    ids.update(session.exec(select(UserSubscription.user_id)).all())
    ids.update(session.exec(select(DBMessage.user_id)).all())
    return sorted(user_id for user_id in ids if user_id and user_id not in ADMIN_IDS)


def subscription_status_text(user_id: int) -> str:
    with Session(engine) as session:
        record = get_user_subscription(session, user_id)
        premium = is_subscription_active_record(record) or user_id in ADMIN_IDS
        if premium:
            plan_text = "Admin Premium" if user_id in ADMIN_IDS else record.plan_title
            expires_text = "навсегда" if user_id in ADMIN_IDS else format_subscription_expires(record.expires_at)
            return (
                f"<b>{GEM_EMOJI} Подписка: Premium</b>\n\n"
                f"<b>Тариф:</b> {escape(plan_text)}\n"
                f"<b>Действует до:</b> <code>{escape(expires_text)}</code>\n\n"
                "<i>Лимиты Free сняты. Приоритетная обработка и автосохранение всех типов медиа включены.</i>"
            )

        command_used = get_usage_count(session, user_id, "command_view")
        save_used = get_usage_count(session, user_id, "business_save")
        command_limit = get_effective_limit(session, user_id, "command_view", FREE_DAILY_COMMAND_LIMIT)
        save_limit = get_effective_limit(session, user_id, "business_save", FREE_DAILY_SAVE_LIMIT)
        return (
            "<b>🆓 Подписка: Free</b>\n\n"
            f"<b>Команды:</b> {command_used}/{format_limit_value(command_limit)} в день\n"
            f"<b>Сохранения:</b> {save_used}/{format_limit_value(save_limit)} в день\n\n"
            "<i>Купите Premium, чтобы убрать лимиты.</i>"
        )


def get_active_plans(session: Session) -> list[SubscriptionPlan]:
    return session.exec(
        select(SubscriptionPlan)
        .where(SubscriptionPlan.is_active == True)
        .order_by(SubscriptionPlan.days)
    ).all()


def get_usage_count(session: Session, user_id: int, action: str) -> int:
    usage = session.get(SubscriptionUsage, f"{user_id}:{action}:{today_key()}")
    return usage.count if usage else 0


def record_usage_event(user_id: int, action: str, amount: int = 1) -> None:
    with Session(engine) as session:
        key = f"{user_id}:{action}:{today_key()}"
        usage = session.get(SubscriptionUsage, key)
        if not usage:
            usage = SubscriptionUsage(
                id=key,
                user_id=user_id,
                action=action,
                day=today_key(),
                count=0,
            )
        usage.count += amount
        session.add(usage)
        session.commit()


def consume_free_limit(user_id: int, action: str, limit: int) -> bool:
    allowed, _, _, _ = consume_user_limit(user_id, action, limit)
    return allowed


class BanMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data: dict[str, Any]):
        user = data.get("event_from_user") or getattr(event, "from_user", None)
        if user and is_user_banned(user.id):
            if isinstance(event, CallbackQuery):
                await event.answer("Вы заблокированы в боте.", show_alert=True)
            elif isinstance(event, Message):
                await event.answer(f"{CROSS_EMOJI} <b>Вы заблокированы в боте.</b>", parse_mode="HTML")
            return None
        return await handler(event, data)


dp.message.middleware(BanMiddleware())
dp.callback_query.middleware(BanMiddleware())


def create_subscription_payment(session: Session, user_id: int, plan: SubscriptionPlan, provider: str) -> SubscriptionPayment:
    discount = get_active_discount(session, user_id)
    discount_percent = discount.discount_percent if discount else 0
    amount = apply_discount_stars(plan.stars, discount_percent) if provider == "stars" else apply_discount_amount(plan.price_usd, discount_percent)
    payment = SubscriptionPayment(
        user_id=user_id,
        plan_id=plan.id,
        provider=provider,
        payload=f"sub:{uuid4().hex}",
        amount=amount,
        status="pending",
        created_at=iso_now(),
    )
    session.add(payment)
    session.commit()
    session.refresh(payment)
    if discount:
        discount.used_at = iso_now()
        session.add(discount)
        session.commit()
    return payment


def activate_subscription_payment(session: Session, payment: SubscriptionPayment, plan: SubscriptionPlan, invoice_id: Optional[str] = None):
    if payment.status == "paid":
        return

    payment.status = "paid"
    payment.paid_at = iso_now()
    if invoice_id:
        payment.invoice_id = invoice_id
    session.add(payment)
    extend_user_subscription(session, payment.user_id, plan.days, plan.title, payment.provider)
    session.commit()


def subscription_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=" Купить подписку", callback_data="subscription_buy", icon_custom_emoji_id=GEM_EMOJI_ID)],
        [InlineKeyboardButton(text=BUTTON_LABELS["back"], callback_data="back_to_menu", icon_custom_emoji_id=BACK_EMOJI_ID)],
    ])


def subscription_plans_keyboard(plans: list[SubscriptionPlan]) -> InlineKeyboardMarkup:
    rows = []
    for plan in plans:
        rows.append([
            InlineKeyboardButton(
                text=f"{plan.title} · {plan.days} дн · ${plan.price_usd:g} / {plan.stars} Stars",
                callback_data=f"subscription_plan:{plan.id}",
                icon_custom_emoji_id=GEM_EMOJI_ID,
            )
        ])
    rows.append([InlineKeyboardButton(text=BUTTON_LABELS["back"], callback_data="subscription")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def subscription_payment_keyboard(plan_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Оплатить Stars", callback_data=f"sub_pay_stars:{plan_id}", icon_custom_emoji_id=STARS_EMOJI_ID),
            InlineKeyboardButton(text="Оплатить Crypto", callback_data=f"sub_pay_crypto:{plan_id}", icon_custom_emoji_id=CRYPTOBOT_EMOJI_ID),
        ],
        [InlineKeyboardButton(text=BUTTON_LABELS["back"], callback_data="subscription_buy")],
    ])


def admin_subscriptions_keyboard(plans: list[SubscriptionPlan]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="Добавить тариф", callback_data="admin_sub_add_plan", icon_custom_emoji_id=GEM_EMOJI_ID)],
        [InlineKeyboardButton(text="Выдать подписку", callback_data="admin_sub_grant", icon_custom_emoji_id=GEM_EMOJI_ID)],
        [
            InlineKeyboardButton(text="Забрать подписку", callback_data="admin_sub_revoke", icon_custom_emoji_id=TRASH_EMOJI_ID),
            InlineKeyboardButton(text="Продлить всем", callback_data="admin_sub_extend_all", icon_custom_emoji_id=PLUS_EMOJI_ID),
        ],
    ]
    for plan in plans:
        plan_text = f"{plan.title} · {plan.days} дн · ${plan.price_usd:g} · {plan.stars} Stars"
        if not plan.is_active:
            plan_text = f"Откл. · {plan_text}"
        plan_button = {
            "text": plan_text,
            "callback_data": f"admin_sub_edit:{plan.id}",
        }
        if plan.is_active:
            plan_button["icon_custom_emoji_id"] = GEM_EMOJI_ID
        rows.append([
            InlineKeyboardButton(**plan_button)
        ])
        rows.append([
            InlineKeyboardButton(text="Изменить", callback_data=f"admin_sub_edit:{plan.id}", icon_custom_emoji_id=RENAME_EMOJI_ID),
            InlineKeyboardButton(text="Вкл/Выкл", callback_data=f"admin_sub_toggle:{plan.id}"),
            InlineKeyboardButton(text="Удалить", callback_data=f"admin_sub_delete:{plan.id}", icon_custom_emoji_id=TRASH_EMOJI_ID),
        ])
    rows.append([InlineKeyboardButton(text=BUTTON_LABELS["back_to_admin"], callback_data="back_to_admin", icon_custom_emoji_id=BACK_EMOJI_ID)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_subscriptions_text() -> tuple[str, InlineKeyboardMarkup]:
    with Session(engine) as session:
        plans = session.exec(select(SubscriptionPlan).order_by(SubscriptionPlan.id)).all()
        active_subs = [
            sub for sub in session.exec(select(UserSubscription)).all()
            if is_subscription_active_record(sub)
        ]
        pending_payments = session.exec(
            select(SubscriptionPayment).where(SubscriptionPayment.status == "pending")
        ).all()

    text = (
        f"<b>{GEM_EMOJI} Управление подписками</b>\n\n"
        f"<b>Активных тарифов:</b> {sum(1 for plan in plans if plan.is_active)}\n"
        f"<b>Всего тарифов:</b> {len(plans)}\n"
        f"<b>Активных подписок:</b> {len(active_subs)}\n"
        f"<b>Ожидают оплаты:</b> {len(pending_payments)}\n\n"
        "<i>Тариф можно изменить, выключить или удалить. Подписки можно выдать, забрать или продлить всем.</i>"
    )
    return text, admin_subscriptions_keyboard(plans)


def get_all_known_user_ids(session: Session) -> list[int]:
    ids = set()
    ids.update(session.exec(select(BotUser.user_id)).all())
    ids.update(session.exec(select(DBMessage.user_id)).all())
    ids.update(session.exec(select(DBMessage.owner_id)).all())
    ids.update(session.exec(select(UserSubscription.user_id)).all())
    return sorted(user_id for user_id in ids if user_id)


def admin_users_text() -> str:
    with Session(engine) as session:
        users = get_all_known_user_ids(session)
        bans = session.exec(select(UserBan)).all()
        overrides = session.exec(select(UserLimitOverride)).all()
        premium = sum(1 for user_id in users if user_id in ADMIN_IDS or is_subscription_active_record(session.get(UserSubscription, user_id)))
    return (
        f"<b>{USER_EMOJI} Пользователи</b>\n\n"
        f"<b>Всего известных:</b> {len(users)}\n"
        f"<b>Premium/Admin:</b> {premium}\n"
        f"<b>Free:</b> {max(len(users) - premium, 0)}\n"
        f"<b>В бане:</b> {len(bans)}\n"
        f"<b>Индивидуальные лимиты:</b> {len(overrides)}\n\n"
        "<i>Можно банить, разбанивать и задавать лимиты конкретному пользователю.</i>"
    )


def admin_top_users_text() -> str:
    with Session(engine) as session:
        bot_users = {user.user_id: user for user in session.exec(select(BotUser)).all()}
        messages = session.exec(select(DBMessage)).all()
        usages = session.exec(select(SubscriptionUsage)).all()

    save_counts: dict[int, int] = {}
    for msg in messages:
        owner_id = msg.owner_id or msg.user_id
        if not owner_id:
            continue
        save_counts[owner_id] = save_counts.get(owner_id, 0) + 1

    command_counts: dict[int, int] = {}
    command_fallback_counts: dict[int, int] = {}
    for usage in usages:
        if usage.action == "command_total":
            command_counts[usage.user_id] = command_counts.get(usage.user_id, 0) + usage.count
        elif usage.action == "command_view":
            command_fallback_counts[usage.user_id] = command_fallback_counts.get(usage.user_id, 0) + usage.count

    if not command_counts:
        command_counts = command_fallback_counts

    def user_label(user_id: int) -> str:
        user = bot_users.get(user_id)
        if user and user.username:
            return f"@{escape(user.username)} · <code>{user_id}</code>"
        if user and user.first_name:
            return f"{escape(user.first_name)} · <code>{user_id}</code>"
        return f"<code>{user_id}</code>"

    def format_top(title: str, counts: dict[int, int]) -> str:
        rows = sorted(counts.items(), key=lambda item: item[1], reverse=True)[:10]
        if not rows:
            return f"<b>{title}</b>\n<i>Пока нет данных.</i>"
        text = f"<b>{title}</b>\n"
        for index, (user_id, count) in enumerate(rows, start=1):
            text += f"{index}. {user_label(user_id)} — <b>{count}</b>\n"
        return text.rstrip()

    return (
        f"<b>{STATISTICS_EMOJI} Топ пользователей</b>\n\n"
        f"{format_top('Больше всего сохранений', save_counts)}\n\n"
        f"{format_top('Чаще всего используют команды', command_counts)}"
    )


def admin_users_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Бан", callback_data="admin_user_ban", icon_custom_emoji_id="5258474669769497337"),
            InlineKeyboardButton(text="Разбан", callback_data="admin_user_unban", icon_custom_emoji_id="5776375003280838798"),
        ],
        [InlineKeyboardButton(text="Лимиты пользователя", callback_data="admin_user_limits", icon_custom_emoji_id=GEM_EMOJI_ID)],
        [InlineKeyboardButton(text="Топ пользователей", callback_data="admin_top_users", icon_custom_emoji_id="5877485980901971030")],
        [InlineKeyboardButton(text=BUTTON_LABELS["back_to_admin"], callback_data="back_to_admin", icon_custom_emoji_id=BACK_EMOJI_ID)],
    ])


def admin_promos_text() -> str:
    with Session(engine) as session:
        promos = session.exec(select(PromoCode).order_by(PromoCode.created_at)).all()
    text = f"<b>{STARS_EMOJI} Управление промокодами</b>\n\n"
    if not promos:
        text += "<i>Промокодов пока нет.</i>"
    else:
        for promo in promos[-12:]:
            status = "вкл" if promo.is_active else "выкл"
            text += (
                f"• <code>{escape(promo.code)}</code> · {status} · "
                f"+{promo.days} дн · скидка {promo.discount_percent}% · "
                f"{promo.used_count}/{promo.max_uses if promo.max_uses > 0 else '∞'}\n"
            )
    return text


def admin_promos_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Добавить промокод", callback_data="admin_promo_add", icon_custom_emoji_id=PLUS_EMOJI_ID)],
        [InlineKeyboardButton(text="Выдать пользователю", callback_data="admin_promo_issue", icon_custom_emoji_id=GEM_EMOJI_ID)],
        [InlineKeyboardButton(text="Удалить промокод", callback_data="admin_promo_delete", icon_custom_emoji_id=TRASH_EMOJI_ID)],
        [InlineKeyboardButton(text=BUTTON_LABELS["back_to_admin"], callback_data="back_to_admin", icon_custom_emoji_id=BACK_EMOJI_ID)],
    ])


GIFT_PAGE_SIZE = 8
OLD_GIFTS = [
    {"emoji_id": "5345935030143196497", "stars": 50, "id": "5922558454332916696"},
    {"emoji_id": "5379850840691476775", "stars": 50, "id": "5956217000635139069"},
    {"emoji_id": "5224628072619216265", "stars": 50, "id": "5801108895304779062"},
    {"emoji_id": "5226661632259691727", "stars": 50, "id": "5800655655995968830"},
    {"emoji_id": "5289761157173775507", "stars": 50, "id": "5866352046986232958"},
    {"emoji_id": "5317000922096769303", "stars": 50, "id": "5893356958802511476"},
    {"emoji_id": "5359736160224586485", "stars": 50, "id": "5935895822435615975"},
    {"emoji_id": "5393309541620291208", "stars": 50, "id": "5969796561943660080"},
    {"emoji_id": "5447213743417105726", "stars": 50, "id": "6026193266406327981"},
]

    
def gift_label(gift: dict) -> str:
    if gift.get("source") == "old":
        return f"{gift['stars']} Stars · old"
    emoji = gift.get("emoji") or "🎁"
    return f"{emoji} {gift['stars']} Stars"


def gift_state_payload(gift: dict) -> dict:
    payload = {
        "gift_source": gift["source"],
        "gift_id": gift["id"],
        "gift_stars": int(gift["stars"]),
    }
    if gift.get("emoji"):
        payload["gift_emoji"] = gift["emoji"]
    if gift.get("emoji_id"):
        payload["gift_emoji_id"] = gift["emoji_id"]
    return payload


def gift_from_state_data(data: dict) -> dict:
    gift = {
        "stars": int(data["gift_stars"]),
        "id": data["gift_id"],
        "source": data["gift_source"],
    }
    if data.get("gift_emoji"):
        gift["emoji"] = data["gift_emoji"]
    if data.get("gift_emoji_id"):
        gift["emoji_id"] = data["gift_emoji_id"]
    return gift


def message_html_text(message: Message) -> str:
    raw_text = message.text or message.caption or ""
    if not raw_text:
        return ""
    try:
        return message.html_text
    except Exception:
        return escape(raw_text)


async def get_gift_catalog(bot: Bot, source: str) -> list[dict]:
    if source == "old":
        return [{**gift, "source": "old"} for gift in OLD_GIFTS]

    gifts = await bot.get_available_gifts()
    catalog = []
    for gift in gifts.gifts:
        sticker = getattr(gift, "sticker", None)
        emoji = getattr(sticker, "emoji", None) or "🎁"
        if getattr(gift, "remaining_count", None) == 0 or getattr(gift, "personal_remaining_count", None) == 0:
            continue
        catalog.append({
            "emoji": emoji,
            "stars": int(gift.star_count),
            "id": gift.id,
            "source": "tg",
        })
    return catalog


async def find_gift_info(bot: Bot, source: str, gift_id: str) -> Optional[dict]:
    for gift in await get_gift_catalog(bot, source):
        if gift["id"] == gift_id:
            return gift
    if source == "tg":
        for fallback_source in ("old",):
            for gift in await get_gift_catalog(bot, fallback_source):
                if gift["id"] == gift_id:
                    return gift
    return None


def admin_gifts_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Актуальные Telegram", callback_data="admin_gift_list:tg:0", icon_custom_emoji_id=STARS_EMOJI_ID)],
        [InlineKeyboardButton(text="Old/deleted gifts", callback_data="admin_gift_list:old:0", icon_custom_emoji_id=TRASH_EMOJI_ID)],
        [InlineKeyboardButton(text=BUTTON_LABELS["back_to_admin"], callback_data="back_to_admin", icon_custom_emoji_id=BACK_EMOJI_ID)],
    ])


def admin_gift_pay_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Stars Счет", callback_data=f"admin_gift_invoice:{order_id}", icon_custom_emoji_id=STARS_EMOJI_ID)],
        [InlineKeyboardButton(text="С баланса бота", callback_data=f"admin_gift_balance:{order_id}", icon_custom_emoji_id=GEM_EMOJI_ID)],
        [InlineKeyboardButton(text=BUTTON_LABELS["back_to_admin"], callback_data="back_to_admin", icon_custom_emoji_id=BACK_EMOJI_ID)],
    ])


async def admin_gift_list_text(bot: Bot, source: str, page: int) -> tuple[str, InlineKeyboardMarkup]:
    catalog = await get_gift_catalog(bot, source)
    page = max(0, page)
    total_pages = max(1, (len(catalog) + GIFT_PAGE_SIZE - 1) // GIFT_PAGE_SIZE)
    page = min(page, total_pages - 1)
    source_title = {
        "tg": "Актуальные Telegram gifts",
        "old": "Old/deleted gifts",
    }.get(source, "Gifts")
    text = (
        f"<b>{STARS_EMOJI} {source_title}</b>\n\n"
        "Выберите подарок, потом укажите пользователя и описание."
    )
    if source == "old":
        text += "\n\n<i>Old/deleted могут не отправиться, если Telegram больше не принимает этот gift_id.</i>"

    rows = []
    page_gifts = catalog[page * GIFT_PAGE_SIZE : (page + 1) * GIFT_PAGE_SIZE]
    for gift in page_gifts:
        button_kwargs = {
            "text": f"{gift_label(gift)} — {gift['id']}",
            "callback_data": f"admin_gift_pick:{source}:{gift['id']}",
        }
        if gift.get("emoji_id"):
            button_kwargs["icon_custom_emoji_id"] = gift["emoji_id"]
        rows.append([InlineKeyboardButton(**button_kwargs)])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="<<", callback_data=f"admin_gift_list:{source}:{page - 1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text=">>", callback_data=f"admin_gift_list:{source}:{page + 1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text=BUTTON_LABELS["back"], callback_data="admin_gifts", icon_custom_emoji_id=BACK_EMOJI_ID)])
    return text, InlineKeyboardMarkup(inline_keyboard=rows)


async def send_admin_gift_order(bot: Bot, order: AdminGiftOrder) -> tuple[bool, Optional[str]]:
    try:
        await bot.send_gift(
            gift_id=order.gift_id,
            user_id=order.target_user_id,
            text=order.text or None,
            text_parse_mode=ParseMode.HTML if order.text else None,
        )
        return True, None
    except Exception as e:
        logging.exception("Failed to send Telegram gift")
        return False, str(e)


def create_admin_gift_order(
    admin_id: int,
    target_user_id: int,
    gift: dict,
    text_value: Optional[str],
    payment_mode: str,
) -> AdminGiftOrder:
    with Session(engine) as session:
        order = AdminGiftOrder(
            admin_id=admin_id,
            target_user_id=target_user_id,
            gift_id=gift["id"],
            gift_label=gift_label(gift),
            star_count=int(gift["stars"]),
            text=text_value,
            payment_mode=payment_mode,
            payload=f"gift:{uuid4().hex}",
            status="created",
            created_at=iso_now(),
        )
        session.add(order)
        session.commit()
        session.refresh(order)
        return order


def admin_referrals_text() -> str:
    with Session(engine) as session:
        reward_days = int(get_setting(session, "referral_reward_days", "3"))
        referrals = session.exec(select(Referral)).all()
        rewarded = sum(1 for ref in referrals if ref.rewarded_at)
    return (
        f"<b>{GEM_EMOJI} Управление рефералкой</b>\n\n"
        f"<b>Награда:</b> {reward_days} дн. Premium\n"
        f"<b>Всего приглашений:</b> {len(referrals)}\n"
        f"<b>Засчитано:</b> {rewarded}\n\n"
        "<i>Награда выдается, когда приглашенный проходит /start и подписку на канал.</i>"
    )


def admin_referrals_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Изменить награду", callback_data="admin_ref_set_days", icon_custom_emoji_id=RENAME_EMOJI_ID)],
        [InlineKeyboardButton(text=BUTTON_LABELS["back_to_admin"], callback_data="back_to_admin", icon_custom_emoji_id=BACK_EMOJI_ID)],
    ])


def revenue_stats_text() -> str:
    now = datetime.now()
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)
    totals = {"day_usd": 0.0, "week_usd": 0.0, "month_usd": 0.0, "day_stars": 0, "week_stars": 0, "month_stars": 0}
    with Session(engine) as session:
        payments = session.exec(select(SubscriptionPayment).where(SubscriptionPayment.status == "paid")).all()
    for payment in payments:
        paid_at = parse_datetime_safe(payment.paid_at)
        if not paid_at:
            continue
        amount = payment.amount or 0
        is_stars = payment.provider == "stars"
        for key, start in [("day", day_start), ("week", week_start), ("month", month_start)]:
            if paid_at >= start:
                if is_stars:
                    totals[f"{key}_stars"] += int(amount)
                else:
                    totals[f"{key}_usd"] += float(amount)
    return (
        f"<b>{STATISTICS_EMOJI} Доходы</b>\n\n"
        f"<b>Сегодня:</b> ${totals['day_usd']:g} / {totals['day_stars']} Stars\n"
        f"<b>7 дней:</b> ${totals['week_usd']:g} / {totals['week_stars']} Stars\n"
        f"<b>30 дней:</b> ${totals['month_usd']:g} / {totals['month_stars']} Stars"
    )


def new_users_graph_text(days: int = 7) -> str:
    buckets = []
    now = datetime.now()
    with Session(engine) as session:
        users = session.exec(select(BotUser)).all()
    for offset in range(days - 1, -1, -1):
        date = (now - timedelta(days=offset)).date()
        count = 0
        for user in users:
            registered = parse_datetime_safe(user.registered_at)
            if registered and registered.date() == date:
                count += 1
        buckets.append((date.strftime("%d.%m"), count))
    max_count = max([count for _, count in buckets] or [1])
    lines = []
    for label, count in buckets:
        bar_len = 1 if count else 0
        if max_count:
            bar_len = max(bar_len, round((count / max_count) * 10)) if count else 0
        lines.append(f"<code>{label}</code> {'█' * bar_len or '·'} {count}")
    return "<b>Новые пользователи за 7 дней:</b>\n" + "\n".join(lines)


def admin_action_logs_text() -> str:
    with Session(engine) as session:
        logs = session.exec(select(AdminActionLog).order_by(AdminActionLog.id.desc())).all()[:20]
    text = f"<b>{DOCUMENT_EMOJI} Логи действий админа</b>\n\n"
    if not logs:
        return text + "<i>Логов пока нет.</i>"
    for log in logs:
        target = f" → <code>{log.target_id}</code>" if log.target_id else ""
        details = f" · {escape(log.details)}" if log.details else ""
        text += f"• <code>{log.created_at}</code> · <code>{log.admin_id}</code> · {escape(log.action)}{target}{details}\n"
    return text


def resolve_subscription_user_id(identifier: str) -> Optional[int]:
    value = (identifier or "").strip()
    if not value:
        return None

    if value.startswith("@"):
        value = value[1:]

    if value.isdigit():
        return int(value)

    username = value.lower()
    with Session(engine) as session:
        users = session.exec(select(BotUser)).all()
        for user in users:
            if (user.username or "").lower().lstrip("@") == username:
                return user.user_id

        messages = session.exec(select(DBMessage)).all()
        for msg in messages:
            if (msg.from_username or "").lower().lstrip("@") == username:
                return msg.user_id

    return None


async def crypto_api_request(method: str, data: Optional[dict] = None) -> dict:
    if not CRYPTOBOT_TOKEN:
        raise RuntimeError("CRYPTOBOT_TOKEN is not configured")

    base_url = "https://testnet-pay.crypt.bot" if CRYPTOBOT_NETWORK == "testnet" else "https://pay.crypt.bot"
    url = f"{base_url}/api/{method}"
    headers = {
        "Crypto-Pay-API-Token": CRYPTOBOT_TOKEN,
        "Accept": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
    }
    timeout = aiohttp.ClientTimeout(total=15)

    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        if data:
            response_ctx = session.post(url, json=data)
        else:
            response_ctx = session.get(url)

        async with response_ctx as response:
            error_body = await response.text()
            status = response.status

    if status >= 400:
        if status in (401, 403):
            details = ""
            if error_body:
                try:
                    error_payload = json.loads(error_body)
                    details = error_payload.get("error") or error_payload.get("description") or error_body
                except Exception:
                    details = error_body
            network_hint = (
                "Проверьте CRYPTOBOT_TOKEN и CRYPTOBOT_NETWORK. "
                "Также проверьте Security/IP allowlist в приложении Crypto Pay. "
                "Для @CryptoBot нужен CRYPTOBOT_NETWORK=mainnet, "
                "для @CryptoTestnetBot нужен CRYPTOBOT_NETWORK=testnet."
            )
            detail_text = f" Ответ API: {details}." if details else ""
            raise RuntimeError(f"Crypto Bot отказал в доступе ({status}).{detail_text} {network_hint}")
        raise RuntimeError(f"Crypto Bot HTTP {status}: {error_body}")

    try:
        payload = json.loads(error_body)
    except json.JSONDecodeError:
        raise RuntimeError(f"Crypto Bot вернул не JSON: {error_body[:200]}")

    if not payload.get("ok"):
        raise RuntimeError(payload.get("error") or payload)

    return payload.get("result") or {}


async def create_crypto_invoice(payment_payload: str, plan_title: str, plan_days: int, price_usd: float) -> dict:
    await crypto_api_request("getMe")
    return await crypto_api_request(
        "createInvoice",
        {
            "asset": "USDT",
            "amount": f"{price_usd:.2f}",
            "description": f"{plan_title} на {plan_days} дней",
            "payload": payment_payload,
            "expires_in": 3600,
        },
    )


async def get_crypto_invoice(invoice_id: str) -> Optional[dict]:
    result = await crypto_api_request(
        "getInvoices",
        {"invoice_ids": invoice_id},
    )
    items = result.get("items") or []
    return items[0] if items else None


def business_owner_id_by_connection_id(connection_id: Optional[str]) -> Optional[int]:
    if not connection_id:
        return None
    for chat_id, entry in load_connections().items():
        if entry.get("business_connection_id") == connection_id:
            try:
                return int(chat_id)
            except ValueError:
                return None
    return None


def _profile_full_name(user) -> str:
    parts = [
        getattr(user, "first_name", None),
        getattr(user, "last_name", None),
    ]
    name = " ".join(part for part in parts if part).strip()
    return name or getattr(user, "username", None) or "Пользователь"


def _first_seen_at(session: Session, user_id: int) -> str:
    messages = session.exec(select(DBMessage).where(DBMessage.user_id == user_id)).all()
    parsed_dates = []
    for msg in messages:
        try:
            parsed_dates.append(parse_timestamp(msg.created_at))
        except Exception:
            continue

    if parsed_dates:
        return min(parsed_dates).isoformat(timespec="seconds")

    return datetime.now().isoformat(timespec="seconds")


def save_bot_user(user) -> BotUser:
    with Session(engine) as session:
        record = session.get(BotUser, user.id)
        if record is None:
            record = BotUser(
                user_id=user.id,
                username=getattr(user, "username", None),
                first_name=_profile_full_name(user),
                registered_at=_first_seen_at(session, user.id),
            )
        else:
            record.username = getattr(user, "username", None)
            record.first_name = _profile_full_name(user)

        session.add(record)
        session.commit()
        session.refresh(record)
        return record


def _format_profile_date(value: str) -> str:
    try:
        return parse_timestamp(value).strftime("%d.%m.%Y %H:%M")
    except Exception:
        return value or "неизвестно"


def profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Кастом карты",
                    callback_data="profile_custom",
                    icon_custom_emoji_id=GEM_EMOJI_ID,
                )
            ],
            [
                InlineKeyboardButton(
                    text=BUTTON_LABELS["back"],
                    callback_data="profile_back_to_menu",
                    icon_custom_emoji_id=BACK_EMOJI_ID,
                )
            ]
        ]
    )


def build_profile_caption(user, bot_user: BotUser) -> str:
    username = f"@{user.username}" if getattr(user, "username", None) else "не указан"
    registered_at = _format_profile_date(bot_user.registered_at)
    status = profile_status_text(user.id)

    return (
        f"<b>{PROFILE_EMOJI} Профиль</b>\n\n"
        f"<b>{USER_EMOJI} Ник:</b> {escape(_profile_full_name(user))}\n"
        f"<b>{GEM_EMOJI} Статус:</b> {escape(status)}\n"
        f"<b>{ID_EMOJI} ID:</b> <code>{user.id}</code>\n"
        f"<b>{PROFILE_EMOJI} User:</b> {escape(username)}\n"
        f"<b>{TIME_EMOJI} Дата регистрации:</b> <code>{escape(registered_at)}</code>"
    )


def _profile_font_path(bold: bool = False) -> Optional[str]:
    if bold:
        candidates = [
            Path("assets") / "Unbounded.ttf",
            Path("assets") / "Bahnschrift.ttf",
            Path("C:/Windows/Fonts/bahnschrift.ttf"),
            Path("C:/Windows/Fonts/segoeuib.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
            Path("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"),
        ]
    else:
        candidates = [
            Path("assets") / "Unbounded.ttf",
            Path("assets") / "Bahnschrift.ttf",
            Path("C:/Windows/Fonts/bahnschrift.ttf"),
            Path("C:/Windows/Fonts/segoeui.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
        ]

    for font_path in candidates:
        if font_path.exists():
            return str(font_path)

    return None


def _load_profile_font(size: int, bold: bool = False):
    from PIL import ImageFont

    font_path = _profile_font_path(bold)
    if font_path:
        try:
            font = ImageFont.truetype(font_path, size)
            if Path(font_path).name.lower().startswith("unbounded") and hasattr(font, "set_variation_by_axes"):
                try:
                    font.set_variation_by_axes([780 if bold else 520])
                except Exception:
                    pass
            return font
        except Exception:
            pass

    return ImageFont.load_default()


def _text_width(draw, text: str, font) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def _trim_to_width(draw, text: str, font, max_width: int) -> str:
    if _text_width(draw, text, font) <= max_width:
        return text

    suffix = "..."
    trimmed = text
    while trimmed and _text_width(draw, trimmed + suffix, font) > max_width:
        trimmed = trimmed[:-1]

    return (trimmed + suffix) if trimmed else suffix


def _fit_profile_font(draw, text: str, size: int, max_width: int, min_size: int = 22, bold: bool = False):
    for font_size in range(size, min_size - 1, -2):
        font = _load_profile_font(font_size, bold=bold)
        if _text_width(draw, text, font) <= max_width:
            return font

    return _load_profile_font(min_size, bold=bold)


def _draw_profile_text(draw, xy: tuple[int, int], text: str, font, max_width: int, fill):
    text = _trim_to_width(draw, text, font, max_width)
    x, y = xy
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        draw.text((x + dx, y + dy), text, font=font, fill=(255, 255, 255, 28))
    draw.text((x, y), text, font=font, fill=fill)


def _draw_centered_profile_text(draw, center_x: int, y: int, text: str, font, max_width: int, fill):
    text = _trim_to_width(draw, text, font, max_width)
    x = center_x - (_text_width(draw, text, font) // 2)
    _draw_profile_text(draw, (x, y), text, font, max_width, fill)


def _draw_right_profile_text(draw, right_x: int, y: int, text: str, font, max_width: int, fill):
    text = _trim_to_width(draw, text, font, max_width)
    x = right_x - _text_width(draw, text, font)
    _draw_profile_text(draw, (x, y), text, font, max_width, fill)


def _profile_initials(name: str) -> str:
    parts = [part for part in name.replace("@", " ").split() if part]
    if not parts:
        return "U"
    return "".join(part[0].upper() for part in parts[:2])


def _paste_profile_avatar(base, avatar_path: Optional[Path], name: str, box: tuple[int, int, int, int]):
    from PIL import Image, ImageDraw, ImageOps

    x, y, size, _ = box
    if avatar_path and Path(avatar_path).exists():
        avatar = Image.open(avatar_path).convert("RGBA")
        resampling = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
        avatar = ImageOps.fit(avatar, (size, size), method=resampling)
    else:
        avatar = Image.new("RGBA", (size, size), (12, 12, 12, 255))
        avatar_draw = ImageDraw.Draw(avatar)
        avatar_draw.ellipse((8, 8, size - 8, size - 8), fill=(22, 22, 22, 255), outline=(255, 255, 255, 70), width=3)
        initials = _profile_initials(name)
        font = _fit_profile_font(avatar_draw, initials, 120, size - 90, min_size=56, bold=True)
        bbox = avatar_draw.textbbox((0, 0), initials, font=font)
        avatar_draw.text(
            ((size - (bbox[2] - bbox[0])) / 2, (size - (bbox[3] - bbox[1])) / 2 - 12),
            initials,
            font=font,
            fill=(245, 245, 245, 235),
        )

    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, size, size), fill=255)
    base.paste(avatar, (x, y), mask)

    ring_draw = ImageDraw.Draw(base)
    ring_draw.ellipse((x, y, x + size, y + size), outline=(255, 255, 255, 120), width=3)


def _profile_card_path(user_id: int) -> Path:
    return MEDIA_PATH / "profile_cards" / f"profile_{user_id}.png"


def _profile_card_meta_path(user_id: int) -> Path:
    return MEDIA_PATH / "profile_cards" / f"profile_{user_id}.json"


def _file_mtime(path: Optional[Path]) -> Optional[float]:
    if path and Path(path).exists():
        return Path(path).stat().st_mtime
    return None


def _profile_card_meta(user, bot_user: BotUser, avatar_path: Optional[Path]) -> dict:
    return {
        "user_id": user.id,
        "layout_version": 6,
        "name": _profile_full_name(user),
        "username": getattr(user, "username", None),
        "status": profile_status_text(user.id),
        "card_bottom": profile_card_bottom_text(user.id),
        "registered_at": bot_user.registered_at,
        "template_mtime": _file_mtime(PROFILE_CARD_TEMPLATE),
        "font_mtime": _file_mtime(Path(_profile_font_path(True))) if _profile_font_path(True) else None,
        "avatar_mtime": _file_mtime(avatar_path),
    }


def _load_profile_card_meta(user_id: int) -> Optional[dict]:
    meta_path = _profile_card_meta_path(user_id)
    if not meta_path.exists():
        return None

    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _save_profile_card_meta(user_id: int, meta: dict):
    meta_path = _profile_card_meta_path(user_id)
    _ensure_dir(meta_path.parent)
    meta_path.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")


def get_cached_avatar_path(user_id: int) -> Optional[Path]:
    avatar_path = MEDIA_PATH / "avatars" / f"{user_id}.jpg"
    return avatar_path if avatar_path.exists() else None


async def get_profile_avatar(bot: Bot, user_id: int) -> Optional[Path]:
    cached_avatar = get_cached_avatar_path(user_id)
    if cached_avatar:
        return cached_avatar

    return await _download_user_avatar(bot, user_id)


def get_cached_profile_card(user, bot_user: BotUser, avatar_path: Optional[Path]) -> Optional[Path]:
    card_path = _profile_card_path(user.id)
    if not card_path.exists():
        return None

    current_meta = _profile_card_meta(user, bot_user, avatar_path)
    cached_meta = _load_profile_card_meta(user.id)
    if cached_meta == current_meta:
        return card_path

    return None


def generate_profile_card(user, bot_user: BotUser, avatar_path: Optional[Path]) -> Path:
    from PIL import Image, ImageDraw

    if PROFILE_CARD_TEMPLATE.exists():
        base = Image.open(PROFILE_CARD_TEMPLATE).convert("RGBA")
    else:
        base = Image.new("RGBA", (PROFILE_CARD_WIDTH, PROFILE_CARD_HEIGHT), (0, 0, 0, 255))
        fallback_draw = ImageDraw.Draw(base)
        fallback_draw.rounded_rectangle((64, 90, 1853, 989), radius=78, outline=(235, 235, 235, 210), width=3)

    width, height = base.size
    scale_x = width / PROFILE_CARD_WIDTH
    scale_y = height / PROFILE_CARD_HEIGHT
    scale = min(scale_x, scale_y)

    def sx(value: int) -> int:
        return int(value * scale_x)

    def sy(value: int) -> int:
        return int(value * scale_y)

    def ss(value: int) -> int:
        return int(value * scale)

    name = _profile_full_name(user)
    username = f"@{user.username}" if getattr(user, "username", None) else "не указан"
    registered_at = _format_profile_date(bot_user.registered_at)
    status_text = profile_card_bottom_text(user.id).upper()

    _paste_profile_avatar(
        base,
        avatar_path,
        name,
        (sx(199), sy(307), ss(485), ss(485)),
    )

    draw = ImageDraw.Draw(base, "RGBA")
    max_width = sx(570)
    text_x = sx(1040)

    covers = [
        (sx(1025), sy(403), sx(1625), sy(528)),
        (sx(1025), sy(592), sx(1625), sy(706)),
        (sx(1025), sy(772), sx(1660), sy(890)),
    ]
    for cover in covers:
        draw.rounded_rectangle(cover, radius=ss(14), fill=(0, 0, 0, 148))

    label_font = _load_profile_font(ss(24), bold=False)
    sub_font = _load_profile_font(ss(18), bold=False)

    header_name_max_width = sx(430)
    header_name_font = _fit_profile_font(draw, name, ss(34), header_name_max_width, min_size=ss(23), bold=True)
    username_text = f"USER: {username}"
    username_font = _fit_profile_font(draw, username_text, ss(32), max_width, min_size=ss(24), bold=True)
    id_font = _fit_profile_font(draw, str(user.id), ss(32), max_width, min_size=ss(24), bold=True)
    date_font = _fit_profile_font(draw, registered_at, ss(30), max_width, min_size=ss(23), bold=True)
    status_font = _fit_profile_font(draw, status_text, ss(18), max_width, min_size=ss(14), bold=False)

    _draw_right_profile_text(
        draw,
        sx(1388),
        sy(272),
        name,
        header_name_font,
        header_name_max_width,
        (255, 255, 255, 245),
    )

    _draw_profile_text(draw, (text_x, sy(430)), "USERNAME", label_font, max_width, (190, 190, 198, 230))
    _draw_profile_text(draw, (text_x, sy(470)), username_text, username_font, max_width, (255, 255, 255, 245))

    _draw_profile_text(draw, (text_x, sy(612)), "ID ПОЛЬЗОВАТЕЛЯ", label_font, max_width, (190, 190, 198, 230))
    _draw_profile_text(draw, (text_x, sy(650)), str(user.id), id_font, max_width, (255, 255, 255, 245))

    _draw_profile_text(draw, (text_x, sy(792)), "ДАТА РЕГИСТРАЦИИ", label_font, max_width, (190, 190, 198, 230))
    _draw_profile_text(draw, (text_x, sy(832)), registered_at, date_font, max_width, (255, 255, 255, 245))
    _draw_profile_text(draw, (text_x, sy(882)), status_text, status_font, max_width, (150, 150, 160, 210))

    out_dir = MEDIA_PATH / "profile_cards"
    _ensure_dir(out_dir)
    out_path = _profile_card_path(user.id)
    base.convert("RGB").save(out_path, "PNG", compress_level=2)
    _save_profile_card_meta(user.id, _profile_card_meta(user, bot_user, avatar_path))
    return out_path


async def ensure_profile_card(bot: Bot, user, bot_user: BotUser) -> Path:
    cached_avatar = get_cached_avatar_path(user.id)
    cached_card = get_cached_profile_card(user, bot_user, cached_avatar)
    if cached_card:
        return cached_card

    avatar_path = await get_profile_avatar(bot, user.id)
    cached_card = get_cached_profile_card(user, bot_user, avatar_path)
    if cached_card:
        return cached_card

    return generate_profile_card(user, bot_user, avatar_path)


def _truncate_label(text: str, max_length: int = 45) -> str:
    return text if len(text) <= max_length else text[: max_length - 3] + "..."


def build_admin_logs_keyboard(logs: list, page: int = 0) -> InlineKeyboardMarkup:
    per_page = 10
    total_pages = max(1, (len(logs) + per_page - 1) // per_page)
    page = max(0, min(page, total_pages - 1))
    page_logs = logs[page * per_page : (page + 1) * per_page]

    buttons = []
    for log in page_logs:
        author = log.from_username or log.first_name or "unknown"
        display_name = f"@{author}" if log.from_username else author
        date_short = log.created_at.split(" ")[0]
        label = f"{display_name} | {log.user_id} | {date_short}"
        buttons.append([
            InlineKeyboardButton(
                text=_truncate_label(label),
                callback_data=f"admin_log_item:{log.id}:{page}"
            )
        ])

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="<<", callback_data=f"admin_log_page:{page - 1}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(text=">>", callback_data=f"admin_log_page:{page + 1}"))
    if nav_row:
        buttons.append(nav_row)

    buttons.append([
        InlineKeyboardButton(
            text=BUTTON_LABELS["back_to_admin"],
            callback_data="back_to_admin",
            icon_custom_emoji_id=BACK_EMOJI_ID
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_admin_deleted_keyboard(deleted_records: list, page: int = 0) -> InlineKeyboardMarkup:
    per_page = 10
    total_pages = max(1, (len(deleted_records) + per_page - 1) // per_page)
    page = max(0, min(page, total_pages - 1))
    page_records = deleted_records[page * per_page : (page + 1) * per_page]

    buttons = []
    for log, msg in page_records:
        author = msg.from_username or msg.first_name or "unknown"
        display_name = f"@{author}" if msg.from_username else author
        date_short = parse_timestamp(log.deleted_at).strftime("%Y-%m-%d")
        msg_type = TYPE_LABELS.get(msg.type, msg.type.capitalize())
        label = f"{display_name} | {msg_type} | {date_short}"
        buttons.append([
            InlineKeyboardButton(
                text=_truncate_label(label),
                callback_data=f"admin_deleted_item:{log.id}:{page}"
            )
        ])

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="<<", callback_data=f"admin_deleted_page:{page - 1}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(text=">>", callback_data=f"admin_deleted_page:{page + 1}"))
    if nav_row:
        buttons.append(nav_row)

    buttons.append([
        InlineKeyboardButton(
            text=BUTTON_LABELS["back_to_admin"],
            callback_data="back_to_admin",
            icon_custom_emoji_id=BACK_EMOJI_ID
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def format_deleted_detail(log, msg) -> str:
    deleted_at = parse_timestamp(log.deleted_at).strftime("%Y-%m-%d %H:%M:%S")
    msg_type = TYPE_LABELS.get(msg.type, msg.type.capitalize())
    author = msg.from_username or msg.first_name or "unknown"
    display_name = f"@{author}" if msg.from_username else author
    content = escape(msg.content or LOG_MESSAGE_NOT_FOUND)
    
    text = (
        f"<b>{TRASH_EMOJI} Удалённое сообщение</b>\n\n"
        f"• <b>{USER_EMOJI} Пользователь: {display_name}</b>\n"
        f"• <b>{ID_EMOJI} ID: <code>{msg.user_id}</code></b>\n"
        f"• <b>{TIME_EMOJI} Тип: <i>{msg_type}</i></b>\n"
        f"• <b>{TIME_EMOJI} Удалено: <code>{deleted_at}</code></b>\n\n"
    )
    
    if msg.type == "text":
        text += f"<b>{PEN_EMOJI} Содержимое:</b>\n<blockquote><b>{content}</b></blockquote>"
    else:
        text += f"<b>{PEN_EMOJI} Содержимое:</b> <i>{content}</i>"
    
    return text

back_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text=BUTTON_LABELS["back"],
                icon_custom_emoji_id="5258236805890710909",
                callback_data="back_to_menu"
            )
        ]
    ]
)

admin_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text=BUTTON_LABELS["admin_stats"], callback_data="admin_stats", icon_custom_emoji_id="5877485980901971030"),
            InlineKeyboardButton(text=" Доходы", callback_data="admin_revenue", icon_custom_emoji_id="5877485980901971030"),
        ],
        [
            InlineKeyboardButton(text=" Пользователи", callback_data="admin_users", icon_custom_emoji_id=USER_EMOJI_ID),
            InlineKeyboardButton(text=" Подписки", callback_data="admin_subscriptions", icon_custom_emoji_id=GEM_EMOJI_ID),
        ],
        [
            InlineKeyboardButton(text=" Подарки", callback_data="admin_gifts", icon_custom_emoji_id=STARS_EMOJI_ID),
            InlineKeyboardButton(text=" Промокоды", callback_data="admin_promos", icon_custom_emoji_id=STARS_EMOJI_ID),
        ],
        [
            InlineKeyboardButton(text=" Рефералка", callback_data="admin_referrals", icon_custom_emoji_id=GEM_EMOJI_ID),
            InlineKeyboardButton(text=BUTTON_LABELS["admin_broadcast"], callback_data="admin_broadcast", icon_custom_emoji_id="5771695636411847302"),
        ],
        [
            InlineKeyboardButton(text=BUTTON_LABELS["admin_logs"], callback_data="admin_logs", icon_custom_emoji_id="5875206779196935950"),
            InlineKeyboardButton(text=BUTTON_LABELS["admin_deleted"], callback_data="admin_deleted", icon_custom_emoji_id="5327934298219624721"),
        ],
        [
            InlineKeyboardButton(text=BUTTON_LABELS["admin_manage"], callback_data="admin_manage", icon_custom_emoji_id="5776424837786374634"),
            InlineKeyboardButton(text=" Логи админов", callback_data="admin_action_logs", icon_custom_emoji_id="5875206779196935950"),
        ],
    ]
)

admin_back_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text=BUTTON_LABELS["back_to_admin"],
                callback_data="back_to_admin",
                icon_custom_emoji_id=BACK_EMOJI_ID
            )
        ]
    ]
)

def build_manage_categories_keyboard(page: int = 0) -> InlineKeyboardMarkup:
    categories_dict = load_custom_commands()
    category_list = sorted(categories_dict.keys())
    per_page = 9
    page = max(0, page)
    total_pages = max(1, (len(category_list) + per_page - 1) // per_page)
    page = min(page, total_pages - 1)
    buttons = []
    row = []

    page_categories = category_list[page * per_page:(page + 1) * per_page]
    for category in page_categories:
        count = len(categories_dict.get(category, []))
        row.append(
            InlineKeyboardButton(
                text=f"{category} ({count})",
                callback_data=f"manage_category:{short_id(category)}"
            )
        )
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text='<<', callback_data=f"manage_cat_page:{page - 1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text='>>', callback_data=f"manage_cat_page:{page + 1}"))
    if nav_buttons:
        buttons.append(nav_buttons)

    action_buttons = [InlineKeyboardButton(text="Создать категорию", callback_data="manage_add_category", icon_custom_emoji_id=PLUS_EMOJI_ID)]
    if category_list:
        action_buttons.append(InlineKeyboardButton(text="Очистить все", callback_data="manage_clear_all_categories", icon_custom_emoji_id=TRASH_EMOJI_ID))
    buttons.append(action_buttons)
    buttons.append([InlineKeyboardButton(text=BUTTON_LABELS["back_to_admin"], callback_data="back_to_admin", icon_custom_emoji_id=BACK_EMOJI_ID)])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_manage_category_keyboard(category: str, page: int = 0) -> InlineKeyboardMarkup:
    categories_dict = load_custom_commands()
    commands = categories_dict.get(category, [])
    category_key = short_id(category)
    per_page = 6
    page = max(0, page)
    total_pages = max(1, (len(commands) + per_page - 1) // per_page)
    page = min(page, total_pages - 1)
    buttons = []

    page_cmds = commands[page * per_page:(page + 1) * per_page]
    for cmd_obj in page_cmds:
        cmd_name = cmd_obj.get("name", "[пусто]")
        cmd_key = short_id(cmd_name)
        buttons.append([
            InlineKeyboardButton(
                text=cmd_name,
                callback_data=f"manage_edit_command:{category_key}:{cmd_key}",
                icon_custom_emoji_id=RENAME_EMOJI_ID
            ),
            InlineKeyboardButton(
                text="Удалить",
                callback_data=f"manage_delete_command:{category_key}:{cmd_key}",
                icon_custom_emoji_id=TRASH_EMOJI_ID
            )
        ])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text='<<', callback_data=f"manage_cmd_page:{category_key}:{page - 1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text='>>', callback_data=f"manage_cmd_page:{category_key}:{page + 1}"))
    if nav_buttons:
        buttons.append(nav_buttons)

    buttons.append([
        InlineKeyboardButton(text="Добавить команду", callback_data=f"manage_add_command:{category_key}", icon_custom_emoji_id=PLUS_EMOJI_ID),
        InlineKeyboardButton(text="Переименовать категорию", callback_data=f"manage_rename_category:{category_key}", icon_custom_emoji_id=RENAME_EMOJI_ID)
    ])
    buttons.append([
        InlineKeyboardButton(text="Удалить категорию", callback_data=f"manage_delete_category:{category_key}", icon_custom_emoji_id=TRASH_EMOJI_ID)
    ])
    buttons.append([
        InlineKeyboardButton(text="Категории", callback_data="manage_back_to_categories", icon_custom_emoji_id=BACK_EMOJI_ID)
    ])
    buttons.append([
        InlineKeyboardButton(text=BUTTON_LABELS["back_to_admin"], callback_data="back_to_admin", icon_custom_emoji_id=BACK_EMOJI_ID),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def parse_custom_command_input(raw: str) -> tuple[Optional[str], Optional[str]]:
    raw = raw.strip()
    if not raw:
        return None, None

    if "|" in raw:
        name_part, desc_part = [part.strip() for part in raw.split("|", 1)]
        name = name_part or None
        description = desc_part or None
        return name, description

    if raw.startswith("."):
        if " " in raw:
            name, desc = raw.split(" ", 1)
            return name.strip(), desc.strip() or None
        return raw, None

    return None, raw


def find_command(categories: dict, category: str, command_name: str) -> dict | None:
    return next((cmd for cmd in categories.get(category, []) if cmd.get("name") == command_name), None)


def get_manage_category_text(category: str) -> str:
    categories_dict = load_custom_commands()
    commands = categories_dict.get(category, [])
    if not commands:
        return (
            f"<b>Категория:</b> {escape(category)}\n"
            "<i>В этой категории пока нет команд.</i>\n\n"
            "Нажмите кнопку «Добавить команду», чтобы создать новую."
        )

    text = (
        f"<b>{CATEGORY_EMOJI} Категория:</b> {escape(category)}\n"
        f"<b>{COMAND_EMOJI} Команд:</b> {len(commands)}\n\n"
        "<blockquote>Нажмите на команду, чтобы отредактировать её, или используйте кнопки ниже.</blockquote>\n\n"
    )
    for cmd in commands[:10]:
        text += f"• <code>{escape(cmd.get('name', ''))}</code> — <b>{escape(cmd.get('description', ''))}</b>\n"
    if len(commands) > 10:
        text += f"<i>и ещё {len(commands) - 10} команд...</i>"
    return text


def get_time():
    return datetime.now().strftime("%d.%m %H:%M:%S")


def build_broadcast_preview(data: dict) -> str:
    text = data.get("broadcast_text") or "<i>Текст не указан</i>"
    photo = data.get("broadcast_photo")
    button_text = data.get("broadcast_button_text")
    button_url = data.get("broadcast_button_url")
    button_style = data.get("broadcast_button_style")
    segment = data.get("broadcast_segment") or "all"
    segment_title = {
        "all": "всем",
        "free": "Free",
        "premium": "Premium",
        "admins": "админам",
    }.get(segment, "всем")

    preview = f"<b>Сегмент:</b> {segment_title}\n\n{text}"
    if photo:
        preview += f"\n\n{PHOTO_EMOJI} <i>С фото</i>"
    if button_text and button_url:
        preview += f"\n\n{CLICK_EMOJI} <b>Кнопка:</b> {button_text}\n🔗 <code>{button_url}</code>"
        if button_style:
            preview += f"\n{COLOR_EMOJI} <i>Стиль:</i> {button_style}"
    return preview


def build_broadcast_keyboard(data: dict) -> InlineKeyboardMarkup:
    segment = data.get("broadcast_segment") or "all"

    def seg_button(label: str, value: str) -> InlineKeyboardButton:
        prefix = "• " if segment == value else ""
        return InlineKeyboardButton(text=f"{prefix}{label}", callback_data=f"broadcast_segment:{value}")

    buttons = [
        [InlineKeyboardButton(text="Текст", callback_data="broadcast_text", icon_custom_emoji_id="5879841310902324730")],
        [
            InlineKeyboardButton(text="Фото", callback_data="broadcast_photo", icon_custom_emoji_id="5890744068203352126"),
            InlineKeyboardButton(text="Инлайн кнопка", callback_data="broadcast_button", icon_custom_emoji_id="5884106131822875141")
        ],
        [seg_button("Всем", "all"), seg_button("Free", "free"), seg_button("Premium", "premium"), seg_button("Админам", "admins")],
        [InlineKeyboardButton(text="Отправить рассылку", callback_data="confirm_broadcast", icon_custom_emoji_id="5776375003280838798")],
        [InlineKeyboardButton(text="Отмена", callback_data="cancel_broadcast", style="danger", icon_custom_emoji_id="5258474669769497337")],
    ]

    if data.get("broadcast_photo"):
        buttons.insert(2, [InlineKeyboardButton(text="Убрать фото", callback_data="remove_broadcast_photo", icon_custom_emoji_id="5327934298219624721")])
    if data.get("broadcast_button_text") and data.get("broadcast_button_url"):
        buttons.insert(3, [InlineKeyboardButton(text="Убрать кнопку", callback_data="remove_broadcast_button", icon_custom_emoji_id="5327934298219624721")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def broadcast_button_style_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Готово", callback_data="button_style:default")],
        [InlineKeyboardButton(text="Синий", callback_data="button_style:primary", style="primary")],
        [InlineKeyboardButton(text="Зелёный", callback_data="button_style:success", style="success")],
        [InlineKeyboardButton(text="Красный", callback_data="button_style:danger", style="danger")],
    ])


def get_broadcast_user_ids(segment: str) -> list[int]:
    with Session(engine) as session:
        all_ids = get_all_known_user_ids(session)
        if segment == "admins":
            return list(ADMIN_IDS)
        if segment == "premium":
            return [
                user_id for user_id in all_ids
                if user_id in ADMIN_IDS or is_subscription_active_record(session.get(UserSubscription, user_id))
            ]
        if segment == "free":
            return [
                user_id for user_id in all_ids
                if user_id not in ADMIN_IDS and not is_subscription_active_record(session.get(UserSubscription, user_id))
            ]
        return all_ids


@dp.callback_query(F.data == "broadcast_button_style")
async def broadcast_button_style_open(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data() or {}
    preview = build_broadcast_preview(data)
    kb = broadcast_button_style_keyboard()
    try:
        await edit_message_inline(callback.message, preview, kb)
    except Exception:
        try:
            await callback.message.edit_text(preview, reply_markup=kb, parse_mode="HTML")
        except Exception:
            pass
    await callback.answer()
 


async def check_subscription(bot: Bot, user_id: int):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status not in ["left", "kicked"]
    except:
        return False


async def check_business_connection(bot: Bot, chat_id: int) -> bool:
    business_connection_id = get_connection_id(chat_id)
    if not business_connection_id:
        return False

    try:
        business_connection = await bot.get_business_connection(business_connection_id)
        if business_connection and business_connection.is_enabled:
            return True

        remove_business_connection(chat_id)
        return False
    except Exception:
        logging.exception("Error while verifying business connection")
        return False


async def check_business_permissions(bot: Bot, business_connection_id: str) -> dict:
    try:
        bc = await bot.get_business_connection(business_connection_id)
        return {
            "is_enabled": bc.is_enabled,
            "can_reply_to_messages": True,
            "can_delete_messages": True, 
            "can_manage": bc.is_enabled,
            "connection_id": bc.id
        }
    except Exception as e:
        logging.exception(f"Error checking business permissions: {e}")
        return {
            "is_enabled": False,
            "error": str(e)
        }


async def get_channel_invite_link(bot: Bot) -> str | None:
    try:
        invite = await bot.create_chat_invite_link(CHANNEL_ID)
        return invite.invite_link
    except Exception:
        try:
            invite = await bot.export_chat_invite_link(CHANNEL_ID)
            return invite.invite_link if hasattr(invite, 'invite_link') else invite
        except Exception:
            return None


async def send_limit_warning_once(bot: Bot, user_id: int, action: str, used: int, limit: int) -> None:
    key = f"{user_id}:limit:{action}:{today_key()}"
    with Session(engine) as session:
        if session.get(UserNotificationState, key):
            return
        session.add(UserNotificationState(id=key, user_id=user_id, kind=f"limit_{action}", sent_at=iso_now()))
        session.commit()

    action_text = "команд" if action == "command_view" else "сохранений"
    try:
        await bot.send_message(
            user_id,
            f"{GEM_EMOJI} <b>Лимит почти исчерпан</b>\n\n"
            f"Использовано <b>{used}/{limit}</b> {action_text} сегодня.\n"
            "<i>Premium снимает лимиты и включает приоритетную обработку.</i>",
            parse_mode="HTML",
        )
    except Exception:
        pass


async def subscription_expiry_notifier(bot: Bot):
    while True:
        try:
            now = datetime.now()
            soon = now + timedelta(hours=24)
            with Session(engine) as session:
                subs = session.exec(select(UserSubscription)).all()
                targets = []
                for sub in subs:
                    expires_at = parse_datetime_safe(sub.expires_at)
                    if not expires_at or expires_at <= now or expires_at > soon:
                        continue
                    key = f"{sub.user_id}:sub_expiring:{expires_at.date().isoformat()}"
                    if session.get(UserNotificationState, key):
                        continue
                    session.add(UserNotificationState(id=key, user_id=sub.user_id, kind="sub_expiring", sent_at=iso_now()))
                    targets.append((sub.user_id, expires_at))
                session.commit()

            for user_id, expires_at in targets:
                try:
                    await bot.send_message(
                        user_id,
                        f"{GEM_EMOJI} <b>Premium скоро закончится</b>\n\n"
                        f"Подписка действует до <code>{expires_at.strftime('%d.%m.%Y %H:%M')}</code>.\n"
                        "Продлите ее заранее, чтобы лимиты Free не вернулись.",
                        parse_mode="HTML",
                    )
                except Exception:
                    pass
        except Exception:
            logging.exception("Subscription expiry notifier failed")

        await asyncio.sleep(3600)


async def download_file(bot, file_id, folder, ext):
    file_name = f"{uuid4()}.{ext}"
    file_path = MEDIA_PATH.joinpath(folder).joinpath(file_name)

    fl = await bot.get_file(file_id)
    await bot.download_file(fl.file_path, file_path)

    return file_name


async def ensure_file_downloaded(bot: Bot, session: Session, file: File, default_ext: str = "bin"):
    if file.file_name:
        file_path = MEDIA_PATH.joinpath(file.folder).joinpath(file.file_name)
        if file_path.exists():
            return file_path

    if not file.file_id:
        return None

    if not file.file_name:
        file.file_name = f"{uuid4()}.{default_ext}"
    file_path = MEDIA_PATH.joinpath(file.folder).joinpath(file.file_name)

    try:
        fl = await bot.get_file(file.file_id)
        await bot.download_file(fl.file_path, file_path)
        session.add(file)
        session.commit()
        return file_path
    except Exception:
        return None

@dp.message(CommandStart())
async def start(message: Message):
    bot = message.bot
    logging.info(f"Received /start from chat_id={message.chat.id} user_id={(message.from_user.id if message.from_user else 'none')}")
    if not message.from_user:
        logging.warning("Start message has no from_user; ignoring.")
        return
    try:
        save_bot_user(message.from_user)
    except Exception:
        logging.exception("Failed to save bot user")

    referrer_id = None
    start_parts = (message.text or "").split(maxsplit=1)
    if len(start_parts) > 1:
        payload = start_parts[1].strip()
        if payload.startswith("ref_") and payload[4:].isdigit():
            referrer_id = int(payload[4:])
            create_referral_if_needed(referrer_id, message.from_user.id)

    try:
        sub = await check_subscription(bot, message.from_user.id)
        logging.info(f"check_subscription result: {sub}")
    except Exception as e:
        logging.exception("Error checking subscription")
        try:
            await message.reply(WARNING_SUBSCRIPTION_CHECK_TEXT + str(e))
        except Exception:
            logging.exception("Failed to reply about subscription error")
        return

    if not sub:
        invite_link = await get_channel_invite_link(bot)
        subscribe_url = invite_link or CHANNEL_URL

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=BUTTON_LABELS["subscribe"],
                        url=subscribe_url
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=BUTTON_LABELS["check_sub"],
                        callback_data="check_sub"
                    )
                ]
            ]
        )

        await message.answer(
            SUBSCRIBE_PROMPT_TEXT,
            reply_markup=kb
        )        
        return        

    with Session(engine) as session:
        reward = apply_referral_reward(session, message.from_user.id)
    if reward:
        ref_user_id, reward_days = reward
        try:
            await bot.send_message(
                ref_user_id,
                f"{GEM_EMOJI} <b>Реферал активирован</b>\n\n"
                f"Вам начислено <b>{reward_days} дн.</b> Premium.",
                parse_mode="HTML",
            )
        except Exception:
            pass

    text = START_TEXT

    try:
        if PHOTO_URL:
            await message.bot.send_photo(
                chat_id=message.chat.id,
                photo=PHOTO_URL,
                caption=text,
                reply_markup=main_kb
            )
        else:
            raise ValueError("PHOTO_URL is not configured")
    except Exception:
        logging.exception("Failed to send main menu photo, falling back to text")
        try:
            await message.answer(text, reply_markup=main_kb, parse_mode="HTML")
        except Exception:
            logging.exception("Failed to send main menu to user")


@dp.callback_query(F.data == "check_business")
async def check_business_callback(query: CallbackQuery, bot: Bot):
    chat = query.message.chat
    try:
        business_connection_id = get_connection_id(chat.id)
        if not business_connection_id:
            await query.answer(NOT_CONNECTED_BUSINESS_TEXT, show_alert=True)
            return

        perms = await check_business_permissions(bot, business_connection_id)
        
        if not perms.get("is_enabled"):
            await query.answer(
                BUSINESS_CONNECT_UNAVAILABLE_TEXT + perms.get("error", UNKNOWN_ERROR_TEXT),
                show_alert=True
            )
            return

        connected = await check_business_connection(bot, chat.id)
        if connected:
            status_text = BUSINESS_CONNECTED_TEXT
        else:
            status_text = NOT_CONNECTED_BUSINESS_TEXT
        
        await query.answer(status_text, show_alert=True)
    except Exception as e:
        logging.exception("Error in check_business_callback")
        await query.answer(WARNING_CONNECTION_CHECK_TEXT + str(e), show_alert=True)


@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery, bot: Bot):
    sub = await check_subscription(bot, callback.from_user.id)

    if not sub:
        await callback.answer(
            NOT_SUBSCRIBED_ALERT,
            show_alert=True
        )
        return

    await callback.answer(SUBSCRIPTION_CONFIRMED_TEXT)

    with Session(engine) as session:
        reward = apply_referral_reward(session, callback.from_user.id)
    if reward:
        ref_user_id, reward_days = reward
        try:
            await callback.bot.send_message(
                ref_user_id,
                f"{GEM_EMOJI} <b>Реферал активирован</b>\n\n"
                f"Вам начислено <b>{reward_days} дн.</b> Premium.",
                parse_mode="HTML",
            )
        except Exception:
            pass

    if not await edit_main_menu_message(callback.message):
        await callback.answer("Не удалось обновить главное меню", show_alert=True)


async def edit_main_menu_message(message) -> bool:
    if PHOTO_URL:
        try:
            await message.edit_media(
                media=InputMediaPhoto(
                    media=PHOTO_URL,
                    caption=START_TEXT,
                    parse_mode="HTML",
                ),
                reply_markup=main_kb,
            )
            return True
        except Exception:
            try:
                await message.bot.send_photo(
                    chat_id=message.chat.id,
                    photo=PHOTO_URL,
                    caption=START_TEXT,
                    reply_markup=main_kb,
                    parse_mode="HTML",
                )
                try:
                    await message.delete()
                except Exception:
                    pass
                return True
            except Exception:
                pass

    return await edit_message_inline(message, START_TEXT, main_kb)


async def edit_admin_menu_message(message) -> bool:
    if ADMIN_URL:
        try:
            await message.edit_media(
                media=InputMediaPhoto(
                    media=ADMIN_URL,
                    caption=ADMIN_PANEL_TEXT,
                    parse_mode="HTML",
                ),
                reply_markup=admin_kb,
            )
            return True
        except Exception:
            try:
                await message.bot.send_photo(
                    chat_id=message.chat.id,
                    photo=ADMIN_URL,
                    caption=ADMIN_PANEL_TEXT,
                    reply_markup=admin_kb,
                    parse_mode="HTML",
                )
                try:
                    await message.delete()
                except Exception:
                    pass
                return True
            except Exception:
                pass

    return await edit_message_inline(message, ADMIN_PANEL_TEXT, admin_kb)


async def edit_admin_subscriptions_message(message) -> bool:
    text, keyboard = admin_subscriptions_text()
    if ADMIN_URL:
        try:
            await message.edit_media(
                media=InputMediaPhoto(
                    media=ADMIN_URL,
                    caption=text,
                    parse_mode="HTML",
                ),
                reply_markup=keyboard,
            )
            return True
        except Exception:
            try:
                await message.bot.send_photo(
                    chat_id=message.chat.id,
                    photo=ADMIN_URL,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )
                try:
                    await message.delete()
                except Exception:
                    pass
                return True
            except Exception:
                pass

    return await edit_message_inline(message, text, keyboard)


async def send_admin_subscriptions_message(message: Message, prefix: Optional[str] = None) -> None:
    text, keyboard = admin_subscriptions_text()
    if prefix:
        text = f"{prefix}\n\n{text}"

    if ADMIN_URL:
        try:
            await message.answer_photo(
                photo=ADMIN_URL,
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
            return
        except Exception:
            pass

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


def onboarding_text() -> str:
    return (
        f"<b>{GEM_EMOJI} Быстрый старт Shell Save</b>\n\n"
        f"<b>1.</b> Подпишитесь на канал и нажмите «Проверить».\n"
        f"<b>2.</b> Подключите Telegram Business к боту.\n"
        f"<b>3.</b> Откройте «Проверить подключение» и убедитесь, что всё активно.\n"
        f"<b>4.</b> Используйте «Профиль», «Статистика», «Избранное» и Premium.\n\n"
        "<i>Premium снимает лимиты, включает приоритетную обработку и кастом профиль-карты.</i>"
    )


def referral_text(user_id: int) -> str:
    bot_name = (BOT_USERNAME or "").lstrip("@")
    link = f"https://t.me/{bot_name}?start=ref_{user_id}" if bot_name else f"ref_{user_id}"
    with Session(engine) as session:
        reward_days = int(get_setting(session, "referral_reward_days", "3"))
        referrals = session.exec(select(Referral).where(Referral.referrer_id == user_id)).all()
        rewarded = sum(1 for ref in referrals if ref.rewarded_at)
    return (
        f"<b>{GEM_EMOJI} Реферальная система</b>\n\n"
        f"<b>Награда:</b> {reward_days} дн. Premium\n"
        f"<b>Приглашено:</b> {len(referrals)}\n"
        f"<b>Засчитано:</b> {rewarded}\n\n"
        f"<b>Ваша ссылка:</b>\n<code>{escape(link)}</code>"
    )


def format_saved_message_line(msg: DBMessage) -> str:
    author = msg.from_username or msg.first_name or "unknown"
    author = f"@{author}" if msg.from_username and not str(author).startswith("@") else author
    return f"{msg.id} · {msg.type} · {author}"


def favorites_keyboard(user_id: int) -> InlineKeyboardMarkup:
    with Session(engine) as session:
        favorites = session.exec(
            select(FavoriteMessage).where(FavoriteMessage.owner_id == user_id).order_by(FavoriteMessage.id.desc())
        ).all()[:8]
        rows = []
        for favorite in favorites:
            msg = session.get(DBMessage, favorite.db_message_id)
            if not msg:
                continue
            rows.append([
                InlineKeyboardButton(
                    text=format_saved_message_line(msg),
                    callback_data=f"fav_del:{favorite.id}",
                    icon_custom_emoji_id=TRASH_EMOJI_ID,
                )
            ])
    rows.append([InlineKeyboardButton(text="Последние сохранения", callback_data="favorites_recent", icon_custom_emoji_id="5985616167740379273")])
    rows.append([InlineKeyboardButton(text=BUTTON_LABELS["back"], callback_data="back_to_menu", icon_custom_emoji_id=BACK_EMOJI_ID)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def recent_saves_keyboard(user_id: int) -> InlineKeyboardMarkup:
    with Session(engine) as session:
        messages = session.exec(
            select(DBMessage).where((DBMessage.owner_id == user_id) | (DBMessage.user_id == user_id)).order_by(DBMessage.id.desc())
        ).all()[:8]
        favorite_ids = {
            fav.db_message_id
            for fav in session.exec(select(FavoriteMessage).where(FavoriteMessage.owner_id == user_id)).all()
        }
    rows = []
    for msg in messages:
        is_fav = msg.id in favorite_ids
        rows.append([
            InlineKeyboardButton(
                text=("В избранном · " if is_fav else "В избранное · ") + format_saved_message_line(msg),
                callback_data=f"fav_add:{msg.id}",
                icon_custom_emoji_id=GEM_EMOJI_ID if is_fav else PLUS_EMOJI_ID,
            )
        ])
    rows.append([InlineKeyboardButton(text=BUTTON_LABELS["back"], callback_data="favorites", icon_custom_emoji_id=BACK_EMOJI_ID)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@dp.callback_query(F.data == "profile")
async def profile_menu(callback: CallbackQuery):
    if not callback.message:
        await callback.answer("Не удалось открыть профиль", show_alert=True)
        return

    await callback.answer("Открываю профиль...")

    try:
        bot_user = save_bot_user(callback.from_user)
        profile_card_path = await ensure_profile_card(callback.bot, callback.from_user, bot_user)
        caption = build_profile_caption(callback.from_user, bot_user)
        keyboard = profile_keyboard()
        media = InputMediaPhoto(
            media=FSInputFile(profile_card_path),
            caption=caption,
            parse_mode="HTML",
        )

        try:
            await callback.message.edit_media(media=media, reply_markup=keyboard)
        except Exception:
            logging.exception("Failed to edit message media for profile card")
            await callback.message.answer_photo(
                photo=FSInputFile(profile_card_path),
                caption=caption,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

    except ImportError:
        logging.exception("Pillow is not installed")
        await callback.message.answer("Для профиль-карты нужно установить Pillow")
    except Exception:
        logging.exception("Failed to build profile menu")
        await callback.message.answer("Не удалось открыть профиль")


@dp.callback_query(F.data == "profile_back_to_menu")
async def profile_back_to_menu(callback: CallbackQuery):
    if not callback.message:
        await callback.answer("Не удалось открыть меню", show_alert=True)
        return

    if not await edit_main_menu_message(callback.message):
        await callback.answer("Не удалось обновить главное меню", show_alert=True)
        return

    await callback.answer()


@dp.callback_query(F.data == "profile_custom")
async def profile_custom(callback: CallbackQuery, state: FSMContext):
    if not is_premium_user(callback.from_user.id):
        await callback.answer("Кастом профиль-карты доступен в Premium", show_alert=True)
        return
    await state.set_state(ProfileCustomState.waiting_for_title)
    await edit_message_inline(
        callback.message,
        f"<b>{GEM_EMOJI} Кастом профиль-карты</b>\n\n"
        "Отправьте короткую подпись для нижней строки карты.\n\n"
        "Пример:\n<code>OWNER SHELL SAVE</code>\n\n"
        "<i>До 28 символов. Чтобы сбросить, отправьте: reset</i>",
        profile_keyboard(),
    )
    await callback.answer()


@dp.message(StateFilter(ProfileCustomState.waiting_for_title))
async def profile_custom_save(message: Message, state: FSMContext):
    if not message.from_user or not is_premium_user(message.from_user.id):
        await state.clear()
        return

    value = (message.text or "").strip()
    if not value:
        await message.answer("Отправьте текст подписи или <code>reset</code>.", parse_mode="HTML")
        return
    if value.lower() != "reset" and len(value) > 28:
        await message.answer("Слишком длинно. Нужно до 28 символов.", parse_mode="HTML")
        return

    with Session(engine) as session:
        settings = get_profile_settings(session, message.from_user.id)
        settings.card_title = None if value.lower() == "reset" else value
        settings.updated_at = iso_now()
        session.add(settings)
        session.commit()

    await state.clear()
    await message.answer(
        f"{GEM_EMOJI} <b>Профиль-карта обновлена.</b>\n\n"
        "<i>Откройте профиль заново, карта перегенерируется.</i>",
        parse_mode="HTML",
    )


@dp.callback_query(F.data == "onboarding")
async def onboarding(callback: CallbackQuery):
    await edit_message_inline(callback.message, onboarding_text(), back_kb)
    await callback.answer()


@dp.callback_query(F.data == "referral")
async def referral_menu(callback: CallbackQuery):
    await edit_message_inline(
        callback.message,
        referral_text(callback.from_user.id),
        InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=BUTTON_LABELS["back"], callback_data="back_to_menu", icon_custom_emoji_id=BACK_EMOJI_ID)]
        ]),
    )
    await callback.answer()


@dp.callback_query(F.data == "promo_enter")
async def promo_enter(callback: CallbackQuery, state: FSMContext):
    await state.set_state(UserPromoState.waiting_for_code)
    await edit_message_inline(
        callback.message,
        f"<b>{STARS_EMOJI} Промокод</b>\n\n"
        "Отправьте промокод одним сообщением.\n\n"
        "<i>Промокод может дать Premium-дни или скидку на следующую покупку.</i>",
        back_kb,
    )
    await callback.answer()


@dp.message(StateFilter(UserPromoState.waiting_for_code))
async def promo_apply(message: Message, state: FSMContext):
    if not message.from_user:
        return
    with Session(engine) as session:
        ok, text = redeem_promo_code(session, message.from_user.id, message.text or "")
    await state.clear()
    await message.answer(text, parse_mode="HTML")


@dp.callback_query(F.data == "my_stats")
async def my_stats(callback: CallbackQuery):
    await edit_message_inline(
        callback.message,
        user_stats_text(callback.from_user.id),
        InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=BUTTON_LABELS["back"], callback_data="back_to_menu", icon_custom_emoji_id=BACK_EMOJI_ID)]
        ]),
    )
    await callback.answer()


@dp.callback_query(F.data == "favorites")
async def favorites(callback: CallbackQuery):
    text = (
        f"<b>{GEM_EMOJI} Избранное</b>\n\n"
        "Здесь важные сохранения. Нажмите на запись, чтобы убрать ее из избранного."
    )
    await edit_message_inline(callback.message, text, favorites_keyboard(callback.from_user.id))
    await callback.answer()


@dp.callback_query(F.data == "favorites_recent")
async def favorites_recent(callback: CallbackQuery):
    text = (
        f"<b>{GEM_EMOJI} Последние сохранения</b>\n\n"
        "Нажмите на запись, чтобы добавить ее в избранное."
    )
    await edit_message_inline(callback.message, text, recent_saves_keyboard(callback.from_user.id))
    await callback.answer()


@dp.callback_query(F.data.startswith("fav_add:"))
async def favorite_add(callback: CallbackQuery):
    msg_id = int(callback.data.split(":", 1)[1])
    with Session(engine) as session:
        exists = session.exec(
            select(FavoriteMessage).where(
                (FavoriteMessage.owner_id == callback.from_user.id) & (FavoriteMessage.db_message_id == msg_id)
            )
        ).first()
        if not exists:
            session.add(FavoriteMessage(owner_id=callback.from_user.id, db_message_id=msg_id, created_at=iso_now()))
            session.commit()
    await edit_message_inline(callback.message, f"<b>{GEM_EMOJI} Последние сохранения</b>", recent_saves_keyboard(callback.from_user.id))
    await callback.answer("Добавлено в избранное")


@dp.callback_query(F.data.startswith("fav_del:"))
async def favorite_delete(callback: CallbackQuery):
    fav_id = int(callback.data.split(":", 1)[1])
    with Session(engine) as session:
        fav = session.get(FavoriteMessage, fav_id)
        if fav and fav.owner_id == callback.from_user.id:
            session.delete(fav)
            session.commit()
    await edit_message_inline(callback.message, f"<b>{GEM_EMOJI} Избранное</b>", favorites_keyboard(callback.from_user.id))
    await callback.answer("Убрано")


@dp.callback_query(F.data == "subscription")
async def subscription_menu(callback: CallbackQuery):
    text = subscription_status_text(callback.from_user.id)
    await edit_message_inline(callback.message, text, subscription_keyboard())
    await callback.answer()


@dp.callback_query(F.data == "subscription_buy")
async def subscription_buy(callback: CallbackQuery):
    with Session(engine) as session:
        plans = get_active_plans(session)

    if not plans:
        await callback.answer("Активных тарифов пока нет", show_alert=True)
        return

    text = (
        f"<b>{GEM_EMOJI} Выберите тариф</b>\n\n"
        "<i>После оплаты подписка включится автоматически.</i>"
    )
    await edit_message_inline(callback.message, text, subscription_plans_keyboard(plans))
    await callback.answer()


@dp.callback_query(F.data.startswith("subscription_plan:"))
async def subscription_plan(callback: CallbackQuery):
    plan_id = int(callback.data.split(":", 1)[1])
    with Session(engine) as session:
        plan = session.get(SubscriptionPlan, plan_id)
        discount = get_active_discount(session, callback.from_user.id)

    if not plan or not plan.is_active:
        await callback.answer("Тариф недоступен", show_alert=True)
        return

    discount_percent = discount.discount_percent if discount else 0
    crypto_price = apply_discount_amount(plan.price_usd, discount_percent)
    stars_price = apply_discount_stars(plan.stars, discount_percent)
    discount_text = f"\n<b>Скидка:</b> {discount_percent}% по промокоду\n" if discount_percent else ""
    text = (
        f"<b>{GEM_EMOJI} {escape(plan.title)}</b>\n\n"
        f"<b>Срок:</b> {plan.days} дней\n"
        f"<b>{CRYPTOBOT_EMOJI} Crypto Bot:</b> ${crypto_price:g}\n"
        f"<b>{STARS_EMOJI} Telegram Stars:</b> {stars_price} Stars\n"
        f"{discount_text}\n"
        "<i>Выберите способ оплаты.</i>"
    )
    await edit_message_inline(callback.message, text, subscription_payment_keyboard(plan.id))
    await callback.answer()


@dp.callback_query(F.data.startswith("sub_pay_stars:"))
async def subscription_pay_stars(callback: CallbackQuery):
    plan_id = int(callback.data.split(":", 1)[1])
    with Session(engine) as session:
        plan = session.get(SubscriptionPlan, plan_id)
        if not plan or not plan.is_active:
            await callback.answer("Тариф недоступен", show_alert=True)
            return
        if plan.stars <= 0:
            await callback.answer("Для тарифа не указана цена в Stars", show_alert=True)
            return
        plan_title = plan.title
        plan_days = plan.days
        payment = create_subscription_payment(session, callback.from_user.id, plan, "stars")
        plan_stars = int(payment.amount)
        payment_payload = payment.payload

    await callback.bot.send_invoice(
        chat_id=callback.from_user.id,
        title=f"{plan_title} на {plan_days} дней",
        description="Premium-подписка Shell Save",
        payload=payment_payload,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=plan_title, amount=plan_stars)],
    )
    await callback.answer("Счет Stars отправлен")


@dp.callback_query(F.data.startswith("sub_pay_crypto:"))
async def subscription_pay_crypto(callback: CallbackQuery):
    if not CRYPTOBOT_TOKEN:
        await callback.answer("Crypto Bot не настроен: добавьте CRYPTOBOT_TOKEN в .env", show_alert=True)
        return

    plan_id = int(callback.data.split(":", 1)[1])
    with Session(engine) as session:
        plan = session.get(SubscriptionPlan, plan_id)
        if not plan or not plan.is_active:
            await callback.answer("Тариф недоступен", show_alert=True)
            return
        if plan.price_usd <= 0:
            await callback.answer("Для тарифа не указана цена в USD", show_alert=True)
            return
        plan_title = plan.title
        plan_days = plan.days
        payment = create_subscription_payment(session, callback.from_user.id, plan, "crypto")
        plan_price_usd = float(payment.amount)
        payment_id = payment.id
        payment_payload = payment.payload

    try:
        invoice = await create_crypto_invoice(payment_payload, plan_title, plan_days, plan_price_usd)
    except Exception as e:
        error_text = str(e).lower()
        if "403" in error_text or "forbidden" in error_text:
            logging.warning("Crypto Bot invoice failed: %s", e)
            alert_text = "Crypto Bot отклонил токен. Проверь CRYPTOBOT_TOKEN в .env."
        else:
            logging.exception("Failed to create Crypto Bot invoice")
            alert_text = "Не удалось создать счет Crypto Bot. Подробности в консоли."
        await callback.answer(alert_text, show_alert=True)
        return

    invoice_id = str(invoice.get("invoice_id") or "")
    pay_url = invoice.get("pay_url") or invoice.get("bot_invoice_url") or invoice.get("mini_app_invoice_url")
    with Session(engine) as session:
        saved_payment = session.get(SubscriptionPayment, payment_id)
        if saved_payment:
            saved_payment.invoice_id = invoice_id
            session.add(saved_payment)
            session.commit()

    crypto_rows = []
    if pay_url:
        crypto_rows.append([InlineKeyboardButton(text="Открыть оплату", url=pay_url)])
    crypto_rows.append([InlineKeyboardButton(text="Проверить оплату", callback_data=f"sub_check_crypto:{payment_id}")])
    crypto_rows.append([InlineKeyboardButton(text=BUTTON_LABELS["back"], callback_data=f"subscription_plan:{plan_id}")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=crypto_rows)
    text = (
        f"<b>{CRYPTOBOT_EMOJI} Оплата Crypto Bot</b>\n\n"
        f"<b>Тариф:</b> {escape(plan_title)}\n"
        f"<b>Сумма:</b> ${plan_price_usd:g} USDT\n\n"
        "<i>После оплаты нажмите «Проверить оплату».</i>"
    )
    await edit_message_inline(callback.message, text, keyboard)
    await callback.answer()


@dp.callback_query(F.data.startswith("sub_check_crypto:"))
async def subscription_check_crypto(callback: CallbackQuery):
    payment_id = int(callback.data.split(":", 1)[1])
    with Session(engine) as session:
        payment = session.get(SubscriptionPayment, payment_id)
        plan = session.get(SubscriptionPlan, payment.plan_id) if payment else None
        if payment:
            payment_user_id = payment.user_id
            payment_status = payment.status
            payment_invoice_id = payment.invoice_id
        else:
            payment_user_id = None
            payment_status = None
            payment_invoice_id = None

    if not payment or not plan or payment_user_id != callback.from_user.id:
        await callback.answer("Платеж не найден", show_alert=True)
        return
    if payment_status == "paid":
        await callback.answer("Подписка уже активна", show_alert=True)
        return
    if not payment_invoice_id:
        await callback.answer("У платежа нет invoice_id", show_alert=True)
        return

    try:
        invoice = await get_crypto_invoice(payment_invoice_id)
    except Exception as e:
        logging.exception("Failed to check Crypto Bot invoice")
        await callback.answer(f"Не удалось проверить оплату: {e}", show_alert=True)
        return

    if not invoice or invoice.get("status") != "paid":
        await callback.answer("Оплата пока не найдена", show_alert=True)
        return

    with Session(engine) as session:
        payment = session.get(SubscriptionPayment, payment_id)
        plan = session.get(SubscriptionPlan, payment.plan_id)
        activate_subscription_payment(session, payment, plan, invoice_id=str(invoice.get("invoice_id") or payment_invoice_id))

    await edit_message_inline(callback.message, subscription_status_text(callback.from_user.id), subscription_keyboard())
    await callback.answer("Подписка активирована")


@dp.pre_checkout_query()
async def subscription_pre_checkout(query: PreCheckoutQuery):
    if query.invoice_payload.startswith("gift:"):
        with Session(engine) as session:
            order = session.exec(
                select(AdminGiftOrder).where(AdminGiftOrder.payload == query.invoice_payload)
            ).first()
        if not order or order.admin_id != query.from_user.id or order.status != "pending_payment":
            await query.answer(ok=False, error_message="Заказ подарка не найден")
            return
        await query.answer(ok=True)
        return

    if not query.invoice_payload.startswith("sub:"):
        await query.answer(ok=False, error_message="Неверный платеж")
        return
    await query.answer(ok=True)


@dp.message(F.successful_payment)
async def subscription_successful_payment(message: Message):
    payment_info = message.successful_payment
    payload = payment_info.invoice_payload

    if payload.startswith("gift:"):
        with Session(engine) as session:
            order = session.exec(select(AdminGiftOrder).where(AdminGiftOrder.payload == payload)).first()
            if not order or order.admin_id != message.from_user.id:
                await message.answer("Платеж получен, но заказ подарка не найден. Напишите администратору.")
                return
            order.status = "paid"
            order.paid_at = iso_now()
            session.add(order)
            session.commit()
            session.refresh(order)

        ok, error = await send_admin_gift_order(message.bot, order)
        with Session(engine) as session:
            saved = session.get(AdminGiftOrder, order.id)
            if saved:
                saved.status = "sent" if ok else "failed"
                saved.error = error
                saved.sent_at = iso_now() if ok else None
                session.add(saved)
                session.commit()
        if ok:
            log_admin_action(message.from_user.id, "send_gift_invoice", order.target_user_id, f"{order.gift_label} {order.gift_id}")
            await message.answer(
                f"{STARS_EMOJI} <b>Подарок оплачен и отправлен</b>\n\n"
                f"<b>Получатель:</b> <code>{order.target_user_id}</code>\n"
                f"<b>Подарок:</b> {escape(order.gift_label)}",
                parse_mode="HTML",
            )
        else:
            await message.answer(
                f"<b>{CROSS_EMOJI} Оплата прошла, но подарок не отправился</b>\n\n"
                f"<b>Ошибка:</b> <code>{escape(error or 'unknown')}</code>",
                parse_mode="HTML",
            )
        return

    with Session(engine) as session:
        payment = session.exec(
            select(SubscriptionPayment).where(SubscriptionPayment.payload == payload)
        ).first()
        plan = session.get(SubscriptionPlan, payment.plan_id) if payment else None
        if not payment or not plan:
            await message.answer("Платеж получен, но тариф не найден. Напишите администратору.")
            return
        plan_title = plan.title
        plan_days = plan.days

        activate_subscription_payment(
            session,
            payment,
            plan,
            invoice_id=getattr(payment_info, "telegram_payment_charge_id", None),
        )

    await message.answer(
        "✅ <b>Подписка активирована</b>\n\n"
        f"Тариф: <b>{escape(plan_title)}</b>\n"
        f"Срок: <b>{plan_days} дней</b>",
        parse_mode="HTML",
    )


@dp.business_connection()
async def business_connection_handler(business_connection: BusinessConnection, bot: Bot):
    try:
        if getattr(business_connection, "is_enabled", True):
            add_business_connection(
                business_connection.user_chat_id,
                business_connection.id,
                added_by=business_connection.user.id
            )

            await bot.send_message(
                business_connection.user_chat_id,
                BUSINESS_CONNECTED_NOTIFICATION_TEXT
            )
        else:
            try:
                remove_business_connection(business_connection.user_chat_id)
            except Exception:
                pass

            await bot.send_message(
                business_connection.user_chat_id,
                BUSINESS_DISCONNECTED_NOTIFICATION_TEXT
            )
    except Exception:
        logging.exception("Failed to handle business connection event")


@dp.callback_query(F.data == "guide")
async def guide(callback: CallbackQuery):
    text = GUIDE_TEXT
    
    guide_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=" iPhone", url=IOS_LINK, icon_custom_emoji_id="5818920837645867167"),
            InlineKeyboardButton(text=" Android", url=ANDROID_LINK, icon_custom_emoji_id="5260721826723549165"),
        ],
        [
            InlineKeyboardButton(text=BUTTON_LABELS["back"], icon_custom_emoji_id="5258236805890710909", callback_data="back_to_menu")
        ]
    ])

    try:
        await callback.message.edit_caption(
            caption=text,
            reply_markup=guide_kb,
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.edit_text(
            text=text,
            reply_markup=guide_kb,
            parse_mode="HTML"
        )
    await callback.answer()


@dp.callback_query(F.data == "features")
async def features(callback: CallbackQuery):
    text = FEATURES_TEXT
    
    try:
        await callback.message.edit_caption(
            caption=text,
            reply_markup=back_kb,
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.edit_text(
            text=text,
            reply_markup=back_kb,
            parse_mode="HTML"
        )
    await callback.answer()


@dp.callback_query(F.data == "help_menu")
async def help_menu(callback: CallbackQuery):
    info = await callback.bot.get_me()
    text = get_help_caption()
    kb = build_help_keyboard(page=0, username=info.username)
    try:
        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=BUTTON_LABELS["back"],
                callback_data="back_to_menu",
                icon_custom_emoji_id=BACK_EMOJI_ID
            )
        ])
    except Exception:
        pass

    try:
        await callback.message.edit_caption(
            caption=text,
            reply_markup=kb,
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.edit_text(
            text=text,
            reply_markup=kb,
            parse_mode="HTML"
        )
    await callback.answer()


@dp.callback_query(F.data == "commands_menu")
async def commands_menu(callback: CallbackQuery):
    categories = load_custom_commands()
    if not categories:
        await callback.answer("Категории не найдены", show_alert=True)
        return
    rows = []
    row = []
    for i, category in enumerate(sorted(categories.keys())):
        count = len(categories.get(category, []))
        row.append(InlineKeyboardButton(text=f"{category} ({count})", callback_data=f"cmdm_category:{short_id(category)}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    rows.append([InlineKeyboardButton(text=BUTTON_LABELS["back"], callback_data="back_to_menu", icon_custom_emoji_id=BACK_EMOJI_ID)])

    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    caption = f"{CATEGORY_EMOJI} <b>Категории команд</b>\n\nВыберите категорию"
    if not await edit_message_inline(callback.message, caption, kb):
        await callback.answer("Не удалось обновить меню команд", show_alert=True)
        return
    await callback.answer()


@dp.callback_query(F.data.startswith("cmdm_cat_page:"))
async def cmdm_cat_page(call: CallbackQuery):
    try:
        parts = call.data.split(":", 1)
        page = int(parts[1]) if len(parts) > 1 else 0
    except Exception:
        page = 0

    categories_dict = load_custom_commands()
    categories = sorted(categories_dict.keys())
    per_page = 9
    total_pages = max(1, (len(categories) + per_page - 1) // per_page)
    page = max(0, min(page, total_pages - 1))
    page_categories = categories[page * per_page:(page + 1) * per_page]

    rows = []
    row = []
    for category in page_categories:
        count = len(categories_dict.get(category, []))
        row.append(InlineKeyboardButton(text=f"{category} ({count})", callback_data=f"cmdm_category:{short_id(category)}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text='<<', callback_data=f'cmdm_cat_page:{page - 1}'))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text='>>', callback_data=f'cmdm_cat_page:{page + 1}'))
    if nav:
        rows.append(nav)

    rows.append([InlineKeyboardButton(text=BUTTON_LABELS["back"], callback_data="back_to_menu", icon_custom_emoji_id=BACK_EMOJI_ID)])

    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    caption = f"<b>Категории команд</b> — страница {page+1}/{total_pages}\n\nВыберите категорию"
    if not await edit_message_inline(call.message, caption, kb):
        await call.answer("Не удалось обновить меню категорий", show_alert=True)
        return
    await call.answer()


@dp.callback_query(F.data.startswith("cmdm_category:"))
async def cmdm_category(call: CallbackQuery):
    category_key = call.data.split(":", 1)[1]
    category = resolve_category_key(category_key)
    if not category:
        logging.error(f"cmdm_category: failed to resolve category from {call.data}")
        await call.answer("Неверная категория", show_alert=True)
        return

    logging.info(f"cmdm_category called with data={call.data} category={category} category_key={category_key}")
    cats = load_custom_commands()
    logging.info(f"Available categories: {list(cats.keys())}")
    cmds = cats.get(category, [])
    if not cmds:
        logging.warning(f"Category '{category}' has no commands or not found")
        await call.answer("В категории нет команд", show_alert=True)
        return
    per_page = 9
    page = 0
    try:
        pass
    except Exception:
        pass
    total_pages = max(1, (len(cmds) + per_page - 1) // per_page)
    page = max(0, min(page, total_pages - 1))
    page_cmds = cmds[page * per_page:(page + 1) * per_page]
    rows = []
    row = []
    category_key = short_id(category)
    for cmd in page_cmds:
        name = cmd.get("name")
        row.append(InlineKeyboardButton(text=name, callback_data=f"cmdm_cmd:{category_key}:{short_id(name)}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text='<<', callback_data=f'cmdm_cmd_page:{page - 1}:{category_key}'))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text='>>', callback_data=f'cmdm_cmd_page:{page + 1}:{category_key}'))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text=BUTTON_LABELS["back"], callback_data="cmdm_back")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    caption = f"<b>Категория:</b> {escape(category)} — страница {page+1}/{total_pages}\n\nВыберите команду"
    if not await edit_message_inline(call.message, caption, kb):
        await call.answer("Не удалось обновить список команд", show_alert=True)
        return
    await call.answer()


@dp.callback_query(F.data.startswith("cmdm_cmd_page:"))
async def cmdm_cmd_page(call: CallbackQuery):
    try:
        parts = call.data.split(":", 2)
        page = int(parts[1]) if len(parts) > 1 else 0
        category_key = parts[2] if len(parts) > 2 else None
        category = resolve_category_key(category_key) if category_key else None
    except Exception:
        await call.answer()
        return
    cats = load_custom_commands()
    cmds = cats.get(category, []) if category else []
    per_page = 9
    total_pages = max(1, (len(cmds) + per_page - 1) // per_page)
    page = max(0, min(page, total_pages - 1))
    page_cmds = cmds[page * per_page:(page + 1) * per_page]
    rows = []
    row = []
    category_key = short_id(category) if category else ""
    for cmd in page_cmds:
        name = cmd.get("name")
        row.append(InlineKeyboardButton(text=name, callback_data=f"cmdm_cmd:{category_key}:{short_id(name)}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text='<<', callback_data=f'cmdm_cmd_page:{page - 1}:{category_key}'))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text='>>', callback_data=f'cmdm_cmd_page:{page + 1}:{category_key}'))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text=BUTTON_LABELS["back"], callback_data="cmdm_back")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    caption = f"<b>Категория:</b> {escape(category)} — страница {page+1}/{total_pages}\n\nВыберите команду"
    if not await edit_message_inline(call.message, caption, kb):
        await call.answer("Не удалось обновить список команд", show_alert=True)
        return
    await call.answer()

@dp.callback_query(F.data.startswith("cmdm_cmd:"))
async def cmdm_cmd(call: CallbackQuery):
    parts = call.data.split(":", 2)
    if len(parts) < 3:
        await call.answer()
        return
    category_key = parts[1]
    command_key = parts[2]
    category = resolve_category_key(category_key)
    cmd = resolve_command_key(category, command_key) if category else None
    if not category or not cmd:
        await call.answer("Неверная команда", show_alert=True)
        return
    allowed, used, limit, almost = consume_user_limit(call.from_user.id, "command_view", FREE_DAILY_COMMAND_LIMIT)
    if not allowed:
        await edit_message_inline(call.message, subscription_status_text(call.from_user.id), subscription_keyboard())
        await call.answer("Лимит Free-команд на сегодня исчерпан", show_alert=True)
        return
    record_usage_event(call.from_user.id, "command_total")
    if almost:
        await send_limit_warning_once(call.bot, call.from_user.id, "command_view", used, limit)

    cats = load_custom_commands()
    desc = "Описание отсутствует"
    for c in cats.get(category, []):
        if c.get("name") == cmd:
            desc = c.get("description") or desc
            break
    caption = get_help_caption(category=category, cmd=cmd)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=BUTTON_LABELS["back"], callback_data=f"cmdm_category:{short_id(category)}")]])
    if not await edit_message_inline(call.message, caption, kb):
        await call.answer("Не удалось показать описание команды", show_alert=True)
        return
    await call.answer()

@dp.callback_query(F.data == "cmdm_back")
async def cmdm_back(call: CallbackQuery):
    await commands_menu(call)

@dp.callback_query(F.data.startswith("help_category:"))
async def help_category_fallback(callback: CallbackQuery):
    try:
        parts = callback.data.split(":", 1)
        category = unquote_plus(parts[1]) if len(parts) > 1 else None
        info = await callback.bot.get_me()
        caption = get_help_caption(category=category)
        kb = build_help_keyboard(page=0, selected_category=category, username=info.username)
        try:
            await callback.message.edit_caption(caption, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await callback.message.edit_text(caption, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await callback.answer()

@dp.callback_query(F.data.startswith("help_cmd:"))
async def help_cmd_fallback(callback: CallbackQuery):
    try:
        parts = callback.data.split(":", 2)
        category = unquote_plus(parts[1]) if len(parts) > 1 else None
        cmd = unquote_plus(parts[2]) if len(parts) > 2 else None
        if cmd is None:
            await callback.answer()
            return
        info = await callback.bot.get_me()
        caption = get_help_caption(category=category, cmd=cmd)
        kb = build_help_keyboard(page=0, selected_category=category, selected_cmd=cmd, username=info.username)
        try:
            await callback.message.edit_caption(caption, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await callback.message.edit_text(caption, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await callback.answer()

@dp.callback_query(F.data.startswith("help_cat_page:"))
async def help_cat_page_fallback(callback: CallbackQuery):
    try:
        parts = callback.data.split(":")
        page = int(parts[1]) if len(parts) > 1 else 0
        info = await callback.bot.get_me()
        caption = get_help_caption()
        kb = build_help_keyboard(page=page, username=info.username)
        try:
            await callback.message.edit_caption(caption, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await callback.message.edit_text(caption, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await callback.answer()

@dp.callback_query(F.data.startswith("help_cmd_page:"))
async def help_cmd_page_fallback(callback: CallbackQuery):
    try:
        parts = callback.data.split(":", 2)
        page = int(parts[1]) if len(parts) > 1 else 0
        category = unquote_plus(parts[2]) if len(parts) > 2 else None
        info = await callback.bot.get_me()
        caption = get_help_caption(category=category)
        kb = build_help_keyboard(page=page, selected_category=category, username=info.username)
        try:
            await callback.message.edit_caption(caption, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await callback.message.edit_text(caption, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await callback.answer()

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, bot: Bot):
    if not await edit_main_menu_message(callback.message):
        await callback.answer("Не удалось обновить главное меню", show_alert=True)
        return
    await callback.answer()


@dp.message(Command("admin"))
async def admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    if ADMIN_URL:
        await message.answer_photo(
            photo=ADMIN_URL,
            caption=ADMIN_PANEL_TEXT,
            reply_markup=admin_kb,
            parse_mode="HTML"
        )
    else:
        await message.answer(
            ADMIN_PANEL_TEXT,
            reply_markup=admin_kb,
            parse_mode="HTML"
        )


@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    with Session(engine) as session:
        messages = session.exec(select(DBMessage)).all()
        files = session.exec(select(File)).all()

        unique_users = len({msg.user_id for msg in messages if msg.user_id is not None})
        connected_business = len(load_connections())
        disconnected_business = max(unique_users - connected_business, 0)

        type_counts = {}
        for msg in messages:
            type_counts[msg.type] = type_counts.get(msg.type, 0) + 1

        text_count = type_counts.get("text", 0)
        photo_count = type_counts.get("photo", 0) + type_counts.get("photos", 0)
        video_count = type_counts.get("video", 0) + type_counts.get("videos", 0)
        round_count = type_counts.get("video_note", 0)
        voice_count = type_counts.get("voice", 0)
        audio_count = type_counts.get("audio", 0)
        sticker_count = type_counts.get("sticker", 0)
        document_count = type_counts.get("document", 0)
        animation_count = type_counts.get("animation", 0)

        text = (
            ADMIN_STATS_HEADER +
            ADMIN_STATS_MESSAGES_TEMPLATE.format(count=len(messages)) +
            ADMIN_STATS_FILES_TEMPLATE.format(count=len(files)) +
            ADMIN_STATS_USERS_TEMPLATE.format(count=unique_users) +
            ADMIN_STATS_BUSINESS_CONNECTED_TEMPLATE.format(count=connected_business) +
            ADMIN_STATS_BUSINESS_DISCONNECTED_TEMPLATE.format(count=disconnected_business) +
            ADMIN_STATS_TYPES_HEADER +
            ADMIN_STATS_TEXT_TEMPLATE.format(count=text_count) +
            ADMIN_STATS_PHOTO_TEMPLATE.format(count=photo_count) +
            ADMIN_STATS_VIDEO_TEMPLATE.format(count=video_count) +
            ADMIN_STATS_ROUND_TEMPLATE.format(count=round_count) +
            ADMIN_STATS_VOICE_TEMPLATE.format(count=voice_count) +
            ADMIN_STATS_AUDIO_TEMPLATE.format(count=audio_count) +
            ADMIN_STATS_STICKER_TEMPLATE.format(count=sticker_count) +
            ADMIN_STATS_DOCUMENT_TEMPLATE.format(count=document_count) +
            ADMIN_STATS_ANIMATION_TEMPLATE.format(count=animation_count) +
            "\n" + new_users_graph_text()
        )

        await edit_message_inline(callback.message, text, admin_back_kb)
        await callback.answer()


@dp.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer()
        return
    await edit_message_inline(callback.message, admin_users_text(), admin_users_keyboard())
    await callback.answer()


@dp.callback_query(F.data == "admin_user_ban")
async def admin_user_ban(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer()
        return
    await state.set_state(AdminProState.waiting_for_ban)
    await edit_message_inline(
        callback.message,
        f"<b>{CROSS_EMOJI} Бан пользователя</b>\n\n"
        "Отправьте:\n<code>ID или @username | причина</code>",
        admin_back_kb,
    )
    await callback.answer()


@dp.message(StateFilter(AdminProState.waiting_for_ban))
async def admin_user_ban_process(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = [part.strip() for part in (message.text or "").split("|", 1)]
    user_id = resolve_subscription_user_id(parts[0] if parts else "")
    if not user_id:
        await message.answer("Не нашел пользователя. Укажите ID или известный @username.", parse_mode="HTML")
        return
    if user_id in ADMIN_IDS:
        await message.answer("Админа банить нельзя.", parse_mode="HTML")
        return
    reason = parts[1] if len(parts) > 1 else ""
    ban_user(message.from_user.id, user_id, reason)
    await state.clear()
    try:
        await message.bot.send_message(user_id, f"{CROSS_EMOJI} <b>Вы заблокированы.</b>\n\n{escape(reason)}", parse_mode="HTML")
    except Exception:
        pass
    await message.answer(f"Пользователь <code>{user_id}</code> заблокирован.", parse_mode="HTML")


@dp.callback_query(F.data == "admin_user_unban")
async def admin_user_unban(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer()
        return
    await state.set_state(AdminProState.waiting_for_unban)
    await edit_message_inline(callback.message, "<b>Разбан</b>\n\nОтправьте ID или @username.", admin_back_kb)
    await callback.answer()


@dp.message(StateFilter(AdminProState.waiting_for_unban))
async def admin_user_unban_process(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    user_id = resolve_subscription_user_id(message.text or "")
    if not user_id:
        await message.answer("Не нашел пользователя.", parse_mode="HTML")
        return
    unban_user(message.from_user.id, user_id)
    await state.clear()
    await message.answer(f"Пользователь <code>{user_id}</code> разбанен.", parse_mode="HTML")


@dp.callback_query(F.data == "admin_user_limits")
async def admin_user_limits(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer()
        return
    await state.set_state(AdminProState.waiting_for_limits)
    await edit_message_inline(
        callback.message,
        f"<b>{GEM_EMOJI} Лимиты пользователя</b>\n\n"
        "Отправьте:\n<code>айди или @username | лимит команд | лимит сохранений</code>\n\n"
        "<i>-1 значит безлимит. 0 значит запрет.</i>",
        admin_back_kb,
    )
    await callback.answer()


@dp.message(StateFilter(AdminProState.waiting_for_limits))
async def admin_user_limits_process(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = [part.strip() for part in (message.text or "").split("|")]
    if len(parts) != 3:
        await message.answer("Формат: <code>айди | команды | сохранения</code>", parse_mode="HTML")
        return
    user_id = resolve_subscription_user_id(parts[0])
    if not user_id:
        await message.answer("Не нашел пользователя.", parse_mode="HTML")
        return
    try:
        command_limit = int(parts[1])
        save_limit = int(parts[2])
    except ValueError:
        await message.answer("Лимиты должны быть числами.", parse_mode="HTML")
        return
    with Session(engine) as session:
        session.add(UserLimitOverride(
            user_id=user_id,
            command_limit=command_limit,
            save_limit=save_limit,
            updated_at=iso_now(),
            updated_by=message.from_user.id,
        ))
        session.commit()
    log_admin_action(message.from_user.id, "set_limits", user_id, f"commands={command_limit}, saves={save_limit}")
    await state.clear()
    await message.answer(
        f"{GEM_EMOJI} <b>Лимиты обновлены</b>\n\n"
        f"<b>Пользователь:</b> <code>{user_id}</code>\n"
        f"<b>Команды:</b> {format_limit_value(command_limit)}\n"
        f"<b>Сохранения:</b> {format_limit_value(save_limit)}",
        parse_mode="HTML",
    )


@dp.callback_query(F.data == "admin_top_users")
async def admin_top_users(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer()
        return
    await edit_message_inline(callback.message, admin_top_users_text(), admin_users_keyboard())
    await callback.answer()


@dp.callback_query(F.data == "admin_gifts")
async def admin_gifts(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer()
        return
    await state.clear()
    try:
        balance = await callback.bot.get_my_star_balance()
        balance_text = f"{balance.amount} Stars"
    except Exception:
        balance_text = "не удалось получить"
    text = (
        f"<b>{STARS_EMOJI} Подарки Telegram</b>\n\n"
        f"<b>Баланс бота:</b> {escape(balance_text)}\n\n"
        "Выберите категорию подарков. Потом бот попросит пользователя, описание и способ оплаты."
    )
    await edit_message_inline(callback.message, text, admin_gifts_keyboard())
    await callback.answer()


@dp.callback_query(F.data.startswith("admin_gift_list:"))
async def admin_gift_list(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer()
        return
    _, source, page_raw = callback.data.split(":")
    try:
        text, keyboard = await admin_gift_list_text(callback.bot, source, int(page_raw))
    except Exception as e:
        logging.exception("Failed to load gifts")
        await callback.answer(f"Не удалось загрузить подарки: {e}", show_alert=True)
        return
    await edit_message_inline(callback.message, text, keyboard)
    await callback.answer()


@dp.callback_query(F.data.startswith("admin_gift_pick:"))
async def admin_gift_pick(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer()
        return
    _, source, gift_id = callback.data.split(":", 2)
    gift = await find_gift_info(callback.bot, source, gift_id)
    if not gift:
        await callback.answer("Подарок не найден или уже недоступен", show_alert=True)
        return
    await state.set_state(AdminGiftState.waiting_for_target)
    await state.update_data(**gift_state_payload(gift))
    await edit_message_inline(
        callback.message,
        f"<b>{STARS_EMOJI} Получатель подарка</b>\n\n"
        f"<b>Подарок:</b> {escape(gift_label(gift))}\n"
        f"<b>ID:</b> <code>{escape(gift_id)}</code>\n\n"
        "Отправьте ID или @username пользователя, который уже есть в боте.",
        admin_back_kb,
    )
    await callback.answer()


@dp.message(StateFilter(AdminGiftState.waiting_for_target))
async def admin_gift_target_process(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    user_id = resolve_subscription_user_id(message.text or "")
    if not user_id:
        await message.answer("Не нашел пользователя. Укажите ID или известный @username.", parse_mode="HTML")
        return
    with Session(engine) as session:
        known_ids = set(get_all_known_user_ids(session))
    if user_id not in known_ids:
        await message.answer("Этот пользователь еще не найден в базе бота. Пусть сначала запустит /start.", parse_mode="HTML")
        return
    await state.update_data(target_user_id=user_id)
    await state.set_state(AdminGiftState.waiting_for_text)
    data = await state.get_data()
    gift = gift_from_state_data(data)
    await message.answer(
        f"<b>{STARS_EMOJI} Описание подарка</b>\n\n"
        f"<b>Подарок:</b> {escape(gift_label(gift))}\n"
        f"<b>Получатель:</b> <code>{user_id}</code>\n\n"
        "Отправьте описание до 128 символов или <code>-</code>, чтобы отправить без описания.\n"
        "<i>Жирный, курсив, ссылки и premium emoji можно отправлять обычным сообщением.</i>",
        parse_mode="HTML",
    )


@dp.message(StateFilter(AdminGiftState.waiting_for_text))
async def admin_gift_text_process(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    plain_text = (message.text or "").strip()
    if not plain_text:
        await message.answer("Отправьте описание или <code>-</code>.", parse_mode="HTML")
        return
    if plain_text not in {"-", "без", "Без"} and len(plain_text) > 128:
        await message.answer("Описание должно быть до 128 символов.", parse_mode="HTML")
        return

    data = await state.get_data()
    text_value = None if plain_text.casefold() in {"-", "без"} else message_html_text(message)
    gift = gift_from_state_data(data)
    order = create_admin_gift_order(
        admin_id=message.from_user.id,
        target_user_id=int(data["target_user_id"]),
        gift=gift,
        text_value=text_value,
        payment_mode="choose",
    )
    await state.clear()
    description = text_value if text_value else "без описания"
    await message.answer(
        f"<b>{STARS_EMOJI} Подтвердите подарок</b>\n\n"
        f"<b>Подарок:</b> {escape(gift_label(gift))}\n"
        f"<b>Gift ID:</b> <code>{escape(gift['id'])}</code>\n"
        f"<b>Получатель:</b> <code>{order.target_user_id}</code>\n"
        f"<b>Описание:</b> {description}\n\n"
        "Выберите способ оплаты:",
        reply_markup=admin_gift_pay_keyboard(order.id),
        parse_mode="HTML",
    )


@dp.callback_query(F.data.startswith("admin_gift_invoice:"))
async def admin_gift_invoice(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer()
        return
    order_id = int(callback.data.split(":", 1)[1])
    with Session(engine) as session:
        order = session.get(AdminGiftOrder, order_id)
        if not order or order.admin_id != callback.from_user.id:
            await callback.answer("Заказ подарка не найден", show_alert=True)
            return
        order.payment_mode = "invoice"
        order.status = "pending_payment"
        if not order.payload:
            order.payload = f"gift:{uuid4().hex}"
        session.add(order)
        session.commit()
        payload = order.payload
        title = order.gift_label
        stars = order.star_count
        target_user_id = order.target_user_id

    await callback.bot.send_invoice(
        chat_id=callback.from_user.id,
        title=f"Telegram gift: {title}",
        description=f"Подарок пользователю {target_user_id}",
        payload=payload,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=title, amount=stars)],
    )
    await callback.answer("Счет Stars отправлен")


@dp.callback_query(F.data.startswith("admin_gift_balance:"))
async def admin_gift_balance(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer()
        return
    order_id = int(callback.data.split(":", 1)[1])
    with Session(engine) as session:
        order = session.get(AdminGiftOrder, order_id)
        if not order or order.admin_id != callback.from_user.id:
            await callback.answer("Заказ подарка не найден", show_alert=True)
            return
        order.payment_mode = "bot_balance"
        order.status = "sending"
        session.add(order)
        session.commit()
        session.refresh(order)

    ok, error = await send_admin_gift_order(callback.bot, order)
    with Session(engine) as session:
        saved = session.get(AdminGiftOrder, order_id)
        if saved:
            saved.status = "sent" if ok else "failed"
            saved.error = error
            saved.sent_at = iso_now() if ok else None
            session.add(saved)
            session.commit()
    if ok:
        log_admin_action(callback.from_user.id, "send_gift_balance", order.target_user_id, f"{order.gift_label} {order.gift_id}")
        await edit_message_inline(
            callback.message,
            f"{STARS_EMOJI} <b>Подарок отправлен</b>\n\n"
            f"<b>Получатель:</b> <code>{order.target_user_id}</code>\n"
            f"<b>Подарок:</b> {escape(order.gift_label)}",
            admin_back_kb,
        )
        await callback.answer("Подарок отправлен")
    else:
        await callback.answer("Не удалось отправить подарок", show_alert=True)
        await edit_message_inline(
            callback.message,
            f"<b>{CROSS_EMOJI} Подарок не отправлен</b>\n\n"
            f"<b>Ошибка:</b> <code>{escape(error or 'unknown')}</code>",
            admin_back_kb,
        )


@dp.callback_query(F.data == "admin_promos")
async def admin_promos(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer()
        return
    await edit_message_inline(callback.message, admin_promos_text(), admin_promos_keyboard())
    await callback.answer()


@dp.callback_query(F.data == "admin_promo_add")
async def admin_promo_add(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer()
        return
    await state.set_state(AdminProState.waiting_for_promo)
    await edit_message_inline(
        callback.message,
        f"<b>{STARS_EMOJI} Новый промокод</b>\n\n"
        "Формат:\n<code>промокод | дни | скидка | лимит | дата</code>\n\n"
        "Пример:\n<code>test | 0 | 30 | 100 | 2026-07-01</code>\n"
        "<code>test | 7 | 0 | 50 | -</code>\n\n"
        "<i>Регистр не важен: test, Test и TEST будут работать одинаково.</i>",
        admin_back_kb,
    )
    await callback.answer()


@dp.message(StateFilter(AdminProState.waiting_for_promo))
async def admin_promo_add_process(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = [part.strip() for part in (message.text or "").split("|")]
    if len(parts) != 5:
        await message.answer("Формат: <code>промокод | дни | скидка | лимит | дата</code>", parse_mode="HTML")
        return
    code = parts[0].upper()
    try:
        days = int(parts[1])
        discount = int(parts[2])
        max_uses = int(parts[3])
        if days < 0 or discount < 0 or discount > 100 or max_uses < 0:
            raise ValueError
    except ValueError:
        await message.answer("Дни/скидка/лимит указаны неверно.", parse_mode="HTML")
        return
    try:
        expires_at = None if parts[4] in ("", "-") else parse_timestamp(parts[4]).isoformat(timespec="seconds")
    except ValueError:
        await message.answer("Дата должна быть в формате <code>YYYY-MM-DD</code> или <code>-</code>.", parse_mode="HTML")
        return
    with Session(engine) as session:
        session.add(PromoCode(
            code=code,
            days=days,
            discount_percent=discount,
            max_uses=max_uses,
            used_count=0,
            is_active=True,
            expires_at=expires_at,
            created_at=iso_now(),
            created_by=message.from_user.id,
        ))
        session.commit()
    log_admin_action(message.from_user.id, "create_promo", details=f"{code}: days={days}, discount={discount}, max={max_uses}")
    await state.clear()
    await message.answer(admin_promos_text(), reply_markup=admin_promos_keyboard(), parse_mode="HTML")


@dp.callback_query(F.data == "admin_promo_issue")
async def admin_promo_issue(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer()
        return
    await state.set_state(AdminProState.waiting_for_issue_promo)
    await edit_message_inline(
        callback.message,
        f"<b>{STARS_EMOJI} Выдать промокод пользователю</b>\n\n"
        "Отправьте:\n<code>айди или @username | промокод</code>\n\n"
        "<i>Регистр не важен. Промокод применится сразу, пользователю придет уведомление.</i>",
        admin_back_kb,
    )
    await callback.answer()


@dp.message(StateFilter(AdminProState.waiting_for_issue_promo))
async def admin_promo_issue_process(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    parts = [part.strip() for part in (message.text or "").split("|", 1)]
    if len(parts) != 2:
        await message.answer("Формат: <code>ID или @username | промокод</code>", parse_mode="HTML")
        return

    user_id = resolve_subscription_user_id(parts[0])
    if not user_id:
        await message.answer("Не нашел пользователя. Укажите ID или известный @username.", parse_mode="HTML")
        return

    code = parts[1].upper()
    with Session(engine) as session:
        ok, result_text = redeem_promo_code(session, user_id, code)

    if not ok:
        await message.answer(result_text, parse_mode="HTML")
        return

    notified = True
    try:
        await message.bot.send_message(
            user_id,
            f"{STARS_EMOJI} <b>Администратор выдал вам промокод</b>\n\n{result_text}",
            parse_mode="HTML",
        )
    except Exception:
        notified = False

    log_admin_action(message.from_user.id, "issue_promo", user_id, code)
    await state.clear()
    await message.answer(
        f"{GEM_EMOJI} <b>Промокод выдан</b>\n\n"
        f"<b>Пользователь:</b> <code>{user_id}</code>\n"
        f"<b>Код:</b> <code>{escape(code)}</code>\n"
        f"<b>Уведомление:</b> {'отправлено' if notified else 'не доставлено'}",
        parse_mode="HTML",
    )


@dp.callback_query(F.data == "admin_promo_delete")
async def admin_promo_delete(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer()
        return
    await state.set_state(AdminProState.waiting_for_promo_delete)
    await edit_message_inline(callback.message, "<b>Удалить промокод</b>\n\nОтправьте код.", admin_back_kb)
    await callback.answer()


@dp.message(StateFilter(AdminProState.waiting_for_promo_delete))
async def admin_promo_delete_process(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    raw_code = (message.text or "").strip()
    code = raw_code.upper()
    with Session(engine) as session:
        promo = session.get(PromoCode, code)
        if not promo:
            promos = session.exec(select(PromoCode)).all()
            promo = next((item for item in promos if item.code.casefold() == raw_code.casefold()), None)
        if not promo:
            await message.answer("Промокод не найден.", parse_mode="HTML")
            return
        code = promo.code
        session.delete(promo)
        session.commit()
    log_admin_action(message.from_user.id, "delete_promo", details=code)
    await state.clear()
    await message.answer(admin_promos_text(), reply_markup=admin_promos_keyboard(), parse_mode="HTML")


@dp.callback_query(F.data == "admin_referrals")
async def admin_referrals(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer()
        return
    await edit_message_inline(callback.message, admin_referrals_text(), admin_referrals_keyboard())
    await callback.answer()


@dp.callback_query(F.data == "admin_ref_set_days")
async def admin_ref_set_days(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer()
        return
    await state.set_state(AdminProState.waiting_for_ref_days)
    await edit_message_inline(callback.message, "Отправьте число дней Premium за реферала.", admin_back_kb)
    await callback.answer()


@dp.message(StateFilter(AdminProState.waiting_for_ref_days))
async def admin_ref_set_days_process(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        days = int((message.text or "").strip())
        if days < 0:
            raise ValueError
    except ValueError:
        await message.answer("Нужно число 0 или больше.", parse_mode="HTML")
        return
    with Session(engine) as session:
        set_setting(session, "referral_reward_days", str(days))
    log_admin_action(message.from_user.id, "set_referral_days", details=str(days))
    await state.clear()
    await message.answer(admin_referrals_text(), reply_markup=admin_referrals_keyboard(), parse_mode="HTML")


@dp.callback_query(F.data == "admin_revenue")
async def admin_revenue(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer()
        return
    await edit_message_inline(callback.message, revenue_stats_text(), admin_back_kb)
    await callback.answer()


@dp.callback_query(F.data == "admin_action_logs")
async def admin_action_logs(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer()
        return
    await edit_message_inline(callback.message, admin_action_logs_text(), admin_back_kb)
    await callback.answer()


@dp.callback_query(F.data == "admin_logs")
async def admin_logs(callback: CallbackQuery):
    with Session(engine) as session:
        logs = session.exec(select(DBMessage).order_by(DBMessage.id.desc())).all()

    text = ADMIN_LOGS_HEADER + "<i>Выберите запись для подробностей.</i>"
    await edit_message_inline(
        callback.message,
        text,
        build_admin_logs_keyboard(logs, page=0)
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("admin_log_page:"))
async def admin_log_page(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    with Session(engine) as session:
        logs = session.exec(select(DBMessage).order_by(DBMessage.id.desc())).all()

    text = ADMIN_LOGS_HEADER + "<i>Выберите запись для подробностей.</i>"
    await edit_message_inline(
        callback.message,
        text,
        build_admin_logs_keyboard(logs, page=page)
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("admin_log_item:"))
async def admin_log_item(callback: CallbackQuery):
    _, log_id, page = callback.data.split(":")
    page = int(page)

    with Session(engine) as session:
        log = session.get(DBMessage, int(log_id))

    if not log:
        await callback.answer("Запись не найдена", show_alert=True)
        return

    text = (
        f"<b>{PEN_EMOJI} Детали лога</b>\n\n" +
        format_admin_log_entry(log, 1)
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Назад к логам", callback_data=f"admin_log_page:{page}", icon_custom_emoji_id="5258236805890710909"),
        ]
    ])

    await edit_message_inline(callback.message, text, keyboard)
    await callback.answer()


@dp.callback_query(F.data == "back_to_admin")
async def back_to_admin(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if not await edit_admin_menu_message(callback.message):
        await callback.answer("Не удалось обновить админ-панель", show_alert=True)
        return
    await callback.answer()


@dp.callback_query(F.data == "admin_deleted")
async def admin_deleted(callback: CallbackQuery):
    with Session(engine) as session:
        all_deleted = session.exec(select(DeletedLog)).all()
        
        total = len(all_deleted)
        week_ago = datetime.now() - timedelta(days=7)
        month_ago = datetime.now() - timedelta(days=30)
        
        week_count = sum(1 for log in all_deleted if parse_timestamp(log.deleted_at) > week_ago)
        month_count = sum(1 for log in all_deleted if parse_timestamp(log.deleted_at) > month_ago)
        
        type_counts = {}
        deleted_records = []
        for log in all_deleted:
            msg = session.get(DBMessage, log.db_message_id)
            if msg:
                type_counts[msg.type] = type_counts.get(msg.type, 0) + 1
                deleted_records.append((log, msg))

    text = (
        ADMIN_DELETED_HEADER +
        format_deleted_stats(total, week_count, month_count, type_counts) +
        "\n\n<i>Выберите запись для подробностей.</i>"
    )

    await edit_message_inline(
        callback.message,
        text,
        build_admin_deleted_keyboard(deleted_records, page=0)
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("admin_deleted_page:"))
async def admin_deleted_page(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    with Session(engine) as session:
        all_deleted = session.exec(select(DeletedLog)).all()
        deleted_records = []
        for log in all_deleted:
            msg = session.get(DBMessage, log.db_message_id)
            if msg:
                deleted_records.append((log, msg))

    type_counts = {}
    for _log, msg in deleted_records:
        type_counts[msg.type] = type_counts.get(msg.type, 0) + 1

    text = (
        ADMIN_DELETED_HEADER +
        format_deleted_stats(
            len(deleted_records),
            sum(1 for log, msg in deleted_records if parse_timestamp(log.deleted_at) > datetime.now() - timedelta(days=7)),
            sum(1 for log, msg in deleted_records if parse_timestamp(log.deleted_at) > datetime.now() - timedelta(days=30)),
            type_counts
        ) +
        "\n\n<i>Выберите запись для подробностей.</i>"
    )

    await edit_message_inline(
        callback.message,
        text,
        build_admin_deleted_keyboard(deleted_records, page=page)
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("admin_deleted_media:"))
async def admin_deleted_media(callback: CallbackQuery):
    _, deleted_id, page = callback.data.split(":")
    page = int(page)

    with Session(engine) as session:
        log = session.get(DeletedLog, int(deleted_id))
        msg = session.get(DBMessage, log.db_message_id) if log else None
        files = []
        if msg:
            files = session.exec(select(File).where(File.message_id == msg.id)).all()

    if not log or not msg:
        await callback.answer("Запись не найдена", show_alert=True)
        return

    if not files:
        await callback.answer("Файлов для просмотра не найдено", show_alert=True)
        return

    sent = False
    for file in files:
        path = await ensure_file_downloaded(callback.bot, Session(engine), file, "jpg" if msg.type == "photos" else "bin")
        if not path:
            continue

        try:
            if msg.type == "photos" or msg.type == "photo":
                await callback.message.answer_photo(
                    FSInputFile(path),
                    caption=f"<b>{PHOTO_EMOJI} Удалённая фотография</b>",
                    protect_content=True,
                    parse_mode="HTML"
                )
                sent = True
                break
            if msg.type == "video":
                await callback.message.answer_video(
                    FSInputFile(path),
                    caption=f"<b>{VIDEO_EMOJI} Удалённое видео</b>",
                    protect_content=True,
                    parse_mode="HTML"
                )
                sent = True
                break
            if msg.type == "voice":
                await callback.message.answer_voice(
                    FSInputFile(path),
                    caption=f"<b>{GOLOS_EMOJI} Удалённое голосовое сообщение</b>",
                    protect_content=True,
                    parse_mode="HTML"
                )
                sent = True
                break
            if msg.type == "audio":
                await callback.message.answer_audio(
                    FSInputFile(path),
                    caption=f"<b>{AUDIO_EMOJI} Удалённое аудио</b>",
                    protect_content=True,
                    parse_mode="HTML"
                )
                sent = True
                break
            if msg.type == "animation":
                await callback.message.answer_animation(
                    FSInputFile(path),
                    caption=f"<b>{GIF_EMOJI} Удалённая анимация</b>",
                    protect_content=True,
                    parse_mode="HTML"
                )
                sent = True
                break
            if msg.type == "document":
                await callback.message.answer_document(
                    FSInputFile(path),
                    caption=f"<b>{DOCUMENT_EMOJI} Удалённый документ</b>",
                    protect_content=True,
                    parse_mode="HTML"
                )
                sent = True
                break
            if msg.type == "sticker":
                await callback.message.answer_sticker(
                    FSInputFile(path),
                    protect_content=True,
                    parse_mode="HTML"
                )
                sent = True
                break
            if msg.type == "video_note":
                await callback.message.answer_video_note(
                    FSInputFile(path),
                    protect_content=True,
                    parse_mode="HTML"
                )
                sent = True
                break
        except Exception:
            continue

    if sent:
        await callback.answer("Медиа отправлено")
    else:
        await callback.answer("Не удалось загрузить медиа", show_alert=True)


@dp.callback_query(F.data.startswith("admin_deleted_item:"))
async def admin_deleted_item(callback: CallbackQuery):
    _, deleted_id, page = callback.data.split(":")
    page = int(page)

    with Session(engine) as session:
        log = session.get(DeletedLog, int(deleted_id))
        msg = session.get(DBMessage, log.db_message_id) if log else None
        files = []
        if msg:
            files = session.exec(select(File).where(File.message_id == msg.id)).all()

    if not log or not msg:
        await callback.answer("Запись не найдена", show_alert=True)
        return

    text = format_deleted_detail(log, msg)
    keyboard = []
    if files:
        keyboard.append([
            InlineKeyboardButton(
                text=" Посмотреть медиа",
                icon_custom_emoji_id="5454419255430767770",
                callback_data=f"admin_deleted_media:{log.id}:{page}"
            )
        ])
    keyboard.append([InlineKeyboardButton(text=" Назад", callback_data=f"admin_deleted_page:{page}", icon_custom_emoji_id="5258236805890710909")])

    await edit_message_inline(callback.message, text, InlineKeyboardMarkup(inline_keyboard=keyboard))
    await callback.answer()


@dp.callback_query(F.data == "admin_accounts")
async def admin_accounts(callback: CallbackQuery):
    text = ADMIN_ACCOUNTS_HEADER
    
    try:
        connections = biz_is_connected(callback.from_user.id)
        if connections:
            text += f"✅ Активное подключение\n\n"
            text += f"ID подключения: <code>{get_connection_id()}</code>"
        else:
            text += ADMIN_ACCOUNTS_EMPTY
    except:
        text += ADMIN_ACCOUNTS_EMPTY
    
    await edit_message_inline(callback.message, text, admin_back_kb)
    await callback.answer()

@dp.callback_query(F.data == "admin_errors")
async def admin_errors(callback: CallbackQuery):
    # В реальности здесь загружать логи из файла
    text = ADMIN_ERRORS_HEADER + ADMIN_ERRORS_EMPTY
    
    await edit_message_inline(callback.message, text, admin_back_kb)
    await callback.answer()


# 8. РАССЫЛКА
@dp.callback_query(F.data == "admin_subscriptions")
async def admin_subscriptions(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer()
        return
    if not await edit_admin_subscriptions_message(callback.message):
        await callback.answer("Не удалось обновить подписки", show_alert=True)
        return
    await callback.answer()


@dp.callback_query(F.data == "admin_sub_add_plan")
async def admin_sub_add_plan(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer()
        return
    await state.set_state(SubscriptionAdminState.waiting_for_plan)
    await edit_message_inline(
        callback.message,
        f"<b>{GEM_EMOJI} Новый тариф</b>\n\n"
        "Отправьте одним сообщением:\n"
        "<code>Название | дни | цена_usd | stars</code>\n\n"
        "Пример:\n"
        "<code>Premium 30 | 30 | 5 | 250</code>",
        admin_back_kb,
    )
    await callback.answer()


@dp.message(StateFilter(SubscriptionAdminState.waiting_for_plan))
async def admin_sub_create_plan(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    parts = [part.strip() for part in (message.text or "").split("|")]
    if len(parts) != 4:
        await message.answer("Формат: <code>Название | дни | цена_usd | stars</code>", parse_mode="HTML")
        return

    title, days_raw, usd_raw, stars_raw = parts
    try:
        days = int(days_raw)
        price_usd = float(usd_raw.replace(",", "."))
        stars = int(stars_raw)
        if days <= 0 or price_usd < 0 or stars < 0:
            raise ValueError
    except ValueError:
        await message.answer("Дни должны быть > 0, цена и stars не меньше 0.")
        return

    with Session(engine) as session:
        session.add(SubscriptionPlan(
            title=title,
            days=days,
            price_usd=price_usd,
            stars=stars,
            is_active=True,
            created_at=iso_now(),
        ))
        session.commit()

    log_admin_action(message.from_user.id, "create_plan", details=f"{title}: {days}d ${price_usd:g} {stars} Stars")
    await state.clear()
    await send_admin_subscriptions_message(message, f"{GEM_EMOJI} <b>Тариф добавлен</b>")


@dp.callback_query(F.data == "admin_sub_grant")
async def admin_sub_grant(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer()
        return
    await state.set_state(SubscriptionAdminState.waiting_for_grant)
    await edit_message_inline(
        callback.message,
        f"<b>{GEM_EMOJI} Выдать подписку</b>\n\n"
        "Отправьте одним сообщением:\n"
        "<code>ID или @username | дни | название</code>\n\n"
        "Примеры:\n"
        "<code>7528568061 | 30 | Premium Admin</code>\n"
        "<code>@nolyktg | 7 | Premium Gift</code>\n\n"
        "<i>Username должен быть уже известен боту: человек запускал бота или попадал в логи.</i>",
        admin_back_kb,
    )
    await callback.answer()


@dp.message(StateFilter(SubscriptionAdminState.waiting_for_grant))
async def admin_sub_grant_process(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    parts = [part.strip() for part in (message.text or "").split("|")]
    if len(parts) < 2:
        await message.answer("Формат: <code>user_id | дни | название</code>", parse_mode="HTML")
        return

    user_identifier = parts[0]
    user_id = resolve_subscription_user_id(user_identifier)
    if not user_id:
        await message.answer(
            "Не нашел пользователя.\n\n"
            "Укажите ID или username пользователя, который уже запускал бота / есть в логах.",
            parse_mode="HTML",
        )
        return

    try:
        days = int(parts[1])
        if days <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Дни должны быть числом больше 0.")
        return

    plan_title = parts[2] if len(parts) > 2 and parts[2] else "Admin Grant"
    with Session(engine) as session:
        sub = extend_user_subscription(session, user_id, days, plan_title, "admin")
        expires_text = format_subscription_expires(sub.expires_at)

    log_admin_action(message.from_user.id, "grant_subscription", user_id, f"{days}d {plan_title}")
    await state.clear()
    notify_text = (
        f"{GEM_EMOJI} <b>Вам выдана подписка Premium</b>\n\n"
        f"<b>Тариф:</b> {escape(plan_title)}\n"
        f"<b>Срок:</b> {days} дн.\n"
        f"<b>Действует до:</b> <code>{escape(expires_text)}</code>\n\n"
        "<i>Спасибо, что пользуетесь Shell Save.</i>"
    )
    notified = True
    try:
        await message.bot.send_message(user_id, notify_text, parse_mode="HTML")
    except Exception:
        notified = False

    await message.answer(
        "✅ <b>Подписка выдана</b>\n\n"
        f"<b>Получатель:</b> <code>{user_id}</code>\n"
        f"<b>Тариф:</b> {escape(plan_title)}\n"
        f"<b>Срок:</b> {days} дн.\n"
        f"<b>До:</b> <code>{escape(expires_text)}</code>\n"
        f"<b>Уведомление:</b> {'отправлено' if notified else 'не доставлено'}",
        parse_mode="HTML",
    )


@dp.callback_query(F.data == "admin_sub_revoke")
async def admin_sub_revoke(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer()
        return
    await state.set_state(SubscriptionAdminState.waiting_for_revoke)
    await edit_message_inline(
        callback.message,
        f"<b>{GEM_EMOJI} Забрать подписку</b>\n\n"
        "Отправьте ID или @username пользователя:\n"
        "<code>7528568061</code>\n"
        "<code>@nolyktg</code>\n\n"
        "<i>У админов Premium навсегда, его нельзя забрать.</i>",
        admin_back_kb,
    )
    await callback.answer()


@dp.message(StateFilter(SubscriptionAdminState.waiting_for_revoke))
async def admin_sub_revoke_process(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    user_id = resolve_subscription_user_id(message.text or "")
    if not user_id:
        await message.answer(
            "Не нашел пользователя.\n\n"
            "Укажите ID или username пользователя, который уже запускал бота / есть в логах.",
            parse_mode="HTML",
        )
        return

    if user_id in ADMIN_IDS:
        await message.answer("У админа Premium навсегда, подписку забрать нельзя.", parse_mode="HTML")
        return

    with Session(engine) as session:
        old_record = session.get(UserSubscription, user_id)
        was_active = is_subscription_active_record(old_record)
        revoke_user_subscription(session, user_id)

    log_admin_action(message.from_user.id, "revoke_subscription", user_id)
    await state.clear()
    notify_text = (
        f"{GEM_EMOJI} <b>Подписка Premium отключена</b>\n\n"
        "Администратор убрал подписку. Теперь действуют лимиты Free."
    )
    notified = True
    try:
        await message.bot.send_message(user_id, notify_text, parse_mode="HTML")
    except Exception:
        notified = False

    await message.answer(
        "✅ <b>Подписка забрана</b>\n\n"
        f"<b>Пользователь:</b> <code>{user_id}</code>\n"
        f"<b>Была активна:</b> {'да' if was_active else 'нет'}\n"
        f"<b>Уведомление:</b> {'отправлено' if notified else 'не доставлено'}",
        parse_mode="HTML",
    )


@dp.callback_query(F.data == "admin_sub_extend_all")
async def admin_sub_extend_all(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer()
        return
    await state.set_state(SubscriptionAdminState.waiting_for_extend_all)
    await edit_message_inline(
        callback.message,
        f"<b>{GEM_EMOJI} Продлить всем</b>\n\n"
        "Отправьте одним сообщением:\n"
        "<code>дни | название</code>\n\n"
        "Пример:\n"
        "<code>7 | Premium Bonus</code>\n\n"
        "<i>Админы пропускаются: у них Premium навсегда.</i>",
        admin_back_kb,
    )
    await callback.answer()


@dp.message(StateFilter(SubscriptionAdminState.waiting_for_extend_all))
async def admin_sub_extend_all_process(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    parts = [part.strip() for part in (message.text or "").split("|", 1)]
    if not parts or not parts[0]:
        await message.answer("Формат: <code>дни | название</code>", parse_mode="HTML")
        return

    try:
        days = int(parts[0])
        if days <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Дни должны быть числом больше 0.", parse_mode="HTML")
        return

    plan_title = parts[1] if len(parts) > 1 and parts[1] else "Premium Bonus"
    with Session(engine) as session:
        user_ids = get_known_subscription_user_ids(session)
        for user_id in user_ids:
            extend_user_subscription(session, user_id, days, plan_title, "admin_mass_extend")

    log_admin_action(message.from_user.id, "extend_all_subscriptions", details=f"{len(user_ids)} users, {days}d {plan_title}")
    await state.clear()
    notify_text = (
        f"{GEM_EMOJI} <b>Ваша подписка Premium продлена</b>\n\n"
        f"<b>Добавлено:</b> {days} дн.\n"
        f"<b>Тариф:</b> {escape(plan_title)}"
    )
    notified = 0
    for user_id in user_ids:
        try:
            await message.bot.send_message(user_id, notify_text, parse_mode="HTML")
            notified += 1
        except Exception:
            pass
        await asyncio.sleep(0.03)

    await message.answer(
        "✅ <b>Подписка продлена всем</b>\n\n"
        f"<b>Пользователей:</b> {len(user_ids)}\n"
        f"<b>Добавлено:</b> {days} дн.\n"
        f"<b>Тариф:</b> {escape(plan_title)}\n"
        f"<b>Уведомления:</b> {notified}/{len(user_ids)}",
        parse_mode="HTML",
    )


@dp.callback_query(F.data.startswith("admin_sub_edit:"))
async def admin_sub_edit(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer()
        return

    plan_id = int(callback.data.split(":", 1)[1])
    with Session(engine) as session:
        plan = session.get(SubscriptionPlan, plan_id)
        if not plan:
            await callback.answer("Тариф не найден", show_alert=True)
            return
        title = plan.title
        days = plan.days
        price_usd = plan.price_usd
        stars = plan.stars

    await state.set_state(SubscriptionAdminState.waiting_for_edit_plan)
    await state.update_data(plan_id=plan_id)
    await edit_message_inline(
        callback.message,
        f"<b>{GEM_EMOJI} Изменить тариф</b>\n\n"
        f"Сейчас:\n<code>{escape(title)} | {days} | {price_usd:g} | {stars}</code>\n\n"
        "Отправьте новые данные:\n"
        "<code>Название | дни | цена_usd | stars</code>",
        admin_back_kb,
    )
    await callback.answer()


@dp.message(StateFilter(SubscriptionAdminState.waiting_for_edit_plan))
async def admin_sub_edit_process(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    data = await state.get_data()
    plan_id = data.get("plan_id")
    parts = [part.strip() for part in (message.text or "").split("|")]
    if len(parts) != 4:
        await message.answer("Формат: <code>Название | дни | цена_usd | stars</code>", parse_mode="HTML")
        return

    title, days_raw, usd_raw, stars_raw = parts
    try:
        days = int(days_raw)
        price_usd = float(usd_raw.replace(",", "."))
        stars = int(stars_raw)
        if days <= 0 or price_usd < 0 or stars < 0:
            raise ValueError
    except ValueError:
        await message.answer("Дни должны быть > 0, цена и stars не меньше 0.")
        return

    with Session(engine) as session:
        plan = session.get(SubscriptionPlan, int(plan_id))
        if not plan:
            await message.answer("Тариф не найден.")
            await state.clear()
            return
        plan.title = title
        plan.days = days
        plan.price_usd = price_usd
        plan.stars = stars
        session.add(plan)
        session.commit()

    log_admin_action(message.from_user.id, "edit_plan", details=f"{title}: {days}d ${price_usd:g} {stars} Stars")
    await state.clear()
    await send_admin_subscriptions_message(message, f"{GEM_EMOJI} <b>Тариф изменен</b>")


@dp.callback_query(F.data.startswith("admin_sub_delete:"))
async def admin_sub_delete(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer()
        return

    plan_id = int(callback.data.split(":", 1)[1])
    with Session(engine) as session:
        plan = session.get(SubscriptionPlan, plan_id)
        if not plan:
            await callback.answer("Тариф не найден", show_alert=True)
            return
        session.delete(plan)
        session.commit()

    log_admin_action(callback.from_user.id, "delete_plan", details=f"plan_id={plan_id}")
    await edit_admin_subscriptions_message(callback.message)
    await callback.answer("Тариф удален")


@dp.callback_query(F.data.startswith("admin_sub_toggle:"))
async def admin_sub_toggle(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer()
        return

    plan_id = int(callback.data.split(":", 1)[1])
    with Session(engine) as session:
        plan = session.get(SubscriptionPlan, plan_id)
        if not plan:
            await callback.answer("Тариф не найден", show_alert=True)
            return
        plan.is_active = not plan.is_active
        session.add(plan)
        session.commit()

    log_admin_action(callback.from_user.id, "toggle_plan", details=f"plan_id={plan_id}")
    await edit_admin_subscriptions_message(callback.message)
    await callback.answer("Тариф обновлен")


@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminBroadcastState.selecting)
    await edit_message_inline(
        callback.message,
        ADMIN_BROADCAST_PROMPT,
        build_broadcast_keyboard({})
    )
    await callback.answer()


@dp.callback_query(F.data == "broadcast_text", StateFilter(AdminBroadcastState.selecting))
async def broadcast_text_choice(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminBroadcastState.waiting_for_text)
    await edit_message_inline(callback.message, ADMIN_BROADCAST_TEXT_PROMPT, admin_back_kb)
    await callback.answer()


@dp.callback_query(F.data == "broadcast_photo", StateFilter(AdminBroadcastState.selecting))
async def broadcast_photo_choice(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminBroadcastState.waiting_for_photo)
    await callback.message.edit_text(
        ADMIN_BROADCAST_PHOTO_PROMPT,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Без фото", callback_data="remove_broadcast_photo")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="broadcast_menu")],
        ]),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "broadcast_button", StateFilter(AdminBroadcastState.selecting))
async def broadcast_button_choice(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminBroadcastState.waiting_for_button_choice)
    await callback.message.edit_text(
        ADMIN_BROADCAST_BUTTON_TEXT_PROMPT,
        parse_mode="HTML"
    )
    await callback.answer()


@dp.message(StateFilter(AdminBroadcastState.waiting_for_text))
async def admin_broadcast_text(message: Message, state: FSMContext):
    await state.update_data(
        broadcast_text=message.text,
        broadcast_text_entities=message.entities
    )
    data = await state.get_data()
    preview_text = build_broadcast_preview(data)

    await message.answer(
        ADMIN_BROADCAST_PREVIEW.format(preview=preview_text),
        reply_markup=build_broadcast_keyboard(data),
        parse_mode="HTML"
    )
    await state.set_state(AdminBroadcastState.selecting)


@dp.message(StateFilter(AdminBroadcastState.waiting_for_photo))
async def admin_broadcast_photo(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer(
            "❌ Отправьте изображение или нажмите кнопку 'Без фото'",
            parse_mode="HTML"
        )
        return

    await state.update_data(broadcast_photo=message.photo[-1].file_id)
    data = await state.get_data()
    preview_text = build_broadcast_preview(data)

    await message.answer(
        ADMIN_BROADCAST_PREVIEW.format(preview=preview_text),
        reply_markup=build_broadcast_keyboard(data),
        parse_mode="HTML"
    )
    await state.set_state(AdminBroadcastState.selecting)


@dp.callback_query(F.data == "remove_broadcast_photo")
async def remove_broadcast_photo(callback: CallbackQuery, state: FSMContext):
    await state.update_data(broadcast_photo=None)
    data = await state.get_data()
    await callback.message.edit_text(
        ADMIN_BROADCAST_PREVIEW.format(preview=build_broadcast_preview(data)),
        reply_markup=build_broadcast_keyboard(data),
        parse_mode="HTML"
    )
    await state.set_state(AdminBroadcastState.selecting)
    await callback.answer()


@dp.message(StateFilter(AdminBroadcastState.waiting_for_button_choice))
async def admin_broadcast_button_text(message: Message, state: FSMContext):
    await state.update_data(broadcast_button_text=message.text)
    await state.set_state(AdminBroadcastState.waiting_for_button_url)
    await message.answer(
        ADMIN_BROADCAST_BUTTON_URL_PROMPT,
        parse_mode="HTML"
    )


@dp.message(StateFilter(AdminBroadcastState.waiting_for_button_url))
async def admin_broadcast_button_url(message: Message, state: FSMContext):
    url = message.text.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        await message.answer("❌ Ссылка должна начинаться с http:// или https://")
        return

    await state.update_data(broadcast_button_url=url)
    # После ввода ссылки — попросим выбрать стиль кнопки
    await state.set_state(AdminBroadcastState.waiting_for_button_style)
    await message.answer(
        ADMIN_BROADCAST_BUTTON_STYLE_PROMPT,
        reply_markup=broadcast_button_style_keyboard(),
        parse_mode="HTML"
    )


@dp.callback_query(F.data.startswith("button_style:"), StateFilter(AdminBroadcastState.waiting_for_button_style))
async def admin_broadcast_button_style(callback: CallbackQuery, state: FSMContext):
    _, style_key = callback.data.split(":", 1)
    style_name = style_key
    await state.update_data(broadcast_button_style=style_name)
    data = await state.get_data()

    await edit_message_inline(
        callback.message,
        ADMIN_BROADCAST_PREVIEW.format(preview=build_broadcast_preview(data)),
        build_broadcast_keyboard(data)
    )
    await state.set_state(AdminBroadcastState.selecting)
    await callback.answer()


@dp.callback_query(F.data == "remove_broadcast_button")
async def remove_broadcast_button(callback: CallbackQuery, state: FSMContext):
    await state.update_data(broadcast_button_text=None, broadcast_button_url=None, broadcast_button_style=None)
    data = await state.get_data()
    await edit_message_inline(
        callback.message,
        ADMIN_BROADCAST_PREVIEW.format(preview=build_broadcast_preview(data)),
        build_broadcast_keyboard(data)
    )
    await state.set_state(AdminBroadcastState.selecting)
    await callback.answer()


@dp.callback_query(F.data == "broadcast_menu")
async def broadcast_menu(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(AdminBroadcastState.selecting)
    await edit_message_inline(
        callback.message,
        ADMIN_BROADCAST_PREVIEW.format(preview=build_broadcast_preview(data)),
        build_broadcast_keyboard(data)
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("broadcast_segment:"), StateFilter(AdminBroadcastState.selecting))
async def broadcast_segment(callback: CallbackQuery, state: FSMContext):
    segment = callback.data.split(":", 1)[1]
    if segment not in {"all", "free", "premium", "admins"}:
        await callback.answer()
        return
    await state.update_data(broadcast_segment=segment)
    data = await state.get_data()
    await edit_message_inline(
        callback.message,
        ADMIN_BROADCAST_PREVIEW.format(preview=build_broadcast_preview(data)),
        build_broadcast_keyboard(data),
    )
    await callback.answer("Сегмент выбран")


@dp.callback_query(F.data == "cancel_broadcast")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await edit_message_inline(
        callback.message,
        ADMIN_PANEL_TEXT,
        admin_kb
    )
    await callback.answer()


@dp.callback_query(F.data == "confirm_broadcast", StateFilter(AdminBroadcastState.selecting))
async def confirm_broadcast(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    broadcast_text = data.get("broadcast_text") or ""
    broadcast_text_entities = data.get("broadcast_text_entities")
    broadcast_photo = data.get("broadcast_photo")
    button_text = data.get("broadcast_button_text")
    button_url = data.get("broadcast_button_url")
    segment = data.get("broadcast_segment") or "all"

    if not broadcast_text and not broadcast_photo:
        await callback.answer("❌ Укажите текст или добавьте фото перед отправкой", show_alert=True)
        return

    broadcast_markup = None
    if button_text and button_url:
        broadcast_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=button_text, url=button_url)]
        ])

    user_ids = get_broadcast_user_ids(segment)

    success_count = 0
    for user_id in user_ids:
        try:
            if broadcast_photo:
                await bot.send_photo(
                    chat_id=user_id,
                    photo=broadcast_photo,
                    caption=broadcast_text or " ",
                    caption_entities=broadcast_text_entities,
                    reply_markup=broadcast_markup
                )
            else:
                await bot.send_message(
                    chat_id=user_id,
                    text=broadcast_text or " ",
                    entities=broadcast_text_entities,
                    reply_markup=broadcast_markup
                )
            success_count += 1
        except Exception:
            continue

    await callback.message.edit_text(
        ADMIN_BROADCAST_SUCCESS.format(count=success_count),
        reply_markup=admin_back_kb,
        parse_mode="HTML"
    )
    await state.clear()
    await callback.answer()


@dp.callback_query(F.data == "admin_manage")
async def admin_manage(callback: CallbackQuery):
    text = (
        f"<b>{RENAME_EMOJI} Управление командами</b>\n\n"
        f"{PLUS_EMOJI} Создайте категорию и добавляйте в неё команды.\n"
        "Нажмите на категорию, чтобы добавить команду, редактировать название или описание."
    )

    await edit_message_inline(
        callback.message,
        text,
        build_manage_categories_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("manage_cat_page:"))
async def manage_category_page(callback: CallbackQuery):
    page = int(callback.data.split(":", 1)[1])
    await edit_message_inline(
        callback.message,
        callback.message.text or "",
        build_manage_categories_keyboard(page=page)
    )
    await callback.answer()


@dp.callback_query(F.data == "manage_back_to_categories")
async def manage_back_to_categories(callback: CallbackQuery):
    await edit_message_inline(
        callback.message,
        f"<b>{RENAME_EMOJI} Управление командами</b>\n\nВыберите категорию для редактирования или создания новой.",
        build_manage_categories_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("manage_category:"))
async def manage_category(callback: CallbackQuery):
    category_key = callback.data.split(":", 1)[1]
    category = resolve_category_key(category_key)
    if not category:
        await callback.answer("Неверная категория", show_alert=True)
        return

    text = get_manage_category_text(category)
    kb = build_manage_category_keyboard(category)
    logging.info(f"manage_category called with category={category} category_key={category_key}")
    if not await edit_message_inline(callback.message, text, kb):
        logging.warning(f"manage_category: edit_message_inline failed for category={category}")
        try:
            await callback.message.edit_caption(caption=text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            try:
                await callback.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
            except Exception:
                logging.exception(f"manage_category: fallback edit failed for category={category}")
                await callback.answer("Не удалось открыть категорию", show_alert=True)
                return
    await callback.answer()


@dp.callback_query(F.data == "manage_add_category")
async def manage_add_category(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminManageState.waiting_for_action)
    await state.update_data(action="add_category")

    await edit_message_inline(
        callback.message,
        "Введите название новой категории:",
        admin_back_kb
    )
    await callback.answer()


@dp.callback_query(F.data == "manage_clear_all_categories")
async def manage_clear_all_categories(callback: CallbackQuery):
    save_custom_commands({})
    await edit_message_inline(
        callback.message,
        "✅ Все категории удалены.",
        build_manage_categories_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("manage_add_command:"))
async def manage_add_command(callback: CallbackQuery, state: FSMContext):
    category_key = callback.data.split(":", 1)[1]
    category = resolve_category_key(category_key)
    if not category:
        await callback.answer("Неверная категория", show_alert=True)
        return
    await state.set_state(AdminManageState.waiting_for_action)
    await state.update_data(action="add_command", category=category)

    await edit_message_inline(
        callback.message,
        "Введите новую команду и описание в формате:\n<code>.hello | Привет от бота</code>",
        admin_back_kb
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("manage_edit_command:"))
async def manage_edit_command(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":", 2)
    category_key = parts[1]
    command_key = parts[2] if len(parts) > 2 else None
    category = resolve_category_key(category_key)
    command_name = resolve_command_key(category, command_key) if category and command_key else None

    if not category or not command_name:
        await callback.answer("Неверная команда или категория", show_alert=True)
        return

    await state.set_state(AdminManageState.waiting_for_action)
    await state.update_data(action="edit_command", category=category, command=command_name)

    await edit_message_inline(
        callback.message,
        f"<b>{SEND_EMOJI} Отправьте новое название команды или же описание:</b>\n\n<code>.newcmd | Новое описание</code>\n\n"
        f"<blockquote><b>Чтобы изменить только описание, отправьте текст без точки.</b></blockquote>",
        admin_back_kb
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("manage_delete_command:"))
async def manage_delete_command(callback: CallbackQuery):
    parts = callback.data.split(":", 2)
    category_key = parts[1]
    command_key = parts[2] if len(parts) > 2 else None
    category = resolve_category_key(category_key)
    command_name = resolve_command_key(category, command_key) if category and command_key else None

    if not category or not command_name:
        await callback.answer("Неверная команда или категория", show_alert=True)
        return

    categories_dict = load_custom_commands()
    commands = categories_dict.get(category, [])
    categories_dict[category] = [cmd for cmd in commands if cmd.get("name") != command_name]
    save_custom_commands(categories_dict)

    await edit_message_inline(
        callback.message,
        f"✅ Команда <code>{escape(command_name)}</code> удалена из категории <b>{escape(category)}</b>",
        build_manage_category_keyboard(category)
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("manage_cmd_page:"))
async def manage_command_page(callback: CallbackQuery):
    parts = callback.data.split(":", 2)
    category_key = parts[1]
    category = resolve_category_key(category_key)
    if not category:
        await callback.answer("Неверная категория", show_alert=True)
        return
    page = int(parts[2])

    await edit_message_inline(
        callback.message,
        get_manage_category_text(category),
        build_manage_category_keyboard(category, page=page)
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("manage_rename_category:"))
async def manage_rename_category(callback: CallbackQuery, state: FSMContext):
    category_key = callback.data.split(":", 1)[1]
    category = resolve_category_key(category_key)
    if not category:
        await callback.answer("Неверная категория", show_alert=True)
        return
    await state.set_state(AdminManageState.waiting_for_edit_category_name)
    await state.update_data(category=category)

    await edit_message_inline(
        callback.message,
        f"Введите новое имя для категории <b>{escape(category)}</b>:",
        admin_back_kb
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("manage_delete_category:"))
async def manage_delete_category(callback: CallbackQuery):
    category_key = callback.data.split(":", 1)[1]
    category = resolve_category_key(category_key)
    if not category:
        await callback.answer("Неверная категория", show_alert=True)
        return
    categories_dict = load_custom_commands()
    categories_dict.pop(category, None)
    save_custom_commands(categories_dict)

    await edit_message_inline(
        callback.message,
        f"{TICK_EMOJI} Категория <b>{escape(category)}</b> удалена.",
        build_manage_categories_keyboard()
    )
    await callback.answer()


@dp.message(AdminManageState.waiting_for_action)
async def manage_command_input(message: Message, state: FSMContext):
    data = await state.get_data()
    action = data.get("action")
    category = data.get("category")
    command_name = data.get("command")
    if not action:
        await message.answer("❌ Неверный шаг. Попробуйте снова.")
        await state.clear()
        return

    name, description = parse_custom_command_input(message.text)
    categories_dict = load_custom_commands()

    if action == "add_category":
        category_name = message.text.strip()
        if not category_name:
            await message.answer("❌ Название категории не может быть пустым.")
            return

        if category_name in categories_dict:
            await message.answer("❌ Такая категория уже существует. Введите другое имя.")
            return

        categories_dict[category_name] = []
        save_custom_commands(categories_dict)

        await message.answer(
            f"✅ Категория <b>{escape(category_name)}</b> создана.",
            reply_markup=build_manage_category_keyboard(category_name),
            parse_mode="HTML"
        )

    elif action == "add_command":
        if not name:
            await message.answer("❌ Укажите команду в формате <code>.hello | Привет</code>.", parse_mode="HTML")
            return

        commands = categories_dict.get(category, [])
        if any(cmd.get("name") == name for cmd in commands):
            await message.answer("❌ Команда с таким именем уже есть в категории.", parse_mode="HTML")
            return

        commands.append({
            "name": name,
            "description": description or "Описание отсутствует"
        })
        categories_dict[category] = commands
        save_custom_commands(categories_dict)

        await message.answer(
            f"✅ Команда <code>{escape(name)}</code> добавлена в категорию <b>{escape(category)}</b>",
            reply_markup=build_manage_category_keyboard(category),
            parse_mode="HTML"
        )

    elif action == "edit_command":
        if category not in categories_dict:
            await message.answer("❌ Категория не найдена.")
            await state.clear()
            return

        commands = categories_dict.get(category, [])
        command = find_command(categories_dict, category, command_name)
        if not command:
            await message.answer("❌ Команда не найдена.")
            await state.clear()
            return

        if name:
            if name != command_name and any(cmd.get("name") == name for cmd in commands):
                await message.answer("❌ Команда с таким именем уже существует.", parse_mode="HTML")
                return
            command["name"] = name

        if description is not None:
            command["description"] = description or "Описание отсутствует"

        save_custom_commands(categories_dict)
        await message.answer(
            f"✅ Команда обновлена: <code>{escape(command.get('name'))}</code>",
            reply_markup=build_manage_category_keyboard(category),
            parse_mode="HTML"
        )

    else:
        await message.answer("❌ Неверное действие. Попробуйте снова.")

    await state.clear()


@dp.message(AdminManageState.waiting_for_edit_category_name)
async def manage_edit_category_name(message: Message, state: FSMContext):
    data = await state.get_data()
    old_category = data.get("category")
    if not old_category:
        await message.answer("❌ Ошибка. Попробуйте снова.")
        await state.clear()
        return

    new_name = message.text.strip()
    if not new_name:
        await message.answer("❌ Название категории не может быть пустым.")
        return

    categories_dict = load_custom_commands()
    if old_category not in categories_dict:
        await message.answer("❌ Категория не найдена.")
        await state.clear()
        return
    if new_name in categories_dict:
        await message.answer("❌ Категория с таким именем уже существует.")
        return

    categories_dict[new_name] = categories_dict.pop(old_category)
    save_custom_commands(categories_dict)

    await message.answer(
        f"✅ Категория переименована в <b>{escape(new_name)}</b>",
        reply_markup=build_manage_category_keyboard(new_name),
        parse_mode="HTML"
    )
    await state.clear()


@dp.callback_query(F.data.startswith("clear_custom_cmd:"))
async def clear_custom_cmd(callback: CallbackQuery, state: FSMContext):
    await callback.answer("❌ Используйте управление категориями.", show_alert=True)
    await state.clear()


async def save_media_file(session: Session, message: Message, file_id: str, folder: str, message_type: str) -> None:
    try:
        session.add(File(
            file_name=None,
            file_id=file_id,
            folder=folder,
            message_id=message.message_id
        ))
        session.commit()
    except Exception as e:
        logging.error(f"Error saving file: {e}")


@dp.business_message(~F.text.startswith("."))
async def business_message(message: Message, bot: Bot):

    from commands import muted_users

    if (
        message.from_user
        and message.from_user.id in muted_users
    ):

        try:

            await bot.delete_business_messages(
                business_connection_id=message.business_connection_id,
                message_ids=[message.message_id]
            )

        except Exception as e:

            print(
                f"MUTE DELETE ERROR: {e}"
            )

        return
    owner_id = business_owner_id_by_connection_id(getattr(message, "business_connection_id", None))
    if owner_id is None:
        try:
            business_connection = await bot.get_business_connection(message.business_connection_id)
            owner_id = business_connection.user_chat_id
        except Exception:
            owner_id = None

    if owner_id:
        allowed, used, limit, almost = consume_user_limit(owner_id, "business_save", FREE_DAILY_SAVE_LIMIT)
        if not allowed:
            return
        if almost:
            await send_limit_warning_once(bot, owner_id, "business_save", used, limit)

    try:
        with Session(engine) as session:
            msg_type = None
            content = None
            file_id = None
            folder = None
            media_group_id = message.media_group_id
            
            if message.photo:
                msg_type = "photos"
                content = message.caption or ""
                best_photo = message.photo[-1]
                file_id = best_photo.file_id
                folder = "photos"

            elif message.video:
                msg_type = "video"
                content = message.caption or ""
                file_id = message.video.file_id
                folder = "videos"

            elif message.voice:
                msg_type = "voice"
                content = VOICE_MESSAGE_CONTENT
                file_id = message.voice.file_id
                folder = "voices"

            elif message.sticker:
                msg_type = "sticker"
                content = message.sticker.emoji or STICKER_CONTENT
                file_id = message.sticker.file_id
                folder = "stickers"

            elif message.video_note:
                msg_type = "video_note"
                content = VIDEO_NOTE_CONTENT
                file_id = message.video_note.file_id
                folder = "video_notes"

            elif message.document:
                msg_type = "document"
                content = message.document.file_name or DOCUMENT_CONTENT
                file_id = message.document.file_id
                folder = "documents"

            elif message.audio:
                msg_type = "audio"
                content = message.audio.title or AUDIO_CONTENT
                file_id = message.audio.file_id
                folder = "audios"

            elif message.animation:
                msg_type = "animation"
                content = message.caption or ANIMATION_CONTENT
                file_id = message.animation.file_id
                folder = "animations"

            else:
                msg_type = "text"
                content = message.text or ""

            db_msg = DBMessage(
                chat_id=message.chat.id,
                id=message.message_id,
                user_id=message.from_user.id,
                owner_id=owner_id,
                from_username=message.from_user.username or UNKNOWN_USER_DISPLAY,
                first_name=message.from_user.first_name or UNKNOWN_USER_DISPLAY,
                type=msg_type,
                content=content,
                media_group_id=media_group_id,
                created_at=get_time()
            )

            session.add(db_msg)
            session.commit()

            if file_id and folder:
                await save_media_file(session, message, file_id, folder, msg_type)

            if message.has_protected_content or message.has_media_spoiler:
                spoiler_indicator = ""
                if message.has_media_spoiler:
                    spoiler_indicator = SPOILER_TEXT
                if message.has_protected_content:
                    spoiler_indicator = ONE_TIME_VIEW_TEXT if not spoiler_indicator else spoiler_indicator + ONE_TIME_TEXT
                
                logging.info(
                    f"Saved {msg_type} from @{message.from_user.username or 'unknown'}{spoiler_indicator} "
                    f"in chat {message.chat.id}"
                )

    except Exception as e:
        logging.error(f"Error in business_message handler: {e}")

@dp.deleted_business_messages()
async def deleted_handler(event: BusinessMessagesDeleted):
    with Session(engine) as session:
        try:
            business_connection = await event.bot.get_business_connection(
                event.business_connection_id
            )
            user_chat_id = business_connection.user_chat_id
        except Exception as e:
            logging.error(f"Failed to get business connection: {e}")
            return

        message_ids = list(event.message_ids)
        messages = session.exec(
            select(DBMessage)
            .where(DBMessage.chat_id == event.chat.id)
            .where(DBMessage.id.in_(message_ids))
        ).all()

        if not messages:
            return

        filtered_messages = [msg for msg in messages if msg.user_id != user_chat_id]
        
        if not filtered_messages:
            logging.info(f"Skipping delete notification: owner deleted own message")
            return

        MAX_DELETE_LIMIT = 100
        if len(filtered_messages) > MAX_DELETE_LIMIT:
            try:
                await event.bot.send_message(
                    user_chat_id,
                    f"<b>{CROSS_EMOJI} Превышен лимит удаления</b>\n\n"
                    f"<blockquoute><b>Удалено {len(filtered_messages)} сообщений — бот обрабатывает максимум <code>{MAX_DELETE_LIMIT}</code>.</b></blockquoute>\n\n"
                    f"<blockquote><b>• {INFO_EMOJI} Никакие Логи не были сохранены. Пожалуйста, удаляйте сообщения частями, чтобы бот мог их обработать.</b></blockquote>",
                    protect_content=True,
                    parse_mode=ParseMode.HTML,
                )
            except Exception as e:
                logging.error(f"Error sending delete limit warning: {e}")
            return

        BULK_THRESHOLD = 10
        if len(filtered_messages) > BULK_THRESHOLD:
            try:
                out_dir = os.path.join('media', 'deleted_logs')
                html_path = await generate_deleted_html(session, event.bot, filtered_messages, out_dir)
                file_id = uuid4().hex
                DELETED_HTML_MAP[file_id] = html_path

                kb = InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text=f"• Просмотреть",
                        callback_data=f"view_deleted:{file_id}",
                        icon_custom_emoji_id=PROFILE_EMOJI_ID
                    )
                ]])

                summary = f"<b>{TRASH_EMOJI} Удалено {len(filtered_messages)} сообщений.\n\n<blockquote>Нажмите кнопку ниже, чтобы просмотреть удаленные сообщения.</blockquote></b>"

                target_ids = {user_chat_id} | set(ADMIN_IDS)
                for target in target_ids:
                    try:
                        await event.bot.send_message(target, summary, protect_content=True, reply_markup=kb, parse_mode=ParseMode.HTML)
                    except Exception as e:
                        logging.error(f"Error sending bulk delete summary to {target}: {e}")

                return
            except Exception as e:
                logging.error(f"Failed to generate/send bulk HTML log: {e}")

        grouped_messages = {}
        for msg in filtered_messages:
            key = msg.media_group_id if msg.media_group_id else f"single-{msg.id}"
            grouped_messages.setdefault(key, []).append(msg)

        for group in grouped_messages.values():
            if len(group) > 1 and group[0].type == "photos" and group[0].media_group_id:
                for msg in group:
                    deleted_log = DeletedLog(
                        db_message_id=msg.id,
                        owner_id=user_chat_id,
                        deleted_at=get_time()
                    )
                    session.add(deleted_log)
                session.commit()

                files = []
                for msg in sorted(group, key=lambda item: item.id):
                    file_rows = session.exec(select(File).where(File.message_id == msg.id)).all()
                    for file in file_rows:
                        path = await ensure_file_downloaded(event.bot, session, file, "jpg")
                        if path:
                            files.append(path)

                if not files:
                    continue

                media = []
                for idx, path in enumerate(files):
                    if idx == 0:
                        media.append(InputMediaPhoto(
                            media=FSInputFile(path),
                            caption=build_delete_photo(group[0], ALBUM_PHOTO_LABEL),
                            has_spoiler=True 
                        ))
                    else:
                        media.append(InputMediaPhoto(
                            media=FSInputFile(path),
                            has_spoiler=True 
                        ))

                try:
                    await event.bot.send_media_group(
                        user_chat_id,
                        media=media,
                        protect_content=True  
                    )
                except Exception as e:
                    logging.error(f"Error sending media group: {e}")
                continue

            for msg in sorted(group, key=lambda item: item.id):
                deleted_log = DeletedLog(
                    db_message_id=msg.id,
                    owner_id=user_chat_id,
                    deleted_at=get_time()
                )
                session.add(deleted_log)
                session.commit()

                try:
                    if msg.type == "text":
                        profile_kb = InlineKeyboardMarkup(inline_keyboard=[[
                            InlineKeyboardButton(
                                text=f"• Посмотреть",
                                url=f"tg://user?id={msg.user_id}",
                                icon_custom_emoji_id="5954175920506933873"
                            )
                        ]])
                        await event.bot.send_message(
                            user_chat_id,
                            build_delete_log(msg, TEXT_LABEL),
                            protect_content=True,
                            reply_markup=profile_kb
                        )
                        continue

                    files = session.exec(
                        select(File).where(File.message_id == msg.id)
                    ).all()

                    if not files:
                        profile_kb = InlineKeyboardMarkup(inline_keyboard=[[
                            InlineKeyboardButton(
                                text=f"• Посмотреть",
                                url=f"tg://user?id={msg.user_id}",
                                icon_custom_emoji_id="5954175920506933873"
                            )
                        ]])
                        await event.bot.send_message(
                            user_chat_id,
                            build_delete_log(msg, TYPE_LABELS.get(msg.type, msg.type.capitalize())),
                            protect_content=True,
                            reply_markup=profile_kb
                        )
                        continue

                    profile_kb = InlineKeyboardMarkup(inline_keyboard=[[
                        InlineKeyboardButton(
                            text=f"• Посмотреть",
                            url=f"tg://user?id={msg.user_id}",
                            icon_custom_emoji_id="5954175920506933873"
                        )
                    ]])
                    
                    if msg.type == "photos":
                        for file in files:
                            path = await ensure_file_downloaded(event.bot, session, file, "jpg")
                            if not path:
                                continue
                            await event.bot.send_photo(
                                user_chat_id,
                                FSInputFile(path),
                                caption=build_delete_photo(msg, PHOTO_LABEL),
                                has_spoiler=True,
                                protect_content=True,
                                reply_markup=profile_kb
                            )
                            break
                        continue

                    file = files[0]
                    ext_map = {
                        "video": "mp4",
                        "voice": "ogg",
                        "audio": "mp3",
                        "sticker": "webp",
                        "video_note": "mp4",
                        "animation": "mp4",
                        "document": "bin"
                    }
                    default_ext = ext_map.get(msg.type, "bin")
                    path = await ensure_file_downloaded(event.bot, session, file, default_ext)
                    if not path:
                        continue

                    if msg.type == "video":
                        await event.bot.send_video(
                            user_chat_id,
                            FSInputFile(path),
                            caption=build_delete_log(msg, VIDEO_LABEL),
                            has_spoiler=True,  
                            protect_content=True,
                            reply_markup=profile_kb
                        )

                    elif msg.type == "voice":
                        await event.bot.send_voice(
                            user_chat_id,
                            FSInputFile(path),
                            caption=build_delete_voice(msg, VOICE_LABEL),
                            protect_content=True,
                            reply_markup=profile_kb
                        )

                    elif msg.type == "audio":
                        await event.bot.send_audio(
                            user_chat_id,
                            FSInputFile(path),
                            caption=build_delete_audio(msg, AUDIO_LABEL),
                            protect_content=True,
                            reply_markup=profile_kb
                        )

                    elif msg.type == "animation":
                        await event.bot.send_animation(
                            user_chat_id,
                            FSInputFile(path),
                            caption=build_delete_animation(msg, ANIMATION_LABEL),
                            has_spoiler=True, 
                            protect_content=True,
                            reply_markup=profile_kb
                        )

                    elif msg.type == "sticker":
                        await event.bot.send_sticker(
                            user_chat_id,
                            FSInputFile(path),
                            protect_content=True
                        )
                        await event.bot.send_message(
                            user_chat_id,
                            build_delete_sticker(msg, STICKER_LABEL),
                            protect_content=True,
                            reply_markup=profile_kb
                        )

                    elif msg.type == "video_note":
                        await event.bot.send_video_note(
                            user_chat_id,
                            FSInputFile(path),
                            protect_content=True
                        )
                        await event.bot.send_message(
                            user_chat_id,
                            build_delete_round(msg, VIDEO_NOTE_LABEL),
                            protect_content=True,
                            reply_markup=profile_kb
                        )

                    elif msg.type == "document":
                        await event.bot.send_document(
                            user_chat_id,
                            FSInputFile(path),
                            caption=build_delete_document(msg, DOCUMENT_LABEL),
                            protect_content=True,
                            reply_markup=profile_kb
                        )

                except Exception as e:
                    logging.error(f"Error sending deleted message notification: {e}")


@dp.edited_message()
async def edited_message_handler(message: Message, bot: Bot):
    try:
        with Session(engine) as session:
            msg = session.exec(
                select(DBMessage)
                .where(DBMessage.chat_id == message.chat.id)
                .where(DBMessage.id == message.message_id)
            ).first()

            if not msg:
                return

            old_content = msg.content

            if message.text:
                msg.content = message.text
            elif message.caption:
                msg.content = message.caption

            session.add(msg)
            session.commit()

            with engine.begin() as conn:
                conn.execute(
                    text("INSERT INTO editedlog (db_message_id, owner_id, edited_at, old_content, new_content) VALUES (:dbm, :owner, :t, :old, :new)"),
                    {"dbm": msg.id, "owner": message.from_user.id, "t": get_time(), "old": old_content, "new": msg.content}
                )

            preview_text = build_edit_log(msg, old_content, msg.content)
            profile_kb = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text=f"• Посмотреть",
                    url=f"tg://user?id={msg.user_id}",
                    icon_custom_emoji_id="5954175920506933873"
                )
            ]])

            for admin in ADMIN_IDS:
                try:
                    await bot.send_message(
                        admin,
                        preview_text,
                        parse_mode=ParseMode.HTML,
                        protect_content=True,
                        reply_markup=profile_kb
                    )
                except Exception:
                    pass

    except Exception as e:
        logging.error(f'edited_message_handler error: {e}')


try:
    @dp.edited_business_message()
    async def edited_business_handler(message: Message, bot: Bot):
        try:
            business_connection_id = getattr(message, "business_connection_id", None)
            if not business_connection_id:
                return

            business_connection = await bot.get_business_connection(business_connection_id)
            user_chat_id = business_connection.user_chat_id
        except Exception as e:
            logging.error(f"Failed to get business connection: {e}")
            return

        if getattr(message, 'from_user', None) and message.from_user.id == user_chat_id:
            logging.info("Skipping edit notification: owner edited own message")
            return

        try:
            with Session(engine) as session:
                msg = session.exec(
                    select(DBMessage)
                    .where(DBMessage.chat_id == message.chat.id)
                    .where(DBMessage.id == message.message_id)
                ).first()

                if not msg:
                    return

                old_content = msg.content
                if message.text:
                    msg.content = message.text
                elif message.caption:
                    msg.content = message.caption

                session.add(msg)
                session.commit()

                new_content = msg.content
                edited_at = get_time()
                with engine.begin() as conn:
                    conn.execute(
                        text("INSERT INTO editedlog (db_message_id, owner_id, edited_at, old_content, new_content) VALUES (:dbm, :owner, :t, :old, :new)"),
                        {"dbm": msg.id, "owner": user_chat_id, "t": edited_at, "old": old_content, "new": new_content}
                    )

                preview_text = build_edit_log(msg, old_content, new_content)

                profile_kb = InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text=f"• Посмотреть",
                        url=f"tg://user?id={msg.user_id}",
                        icon_custom_emoji_id="5954175920506933873"
                    )
                ]])

                try:
                    if msg.type == "photos":
                        files = session.exec(select(File).where(File.message_id == msg.id)).all()
                        for file in files:
                            path = await ensure_file_downloaded(bot, session, file, "jpg")
                            if not path:
                                continue
                            await bot.send_photo(
                                user_chat_id,
                                FSInputFile(path),
                                has_spoiler=True,
                                protect_content=True
                            )
                        await bot.send_message(
                            user_chat_id,
                            preview_text,
                            parse_mode=ParseMode.HTML,
                            protect_content=True,
                            reply_markup=profile_kb
                        )
                    else:
                        await bot.send_message(
                            user_chat_id,
                            preview_text,
                            parse_mode=ParseMode.HTML,
                            protect_content=True,
                            reply_markup=profile_kb
                        )
                except Exception as e:
                    logging.error(f"Error sending edit notification: {e}")
        except Exception as e:
            logging.error(f'edited_business_handler error: {e}')
except Exception:
    pass


async def startup_debug(bot: Bot):
    ensure_default_subscription_plans()
    asyncio.create_task(subscription_expiry_notifier(bot))
    logging.warning(f"DEBUG: Dispatcher has {len(dp.observers)} observers")
    for router_obj in dp.sub_routers:
        logging.warning(f"DEBUG: Included router with handlers")


dp.startup.register(startup_debug)

@dp.callback_query(F.data.startswith("view_deleted:"))
async def view_deleted_callback(query: CallbackQuery, bot: Bot):
    try:
        data = query.data or ""
        _, fid = data.split(":", 1)
        path = DELETED_HTML_MAP.get(fid)
        if not path or not os.path.exists(path):
            try:
                await query.answer("Файл недоступен.", show_alert=True)
            except Exception:
                pass
            return

        try:
            await bot.send_document(query.from_user.id, FSInputFile(path))
            await query.answer()
        except Exception as e:
            logging.error(f"Error sending html log to user: {e}")
            try:
                await query.answer("Ошибка при отправке файла.", show_alert=True)
            except Exception:
                pass
    except Exception as e:
        logging.error(f"view_deleted_callback error: {e}")


@dp.edited_channel_post()
async def edited_channel_post_handler(message: Message, bot: Bot):
    try:
        business_connection_id = getattr(message, "business_connection_id", None)
        if business_connection_id:
            handler = globals().get("edited_business_handler")
            if callable(handler):
                return await handler(message, bot)

        return await edited_message_handler(message, bot)
    except Exception as e:
        logging.error(f'edited_channel_post_handler error: {e}')


async def main():
    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        )
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout
    )

    asyncio.run(main())
