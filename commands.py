import logging
import os
import asyncio
import uuid
import random
import json
import ast
import math
import re
import secrets
import shutil
import shlex
import string
import subprocess
import time
from pathlib import Path
from typing import Any, Optional, Tuple
import aiohttp
import edge_tts
from urllib.parse import quote_plus, unquote_plus
import hashlib
from typing import Dict
from datetime import datetime

from aiogram import F, Bot, Router
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, CopyTextButton, FSInputFile, InputProfilePhotoStatic, MessageEntity
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from html import escape
from pathlib import Path
from uuid import uuid4
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageOps

from emoji import GOLOS_EMOJI, PEN_EMOJI, INFO_EMOJI, CROSS_EMOJI, PHOTO_EMOJI, QUESTION_EMOJI, ROUND_EMOJI, SECRET_EMOJI, VIDEO_EMOJI, USER_EMOJI, ID_EMOJI, TIME_EMOJI, GEM_EMOJI, STARS_EMOJI, TICK_EMOJI

games = {}

muted_users = set()

last_muted_user = {}

copied_profiles = {}

spam_tasks = {}

mines_games = {}

copytg_backup = {}

copy_profiles = {}

business_chats = {}

GENERATED_MEDIA_DIR = Path("generated_media")

PGEN_MEDIA_DIR = Path("profile_generator_media")

PGEN_BACKUP_FILE = Path("pgen_backups.json")

pgen_tasks = {}

pgen_backups = {}

pgen_restore_tasks = {}

pgen_restore_eta = {}

PGEN_STYLES = [
    "lorelei",
    "lorelei-neutral",
    "adventurer",
    "adventurer-neutral",
    "bottts",
    "bottts-neutral",
    "croodles",
    "croodles-neutral",
    "dylan",
    "fun-emoji",
    "micah",
    "miniavs",
    "notionists",
    "notionists-neutral",
    "personas",
    "pixel-art",
    "pixel-art-neutral",
    "toon-head",
    "thumbs",
    "rings",
    "shapes",
    "identicon",
]

PGEN_SWAG_BASES = [
    "luv",
    "void",
    "angel",
    "zero",
    "skyluv",
    "hell",
    "heaven",
    "night",
    "soul",
    "silent",
    "shxdow",
    "kira",
    "yami",
    "akira",
    "senpai",
    "vamp",
    "drain",
    "neon",
    "glitch",
    "cyber",
    "dream",
    "zetsu",
    "kitsune",
    "tokyo",
    "karma",
    "rage",
    "tilted",
    "psycho",
    "toxic",
    "lost",
    "broken",
    "grave",
    "blood",
    "demon",
    "frost",
    "blade",
    "panic",
    "trash",
    "error",
    "sleepy",
    "deadinside",
    "graveyard",
    "murder",
    "ritual",
    "scary",
    "m0on",
    "sorrow",
    "lonely",
    "cringe",
    "chaos",
]

PGEN_SWAG_ENDS = [
    "boy",
    "girl",
    "kid",
    "core",
    "luv",
    "exe",
    "mp3",
    "jpg",
    "png",
    "404",
    "777",
    "999",
    "x",
    "xo",
    "wtf",
    "dead",
    "hurt",
    "scene",
    "swag",
    "mmr",
    "mid",
    "feed",
    "diff",
    "gap",
    "rank",
    "soul",
    "rage",
    "tilt",
    "smurf",
    "arc",
    "void",
    "demon",
]

PGEN_DOTA_BASES = [
    "sf",
    "nevermore",
    "invoker",
    "pudge",
    "am",
    "antimage",
    "morph",
    "morphling",
    "jugger",
    "voidspirit",
    "storm",
    "ember",
    "slark",
    "tinker",
    "meepo",
    "techies",
    "roshan",
    "aegis",
    "rapier",
    "blink",
    "dagger",
    "bkb",
    "manta",
    "midonly",
    "pos1",
    "pos5",
    "smurf",
    "rampage",
    "divine",
    "immortal",
    "herald",
    "ancient",
    "lowprio",
    "feedmachine",
    "ezmid",
    "midgap",
    "supportdiff",
    "carrydiff",
    "mmrthief",
]

PGEN_SWAG_TEMPLATES = [
    "{base}.{end}",
    "{base}_{end}",
    "x{base}",
    "{base}x",
    "{base}{num}",
    "{base}.{num}",
    "{base}_{num}",
    "{base}{end}",
    "{base}4{end}",
    "luv{base}",
    "{base}luv",
    "im{base}",
    "not{base}",
    "{base}woke",
    "{base}diff",
    "{base}gap",
    "{base}666",
    "{base}1337",
    "x{base}x",
    "{base}.exe",
    "{base}.jpg",
    "{base}.mp3",
    "{base}_0",
    "xx{base}",
    "{base}qt",
    "{base}solo",
]

PGEN_INTERVAL_MIN = 25.0

PGEN_INTERVAL_MAX = 45.0

PGEN_ANIME_CATEGORIES = ["neko", "waifu", "husbando", "kitsune"]

PGEN_WAIFU_TAGS = ["waifu", "uniform", "maid", "selfies"]

PGEN_ANIME_SOURCE_WEIGHTS = ["waifu.im", "waifu.im", "nekos.best", "nekos.best", "dicebear"]

PGEN_DARK_FILTERS = ["snow_mono", "cold_shadow", "highkey_bw", "blue_manga"]



SIZE = 6
MINES = 8

def user_link(user_id, name):
    return f'<a href="tg://user?id={user_id}">{name}</a>'


def get_business_connection_id(msg: Message) -> Optional[str]:
    return getattr(msg, "business_connection_id", None)


async def is_business_owner(msg: Message, bot: Bot) -> bool:
    feedback = get_business_connection_id(msg)
    if not feedback:
        return True
    try:
        connection = await bot.get_business_connection(feedback)
    except Exception:
        return False
    return connection is None or msg.from_user.id == connection.user.id


async def send_html(
    msg: Message,
    bot: Bot,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
):
    return await bot.send_message(
        chat_id=msg.chat.id,
        text=text,
        parse_mode="HTML",
        reply_markup=reply_markup,
        business_connection_id=get_business_connection_id(msg),
    )


async def delete_command_message(msg: Message, bot: Bot) -> None:
    try:
        feedback = get_business_connection_id(msg)
        if feedback:
            await bot.delete_business_messages(
                business_connection_id=feedback,
                message_ids=[msg.message_id],
            )
        else:
            await bot.delete_message(
                chat_id=msg.chat.id,
                message_id=msg.message_id,
            )
    except Exception:
        pass


async def edit_message_html(msg: Message, bot: Bot, text: str):
    return await bot.edit_message_text(
        chat_id=msg.chat.id,
        message_id=msg.message_id,
        business_connection_id=get_business_connection_id(msg),
        text=text,
        parse_mode="HTML",
    )


async def start_editable_status(msg: Message, bot: Bot, text: str) -> tuple[Any, bool]:
    try:
        status = await edit_message_html(msg, bot, text)
        return status, True
    except Exception:
        await delete_command_message(msg, bot)
        status = await send_html(msg, bot, text)
        return status, False


async def update_editable_status(
    msg: Message,
    bot: Bot,
    status: Any,
    is_command_status: bool,
    text: str,
) -> None:
    try:
        if is_command_status:
            await edit_message_html(msg, bot, text)
        else:
            await status.edit_text(text, parse_mode="HTML")
    except Exception:
        await send_html(msg, bot, text)


async def delete_editable_status(
    msg: Message,
    bot: Bot,
    status: Any,
    is_command_status: bool,
) -> None:
    try:
        if is_command_status:
            await delete_command_message(msg, bot)
        else:
            await status.delete()
    except Exception:
        pass


def command_args(msg: Message, command: str) -> str:
    text = msg.text or ""
    return text[len(command):].strip()


SAFE_CALC_FUNCS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "floor": math.floor,
    "ceil": math.ceil,
}

SAFE_CALC_NAMES = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}


def safe_calc(expr: str) -> float:
    if not expr or len(expr) > 160:
        raise ValueError("Слишком длинный пример")

    def eval_node(node):
        if isinstance(node, ast.Expression):
            return eval_node(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.Name):
            if node.id in SAFE_CALC_NAMES:
                return SAFE_CALC_NAMES[node.id]
            raise ValueError(f"Нельзя использовать имя: {node.id}")
        if isinstance(node, ast.UnaryOp):
            value = eval_node(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +value
            if isinstance(node.op, ast.USub):
                return -value
            raise ValueError("Оператор не поддерживается")
        if isinstance(node, ast.BinOp):
            left = eval_node(node.left)
            right = eval_node(node.right)
            if isinstance(node.op, ast.Add):
                result = left + right
            elif isinstance(node.op, ast.Sub):
                result = left - right
            elif isinstance(node.op, ast.Mult):
                result = left * right
            elif isinstance(node.op, ast.Div):
                result = left / right
            elif isinstance(node.op, ast.FloorDiv):
                result = left // right
            elif isinstance(node.op, ast.Mod):
                result = left % right
            elif isinstance(node.op, ast.Pow):
                if abs(right) > 12:
                    raise ValueError("Степень слишком большая")
                result = left ** right
            else:
                raise ValueError("Оператор не поддерживается")
            if abs(result) > 10 ** 15:
                raise ValueError("Результат слишком большой")
            return result
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            func = SAFE_CALC_FUNCS.get(node.func.id)
            if not func:
                raise ValueError("Функция не поддерживается")
            args = [eval_node(arg) for arg in node.args]
            if len(args) > 4:
                raise ValueError("Слишком много аргументов")
            return func(*args)
        raise ValueError("Пример содержит запрещенные символы")

    tree = ast.parse(expr.replace(",", "."), mode="eval")
    return eval_node(tree)


def format_calc_result(value: float) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return f"{value:.10g}"


WEATHER_CODES = {
    0: "ясно",
    1: "в основном ясно",
    2: "переменная облачность",
    3: "пасмурно",
    45: "туман",
    48: "изморозь/туман",
    51: "легкая морось",
    53: "морось",
    55: "сильная морось",
    61: "легкий дождь",
    63: "дождь",
    65: "сильный дождь",
    71: "легкий снег",
    73: "снег",
    75: "сильный снег",
    80: "ливень",
    81: "сильный ливень",
    82: "очень сильный ливень",
    95: "гроза",
    96: "гроза с градом",
    99: "сильная гроза с градом",
}


async def fetch_json(url: str, params: dict) -> dict:
    timeout = aiohttp.ClientTimeout(total=12)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()


async def fetch_bytes(url: str, params: Optional[dict] = None) -> bytes:
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.read()


async def geocode_city(city: str) -> Optional[dict]:
    data = await fetch_json(
        "https://geocoding-api.open-meteo.com/v1/search",
        {"name": city, "count": 1, "language": "ru", "format": "json"},
    )
    results = data.get("results") or []
    return results[0] if results else None


async def current_forecast(place: dict) -> dict:
    return await fetch_json(
        "https://api.open-meteo.com/v1/forecast",
        {
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
            "timezone": "auto",
        },
    )


def normalize_profile_name(name: str) -> str:
    value = re.sub(r"\s+", " ", (name or "").strip())
    value = re.sub(r"[^\w .-]+", "", value, flags=re.UNICODE).strip(" .-_")
    if not value:
        value = f"{random.choice(PGEN_SWAG_BASES)}_{random.choice(PGEN_SWAG_ENDS)}"
    return value[:64]


def generate_profile_name() -> str:
    if random.random() < 0.42:
        base = random.choice(PGEN_DOTA_BASES)
    else:
        base = random.choice(PGEN_SWAG_BASES)
    end = random.choice(PGEN_SWAG_ENDS)
    num = random.choice([
        str(random.randint(7, 99)),
        str(random.randint(100, 999)),
        "1337",
        "404",
        "777",
        "999",
    ])
    template = random.choice(PGEN_SWAG_TEMPLATES)
    value = template.format(base=base, end=end, num=num)
    if random.random() < 0.28:
        value = value.replace("o", "0").replace("a", "x", 1)
    if random.random() < 0.22:
        value = f"_{value}"
    if random.random() < 0.22:
        value = f"{value}_"
    if random.random() < 0.18:
        value = value.replace("i", "1").replace("e", "3", 1)
    return normalize_profile_name(value.lower())


async def download_pgen_avatar(path: Path, seed: str) -> str:
    sources = [random.choice(PGEN_ANIME_SOURCE_WEIGHTS), "waifu.im", "nekos.best", "dicebear"]
    last_error = None
    for source in sources:
        try:
            image_url = None
            source_name = source
            if source == "waifu.im":
                tag = random.choice(PGEN_WAIFU_TAGS)
                data = await fetch_json(
                    "https://api.waifu.im/images",
                    {"IncludedTags": tag, "IsNsfw": "False"},
                )
                item = (data.get("images") or data.get("results") or [{}])[0]
                image_url = item.get("url") or item.get("path") or item.get("image")
                if image_url and image_url.startswith("/"):
                    image_url = "https://www.waifu.im" + image_url
                source_name = f"waifu.im/{tag}"
            elif source == "nekos.best":
                category = random.choice(PGEN_ANIME_CATEGORIES)
                data = await fetch_json(f"https://nekos.best/api/v2/{category}", {})
                result = (data.get("results") or [{}])[0]
                image_url = result.get("url")
                source_name = f"nekos.best/{category}"
            else:
                style = random.choice(PGEN_STYLES)
                image_url = f"https://api.dicebear.com/10.x/{style}/png"
                source_name = f"dicebear/{style}"

            if image_url:
                if source == "dicebear":
                    content = await fetch_bytes(
                        image_url,
                        {
                            "seed": seed,
                            "size": 512,
                            "backgroundColor": "0a0a0a,111827,1f2937,18181b,f8fafc",
                            "radius": 50,
                        },
                    )
                else:
                    content = await fetch_bytes(image_url)
                await asyncio.to_thread(save_profile_avatar_image, content, path)
                return source_name
        except Exception as e:
            last_error = e
            print(f"PGEN AVATAR SOURCE ERROR ({source}): {e}")
    raise RuntimeError(f"Не удалось получить аватар: {last_error}")


def apply_modern_anime_pfp_style(image: Image.Image) -> Image.Image:
    image = ImageOps.autocontrast(image, cutoff=random.randint(1, 3))
    mode = random.choice(PGEN_DARK_FILTERS)

    if mode == "snow_mono":
        gray = ImageOps.grayscale(image)
        image = Image.merge("RGB", (gray, gray, gray))
        image = ImageEnhance.Contrast(image).enhance(1.55)
        image = ImageEnhance.Brightness(image).enhance(1.12)
    elif mode == "cold_shadow":
        gray = ImageOps.grayscale(image)
        image = Image.merge("RGB", (gray, gray, gray))
        tint = Image.new("RGB", image.size, (176, 197, 225))
        image = Image.blend(image, tint, 0.18)
        image = ImageEnhance.Contrast(image).enhance(1.45)
        image = ImageEnhance.Brightness(image).enhance(0.92)
    elif mode == "highkey_bw":
        gray = ImageOps.grayscale(image)
        image = ImageOps.autocontrast(gray, cutoff=2).convert("RGB")
        image = ImageEnhance.Contrast(image).enhance(1.8)
        image = ImageEnhance.Brightness(image).enhance(1.18)
    else:
        gray = ImageOps.grayscale(image)
        image = Image.merge("RGB", (gray, gray, gray))
        tint = Image.new("RGB", image.size, (120, 145, 185))
        image = Image.blend(image, tint, 0.26)
        image = ImageEnhance.Contrast(image).enhance(1.6)

    image = ImageEnhance.Sharpness(image).enhance(1.8)
    image = image.filter(ImageFilter.UnsharpMask(radius=1.2, percent=120, threshold=3))

    width, height = image.size
    vignette = Image.new("L", image.size, 0)
    pixels = vignette.load()
    cx, cy = width / 2, height / 2
    max_dist = (cx ** 2 + cy ** 2) ** 0.5
    for y in range(height):
        for x in range(width):
            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 / max_dist
            pixels[x, y] = int(max(0, min(120, (dist - 0.35) * 210)))
    dark = Image.new("RGB", image.size, (0, 0, 0))
    image = Image.composite(dark, image, vignette)

    if random.random() < 0.65:
        snow = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(snow)
        for _ in range(random.randint(8, 18)):
            size = random.randint(2, 9)
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            draw.ellipse((x, y, x + size, y + size), fill=(255, 255, 255, random.randint(45, 135)))
        snow = snow.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.4, 1.2)))
        image = Image.alpha_composite(image.convert("RGBA"), snow).convert("RGB")

    return image


def save_profile_avatar_image(content: bytes, path: Path) -> None:
    from io import BytesIO

    image = Image.open(BytesIO(content)).convert("RGB")
    width, height = image.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    resampling = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
    image = image.crop((left, top, left + side, top + side)).resize((512, 512), resampling)
    image = apply_modern_anime_pfp_style(image)
    image.save(path, format="JPEG", quality=92)


async def backup_business_profile(msg: Message, bot: Bot, feedback: str) -> dict:
    PGEN_MEDIA_DIR.mkdir(exist_ok=True)
    backup = {
        "feedback": feedback,
        "first_name": msg.from_user.first_name or "Telegram",
        "last_name": msg.from_user.last_name or "",
        "photo_path": None,
    }
    try:
        photos = await bot.get_user_profile_photos(msg.from_user.id, limit=1)
        if photos.total_count and photos.photos:
            photo = photos.photos[0][-1]
            file = await bot.get_file(photo.file_id)
            photo_path = PGEN_MEDIA_DIR / f"original_{msg.from_user.id}_{uuid4().hex}.jpg"
            await bot.download_file(file.file_path, destination=str(photo_path))
            backup["photo_path"] = str(photo_path)
    except Exception as e:
        print(f"PGEN BACKUP PHOTO ERROR: {e}")
    return backup


def load_pgen_backup_store() -> dict:
    if not PGEN_BACKUP_FILE.exists():
        return {}
    try:
        data = json.loads(PGEN_BACKUP_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_pgen_backup_store(data: dict) -> None:
    PGEN_BACKUP_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def format_pgen_wait(seconds: Optional[float]) -> str:
    if seconds is None:
        return "несколько минут"
    seconds = max(1, int(seconds))
    minutes, rest = divmod(seconds, 60)
    if minutes and rest:
        return f"{minutes} мин. {rest} сек."
    if minutes:
        return f"{minutes} мин."
    return f"{rest} сек."


def remember_pgen_backup(user_id: int, backup: dict) -> None:
    pgen_backups[user_id] = backup
    store = load_pgen_backup_store()
    store[str(user_id)] = backup
    save_pgen_backup_store(store)


def get_pgen_backup(user_id: int) -> Optional[dict]:
    backup = pgen_backups.get(user_id)
    if backup:
        return backup
    return load_pgen_backup_store().get(str(user_id))


def clear_pgen_backup(user_id: int) -> None:
    pgen_backups.pop(user_id, None)
    store = load_pgen_backup_store()
    store.pop(str(user_id), None)
    save_pgen_backup_store(store)


def pop_pgen_backup(user_id: int) -> Optional[dict]:
    backup = pgen_backups.pop(user_id, None)
    store = load_pgen_backup_store()
    disk_backup = store.pop(str(user_id), None)
    save_pgen_backup_store(store)
    return backup or disk_backup


async def restore_business_profile(bot: Bot, backup: dict) -> tuple[bool, Optional[str], Optional[int]]:
    feedback = backup.get("feedback")
    if not feedback:
        return False, "business_connection_id не найден", None
    try:
        await bot.set_business_account_name(
            business_connection_id=feedback,
            first_name=backup.get("first_name") or "Telegram",
            last_name=backup.get("last_name") or "",
        )
    except TelegramRetryAfter as e:
        return False, str(e), int(e.retry_after)
    except Exception as e:
        return False, str(e), None
    try:
        await bot.remove_business_account_profile_photo(business_connection_id=feedback)
    except TelegramRetryAfter as e:
        return False, str(e), int(e.retry_after)
    except Exception:
        pass
    photo_path = backup.get("photo_path")
    if photo_path and Path(photo_path).exists():
        try:
            await bot.set_business_account_profile_photo(
                business_connection_id=feedback,
                photo=InputProfilePhotoStatic(photo=FSInputFile(photo_path)),
                is_public=False,
            )
        except TelegramRetryAfter as e:
            return False, str(e), int(e.retry_after)
        except Exception as e:
            return False, str(e), None
        try:
            Path(photo_path).unlink(missing_ok=True)
        except Exception:
            pass
    return True, None, None

async def delayed_pgen_restore(
    user_id: int,
    bot: Bot,
    backup: dict,
    chat_id: Optional[int],
    feedback: Optional[str],
    retry_after: Optional[int],
) -> None:
    wait_seconds = max(3, int(retry_after or 60) + 2)
    pgen_restore_eta[user_id] = time.time() + wait_seconds
    try:
        await asyncio.sleep(wait_seconds)
        while True:
            success, error, next_retry = await restore_business_profile(bot, backup)
            if success:
                clear_pgen_backup(user_id)
                if chat_id:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=(
                            "<blockquote>"
                            f"{TICK_EMOJI} <b>Profile Generator восстановлен</b>\n\n"
                            "├ <b>Ник:</b> возвращён\n"
                            "├ <b>Ава:</b> возвращена\n"
                            "└ <b>Cooldown Telegram:</b> пройден"
                            "</blockquote>"
                        ),
                        parse_mode="HTML",
                        business_connection_id=feedback,
                    )
                return
            if next_retry:
                wait_seconds = max(3, int(next_retry) + 2)
                pgen_restore_eta[user_id] = time.time() + wait_seconds
                await asyncio.sleep(wait_seconds)
                continue
            if chat_id:
                await bot.send_message(
                    chat_id=chat_id,
                    text=(
                        "<blockquote>"
                        f"{CROSS_EMOJI} <b>Не удалось восстановить профиль</b>\n\n"
                        f"<code>{escape(error or 'unknown error')}</code>"
                        "</blockquote>"
                    ),
                    parse_mode="HTML",
                    business_connection_id=feedback,
                )
            return
    finally:
        pgen_restore_tasks.pop(user_id, None)
        pgen_restore_eta.pop(user_id, None)


async def pgen_worker(user_id: int, bot: Bot, feedback: str):
    while True:
        avatar_path = PGEN_MEDIA_DIR / f"pgen_{user_id}_{uuid4().hex}.jpg"
        try:
            nickname = generate_profile_name()
            seed = f"{nickname}-{user_id}-{uuid4().hex}"
            style = await download_pgen_avatar(avatar_path, seed)
            try:
                await bot.remove_business_account_profile_photo(business_connection_id=feedback)
            except Exception:
                pass
            await bot.set_business_account_profile_photo(
                business_connection_id=feedback,
                photo=InputProfilePhotoStatic(photo=FSInputFile(str(avatar_path))),
                is_public=False,
            )
            await bot.set_business_account_name(
                business_connection_id=feedback,
                first_name=nickname,
                last_name="",
            )
            print(f"PGEN PROFILE UPDATED: user={user_id} name={nickname} style={style}")
            await asyncio.sleep(random.uniform(PGEN_INTERVAL_MIN, PGEN_INTERVAL_MAX))
        except asyncio.CancelledError:
            raise
        except TelegramRetryAfter as e:
            await asyncio.sleep(float(e.retry_after) + 1)
        except Exception as e:
            print(f"PGEN LOOP ERROR: {e}")
            await asyncio.sleep(10)
        finally:
            try:
                avatar_path.unlink(missing_ok=True)
            except Exception:
                pass


async def stop_pgen_for_user(
    user_id: int,
    bot: Bot,
    chat_id: Optional[int] = None,
    feedback: Optional[str] = None,
) -> dict:
    task = pgen_tasks.pop(user_id, None)
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    restore_task = pgen_restore_tasks.get(user_id)
    if restore_task and not restore_task.done():
        remaining = max(1, int(pgen_restore_eta.get(user_id, time.time()) - time.time()))
        return {"status": "delayed", "retry_after": remaining}

    backup = get_pgen_backup(user_id)
    if not backup:
        return {"status": "not_running"}

    success, error, retry_after = await restore_business_profile(bot, backup)
    if success:
        clear_pgen_backup(user_id)
        return {"status": "restored"}
    if retry_after:
        pgen_restore_tasks[user_id] = asyncio.create_task(
            delayed_pgen_restore(user_id, bot, backup, chat_id, feedback, retry_after)
        )
        return {"status": "delayed", "retry_after": retry_after}
    return {"status": "error", "error": error}


def place_title(place: dict) -> str:
    parts = [place.get("name"), place.get("admin1"), place.get("country")]
    return ", ".join(str(part) for part in parts if part)


def get_media_file_id(reply: Message) -> tuple[Optional[str], Optional[str]]:
    if reply.video:
        return reply.video.file_id, "mp4"
    if reply.animation:
        return reply.animation.file_id, "mp4"
    if reply.video_note:
        return reply.video_note.file_id, "mp4"
    return None, None


def resolve_ffmpeg_path() -> Optional[str]:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return ffmpeg

    candidates = [
        os.getenv("FFMPEG_PATH"),
        os.getenv("FFMPEG_BINARY"),
        "ffmpeg.exe",
        "bin/ffmpeg.exe",
        "tools/ffmpeg.exe",
        "tools/ffmpeg/bin/ffmpeg.exe",
        ".venv/Scripts/ffmpeg.exe",
    ]
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate)
        if not path.is_absolute():
            path = Path.cwd() / path
        if path.exists():
            return str(path)
    return None


def ffmpeg_missing_text(command: str) -> str:
    return (
        f"ffmpeg не найден. Для {command} нужно установить ffmpeg или положить "
        "ffmpeg.exe в папку tools/ffmpeg/bin/ внутри проекта."
    )


VOICEFX_VALUE_FLAGS = {
    "-dist": ("dist", 200),
    "-distortion": ("dist", 200),
    "-crush": ("crush", 100),
    "-bitcrush": ("crush", 100),
    "-echo": ("echo", 55),
    "-reverb": ("reverb", 55),
    "-pitch": ("pitch", 25),
    "-speed": ("speed", 110),
    "-deep": ("deep", 55),
    "-low": ("deep", 55),
    "-chipmunk": ("chipmunk", 55),
    "-high": ("chipmunk", 55),
    "-robot": ("robot", 70),
    "-bass": ("bass", 55),
    "-treble": ("treble", 45),
    "-tremolo": ("tremolo", 55),
    "-vibrato": ("vibrato", 45),
    "-8d": ("eightd", 60),
    "-volume": ("volume", 120),
    "-vol": ("volume", 120),
}

VOICEFX_BOOL_FLAGS = {
    "-reverse": "reverse",
    "-rev": "reverse",
    "-normalize": "normalize",
    "-norm": "normalize",
    "-phone": "phone",
    "-radio": "radio",
    "-lofi": "lofi",
    "-nightcore": "nightcore",
    "-demon": "demon",
    "-alien": "alien",
    "-megaphone": "megaphone",
}

VOICEFX_PRESETS = {
    "robot": {"robot": 80, "dist": 90, "treble": 25},
    "demon": {"deep": 85, "bass": 80, "reverb": 55, "dist": 80},
    "alien": {"chipmunk": 45, "vibrato": 70, "echo": 25},
    "nightcore": {"chipmunk": 40, "speed": 118, "treble": 30},
    "lofi": {"lofi": True, "dist": 90, "bass": 25},
    "phone": {"phone": True, "dist": 60},
    "radio": {"radio": True, "treble": 35},
    "megaphone": {"megaphone": True, "dist": 110},
}


def is_number_token(value: str) -> bool:
    try:
        float(value.replace(",", "."))
        return True
    except Exception:
        return False


def clamp_float(value: Any, minimum: float, maximum: float) -> float:
    try:
        number = float(str(value).replace(",", "."))
    except Exception:
        number = minimum
    return max(minimum, min(maximum, number))


def parse_voicefx_args(raw: str) -> tuple[dict, list[str]]:
    options = {}
    errors = []
    try:
        tokens = shlex.split(raw or "")
    except ValueError:
        tokens = (raw or "").split()
    i = 0
    while i < len(tokens):
        token = tokens[i].lower()
        if token in {"help", "-help", "--help", "effects"}:
            options["help"] = True
            i += 1
            continue
        if token in {"-preset", "-p"}:
            preset = tokens[i + 1].lower() if i + 1 < len(tokens) else ""
            if preset in VOICEFX_PRESETS:
                options.update(VOICEFX_PRESETS[preset])
                i += 2
                continue
            errors.append(f"неизвестный preset: {preset or token}")
            i += 2 if i + 1 < len(tokens) else 1
            continue
        if token in VOICEFX_VALUE_FLAGS:
            key, default = VOICEFX_VALUE_FLAGS[token]
            value = default
            if i + 1 < len(tokens) and is_number_token(tokens[i + 1]):
                value = tokens[i + 1]
                i += 1
            options[key] = value
        elif token in VOICEFX_BOOL_FLAGS:
            options[VOICEFX_BOOL_FLAGS[token]] = True
        else:
            errors.append(f"неизвестный флаг: {token}")
        i += 1
    return options, errors


def voicefx_help_text() -> str:
    return (
        "<blockquote>"
        f"{GOLOS_EMOJI} <b>VoiceFX</b>\n\n"
        "├ <b>Формат:</b> ответом на voice/audio/video\n"
        "├ <b>Пример:</b> <code>.voicefx -dist 200 -reverse</code>\n"
        "├ <b>Preset:</b> <code>-preset robot/demon/alien/nightcore/lofi/phone/radio</code>\n\n"
        "<b>Эффекты:</b>\n"
        "├ <code>-dist 0-300</code> distortion/overdrive\n"
        "├ <code>-crush 0-100</code> bitcrusher/robot noise\n"
        "├ <code>-deep 0-100</code> низкий голос\n"
        "├ <code>-chipmunk 0-100</code> высокий голос\n"
        "├ <code>-pitch -80..80</code> ручная высота\n"
        "├ <code>-speed 50-200</code> скорость\n"
        "├ <code>-echo 0-100</code> эхо\n"
        "├ <code>-reverb 0-100</code> объём\n"
        "├ <code>-bass 0-100</code> бас\n"
        "├ <code>-treble 0-100</code> верх\n"
        "├ <code>-robot 0-100</code> робот\n"
        "├ <code>-tremolo 0-100</code> дрожание\n"
        "├ <code>-vibrato 0-100</code> вибрато\n"
        "├ <code>-8d 0-100</code> stereo swirl\n"
        "├ <code>-volume 0-200</code> громкость\n"
        "├ <code>-reverse</code> реверс\n"
        "├ <code>-phone</code> телефон\n"
        "├ <code>-radio</code> радио\n"
        "├ <code>-lofi</code> low quality\n"
        "├ <code>-nightcore</code> fast/high\n"
        "├ <code>-demon</code> deep dark\n"
        "├ <code>-alien</code> alien voice\n"
        "└ <code>-normalize</code> выравнивание громкости"
        "</blockquote>"
    )


def get_voicefx_media_file(reply: Message) -> tuple[Optional[str], str, str]:
    if reply.voice:
        return reply.voice.file_id, "ogg", "voice"
    if reply.audio:
        suffix = Path(reply.audio.file_name or "").suffix.lower().lstrip(".") or "mp3"
        return reply.audio.file_id, suffix[:8], "audio"
    if reply.video:
        return reply.video.file_id, "mp4", "video"
    if reply.animation:
        return reply.animation.file_id, "mp4", "animation"
    if reply.video_note:
        return reply.video_note.file_id, "mp4", "video_note"
    if reply.document and reply.document.mime_type:
        mime = reply.document.mime_type.lower()
        if mime.startswith("audio/") or mime.startswith("video/"):
            suffix = Path(reply.document.file_name or "").suffix.lower().lstrip(".") or "bin"
            return reply.document.file_id, suffix[:8], "document"
    return None, "bin", ""


def add_atempo_filters(filters: list[str], factor: float) -> None:
    factor = clamp_float(factor, 0.25, 4.0)
    while factor > 2.0:
        filters.append("atempo=2.0")
        factor /= 2.0
    while factor < 0.5:
        filters.append("atempo=0.5")
        factor /= 0.5
    filters.append(f"atempo={factor:.5f}")


def add_pitch_filters(filters: list[str], factor: float) -> None:
    factor = clamp_float(factor, 0.45, 1.9)
    if abs(factor - 1.0) < 0.01:
        return
    filters.append(f"asetrate=48000*{factor:.5f}")
    filters.append("aresample=48000")
    add_atempo_filters(filters, 1.0 / factor)


def voicefx_filter_chain(options: dict) -> tuple[str, list[str]]:
    filters = ["aformat=sample_rates=48000"]
    labels = []

    if options.get("nightcore"):
        options.setdefault("chipmunk", 38)
        options.setdefault("speed", 118)
        options.setdefault("treble", 25)
        labels.append("nightcore")
    if options.get("demon"):
        options.setdefault("deep", 85)
        options.setdefault("bass", 80)
        options.setdefault("reverb", 45)
        options.setdefault("dist", 80)
        labels.append("demon")
    if options.get("alien"):
        options.setdefault("chipmunk", 45)
        options.setdefault("vibrato", 70)
        options.setdefault("echo", 25)
        labels.append("alien")

    if "pitch" in options:
        pitch = clamp_float(options["pitch"], -80, 80)
        add_pitch_filters(filters, 1.0 + pitch / 100.0)
        labels.append(f"pitch {pitch:g}%")
    if "deep" in options:
        amount = clamp_float(options["deep"], 0, 100)
        add_pitch_filters(filters, 1.0 - amount / 180.0)
        labels.append(f"deep {amount:g}%")
    if "chipmunk" in options:
        amount = clamp_float(options["chipmunk"], 0, 100)
        add_pitch_filters(filters, 1.0 + amount / 120.0)
        labels.append(f"chipmunk {amount:g}%")

    if "speed" in options:
        speed = clamp_float(options["speed"], 50, 200)
        add_atempo_filters(filters, speed / 100.0)
        labels.append(f"speed {speed:g}%")

    if options.get("phone"):
        filters.extend(["highpass=f=300", "lowpass=f=3400", "acompressor=threshold=-18dB:ratio=4:attack=5:release=80"])
        labels.append("phone")
    if options.get("radio"):
        filters.extend(["highpass=f=500", "lowpass=f=2600", "acompressor=threshold=-22dB:ratio=5:attack=4:release=60"])
        labels.append("radio")
    if options.get("megaphone"):
        filters.extend(["highpass=f=650", "lowpass=f=3200", "acompressor=threshold=-25dB:ratio=6:attack=3:release=45", "volume=1.25"])
        labels.append("megaphone")
    if options.get("lofi"):
        filters.extend(["aresample=16000", "aresample=48000", "lowpass=f=3600", "acrusher=bits=9:mix=0.35"])
        labels.append("lofi")

    if "dist" in options:
        amount = clamp_float(options["dist"], 0, 300)
        drive = 1.0 + amount / 17.0
        post_gain = max(0.22, 1.0 - amount / 430.0)
        clip_param = min(3.0, 0.85 + amount / 95.0)
        filters.extend([
            f"volume={drive:.2f}",
            f"asoftclip=type=tanh:param={clip_param:.2f}",
        ])
        if amount >= 140:
            filters.extend([
                f"volume={1.0 + amount / 95.0:.2f}",
                "asoftclip=type=atan:param=2.85",
            ])
        if amount >= 230:
            filters.extend([
                f"volume={1.0 + amount / 120.0:.2f}",
                "asoftclip=type=tanh:param=3.0",
            ])
        filters.extend([
            f"volume={post_gain:.2f}",
            "acompressor=threshold=-8dB:ratio=2.2:attack=2:release=60",
            "alimiter=limit=0.94",
        ])
        labels.append(f"dist {amount:g}%")
    if "crush" in options:
        amount = clamp_float(options["crush"], 0, 100)
        bits = max(2, min(16, int(round(14 - amount * 0.12))))
        samples = max(1, min(32, int(round(1 + amount / 5))))
        mix = max(0.08, min(1.0, amount / 100.0))
        filters.append(f"acrusher=bits={bits}:samples={samples}:mix={mix:.2f}:mode=log")
        filters.append("alimiter=limit=0.9")
        labels.append(f"crush {amount:g}%")
    if "robot" in options:
        amount = clamp_float(options["robot"], 0, 100)
        depth = 0.18 + amount / 180.0
        filters.extend([
            f"tremolo=f={22 + amount / 4:.2f}:d={min(0.85, depth):.2f}",
            f"acrusher=bits={max(5, int(12 - amount / 18))}:mix={min(0.65, amount / 140):.2f}",
        ])
        labels.append(f"robot {amount:g}%")
    if "bass" in options:
        amount = clamp_float(options["bass"], 0, 100)
        filters.append(f"bass=g={amount / 8:.2f}:f=110:w=0.55")
        labels.append(f"bass {amount:g}%")
    if "treble" in options:
        amount = clamp_float(options["treble"], 0, 100)
        filters.append(f"treble=g={amount / 10:.2f}:f=5200:w=0.45")
        labels.append(f"treble {amount:g}%")
    if "echo" in options:
        amount = clamp_float(options["echo"], 0, 100)
        delay = int(70 + amount * 5)
        decay = 0.12 + amount / 180.0
        filters.append(f"aecho=0.8:0.88:{delay}:{min(0.78, decay):.2f}")
        labels.append(f"echo {amount:g}%")
    if "reverb" in options:
        amount = clamp_float(options["reverb"], 0, 100)
        decay1 = min(0.8, 0.18 + amount / 160.0)
        decay2 = min(0.55, 0.12 + amount / 220.0)
        decay3 = min(0.38, 0.08 + amount / 300.0)
        filters.append(f"aecho=0.75:0.88:60|125|190:{decay1:.2f}|{decay2:.2f}|{decay3:.2f}")
        labels.append(f"reverb {amount:g}%")
    if "tremolo" in options:
        amount = clamp_float(options["tremolo"], 0, 100)
        filters.append(f"tremolo=f={4 + amount / 8:.2f}:d={min(0.95, amount / 100):.2f}")
        labels.append(f"tremolo {amount:g}%")
    if "vibrato" in options:
        amount = clamp_float(options["vibrato"], 0, 100)
        filters.append(f"vibrato=f={4 + amount / 12:.2f}:d={min(1.0, amount / 100):.2f}")
        labels.append(f"vibrato {amount:g}%")
    if "eightd" in options:
        amount = clamp_float(options["eightd"], 0, 100)
        filters.extend([
            "aformat=channel_layouts=stereo",
            f"apulsator=hz={0.05 + amount / 900:.3f}:amount={min(1.0, amount / 100):.2f}",
        ])
        labels.append(f"8d {amount:g}%")
    if "volume" in options:
        volume = clamp_float(options["volume"], 0, 200)
        filters.append(f"volume={volume / 100:.3f}")
        labels.append(f"volume {volume:g}%")
    if options.get("normalize"):
        filters.append("dynaudnorm=f=150:g=15")
        labels.append("normalize")
    if options.get("reverse"):
        filters.append("areverse")
        labels.append("reverse")

    filters.append("alimiter=limit=0.98")
    return ",".join(filters), labels


async def convert_voicefx(input_path: Path, output_path: Path, options: dict) -> tuple[bool, str, list[str]]:
    ffmpeg = resolve_ffmpeg_path()
    if not ffmpeg:
        return False, ffmpeg_missing_text(".voicefx"), []
    filter_chain, labels = voicefx_filter_chain(options)
    if not labels:
        return False, "эффекты не выбраны", []
    process = await asyncio.create_subprocess_exec(
        ffmpeg,
        "-y",
        "-i",
        str(input_path),
        "-t",
        "300",
        "-vn",
        "-map",
        "0:a:0?",
        "-filter:a",
        filter_chain,
        "-c:a",
        "libopus",
        "-b:a",
        "96k",
        "-vbr",
        "on",
        str(output_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()
    if process.returncode != 0:
        return False, stderr.decode("utf-8", errors="ignore")[-700:] or "ошибка ffmpeg", labels
    return True, "", labels


def get_text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def wrap_watermark_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        width, _ = get_text_size(draw, candidate, font)
        if width <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines[:4]


def create_watermark_image(input_path: Path, output_path: Path, text: str) -> None:
    image = Image.open(input_path).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    width, height = image.size
    font_size = max(24, min(width, height) // 18)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    lines = wrap_watermark_text(draw, text, font, int(width * 0.72))
    line_sizes = [get_text_size(draw, line, font) for line in lines]
    text_width = max((size[0] for size in line_sizes), default=0)
    line_height = max((size[1] for size in line_sizes), default=font_size)
    padding = max(16, font_size // 2)
    block_width = text_width + padding * 2
    block_height = line_height * len(lines) + padding * 2 + max(0, len(lines) - 1) * 8
    x = max(padding, width - block_width - padding)
    y = max(padding, height - block_height - padding)
    draw.rounded_rectangle(
        (x, y, x + block_width, y + block_height),
        radius=max(12, padding // 2),
        fill=(0, 0, 0, 145),
        outline=(255, 255, 255, 95),
        width=max(2, font_size // 18),
    )
    cursor_y = y + padding
    for line in lines:
        draw.text(
            (x + padding, cursor_y),
            line,
            font=font,
            fill=(255, 255, 255, 240),
            stroke_width=2,
            stroke_fill=(0, 0, 0, 180),
        )
        cursor_y += line_height + 8
    watermarked = Image.alpha_composite(image, overlay).convert("RGB")
    watermarked.save(output_path, quality=94)


async def convert_to_circle(input_path: Path, output_path: Path) -> tuple[bool, str]:
    ffmpeg = resolve_ffmpeg_path()
    if not ffmpeg:
        return False, ffmpeg_missing_text(".circle")
    process = await asyncio.create_subprocess_exec(
        ffmpeg,
        "-y",
        "-i",
        str(input_path),
        "-t",
        "60",
        "-vf",
        "crop=min(iw\\,ih):min(iw\\,ih),scale=512:512,setsar=1",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-pix_fmt",
        "yuv420p",
        str(output_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()
    if process.returncode != 0:
        return False, stderr.decode("utf-8", errors="ignore")[-500:] or "ошибка ffmpeg"
    return True, ""


def make_board(board):

    kb = []

    for i in range(3):

        row = []

        for j in range(3):

            idx = i * 3 + j

            row.append(
                InlineKeyboardButton(
                    text=f"  {board[idx]}  ",
                    callback_data=f"xo_move:{idx}"
                )
            )

        kb.append(row)
    
    kb.append(
        [
            InlineKeyboardButton(
                text="Сдаться",
                callback_data="xo_surrender"
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=kb
    )


def check_winner(board):

    wins = [
        [0,1,2],
        [3,4,5],
        [6,7,8],

        [0,3,6],
        [1,4,7],
        [2,5,8],

        [0,4,8],
        [2,4,6]
    ]

    for combo in wins:

        a, b, c = combo

        if (
            board[a] == board[b] == board[c]
            and board[a] != "⬜️"
        ):
            return board[a]

    if "⬜️" not in board:
        return "draw"

    return None


CUSTOM_COMMANDS_FILE = Path("custom_commands.json")


def load_custom_commands() -> dict[str, list[dict]]:
    if not CUSTOM_COMMANDS_FILE.exists():
        save_custom_commands({})
        return {}

    try:
        data = json.loads(CUSTOM_COMMANDS_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    save_custom_commands({})
    return {}


def save_custom_commands(categories: dict[str, list[dict]]) -> None:
    CUSTOM_COMMANDS_FILE.write_text(
        json.dumps(categories, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def get_help_commands() -> list[str]:
    commands = []
    for category_cmds in load_custom_commands().values():
        for cmd in category_cmds:
            if cmd.get("name"):
                commands.append(cmd["name"])
    return commands


def get_category_counts() -> dict[str, int]:
    categories = load_custom_commands()
    return {cat: len(cmds) for cat, cmds in categories.items()}


def build_help_keyboard(
    page: int = 0,
    selected_category: Optional[str] = None,
    selected_cmd: Optional[str] = None,
    username: Optional[str] = None,
) -> InlineKeyboardMarkup:
    categories_dict = load_custom_commands()
    page = max(0, page)
    per_page = 9
    builder = InlineKeyboardBuilder()
    row = []
    if selected_category is None:
        category_list = sorted(categories_dict.keys())
        total_pages = max(
            1,
            (len(category_list) + per_page - 1) // per_page
        )
        page = min(page, total_pages - 1)
        page_categories = category_list[
            page * per_page:(page + 1) * per_page
        ]
        for category in page_categories:
            count = len(categories_dict.get(category, []))
            row.append(
                InlineKeyboardButton(
                    text=f"{category} ({count})",
                    callback_data=f"help_category:{category}"
                )
            )
            if len(row) == 3:
                builder.row(*row)
                row = []
        if row:
            builder.row(*row)
        nav = []
        if page > 0:
            nav.append(
                InlineKeyboardButton(
                    text="⬅",
                    callback_data=f"help_cat_page:{page - 1}"
                )
            )
        if page < total_pages - 1:
            nav.append(
                InlineKeyboardButton(
                    text="➡",
                    callback_data=f"help_cat_page:{page + 1}"
                )
            )
        if nav:
            builder.row(*nav)
    else:
        commands = categories_dict.get(selected_category, [])
        total_pages = max(
            1,
            (len(commands) + per_page - 1) // per_page
        )
        page = min(page, total_pages - 1)
        page_commands = commands[
            page * per_page:(page + 1) * per_page
        ]
        for cmd_obj in page_commands:
            cmd_name = cmd_obj.get("name", "")
            row.append(
                InlineKeyboardButton(
                    text=cmd_name,
                    callback_data=f"help_cmd:{selected_category}:{cmd_name}"
                )
            )
            if len(row) == 3:
                builder.row(*row)
                row = []
        if row:
            builder.row(*row)
        nav = []
        if page > 0:
            nav.append(
                InlineKeyboardButton(
                    text="⬅",
                    callback_data=f"help_cmd_page:{page - 1}:{selected_category}"
                )
            )
        if page < total_pages - 1:
            nav.append(
                InlineKeyboardButton(
                    text="➡",
                    callback_data=f"help_cmd_page:{page + 1}:{selected_category}"
                )
            )
        if nav:
            builder.row(*nav)
        builder.row(
            InlineKeyboardButton(
                text="‹ Назад",
                callback_data="help_back"
            )
        )

    for row in builder.export():
        for btn in row:
            if btn.callback_data:
                print(
                    f"BTN: {btn.text} | "
                    f"LEN: {len(btn.callback_data.encode('utf-8'))} | "
                    f"DATA: {btn.callback_data}"
                )

    return builder.as_markup()

def get_help_caption(category: Optional[str] = None, cmd: Optional[str] = None):
    categories_dict = load_custom_commands()
    
    if category is None and cmd is None:
        return (
            "<blockquote expandable>"
            "<b>"
            f"{PEN_EMOJI} "
            "Список команд"
            "</b>\n\n"
            "├ Выберите категорию ниже\n"
            "├ Чтобы посмотреть команды внутри\n"
            "└ И узнать описание каждой\n"
            "</blockquote>\n\n"
        )

    if category is not None and cmd is None:
        cmds = categories_dict.get(category, [])
        count = len(cmds)
        return (
            "<blockquote expandable>"
            "<b>"
            f"{PEN_EMOJI} "
            f"Категория: {category}"
            "</b>\n\n"
            f"├ Команд в категории: {count}\n"
            "├ Выберите нужную команду\n"
            "└ Посмотрите описание и использование"
            "</blockquote>"
        )

    if category is not None and cmd is not None:
        cmds = categories_dict.get(category, [])
        for cmd_obj in cmds:
            if cmd_obj.get("name") == cmd:
                desc = cmd_obj.get("description", "Описание отсутствует")
                return (
                    "<blockquote expandable>"
                    "<b>"
                    f"{PEN_EMOJI} "
                    f"{cmd}"
                    "</b>\n\n"
                    "├ <b>Категория:</b> "
                    f"{category}\n"
                    "├ <b>Использование:</b>\n"
                    f"│ <code>{cmd}</code>\n\n"
                    "└ Команда успешно найдена"
                    "</blockquote>\n\n"
                    "<blockquote expandable>"
                    "<b>"
                    f"{INFO_EMOJI} "
                    "Описание команды"
                    "</b>\n\n"
                    f"{desc}"
                    "</blockquote>"
                )

    return (
        "<blockquote expandable>"
        "<b>"
        f"{CROSS_EMOJI} "
        "Команда не найдена"
        "</b>"
        "</blockquote>"
    )
def help_kb(username: Optional[str] = None) -> InlineKeyboardMarkup:
    buttons = []
    if username:
        buttons.append([
            InlineKeyboardButton(
                text="Перейти в бота",
                url=f"https://t.me/{username}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else InlineKeyboardMarkup(inline_keyboard=[])


def is_business_message(msg: Message) -> bool:
    return bool(getattr(msg, "business_connection_id", None))


async def get_edit_target(msg: Message, initial_text: str = "", **kwargs) -> Message:
    if is_business_message(msg):
        return msg
    return await msg.answer(text=initial_text, **kwargs)

def create_mines_field():
    size = 6
    field = []
    for y in range(size):
        row = []
        for x in range(size):
            if random.randint(1, 5) == 1:
                row.append("💣")
            else:
                row.append(
                    random.choice([
                        "1️⃣",
                        "2️⃣",
                        "3️⃣",
                        "4️⃣"
                     ])
                )
        field.append(row)
    return field


def count_bombs(field, x, y):
    bombs = 0
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            nx = x + dx
            ny = y + dy
            if (
                0 <= nx < SIZE
                and 0 <= ny < SIZE
            ):
                if field[ny][nx] == "💣":
                    bombs += 1
    return bombs



def build_mines_keyboard(game_id):

    game = mines_games[game_id]

    builder = InlineKeyboardBuilder()

    size = 6

    for y in range(size):

        row = []

        for x in range(size):

            key = f"{x}:{y}"

            if key in game["opened"]:

                value = game["field"][y][x]

                if value == "💣":

                    text = "💣"

                else:

                    text = value

            else:

                text = "⬜️"

            row.append(

                InlineKeyboardButton(
                    text=text,
                    callback_data=f"m:{game_id}:{x}:{y}"
                )
            )

        builder.row(*row)

    return builder.as_markup()


def other_commands() -> Router:
    router = Router()


    @router.business_message(F.text==".help")
    @router.message(F.text==".help")
    async def helper(msg: Message, bot: Bot, state: Any = None) -> None:
        info = await bot.get_me()
        caption = get_help_caption()
        if is_business_message(msg):
            await msg.edit_text(text=caption, parse_mode='HTML', reply_markup=build_help_keyboard(page=0, username=info.username))
        else:
            await msg.answer(text=caption, parse_mode='HTML', reply_markup=build_help_keyboard(page=0, username=info.username))

    @router.callback_query(F.data.startswith("help_cat_page:"))
    @router.callback_query(F.data.startswith("help_page:"))
    async def help_cat_page_callback(call: CallbackQuery):
        parts = call.data.split(":")
        page = int(parts[1])
        selected_cmd = parts[2] if len(parts) > 2 else None
        if selected_cmd == "None":
            selected_cmd = None

        selected_category = None
        if selected_cmd is not None:
            for category, cmds in load_custom_commands().items():
                for cmd in cmds:
                    if cmd.get("name") == selected_cmd:
                        selected_category = category or "Общие"
                        break
                if selected_category is not None:
                    break

        info = await call.bot.get_me()
        caption = get_help_caption(category=selected_category, cmd=selected_cmd)
        try:
            await call.message.edit_text(
                text=caption,
                parse_mode='HTML',
                reply_markup=build_help_keyboard(page=page, selected_category=selected_category, selected_cmd=selected_cmd, username=info.username)
            )
        except Exception:
            pass
        await call.answer()

    @router.callback_query(F.data == "help_back")
    async def help_back_callback(call: CallbackQuery):
        info = await call.bot.get_me()
        caption = get_help_caption()
        try:
            await call.message.edit_text(
                text=caption,
                parse_mode='HTML',
                reply_markup=build_help_keyboard(page=0, username=info.username)
            )
        except Exception:
            pass
        await call.answer()

    @router.callback_query(F.data.startswith("help_category:"))
    async def help_category_callback(call: CallbackQuery):
        try:
            logging.info(f"help_category_callback called with data: {call.data}")
            parts = call.data.split(":", 1)
            logging.info(f"Split parts: {parts}")

            category = None
            if len(parts) > 1:
                category = parts[1]
                logging.info(f"Extracted category: {category}")

            if category is None:
                logging.warning("Category is None or could not be resolved, returning")
                await call.answer()
                return

            info = await call.bot.get_me()
            caption = get_help_caption(category=category)
            logging.info(f"Generated caption for category {category}")
            
            await call.message.edit_text(
                text=caption,
                parse_mode='HTML',
                reply_markup=build_help_keyboard(page=0, selected_category=category, username=info.username)
            )
            logging.info(f"Successfully edited message for category {category}")
            await call.answer()
        except Exception as e:
            logging.error(f"Error in help_category_callback: {e}", exc_info=True)
            await call.answer()

    @router.callback_query(F.data.startswith("help_cmd_page:"))
    async def help_cmd_page_callback(call: CallbackQuery):
        try:
            logging.info(f"help_cmd_page_callback called with data: {call.data}")
            parts = call.data.split(":", 2)
            page = int(parts[1]) if len(parts) > 1 else 0
            category = unquote_plus(parts[2]) if len(parts) > 2 else None
            logging.info(f"Parsed: page={page}, category={category}")

            info = await call.bot.get_me()
            caption = get_help_caption(category=category)
            await call.message.edit_text(
                text=caption,
                parse_mode='HTML',
                reply_markup=build_help_keyboard(page=page, selected_category=category, username=info.username)
            )
            logging.info(f"Successfully updated page {page} for category {category}")
            await call.answer()
        except Exception as e:
            logging.error(f"Error in help_cmd_page_callback: {e}", exc_info=True)
            await call.answer()

    @router.callback_query(F.data.startswith("help_cmd:"))
    async def help_cmd_callback(call: CallbackQuery):
        try:
            logging.info(f"help_cmd_callback called with data: {call.data}")
            parts = call.data.split(":", 2)
            category = None
            cmd = None
            if len(parts) >= 3:
                category = parts[1]
                cmd = parts[2]
                logging.info(f"Parsed: category={category}, cmd={cmd}")
            else:
                logging.warning(f"Invalid command callback format: {call.data}")
            
            if cmd is None:
                await call.answer()
                return

            info = await call.bot.get_me()
            caption = get_help_caption(category=category, cmd=cmd)
            await call.message.edit_text(
                text=caption,
                parse_mode='HTML',
                reply_markup=build_help_keyboard(page=0, selected_category=category, selected_cmd=cmd, username=info.username)
            )
            logging.info(f"Successfully showed command {cmd} from category {category}")
            await call.answer()
        except Exception as e:
            logging.error(f"Error in help_cmd_callback: {e}", exc_info=True)
            await call.answer()

    @router.message(F.text == ".xo")
    @router.business_message(F.text == ".xo")
    async def xo_create(msg: Message, bot):

        feedback = getattr(
            msg,
            "business_connection_id",
            None
        )

        business_connection = None

        if feedback is not None:
            business_connection = await bot.get_business_connection(
                feedback
            )

        if (
            business_connection is not None
            and msg.from_user.id != business_connection.user.id
        ):
            return

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Присоединиться",
                         callback_data=f"xo_join:{msg.from_user.id}"
                    )
                ]
            ]
        )

        await msg.edit_text(
            "<b>"
            '<tg-emoji emoji-id="6077657514462158077">🛡</tg-emoji> '
            "Создана игра в крестики-нолики\n\n"
            "Нажмите кнопку ниже чтобы присоединиться."
            "</b>",
            reply_markup=kb,
            parse_mode="HTML"
        )

    @router.callback_query(F.data.startswith("xo_join:"))
    async def xo_join(call: CallbackQuery):

        creator_id = int(
            call.data.split(":")[1]
        )

        if call.from_user.id == creator_id:

            return await call.answer(
                "Нельзя играть с собой",
                show_alert=True
            )

        x_player, o_player = random.sample(
            [creator_id, call.from_user.id],
            2
        )

        board = ["⬜️"] * 9

        games[call.message.message_id] = {
            "board": board,
            "turn": x_player,
            "x": x_player,
            "o": o_player
        }

        game = games[call.message.message_id]

        x_user = await call.bot.get_chat(game["x"])
        o_user = await call.bot.get_chat(game["o"])

        x_name = user_link(
             game["x"],
            x_user.first_name
        )

        o_name = user_link(
            game["o"],
                o_user.first_name
        )

        turn_symbol = (
            '❌'
            if game["turn"] == game["x"]
            else '⭕️'
        )

        text = (
            "<b>"
            '<tg-emoji emoji-id="6077657514462158077">🛡</tg-emoji> '
            "Крестики-нолики\n\n"

            f"<blockquote>├ {x_name} — "
            '❌\n'
            f"└ {o_name} — "
            '⭕️</blockquote>\n\n'

            f"Ход: {turn_symbol}"
            "</b>"
        )

        await call.message.edit_text(
            text,
            reply_markup=make_board(board),
            parse_mode="HTML"
        )

    @router.callback_query(F.data.startswith("xo_move:"))
    async def xo_move(call: CallbackQuery):

        pos = int(
            call.data.split(":")[1]
        )

        game = games.get(
            call.message.message_id
        )

        if not game:

            return await call.answer(
                 "Игра не найдена",
                show_alert=True
            )

        if call.from_user.id != game["turn"]:

            return await call.answer(
                "Сейчас не ваш ход",
                show_alert=True
            )

        board = game["board"]

        if board[pos] != "⬜️":

            return await call.answer(
                "Клетка занята",
                show_alert=True
            )

        symbol = (
           "❌"
           if call.from_user.id == game["x"]
           else "⭕️"
        )         

        board[pos] = symbol

        winner = check_winner(board)

        if winner:

            if winner == "draw":

                text = (
                    "<b><i>"
                    '<tg-emoji emoji-id="6077657514462158077">🛡</tg-emoji> '
                    "Ничья"
                    "</i></b>"
                )

            else:

                winner_id = (
                    game["x"]
                    if winner == "❌"
                    else game["o"]
                )

                winner_user = await call.bot.get_chat(
                     winner_id
                )

                winner_name = user_link(
                    winner_id,
                    winner_user.first_name
                )             
                winner_symbol = (
                    '❌'
                    if winner == "❌"
                    else '⭕️'
                )    

                text = (
                    "<b>"
                    '<tg-emoji emoji-id="6077657514462158077">🛡</tg-emoji> '
                    "Победитель\n\n"
                    f"<blockquote>└ {winner_name} — {winner_symbol}</blockquote>"
                    "</b>"
                )

            try:

                await call.message.edit_text(
                    text,
                    reply_markup=make_board(board),
                    parse_mode="HTML"
                )

            except TelegramBadRequest:
                pass

            del games[call.message.message_id]

            return

        game["turn"] = (
        game["o"]
            if game["turn"] == game["x"]
            else game["x"]
        )

        x_user = await call.bot.get_chat(game["x"])
        o_user = await call.bot.get_chat(game["o"])

        x_name = user_link(
            game["x"],
            x_user.first_name
        )

        o_name = user_link(
            game["o"],
            o_user.first_name
        )

        turn_symbol = (
            '❌'
            if game["turn"] == game["x"]
            else '⭕️'
        )

        text = (
            "><b>"
            '<tg-emoji emoji-id="6077657514462158077">🛡</tg-emoji> '
            "Крестики-нолики\n\n"

            f"<blockquote>├ {x_name} — "
            '❌\n'

            f"└ {o_name} — "
            '⭕️</blockquote>\n\n'

            f"Ход: {turn_symbol}"
            "</b>"
        )

        try:

            await call.message.edit_text(
                text,
               reply_markup=make_board(board),
                parse_mode="HTML"
            )

        except TelegramBadRequest:
            pass

        await call.answer()

    @router.callback_query(F.data == "xo_surrender")
    async def xo_surrender(call: CallbackQuery):

        game = games.get(
            call.message.message_id
        )

        if not game:
            return await call.answer(
                "Игра не найдена",
                show_alert=True
            )

        if call.from_user.id not in [
            game["x"],
            game["o"]
        ]:
            return await call.answer()

        loser_id = call.from_user.id

        winner_id = (
            game["o"]
            if loser_id == game["x"]
            else game["x"]
        ) 

        winner_user = await call.bot.get_chat(
            winner_id
        )

        winner_name = user_link(
            winner_id,
            winner_user.first_name
        )

        text = (
            "<b>"
            '<tg-emoji emoji-id="6077657514462158077">🛡</tg-emoji> '
            "Игрок сдался\n\n"
            f"<blockquote><tg-emoji emoji-id='5409008750893734809'>🏆</tg-emoji> Победитель: \n └ {winner_name}</blockquote>"
            "</b>"
        )

        try:

            await call.message.edit_text(
                text,
                parse_mode="HTML"
            )

        except TelegramBadRequest as e:
            print(e)

        del games[call.message.message_id]

        await call.answer(
            "Вы сдались"
        )

    @router.message(F.text.startswith(".tts"))
    @router.business_message(F.text.startswith(".tts"))
    async def tts_handler(msg: Message, bot):

        feedback = getattr(
            msg,
            "business_connection_id",
            None
        )

        business_connection = None

        if feedback is not None:
            business_connection = await bot.get_business_connection(
                feedback
            )
        if (
            business_connection is not None
            and msg.from_user.id != business_connection.user.id
        ):
            return

        args = msg.text.split()

        if len(args) == 1:

            text = (
                "<b>"
                '<tg-emoji emoji-id="5258331647358540449">✍️</tg-emoji> '
                "Использование команды:\n"
                "<code>.tts [текст]</code>"
                "</b>\n\n"

                "<b>"
                '<tg-emoji emoji-id="5258216851472654189">💡</tg-emoji> '
                "Описание команды:"
                "</b>\n"

                "<blockquote expandable>"

                "Преобразует текст в голосовое сообщение.\n\n"

                "<b>Примеры использования:</b>\n\n"

                "• <code>.tts Привет мир</code>\n"
                "• <code>.tts -voice dima Привет</code>\n"
                "• <code>.tts -voice jenny hello</code>\n"
                "• <code>.tts -speed 1.5 Привет</code>\n"
                "• <code>.tts -dm Привет</code>\n\n"

                "<b>Голоса RU:</b>\n"
                "├ <code>dima</code>\n"
                "└ <code>sveta</code>\n\n"

                "<b>Голоса EN:</b>\n"
                "├ <code>jenny</code>\n"
                "├ <code>guy</code>\n"
                "└ <code>aria</code>"

                "</blockquote>\n\n"

                "<b>"
                '<tg-emoji emoji-id="5258474669769497337">❗️</tg-emoji> '
                "Дополнительные моменты:"
                "</b>\n"

                "<blockquote>"

                "<code>-voice [голос]</code> — выбрать голос\n\n"

                "<code>-speed [значение]</code> — скорость озвучки\n"
                "от <code>0.5</code> до <code>2.0</code>\n\n"

                "<code>-dm</code> — отправить голосовое сообщение в ЛС"

                "</blockquote>"
            )

            try:
                if feedback:
                    await bot.edit_message_text(
                        chat_id=msg.chat.id,
                        message_id=msg.message_id,
                        business_connection_id=feedback,
                        text=text,
                        parse_mode="HTML"
                    )

                else:
                    await msg.edit_text(
                        text,
                        parse_mode="HTML"
                    )

            except:
                await bot.send_message(
                    chat_id=msg.chat.id,
                    text=text,
                    parse_mode="HTML",
                    business_connection_id=feedback
                )

            return

        voice_map = {
            "dima": "ru-RU-DmitryNeural",
            "sveta": "ru-RU-SvetlanaNeural",

            "jenny": "en-US-JennyNeural",
            "guy": "en-US-GuyNeural",
            "aria": "en-US-AriaNeural"
        }

        voice = "ru-RU-DmitryNeural"
        speed = "+0%"
        send_dm = False

        text_parts = []
        i = 1

        while i < len(args):
            arg = args[i]
            if arg == "-voice" and i + 1 < len(args):
                custom_voice = args[i + 1].lower()
                if custom_voice in voice_map:
                    voice = voice_map[custom_voice]

                i += 2
                continue

            elif arg == "-speed" and i + 1 < len(args):

                try:
                    speed_value = float(args[i + 1])
                    percent = int((speed_value - 1.0) * 100)
                    if percent >= 0:
                        speed = f"+{percent}%"
                    else:
                        speed = f"{percent}%"

                except:
                    pass

                i += 2
                continue

            elif arg == "-dm":
                send_dm = True
                i += 1
                continue

            else:
                text_parts.append(arg)
                i += 1

        text_to_voice = " ".join(text_parts)
        if not text_to_voice:
            return

        status_message = None

        try:

            await bot.edit_message_text(
                chat_id=msg.chat.id,
                message_id=msg.message_id,
                business_connection_id=feedback if feedback else None,
                text=(
                    "<b>"
                    '<tg-emoji emoji-id="5258258882022612173">⏲</tg-emoji> '
                    "Создание озвучки..."
                    "</b>"
                ),
                parse_mode="HTML"
            )

        except Exception as e:

            print(f"EDIT ERROR: {e}")

            try:

                await bot.edit_message_caption(
                    chat_id=msg.chat.id,
                    message_id=msg.message_id,
                    business_connection_id=feedback if feedback else None,
                    caption="<tg-emoji emoji-id='5258258882022612173'>⏲</tg-emoji> Создание озвучки...",
                    parse_mode="HTML"
                )

            except Exception as e2:
                print(f"CAPTION ERROR: {e2}")

        try:
            filename = f"tts_{uuid.uuid4().hex}.mp3"
            communicate = edge_tts.Communicate(
                text=text_to_voice,
                voice=voice,
                rate=speed
            )

            await communicate.save(filename)
            voice_file = FSInputFile(filename)

            if send_dm:
                await bot.send_voice(
                    chat_id=msg.from_user.id,
                    voice=voice_file
                )

            else:
                await bot.send_voice(
                    chat_id=msg.chat.id,
                    voice=voice_file,
                    business_connection_id=feedback
                )

            try:
                if feedback:
                    await bot.delete_business_messages(
                        business_connection_id=feedback,
                        message_ids=[msg.message_id]
                    )

                else:
                    await bot.delete_message(
                        chat_id=msg.chat.id,
                        message_id=msg.message_id
                    )
            except Exception as e:
                print(f"DELETE CMD ERROR: {e}")

            try:
                if status_message:
                    if feedback:
                        await bot.delete_business_messages(
                            business_connection_id=feedback,
                            message_ids=[status_message.message_id]
                        )
                    else:
                        await bot.delete_message(
                            chat_id=status_message.chat.id,
                            message_id=status_message.message_id
                        )

            except Exception as e:
                print(f"DELETE STATUS ERROR: {e}")
            try:
                os.remove(filename)
            except:
                pass

        except Exception as e:
            try:
                if status_message:
                    await status_message.edit_text(
                        f"<code>{e}</code>",
                        parse_mode="HTML"
                    )
            except:
                pass

    @router.business_message(F.text == ".info")
    @router.message(F.text == ".info")
    async def get_info(msg: Message, bot: Bot):

        feedback = getattr(
            msg,
            "business_connection_id",
            None
        )

        business_connection = None

        if feedback is not None:
            business_connection = await bot.get_business_connection(
                feedback
            )

        if (
            business_connection is not None
            and msg.from_user.id != business_connection.user.id
        ):
            return

        if not msg.reply_to_message:

            text = (
                "<b>"
                '<tg-emoji emoji-id="5258474669769497337">❗️</tg-emoji> '
                "Ответьте на сообщение"
                "</b>"
            )

            try:

                if feedback:

                    await bot.edit_message_text(
                        chat_id=msg.chat.id,
                        message_id=msg.message_id,
                        business_connection_id=feedback,
                        text=text,
                        parse_mode="HTML"
                    )

                else:

                    await msg.edit_text(
                        text,
                        parse_mode="HTML"
                    )

            except:

                await bot.send_message(
                    chat_id=msg.chat.id,
                    text=text,
                    parse_mode="HTML",
                    business_connection_id=feedback
                )

            return
        try:
            if feedback:

                await bot.edit_message_text(
                    chat_id=msg.chat.id,
                    message_id=msg.message_id,
                    business_connection_id=feedback,
                    text=(
                        "<b>"
                        '<tg-emoji emoji-id="5258258882022612173">⏲</tg-emoji> '
                        "Собираю информацию..."
                        "</b>"
                    ),
                    parse_mode="HTML"
                )

            else:

                await msg.edit_text(
                    "<b>"
                    '<tg-emoji emoji-id="5258258882022612173">⏲</tg-emoji> '
                    "Собираю информацию..."
                    "</b>",
                    parse_mode="HTML"
                )

        except Exception as e:
            print(f"STATUS ERROR: {e}")

        user = msg.reply_to_message.from_user

        username = (
            f"@{user.username}"
            if user.username else "Нет"
        )

        premium = (
            "Да"
            if user.is_premium else "Нет"
        )

        full_name = (
            user.full_name
            if user.full_name else "Нет"
        )

        first_name = (
            user.first_name
            if user.first_name else "Нет"
        )

        text = (
            "<blockquote>"

            '<tg-emoji emoji-id="5260399854500191689">👤</tg-emoji> '
            "<b>Информация о пользователе</b>\n\n"

            f"├ <b>User ID:</b> "
            f"<code>{user.id}</code>\n"

            f"├ <b>Username:</b> "
            f"<code>{username}</code>\n"

            f"├ <b>First Name:</b> "
            f"<code>{first_name}</code>\n"

            f"├ <b>Profile:</b> "
            f'<b><a href="tg://user?id={user.id}">{full_name}</a></b>\n'

            f"└ <b>Premium:</b> "
            f"<code>{premium}</code>\n"

            "</blockquote>"
        )

        await bot.send_message(
            chat_id=msg.chat.id,
            text=text,
            parse_mode="HTML",
            business_connection_id=feedback
        )

        try:

            if feedback:

                await bot.delete_business_messages(
                    business_connection_id=feedback,
                    message_ids=[msg.message_id]
                )

            else:

                await bot.delete_message(
                    chat_id=msg.chat.id,
                    message_id=msg.message_id
                )

        except Exception as e:
            print(f"DELETE ERROR: {e}")

    @router.business_message(F.text.startswith(".who"))
    @router.message(F.text.startswith(".who"))
    async def who_command(msg: Message, bot: Bot):
        if not await is_business_owner(msg, bot):
            return
        await delete_command_message(msg, bot)
        target = msg.reply_to_message.from_user if msg.reply_to_message and msg.reply_to_message.from_user else msg.from_user
        username = f"@{target.username}" if target.username else "нет"
        premium = "да" if getattr(target, "is_premium", False) else "нет"
        is_bot = "да" if getattr(target, "is_bot", False) else "нет"
        language = getattr(target, "language_code", None) or "неизвестно"
        caption = (
            "<blockquote>"
            f"{USER_EMOJI} <b>WHOIS профиль</b>\n\n"
            f"├ {ID_EMOJI} <b>ID:</b> <code>{target.id}</code>\n"
            f"├ <b>Имя:</b> <a href=\"tg://user?id={target.id}\">{escape(target.full_name or 'User')}</a>\n"
            f"├ <b>Username:</b> <code>{escape(username)}</code>\n"
            f"├ {GEM_EMOJI} <b>Premium:</b> <code>{premium}</code>\n"
            f"├ <b>Bot:</b> <code>{is_bot}</code>\n"
            f"└ <b>Language:</b> <code>{escape(language)}</code>"
            "</blockquote>"
        )
        try:
            photos = await bot.get_user_profile_photos(target.id, limit=1)
            if photos.total_count and photos.photos:
                await bot.send_photo(
                    chat_id=msg.chat.id,
                    photo=photos.photos[0][-1].file_id,
                    caption=caption,
                    parse_mode="HTML",
                    business_connection_id=get_business_connection_id(msg),
                )
                return
        except Exception:
            pass
        await send_html(msg, bot, caption)

    @router.business_message(F.text.startswith(".pgen"))
    @router.message(F.text.startswith(".pgen"))
    async def pgen_command(msg: Message, bot: Bot):
        if not await is_business_owner(msg, bot):
            return
        await delete_command_message(msg, bot)
        feedback = get_business_connection_id(msg)
        if not feedback:
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{CROSS_EMOJI} <b>Profile Generator недоступен</b>\n\n"
                "Эта команда работает только через Telegram Business подключение."
                "</blockquote>",
            )
            return
        user_id = msg.from_user.id
        restore_task = pgen_restore_tasks.get(user_id)
        if restore_task and not restore_task.done():
            remaining = max(1, int(pgen_restore_eta.get(user_id, time.time()) - time.time()))
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{TIME_EMOJI} <b>Profile Generator ждёт cooldown Telegram</b>\n\n"
                f"├ <b>До восстановления:</b> <code>{format_pgen_wait(remaining)}</code>\n"
                "└ <b>Новый запуск пока нельзя:</b> сначала вернём профиль"
                "</blockquote>",
            )
            return
        if user_id in pgen_tasks and not pgen_tasks[user_id].done():
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{INFO_EMOJI} <b>Profile Generator уже запущен</b>\n\n"
                "└ <b>Остановить:</b> <code>.pstop</code>"
                "</blockquote>",
            )
            return
        if user_id not in pgen_backups and str(user_id) not in load_pgen_backup_store():
            remember_pgen_backup(user_id, await backup_business_profile(msg, bot, feedback))
        pgen_tasks[user_id] = asyncio.create_task(pgen_worker(user_id, bot, feedback))
        await send_html(
            msg,
            bot,
            "<blockquote>"
            f"{GEM_EMOJI} <b>Profile Generator запущен</b>\n\n"
            "├ <b>Ник:</b> random swag + dota\n"
            "├ <b>Ава:</b> modern dark anime pfp\n"
            f"├ <b>Интервал:</b> <code>{PGEN_INTERVAL_MIN:g}-{PGEN_INTERVAL_MAX:g} сек.</code>\n"
            f"└ {TIME_EMOJI} <b>Остановить:</b> <code>.pstop</code>"
            "</blockquote>",
        )

    @router.business_message(F.text.startswith(".pstop"))
    @router.message(F.text.startswith(".pstop"))
    async def pstop_command(msg: Message, bot: Bot):
        if not await is_business_owner(msg, bot):
            return
        await delete_command_message(msg, bot)
        feedback = get_business_connection_id(msg)
        result = await stop_pgen_for_user(msg.from_user.id, bot, msg.chat.id, feedback)
        if result["status"] == "not_running":
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{INFO_EMOJI} <b>Profile Generator не запущен</b>\n\n"
                "└ <b>Запуск:</b> <code>.pgen</code>"
                "</blockquote>",
            )
            return
        if result["status"] == "delayed":
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{TIME_EMOJI} <b>Profile Generator остановлен</b>\n\n"
                "├ <b>Генерация:</b> остановлена сразу\n"
                f"├ <b>Telegram cooldown:</b> <code>{format_pgen_wait(result.get('retry_after'))}</code>\n"
                "└ <b>Профиль:</b> восстановлю автоматически после cooldown"
                "</blockquote>",
            )
            return
        if result["status"] == "error":
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{CROSS_EMOJI} <b>Не удалось восстановить профиль</b>\n\n"
                f"<code>{escape(result.get('error') or 'unknown error')}</code>"
                "</blockquote>",
            )
            return
        await send_html(
            msg,
            bot,
            "<blockquote>"
            f"{TICK_EMOJI} <b>Profile Generator остановлен</b>\n\n"
            "├ <b>Ник:</b> восстановлен\n"
            "├ <b>Ава:</b> восстановлена\n"
            "└ <b>Сгенерированная ава:</b> удалена"
            "</blockquote>",
        )

    @router.business_message(F.text.startswith(".watermark"))
    @router.message(F.text.startswith(".watermark"))
    async def watermark_command(msg: Message, bot: Bot):
        if not await is_business_owner(msg, bot):
            return
        await delete_command_message(msg, bot)
        text = command_args(msg, ".watermark")
        if not text:
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{PHOTO_EMOJI} <b>Watermark</b>\n\n"
                "├ <b>Использование:</b> <code>.watermark текст</code>\n"
                "└ <b>Формат:</b> ответом на фото"
                "</blockquote>",
            )
            return
        if not msg.reply_to_message or not msg.reply_to_message.photo:
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{CROSS_EMOJI} <b>Фото не найдено</b>\n\n"
                "Ответьте командой <code>.watermark текст</code> на нужное фото."
                "</blockquote>",
            )
            return
        GENERATED_MEDIA_DIR.mkdir(exist_ok=True)
        input_path = GENERATED_MEDIA_DIR / f"wm_in_{uuid4().hex}.jpg"
        output_path = GENERATED_MEDIA_DIR / f"wm_out_{uuid4().hex}.jpg"
        try:
            media = msg.reply_to_message.photo[-1]
            tg_file = await bot.get_file(media.file_id)
            await bot.download_file(tg_file.file_path, destination=str(input_path))
            await asyncio.to_thread(create_watermark_image, input_path, output_path, text[:120])
            await bot.send_photo(
                chat_id=msg.chat.id,
                photo=FSInputFile(str(output_path)),
                caption=(
                    "<blockquote>"
                    f"{TICK_EMOJI} <b>Watermark готов</b>\n\n"
                    f"└ {PHOTO_EMOJI} <b>Фото обработано</b>"
                    "</blockquote>"
                ),
                parse_mode="HTML",
                business_connection_id=get_business_connection_id(msg),
            )
        except Exception as e:
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{CROSS_EMOJI} <b>Watermark не создан</b>\n\n"
                f"<code>{escape(str(e))}</code>"
                "</blockquote>",
            )
        finally:
            for path in (input_path, output_path):
                try:
                    path.unlink(missing_ok=True)
                except Exception:
                    pass

    @router.business_message(F.text.startswith(".circle"))
    @router.message(F.text.startswith(".circle"))
    async def circle_command(msg: Message, bot: Bot):
        if not await is_business_owner(msg, bot):
            return
        await delete_command_message(msg, bot)
        if not msg.reply_to_message:
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{ROUND_EMOJI} <b>Video circle</b>\n\n"
                "├ <b>Использование:</b> <code>.circle</code>\n"
                "└ <b>Формат:</b> ответом на видео/GIF"
                "</blockquote>",
            )
            return
        file_id, extension = get_media_file_id(msg.reply_to_message)
        if not file_id:
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{CROSS_EMOJI} <b>Видео не найдено</b>\n\n"
                "Для <code>.circle</code> нужен реплай на видео, GIF или кружок."
                "</blockquote>",
            )
            return
        GENERATED_MEDIA_DIR.mkdir(exist_ok=True)
        input_path = GENERATED_MEDIA_DIR / f"circle_in_{uuid4().hex}.{extension}"
        output_path = GENERATED_MEDIA_DIR / f"circle_out_{uuid4().hex}.mp4"
        status = await send_html(
            msg,
            bot,
            "<blockquote>"
            f"{TIME_EMOJI} <b>Делаю кружок...</b>\n\n"
            f"└ {ROUND_EMOJI} <b>Конвертация видео</b>"
            "</blockquote>",
        )
        try:
            tg_file = await bot.get_file(file_id)
            await bot.download_file(tg_file.file_path, destination=str(input_path))
            ok, error = await convert_to_circle(input_path, output_path)
            if not ok:
                await status.edit_text(
                    "<blockquote>"
                    f"{CROSS_EMOJI} <b>Кружок не создан</b>\n\n"
                    f"<code>{escape(error)}</code>"
                    "</blockquote>",
                    parse_mode="HTML",
                )
                return
            await bot.send_video_note(
                chat_id=msg.chat.id,
                video_note=FSInputFile(str(output_path)),
                length=512,
                duration=60,
                business_connection_id=get_business_connection_id(msg),
            )
            try:
                await status.delete()
            except Exception:
                pass
        except Exception as e:
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{CROSS_EMOJI} <b>Ошибка .circle</b>\n\n"
                f"<code>{escape(str(e))}</code>"
                "</blockquote>",
            )
        finally:
            for path in (input_path, output_path):
                try:
                    path.unlink(missing_ok=True)
                except Exception:
                    pass

    @router.business_message(F.text.startswith(".voicefx"))
    @router.message(F.text.startswith(".voicefx"))
    async def voicefx_command(msg: Message, bot: Bot):
        if not await is_business_owner(msg, bot):
            return
        raw = command_args(msg, ".voicefx")
        options, errors = parse_voicefx_args(raw)
        if not raw or options.get("help"):
            await start_editable_status(msg, bot, voicefx_help_text())
            return
        if errors:
            await start_editable_status(
                msg,
                bot,
                "<blockquote>"
                f"{CROSS_EMOJI} <b>VoiceFX</b>\n\n"
                f"├ <b>Ошибка:</b> <code>{escape('; '.join(errors[:4]))}</code>\n"
                "└ <b>Помощь:</b> <code>.voicefx</code>"
                "</blockquote>",
            )
            return
        if not msg.reply_to_message:
            await start_editable_status(
                msg,
                bot,
                "<blockquote>"
                f"{GOLOS_EMOJI} <b>VoiceFX</b>\n\n"
                "├ <b>Использование:</b> ответом на voice/audio/video\n"
                "├ <b>Пример:</b> <code>.voicefx -dist 200 -reverse</code>\n"
                "└ <b>Список эффектов:</b> <code>.voicefx</code>"
                "</blockquote>",
            )
            return
        file_id, extension, media_type = get_voicefx_media_file(msg.reply_to_message)
        if not file_id:
            await start_editable_status(
                msg,
                bot,
                "<blockquote>"
                f"{CROSS_EMOJI} <b>Голос не найден</b>\n\n"
                "Ответьте командой <code>.voicefx -dist 200</code> на голосовое, аудио или видео."
                "</blockquote>",
            )
            return

        GENERATED_MEDIA_DIR.mkdir(exist_ok=True)
        input_path = GENERATED_MEDIA_DIR / f"voicefx_in_{uuid4().hex}.{extension}"
        output_path = GENERATED_MEDIA_DIR / f"voicefx_out_{uuid4().hex}.ogg"
        status_text = (
            "<blockquote>"
            f"{TIME_EMOJI} <b>VoiceFX обрабатывает...</b>\n\n"
            f"├ <b>Файл:</b> <code>{escape(media_type)}</code>\n"
            "└ <b>Статус:</b> применяю эффекты"
            "</blockquote>"
        )
        status, is_command_status = await start_editable_status(
            msg,
            bot,
            status_text,
        )
        try:
            tg_file = await bot.get_file(file_id)
            await bot.download_file(tg_file.file_path, destination=str(input_path))
            ok, error, labels = await convert_voicefx(input_path, output_path, options)
            if not ok:
                await update_editable_status(
                    msg,
                    bot,
                    status,
                    is_command_status,
                    "<blockquote>"
                    f"{CROSS_EMOJI} <b>VoiceFX не создан</b>\n\n"
                    f"<code>{escape(error)}</code>"
                    "</blockquote>",
                )
                return
            await bot.send_voice(
                chat_id=msg.chat.id,
                voice=FSInputFile(str(output_path)),
                business_connection_id=get_business_connection_id(msg),
            )
            await delete_editable_status(msg, bot, status, is_command_status)
        except Exception as e:
            await update_editable_status(
                msg,
                bot,
                status,
                is_command_status,
                "<blockquote>"
                f"{CROSS_EMOJI} <b>Ошибка .voicefx</b>\n\n"
                f"<code>{escape(str(e))}</code>"
                "</blockquote>",
            )
        finally:
            for path in (input_path, output_path):
                try:
                    path.unlink(missing_ok=True)
                except Exception:
                    pass

    @router.business_message(F.text == ".dice")
    @router.message(F.text == ".dice")
    async def dice_command(msg: Message, bot: Bot):
        if not await is_business_owner(msg, bot):
            return
        await delete_command_message(msg, bot)
        value = random.randint(1, 6)
        await send_html(
            msg,
            bot,
            "<blockquote>"
            f"{GEM_EMOJI} <b>Кости</b>\n\n"
            f"├ <b>Результат:</b> <code>{value}</code>/6\n"
            f"└ {STARS_EMOJI} <b>Статус:</b> бросок завершен"
            "</blockquote>",
        )

    @router.business_message(F.text == ".casino")
    @router.message(F.text == ".casino")
    async def casino_command(msg: Message, bot: Bot):
        if not await is_business_owner(msg, bot):
            return
        await delete_command_message(msg, bot)
        value = random.randint(1, 64)
        if value == 64:
            result = "джекпот"
        elif value >= 48:
            result = "крупный занос"
        elif value >= 32:
            result = "почти"
        else:
            result = "мимо"
        await send_html(
            msg,
            bot,
            "<blockquote>"
            f"{STARS_EMOJI} <b>Casino</b>\n\n"
            f"├ <b>Значение:</b> <code>{value}</code>/64\n"
            f"└ <b>Итог:</b> {escape(result)}"
            "</blockquote>",
        )

    @router.business_message(F.text.startswith(".calc"))
    @router.message(F.text.startswith(".calc"))
    async def calc_command(msg: Message, bot: Bot):
        if not await is_business_owner(msg, bot):
            return
        await delete_command_message(msg, bot)
        expr = command_args(msg, ".calc")
        if not expr:
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{ID_EMOJI} <b>Калькулятор</b>\n\n"
                "└ <b>Использование:</b> <code>.calc 2+2*5</code>"
                "</blockquote>",
            )
            return
        try:
            result = safe_calc(expr)
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{ID_EMOJI} <b>Калькулятор</b>\n\n"
                f"├ <b>Пример:</b> <code>{escape(expr)}</code>\n"
                f"└ {TICK_EMOJI} <b>Ответ:</b> <code>{escape(format_calc_result(result))}</code>"
                "</blockquote>",
            )
        except Exception as e:
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{CROSS_EMOJI} <b>Не смог посчитать</b>\n\n"
                f"<code>{escape(str(e))}</code>"
                "</blockquote>",
            )

    @router.business_message(F.text.startswith(".qr"))
    @router.message(F.text.startswith(".qr"))
    async def qr_command(msg: Message, bot: Bot):
        if not await is_business_owner(msg, bot):
            return
        await delete_command_message(msg, bot)
        data = command_args(msg, ".qr")
        if not data:
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{PHOTO_EMOJI} <b>QR генератор</b>\n\n"
                "└ <b>Использование:</b> <code>.qr текст/ссылка</code>"
                "</blockquote>",
            )
            return
        if len(data) > 700:
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{CROSS_EMOJI} <b>QR слишком длинный</b>\n\n"
                "└ <b>Лимит:</b> <code>700 символов</code>"
                "</blockquote>",
            )
            return
        qr_url = "https://api.qrserver.com/v1/create-qr-code/?size=512x512&data=" + quote_plus(data)
        try:
            await bot.send_photo(
                chat_id=msg.chat.id,
                photo=qr_url,
                caption=(
                    "<blockquote>"
                    f"{TICK_EMOJI} <b>QR готов</b>\n\n"
                    f"└ <code>{escape(data[:180])}</code>"
                    "</blockquote>"
                ),
                parse_mode="HTML",
                business_connection_id=get_business_connection_id(msg),
            )
        except Exception:
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{INFO_EMOJI} <b>QR ссылка</b>\n\n"
                f"└ {escape(qr_url)}"
                "</blockquote>",
            )

    @router.business_message(F.text.startswith(".weather"))
    @router.message(F.text.startswith(".weather"))
    async def weather_command(msg: Message, bot: Bot):
        if not await is_business_owner(msg, bot):
            return
        await delete_command_message(msg, bot)
        city = command_args(msg, ".weather")
        if not city:
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{INFO_EMOJI} <b>Погода</b>\n\n"
                "└ <b>Использование:</b> <code>.weather город</code>"
                "</blockquote>",
            )
            return
        try:
            place = await geocode_city(city)
            if not place:
                await send_html(
                    msg,
                    bot,
                    "<blockquote>"
                    f"{CROSS_EMOJI} <b>Город не найден</b>\n\n"
                    f"└ <b>Запрос:</b> <code>{escape(city)}</code>"
                    "</blockquote>",
                )
                return
            forecast = await current_forecast(place)
            current = forecast.get("current") or {}
            code = int(current.get("weather_code", -1))
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{INFO_EMOJI} <b>Погода</b>\n\n"
                f"├ <b>Место:</b> {escape(place_title(place))}\n"
                f"├ <b>Сейчас:</b> <code>{current.get('temperature_2m', '?')}°C</code>\n"
                f"├ <b>Ощущается:</b> <code>{current.get('apparent_temperature', '?')}°C</code>\n"
                f"├ <b>Состояние:</b> {escape(WEATHER_CODES.get(code, 'неизвестно'))}\n"
                f"├ <b>Влажность:</b> <code>{current.get('relative_humidity_2m', '?')}%</code>\n"
                f"├ <b>Ветер:</b> <code>{current.get('wind_speed_10m', '?')} км/ч</code>\n"
                f"└ {TIME_EMOJI} <b>Осадки:</b> <code>{current.get('precipitation', '?')} мм</code>"
                "</blockquote>",
            )
        except Exception as e:
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{CROSS_EMOJI} <b>Погоду не получил</b>\n\n"
                f"<code>{escape(str(e))}</code>"
                "</blockquote>",
            )

    @router.business_message(F.text.startswith(".time"))
    @router.message(F.text.startswith(".time"))
    async def time_command(msg: Message, bot: Bot):
        if not await is_business_owner(msg, bot):
            return
        await delete_command_message(msg, bot)
        city = command_args(msg, ".time")
        if not city:
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{TIME_EMOJI} <b>Время</b>\n\n"
                "└ <b>Использование:</b> <code>.time город</code>"
                "</blockquote>",
            )
            return
        try:
            place = await geocode_city(city)
            if not place:
                await send_html(
                    msg,
                    bot,
                    "<blockquote>"
                    f"{CROSS_EMOJI} <b>Город не найден</b>\n\n"
                    f"└ <b>Запрос:</b> <code>{escape(city)}</code>"
                    "</blockquote>",
                )
                return
            forecast = await current_forecast(place)
            current = forecast.get("current") or {}
            timezone = forecast.get("timezone") or place.get("timezone") or "unknown"
            local_time = str(current.get("time", "")).replace("T", " ")
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{TIME_EMOJI} <b>Время</b>\n\n"
                f"├ <b>Место:</b> {escape(place_title(place))}\n"
                f"├ <b>Время:</b> <code>{escape(local_time or 'неизвестно')}</code>\n"
                f"└ <b>Timezone:</b> <code>{escape(timezone)}</code>"
                "</blockquote>",
            )
        except Exception as e:
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{CROSS_EMOJI} <b>Время не получил</b>\n\n"
                f"<code>{escape(str(e))}</code>"
                "</blockquote>",
            )

    @router.business_message(F.text.startswith(".password"))
    @router.message(F.text.startswith(".password"))
    async def password_command(msg: Message, bot: Bot):
        if not await is_business_owner(msg, bot):
            return
        await delete_command_message(msg, bot)
        raw = command_args(msg, ".password")
        try:
            length = int(raw) if raw else 16
        except ValueError:
            length = 16
        length = max(8, min(length, 64))
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="Скопировать", copy_text=CopyTextButton(text=password))
        ]])
        await send_html(
            msg,
            bot,
            "<blockquote>"
            f"{GEM_EMOJI} <b>Пароль создан</b>\n\n"
            f"├ <b>Длина:</b> <code>{length}</code>\n"
            f"└ {TICK_EMOJI} <code>{escape(password)}</code>"
            "</blockquote>",
            reply_markup=kb,
        )

    @router.business_message(F.text.startswith(".pin"))
    @router.message(F.text.startswith(".pin"))
    async def pin_command(msg: Message, bot: Bot):
        if not await is_business_owner(msg, bot):
            return
        await delete_command_message(msg, bot)
        if not msg.reply_to_message:
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{INFO_EMOJI} <b>Закреп сообщения</b>\n\n"
                "└ <b>Использование:</b> ответьте <code>.pin</code> на сообщение"
                "</blockquote>",
            )
            return
        try:
            await bot.pin_chat_message(
                chat_id=msg.chat.id,
                message_id=msg.reply_to_message.message_id,
                business_connection_id=get_business_connection_id(msg),
                disable_notification=True,
            )
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{TICK_EMOJI} <b>Сообщение закреплено</b>\n\n"
                f"└ {ID_EMOJI} <b>Message ID:</b> <code>{msg.reply_to_message.message_id}</code>"
                "</blockquote>",
            )
        except Exception as e:
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{CROSS_EMOJI} <b>Закреп не сработал</b>\n\n"
                f"<code>{escape(str(e))}</code>\n\n"
                "<i>Боту нужны права на закрепление сообщений.</i>"
                "</blockquote>",
            )

    @router.business_message(F.text.startswith(".unpin"))
    @router.message(F.text.startswith(".unpin"))
    async def unpin_command(msg: Message, bot: Bot):
        if not await is_business_owner(msg, bot):
            return
        await delete_command_message(msg, bot)
        feedback = get_business_connection_id(msg)
        target_message_id = msg.reply_to_message.message_id if msg.reply_to_message else None
        if feedback and target_message_id is None:
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{INFO_EMOJI} <b>Снятие закрепа</b>\n\n"
                "В business-режиме ответьте <code>.unpin</code> на закрепленное сообщение."
                "</blockquote>",
            )
            return
        try:
            await bot.unpin_chat_message(
                chat_id=msg.chat.id,
                message_id=target_message_id,
                business_connection_id=feedback,
            )
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{TICK_EMOJI} <b>Закреп снят</b>\n\n"
                f"└ {ID_EMOJI} <b>Message ID:</b> <code>{target_message_id or 'последний закреп'}</code>"
                "</blockquote>",
            )
        except Exception as e:
            await send_html(
                msg,
                bot,
                "<blockquote>"
                f"{CROSS_EMOJI} <b>Закреп не снят</b>\n\n"
                f"<code>{escape(str(e))}</code>\n\n"
                "<i>Боту нужны права на закрепление сообщений.</i>"
                "</blockquote>",
            )

    @router.business_message(F.text == ".mute")
    @router.message(F.text == ".mute")
    async def mute_user(msg: Message, bot: Bot):

        feedback = getattr(
            msg,
            "business_connection_id",
            None
        )

        business_connection = None

        if feedback is not None:

            try:

                business_connection = await bot.get_business_connection(
                    feedback
                )

            except:
                pass

        if (
            business_connection is not None
            and msg.from_user.id != business_connection.user.id
        ):
            return

        if not msg.reply_to_message:

            text = (
                "<b>"
                '<tg-emoji emoji-id="5258474669769497337">❗️</tg-emoji> '
                "Ответьте на сообщение пользователя"
                "</b>"
            )

            try:

                if feedback:

                    await bot.edit_message_text(
                        chat_id=msg.chat.id,
                        message_id=msg.message_id,
                        business_connection_id=feedback,
                        text=text,
                        parse_mode="HTML"
                    )

                else:

                    await msg.edit_text(
                        text,
                        parse_mode="HTML"
                    )

            except:

                await bot.send_message(
                    chat_id=msg.chat.id,
                    text=text,
                    parse_mode="HTML",
                    business_connection_id=feedback
                )

            return

        user = msg.reply_to_message.from_user

        if not user:
            return

        muted_users.add(user.id)

        full_name = (
            user.full_name
            if user.full_name else "Пользователь"
        )

        text = (
            "<b>"
            '<tg-emoji emoji-id="5258267368877989660">🔇</tg-emoji> '
            f'Пользователь <a href="tg://user?id={user.id}">{full_name}</a> '
            "замучен"
            "</b>\n\n"

            "<blockquote>"
            "└ Чтобы размутить пользователя — "
            "<code>.unmute</code>"
            "</blockquote>"
        )

        await bot.send_message(
            chat_id=msg.chat.id,
            text=text,
            parse_mode="HTML",
            business_connection_id=feedback
        )

        try:

            if feedback:

                await bot.delete_business_messages(
                    business_connection_id=feedback,
                    message_ids=[msg.message_id]
                )

            else:

                await bot.delete_message(
                    chat_id=msg.chat.id,
                    message_id=msg.message_id
                )

        except Exception as e:

            print(
                f"MUTE DELETE ERROR: {e}"
            )


    @router.business_message(F.text == ".unmute")
    @router.message(F.text == ".unmute")
    async def unmute_user(msg: Message, bot: Bot):

        feedback = getattr(
            msg,
            "business_connection_id",
            None
        )

        business_connection = None

        if feedback is not None:

            try:

                business_connection = await bot.get_business_connection(
                    feedback
                )

            except:
                pass

        if (
            business_connection is not None
            and msg.from_user.id != business_connection.user.id
        ):
            return

        if not msg.reply_to_message:

            text = (
                "<b>"
                '<tg-emoji emoji-id="5258474669769497337">❗️</tg-emoji> '
                "Ответьте на сообщение пользователя"
                "</b>"
            )

            await bot.send_message(
                chat_id=msg.chat.id,
                text=text,
                parse_mode="HTML",
                business_connection_id=feedback
            )

            return

        user = msg.reply_to_message.from_user

        if not user:
            return

        muted_users.discard(user.id)

        full_name = (
            user.full_name
            if user.full_name else "Пользователь"
        )

        text = (
            "<b>"
            '<tg-emoji emoji-id="5260325873688518261">🔊</tg-emoji> '
            f'Пользователь <a href="tg://user?id={user.id}">{full_name}</a> '
            "размучен"
            "</b>"
        )

        await bot.send_message(
            chat_id=msg.chat.id,
            text=text,
            parse_mode="HTML",
            business_connection_id=feedback
        )

        try:

            if feedback:

                await bot.delete_business_messages(
                    business_connection_id=feedback,
                    message_ids=[msg.message_id]
                )

            else:

                await bot.delete_message(
                    chat_id=msg.chat.id,
                    message_id=msg.message_id
                )

        except Exception as e:

            print(
                f"UNMUTE DELETE ERROR: {e}"
            )

    @router.message(F.text.startswith(".spam"))
    @router.business_message(F.text.startswith(".spam"))
    async def spam_command(msg: Message, bot: Bot):

        feedback = getattr(
            msg,
            "business_connection_id",
            None
        )

        business_connection = None

        if feedback is not None:

            business_connection = await bot.get_business_connection(
                feedback
            )

        if (
            business_connection is not None
            and msg.from_user.id != business_connection.user.id
        ):
            return

        args = msg.text.split()

        if len(args) < 3:

            text = (
                "<blockquote expandable>"

                "<b>"
                '<tg-emoji emoji-id="5258514780469075716">'
                '📂'
                '</tg-emoji> '
                "Использование команды"
                "</b>\n\n"

                "├ <code>.spam [кол-во] [текст]</code>\n"
                "├ <code>-speed [0.1 - 5.0]</code>\n"
                "├ <code>-delay [секунды]</code>\n"
                "└ Premium emoji поддерживаются"

                "</blockquote>\n\n"

                "<blockquote expandable>"

                "<b>"
                '<tg-emoji emoji-id="5258503720928288433">'
                'ℹ️'
                '</tg-emoji> '
                "Примеры"
                "</b>\n\n"

                "├ <code>.spam 5 привет🎁</code>\n"
                "├ <code>.spam 10 lol💎 -speed 0.5</code>\n"
                "├ <code>.spam 3 hello🔥 -delay 2</code>\n"
                "└ <code>.spam 20 test❤️‍🔥 -speed 0.3</code>"

                "</blockquote>"
            )

            await bot.send_message(
                chat_id=msg.chat.id,
                text=text,
                parse_mode="HTML",
                business_connection_id=feedback
            )

            return

        count = 1
        speed = 1.0
        delay = 0.0

        try:

            count = int(args[1])

        except:
            return

        count = max(1, min(count, 100))

        text_parts = []

        i = 2

        while i < len(args):

            arg = args[i]

            if arg == "-speed" and i + 1 < len(args):

                try:

                    speed = float(args[i + 1])

                except:
                    pass

                i += 2
                continue

            elif arg == "-delay" and i + 1 < len(args):

                try:

                    delay = float(args[i + 1])

                except:
                    pass

                i += 2
                continue

            else:

                text_parts.append(arg)

            i += 1

        spam_text = " ".join(text_parts)

        if not spam_text:
            return

        user_id = msg.from_user.id

        if user_id in spam_tasks:

            spam_tasks[user_id].cancel()

        entities = []

        if msg.entities:

            original_text = msg.text

            spam_start = original_text.find(
                spam_text
            )

            for entity in msg.entities:

                if entity.offset < spam_start:
                    continue

                try:

                    new_offset = (
                        entity.offset - spam_start
                    )

                    entities.append(
                        MessageEntity(
                            type=entity.type,
                            offset=new_offset,
                            length=entity.length,
                            url=entity.url,
                            user=entity.user,
                            language=entity.language,
                            custom_emoji_id=entity.custom_emoji_id
                        )
                    )

                except Exception as e:

                    print(
                        f"ENTITY ERROR: {e}"
                    )

        start_text = (
            "<blockquote expandable>"

            "<b>"
            '<tg-emoji emoji-id="5334544901428229844">'
            '⚡️'
            '</tg-emoji> '
            "Спам запущен"
            "</b>\n\n"

            f"├ Сообщений: <code>{count}</code>\n"
            f"├ Speed: <code>{speed}</code>\n"
            f"├ Delay: <code>{delay}</code>\n"
            f"└ Текст: {escape(spam_text)}"

            "</blockquote>"
        )

        await bot.send_message(
            chat_id=msg.chat.id,
            text=start_text,
            parse_mode="HTML",
            business_connection_id=feedback
        )

        async def spam_worker():

            interval = (
                max(speed, 0.1) + delay
            )

            try:

                for _ in range(count):

                    if entities:

                        await bot.send_message(
                            chat_id=msg.chat.id,
                            text=spam_text,
                            entities=entities,
                            business_connection_id=feedback
                        )

                    else:

                        await bot.send_message(
                            chat_id=msg.chat.id,
                            text=spam_text,
                            business_connection_id=feedback
                        )

                    await asyncio.sleep(
                        interval
                    )

            except asyncio.CancelledError:

                await bot.send_message(
                    chat_id=msg.chat.id,
                    text=(
                        "<blockquote expandable>"

                        "<b>"
                        '<tg-emoji emoji-id="5258474669769497337">'
                        '❌'
                        '</tg-emoji> '
                        "Спам остановлен"
                        "</b>"

                        "</blockquote>"
                    ),
                    parse_mode="HTML",
                    business_connection_id=feedback
                )

            except Exception as e:

                print(
                    f"SPAM ERROR: {e}"
                )

            finally:

                spam_tasks.pop(
                    user_id,
                    None
                )

        spam_tasks[user_id] = (
            asyncio.create_task(
                spam_worker()
            )
        )

        try:

            if feedback:

                await bot.delete_business_messages(
                    business_connection_id=feedback,
                    message_ids=[msg.message_id]
                )

            else:

                await bot.delete_message(
                    chat_id=msg.chat.id,
                    message_id=msg.message_id
                )

        except:
            pass

    @router.message(F.text == ".stop")
    @router.business_message(F.text == ".stop")
    async def stop_spam(msg: Message, bot: Bot):

        feedback = getattr(
            msg,
            "business_connection_id",
            None
        )

        user_id = msg.from_user.id

        if user_id not in spam_tasks:

            text = (
                "<b>"
                '<tg-emoji emoji-id="5258503720928288433">ℹ️</tg-emoji> '
                "Активный spam не найден"
                "</b>"
            )

            await bot.send_message(
                chat_id=msg.chat.id,
                text=text,
                parse_mode="HTML",
                business_connection_id=feedback
            )

            return

        spam_tasks[user_id].cancel()

        text = (
            "<b>"
            '<tg-emoji emoji-id="5258474669769497337">❌</tg-emoji> '
            "Спам остановлен"
            "</b>"
        )

        await bot.send_message(
            chat_id=msg.chat.id,
            text=text,
            parse_mode="HTML",
            business_connection_id=feedback
        )

        try:

            if feedback:

                await bot.delete_business_messages(
                    business_connection_id=feedback,
                    message_ids=[msg.message_id]
                )

            else:

                await bot.delete_message(
                    chat_id=msg.chat.id,
                    message_id=msg.message_id
                )

        except:
            pass
    
    @router.message(F.text == ".mins")
    @router.business_message(F.text == ".mins")
    async def mins_create(msg: Message, bot: Bot):

        feedback = getattr(
            msg,
            "business_connection_id",
            None
        )

        game_id = str(
            random.randint(
                100,
                999
            )
        )

        mines_games[game_id] = {
            "creator": msg.from_user.id,
            "creator_name": msg.from_user.full_name,
            "player": None,
            "player_name": None,
            "started": False,
            "field": create_mines_field(),
            "opened": [],
            "turn": None,
            "scores": {}
        }

        creator_link = (
            f"<a href='tg://user?id={msg.from_user.id}'>"
            f"<b>{msg.from_user.full_name}</b>"
            f"</a>"
        )

        text = (
            "<b>"

            '<tg-emoji emoji-id="5469654973308476699">'
            '💣'
            '</tg-emoji> '

            "Mines Game"

            "</b>\n\n"

            "<blockquote>"

            f"├ Создатель: {creator_link}\n"
            "└ Нажмите кнопку ниже\n"
            "  чтобы начать игру"

            "</blockquote>"
        )

        builder = InlineKeyboardBuilder()

        builder.row(

            InlineKeyboardButton(
                text="🎮 Играть",
                callback_data=f"mines_join:{game_id}"
            ),

            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"mines_decline:{game_id}"
            )
        )

        sent = await bot.send_message(
            chat_id=msg.chat.id,
            text=text,
            parse_mode="HTML",
            reply_markup=builder.as_markup(),
            business_connection_id=feedback
        )

        mines_games[game_id]["message_id"] = sent.message_id

        try:

            if feedback:

                await bot.delete_business_messages(
                    business_connection_id=feedback,
                    message_ids=[msg.message_id]
                )

            else:

                await bot.delete_message(
                    chat_id=msg.chat.id,
                    message_id=msg.message_id
                )

        except:
            pass


    @router.callback_query(F.data.startswith("mines_decline:"))
    async def mins_decline(call: CallbackQuery):

        game_id = call.data.split(":")[1]

        if game_id not in mines_games:
            return

        user_link = (
            f"<a href='tg://user?id={call.from_user.id}'>"
            f"<b>{call.from_user.full_name}</b>"
            f"</a>"
        )

        text = (
            "<b>"

            '<tg-emoji emoji-id="5985346521103604145">'
            '❌'
            '</tg-emoji> '

            "Игра отклонена"

            "</b>\n\n"

            "<blockquote>"

            f"└ Игру отклонил {user_link}"

            "</blockquote>"
        )

        await call.message.edit_text(
            text=text,
            parse_mode="HTML"
        )

        mines_games.pop(game_id, None)

        await call.answer()


    @router.callback_query(F.data.startswith("mines_join:"))
    async def mines_join(call: CallbackQuery):

        game_id = call.data.split(":")[1]

        if game_id not in mines_games:
            return

        game = mines_games[game_id]

        if game["started"]:
            return

        if call.from_user.id == game["creator"]:

            await call.answer(
                "Нельзя играть с собой",
                show_alert=True
            )

            return

        game["player"] = call.from_user.id
        game["player_name"] = call.from_user.full_name
        game["started"] = True

        game["turn"] = random.choice([
            game["creator"],
            game["player"]
        ])

        game["scores"] = {
            game["creator"]: 0,
            game["player"]: 0
        }

        creator_link = (
            f"<a href='tg://user?id={game['creator']}'>"

            '<tg-emoji emoji-id="5879770735999717115">'
            '👤'
            '</tg-emoji> '

            f"<b>{game['creator_name']}</b>"
            f"</a>"
        )

        player_link = (
            f"<a href='tg://user?id={game['player']}'>"

            '<tg-emoji emoji-id="5879770735999717115">'
            '👤'
            '</tg-emoji> '

            f"<b>{game['player_name']}</b>"
            f"</a>"
        )

        turn_link = (
            creator_link
            if game["turn"] == game["creator"]
            else player_link
        )

        text = (
            "<b>"

            '<tg-emoji emoji-id="5469654973308476699">'
            '💣'
            '</tg-emoji> '

            "Mines Game"

            "</b>\n\n"

            "<blockquote>"

            "<b>├ Игра началась</b>\n\n"

            f"<b>├ {creator_link}</b>\n"
            f"<b>├ {player_link}</b>\n\n"

            f"<b>└ Ходит: {turn_link}</b>"

            "</blockquote>"
        )

        await call.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=build_mines_keyboard(game_id)
        )

        await call.answer()


    @router.callback_query(F.data.startswith("m:"))
    async def mines_click(call: CallbackQuery):

        parts = call.data.split(":")

        game_id = parts[1]

        x = int(parts[2])
        y = int(parts[3])

        if game_id not in mines_games:
            return

        game = mines_games[game_id]

        if not game["started"]:
            return

        if call.from_user.id != game["turn"]:

            await call.answer(
                "Сейчас не ваш ход",
                show_alert=True
            )

            return

        key = f"{x}:{y}"

        if key in game["opened"]:

            await call.answer()

            return

        game["opened"].append(key)

        value = game["field"][y][x]

        if value == "💣":

            loser = call.from_user.id

            winner = (
                game["creator"]
                if loser == game["player"]
                else game["player"]
            )

            loser_name = (
                game["creator_name"]
                if loser == game["creator"]
                else game["player_name"]
            )

            winner_name = (
                game["creator_name"]
                if winner == game["creator"]
                else game["player_name"]
            )

            loser_link = (
                f"<a href='tg://user?id={loser}'>"

                '<tg-emoji emoji-id="5258011929993026890">'
                '👤'
                '</tg-emoji> '

                f"<b>{loser_name}</b>"
                f"</a>"
            )

            winner_link = (
                f"<a href='tg://user?id={winner}'>"

                '<tg-emoji emoji-id="5258011929993026890">'
                '👤'
                '</tg-emoji> '

                f"<b>{winner_name}</b>"
                f"</a>"
            )

            text = (
                "<b>"

                '<tg-emoji emoji-id="5469654973308476699">'
                '💣'
                '</tg-emoji> '

                "Игрок взорвался"

                "</b>\n\n"

                "<blockquote>"

                f"<b>├ Игрок: {loser_link}</b>\n\n"

                f"<b>└ Победил: {winner_link}</b> "

                '<tg-emoji emoji-id="5258501105293205250">'
                '👏'
                '</tg-emoji>'

                "</blockquote>"
            )

            await call.message.edit_text(
                text=text,
                parse_mode="HTML",
                reply_markup=build_mines_keyboard(game_id)
            )

            mines_games.pop(game_id, None)

            await call.answer()

            return

        game["scores"][call.from_user.id] += 1

        game["turn"] = (
            game["creator"]
            if game["turn"] == game["player"]
            else game["player"]
        )

        creator_link = (
            f"<a href='tg://user?id={game['creator']}'>"

            '<tg-emoji emoji-id="5258011929993026890">'
            '👤'
            '</tg-emoji> '

            f"<b>{game['creator_name']}</b>"
            f"</a>"
        )

        player_link = (
            f"<a href='tg://user?id={game['player']}'>"

            '<tg-emoji emoji-id="5258011929993026890">'
            '👤'
            '</tg-emoji> '

            f"<b>{game['player_name']}</b>"
            f"</a>"
        )

        turn_link = (
            creator_link
            if game["turn"] == game["creator"]
            else player_link
        )

        creator_score = game["scores"][game["creator"]]
        player_score = game["scores"][game["player"]]

        text = (
            "<b>"

            '<tg-emoji emoji-id="5469654973308476699">'
            '💣'
            '</tg-emoji> '

            "Mines Game"

            "</b>\n\n"

            "<blockquote>"

            f"<b>├ {creator_link} — {creator_score}</b>\n"

            f"<b>├ {player_link} — {player_score}</b>\n\n"

            f"<b>└ Ходит: {turn_link}</b>"

            "</blockquote>"
        )

        await call.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=build_mines_keyboard(game_id)
        )

        await call.answer()

    @router.message(F.text.startswith(".copytg"))
    @router.business_message(F.text.startswith(".copytg"))
    async def copytg_command(
        msg: Message,
        bot: Bot
    ):

        feedback = getattr(
            msg,
            "business_connection_id",
            None
        )

        if not feedback:
            return

        business_connection = None

        try:

            business_connection = await bot.get_business_connection(
                feedback
            )

        except Exception as e:

            print(
                f"BUSINESS CONNECTION ERROR: {e}"
            )

            return

        if (
            business_connection is not None
            and msg.from_user.id != business_connection.user.id
        ):
            return

        if msg.text == ".copytg -back":

            old_data = copy_profiles.get(
                msg.from_user.id
            )

            if not old_data:

                text = (
                    "<b>"
                    '<tg-emoji emoji-id="5258474669769497337">❌</tg-emoji> '
                    "Старый профиль не найден"
                    "</b>"
                )

                await bot.send_message(
                    chat_id=msg.chat.id,
                    text=text,
                    parse_mode="HTML",
                    business_connection_id=feedback
                )

                return

            try:

                await bot.set_business_account_name(
                    business_connection_id=feedback,
                    first_name=old_data["first_name"],
                    last_name=old_data["last_name"]
                )

            except Exception as e:

                print(
                    f"BACK NAME ERROR: {e}"
                )

            try:

                await bot.set_business_account_bio(
                    business_connection_id=feedback,
                    bio=old_data["bio"]
                )

            except Exception as e:

                print(
                    f"BACK BIO ERROR: {e}"
                )

            try:

                try:

                    await bot.remove_business_account_profile_photo(
                        business_connection_id=feedback
                    )

                except Exception as e:

                    print(
                        f"REMOVE CURRENT PHOTO ERROR: {e}"
                    )

                photo_path = old_data.get(
                    "photo"
                )

                if (
                    photo_path
                    and Path(photo_path).exists()
                ):

                    await bot.set_business_account_profile_photo(
                        business_connection_id=feedback,
                        photo=InputProfilePhotoStatic(
                            photo=FSInputFile(
                                str(photo_path)
                            )
                        ),
                        is_public=False
                    )

                    try:

                        Path(photo_path).unlink(
                            missing_ok=True
                        )

                    except Exception as e:

                        print(
                            f"DELETE PHOTO FILE ERROR: {e}"
                        )

            except Exception as e:

                print(
                    f"BACK PHOTO ERROR: {e}"
                )

            copy_profiles.pop(
                msg.from_user.id,
                None
            )

            text = (
                "<b>"
                '<tg-emoji emoji-id="5260341314095947411">👀</tg-emoji> '
                "Профиль восстановлен!"
                "</b>\n\n"

                "<blockquote>"

                "├ Имя: восстановлено\n"
                "├ Био: восстановлено\n"
                "└ Аватарка: восстановлена"

                "</blockquote>"
            )

            await bot.send_message(
                chat_id=msg.chat.id,
                text=text,
                parse_mode="HTML",
                business_connection_id=feedback
            )

            return

        if not msg.reply_to_message:

            text = (
                "<b>"
                '<tg-emoji emoji-id="5258503720928288433">ℹ️</tg-emoji> '
                "Ответьте на сообщение"
                "</b>\n\n"

                "<blockquote>"

                "├ Копирование:\n"
                "│ <code>.copytg</code>\n\n"
                "└ Возврат:\n"
                "  <code>.copytg -back</code>"

                "</blockquote>"
            )

            await bot.send_message(
                chat_id=msg.chat.id,
                text=text,
                parse_mode="HTML",
                business_connection_id=feedback
            )

            return

        target = msg.reply_to_message.from_user

        if not target:
            return

        if msg.from_user.id not in copy_profiles:

            try:

                my_bio = ""

                photos_dir = Path(
                    "profile_photos"
                )

                photos_dir.mkdir(
                    exist_ok=True
                )

                saved_photo = None

                try:

                    profile_photos = await bot.get_user_profile_photos(
                        msg.from_user.id,
                        limit=1
                    )

                    if profile_photos.total_count > 0:

                        photo = profile_photos.photos[0][-1]

                        file = await bot.get_file(
                            photo.file_id
                        )

                        saved_photo = (
                            photos_dir /
                            f"{uuid4().hex}.jpg"
                        )

                        await bot.download_file(
                            file.file_path,
                            destination=str(saved_photo)
                        )

                except Exception as e:

                    print(
                        f"SAVE PHOTO ERROR: {e}"
                    )

                copy_profiles[msg.from_user.id] = {

                    "first_name": (
                        msg.from_user.first_name
                        or "Telegram"
                    ),

                    "last_name": (
                        msg.from_user.last_name
                        or ""
                    ),

                    "bio": my_bio,

                    "photo": saved_photo
                }

            except Exception as e:

                print(
                    f"SAVE PROFILE ERROR: {e}"
                )

        try:

            await bot.set_business_account_name(
                business_connection_id=feedback,
                first_name=target.first_name or "Telegram",
                last_name=target.last_name or ""
            )

        except Exception as e:

            print(
                f"SET NAME ERROR: {e}"
            )

        target_bio = ""

        try:

            target_chat = await bot.get_chat(
                target.id
            )

            target_bio = getattr(
                target_chat,
                "bio",
                ""
            )

            await bot.set_business_account_bio(
                business_connection_id=feedback,
                bio=target_bio or ""
            )

        except Exception as e:

            print(
                f"SET BIO ERROR: {e}"
            )

        avatar_status = "не установлена"

        try:

            target_photos = await bot.get_user_profile_photos(
                target.id,
                limit=1
            )

            if target_photos.total_count > 0:

                photos_dir = Path(
                    "profile_photos"
                )

                photos_dir.mkdir(
                    exist_ok=True
                )

                photo = target_photos.photos[0][-1]

                file = await bot.get_file(
                    photo.file_id
                )

                temp_photo = (
                    photos_dir /
                    f"{uuid4().hex}.jpg"
                )

                await bot.download_file(
                    file.file_path,
                    destination=str(temp_photo)
                )

                try:

                    await bot.remove_business_account_profile_photo(
                        business_connection_id=feedback
                    )

                except Exception as e:

                    print(
                        f"REMOVE OLD PHOTO ERROR: {e}"
                    )

                await bot.set_business_account_profile_photo(
                    business_connection_id=feedback,
                    photo=InputProfilePhotoStatic(
                        photo=FSInputFile(
                            str(temp_photo)
                        )
                    ),
                    is_public=False
                )

                avatar_status = "установлена"

        except Exception as e:

            print(
                f"SET PHOTO ERROR: {e}"
            )

        full_name = (
            target.full_name
            or "Telegram"
        )

        text = (
            "<b>"
            '<tg-emoji emoji-id="5260341314095947411">👀</tg-emoji> '
            "Профиль скопирован!"
            "</b>\n\n"

            "<blockquote>"

            f"├ Имя: {full_name}\n"
            f"├ Био: {'установлено' if target_bio else 'не установлено'}\n"
            f"└ Аватарка: {avatar_status}"

            "</blockquote>\n\n"

            "<b>"
            '<tg-emoji emoji-id="5258503720928288433">ℹ️</tg-emoji> '
            "Чтобы вернуть обратно:"
            "</b>\n"

            "<blockquote>"
            "<code>.copytg -back</code>"
            "</blockquote>"
        )

        await bot.send_message(
            chat_id=msg.chat.id,
            text=text,
            parse_mode="HTML",
            business_connection_id=feedback
        )
    
    @router.message(F.text == ".save")
    @router.business_message(F.text == ".save")
    async def save_once_media(
        msg: Message,
        bot: Bot
    ):
        feedback = getattr(
            msg,
            "business_connection_id",
            None
        )
        if not feedback:
            return
        business_connection = None
        try:
            business_connection = await bot.get_business_connection(
                feedback
            )
        except Exception as e:
            print(
                f"BUSINESS CONNECTION ERROR: {e}"
            )
            return
        if (
            business_connection is not None
            and msg.from_user.id != business_connection.user.id
        ):
            return
        
        if not msg.reply_to_message:
            try:
                await bot.delete_business_messages(
                    business_connection_id=feedback,
                    message_ids=[
                        msg.message_id
                    ]
                )
            except Exception as e:
                print(
                    f"DELETE COMMAND ERROR: {e}"
                )
            text = (
                "<b>"
                f"{SECRET_EMOJI} "
                "Сохранение одноразовых медиа"
                "</b>\n"

                "<blockquote expandable>"
                "<b>"
                "Использование:\n"
                "<code>.save</code> отвечаете на ваше нужное медиа\n\n"
                "</b>"
                "<b>Поддерживаемые типы:\n\n"

                f"{PHOTO_EMOJI} Фото\n"
                f"{VIDEO_EMOJI} Видео\n"
                f"{GOLOS_EMOJI} Голосовое сообщение\n"
                f"{ROUND_EMOJI} Видео-кружок\n\n"
                "</b>"
                "</blockquote>\n"

                f"{QUESTION_EMOJI} "

                "<b>Как использовать:</b>\n"
                "<blockquote expandable>"
                "<b>"
                "1. Ответьте на одноразовое медиа\n"
                "2. Отправьте команду <code>.save</code>\n"
                "3. Сохранённый файл будет отправлен вам в личные сообщения"
                "</b>"
                "</blockquote>\n\n"

                "<b>"
                '<tg-emoji emoji-id="5258474669769497337">❗️</tg-emoji> '
                "Важно:"
                "</b>\n"

                "<blockquote expandable>"

                "• Работает только ответом на сообщение\n"
                "• Поддерживаются фото, видео, голосовые и кружки\n"
                "• Медиа сохраняется в исходном качестве\n"
                "• После сохранения файл отправляется в ваши ЛС"

                "</blockquote>"
            )

            await bot.send_message(
                chat_id=msg.chat.id,
                text=text,
                parse_mode="HTML",
                business_connection_id=feedback
            )

            return
        reply = msg.reply_to_message
        if not getattr(
            reply,
            "has_protected_content",
            False
        ):
            await bot.send_message(
                chat_id=msg.chat.id,
                text=(
                    "<b>"
                    "❌ Это не защищённое медиа"
                    "</b>"
                ),
                parse_mode="HTML",
                business_connection_id=feedback
            )
            return
        media = None
        media_type = None
        extension = None
        if reply.photo:
            media = reply.photo[-1]
            media_type = "фото"
            extension = "jpg"
        elif reply.video:
            media = reply.video
            media_type = "видео"
            extension = "mp4"
        elif reply.video_note:
            media = reply.video_note
            media_type = "кружок"
            extension = "mp4"
        elif reply.voice:
            media = reply.voice
            media_type = "голосовое сообщение"
            extension = "ogg"
        if not media:
            await bot.send_message(
                chat_id=msg.chat.id,
                text=(
                    "<b>"
                    "❌ Тип медиа не поддерживается"
                    "</b>"
                ),
                parse_mode="HTML",
                business_connection_id=feedback
            )
            return
        
        try:
            save_dir = Path(
                "saved_once_media"
            )
            save_dir.mkdir(
                exist_ok=True
            )
            file = await bot.get_file(
                media.file_id
            )
            file_path = (
                save_dir /
                f"{uuid4().hex}.{extension}"
            )
            await bot.download_file(
                file.file_path,
                destination=str(
                    file_path
                )
            )
            if media_type == "фото":
                await bot.send_photo(
                    chat_id=msg.from_user.id,
                    photo=FSInputFile(
                        str(file_path)
                    ),
                    caption=f"<b>{SECRET_EMOJI} Сохранено одноразовое {media_type}</b>",
                    parse_mode="HTML"
                )
            elif media_type == "видео":
                await bot.send_video(
                    chat_id=msg.from_user.id,
                    video=FSInputFile(
                        str(file_path)
                    ),
                    caption=f"<b>{SECRET_EMOJI} Сохранено одноразовое {media_type}</b>",
                    parse_mode="HTML"
                )
            elif media_type == "кружок":
                await bot.send_video_note(
                    chat_id=msg.from_user.id,
                    video_note=FSInputFile(
                        str(file_path)
                    ),
                    caption=f"<b>{SECRET_EMOJI} Сохранен одноразовый {media_type}</b>",
                    parse_mode="HTML"
                )
            elif media_type == "голосовое сообщение":
                await bot.send_voice(
                    chat_id=msg.from_user.id,
                    voice=FSInputFile(
                        str(file_path)
                    ),
                    caption=f"<b>{SECRET_EMOJI} Сохранено одноразовое {media_type}</b>",
                    parse_mode="HTML"
                )
            try:
                await bot.delete_business_messages(
                    business_connection_id=feedback,
                    message_ids=[
                        msg.message_id
                    ]
                )
            except Exception as e:
                print(
                    f"DELETE COMMAND ERROR: {e}"
                )
            await bot.send_message(
                chat_id=msg.chat.id,
                text=(
                    "<b>"
                    '<tg-emoji emoji-id="5327904946413121515">©️</tg-emoji> '
                    "Медиа успешно сохранено"
                    "</b>\n\n"
                    "<blockquote>"
                    "<b>"
                    f"├ Тип: {media_type}\n"
                    "└ Статус: сохранено"
                    "</b>"
                    "</blockquote>"
                ),
                parse_mode="HTML",
                business_connection_id=feedback
            )

        except Exception as e:
            print(
                f"SAVE ERROR: {e}"
            )
            await bot.send_message(
                chat_id=msg.chat.id,
                text=(
                    "<b>"
                    '<tg-emoji emoji-id="5258474669769497337">❌</tg-emoji> '
                    "Ошибка сохранения"
                    "</b>\n\n"
                    f"<code>{e}</code>"
                ),
                parse_mode="HTML",
                business_connection_id=feedback
            )

    @router.callback_query(F.data.contains("help"))
    async def help_debug_handler(call: CallbackQuery):
        logging.warning(f"DEBUG: Unhandled help callback received: {call.data}")
        await call.answer()

    return router
