import asyncio
import aiosqlite
import os
import random
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ====================== НАСТРОЙКИ ======================
BOT_TOKEN = "8839150169:AAF9tmdYkTaYPRYSA-oqRkfCYLgaVOAjhJQ"
ADMIN_IDS = [8558077464]

# 👇 Юзернейм продавца (без @) — сюда будут писать покупатели
SELLER_USERNAME = "parlament_manager"
SELLER_NAME = "Парламент"

# 👇 Канал с отзывами (только юзернейм, без ссылки и @)
REVIEWS_CHANNEL = "otziviuparlament_shop"
REVIEWS_CHANNEL_NAME = "⭐ Отзывы Parlament"

# Цены
PRICE_PER_NUMBER = 50
REF_PERCENT = 10
CASHBACK_PERCENT = 2

SERVICES = {
    "telegram":  {"name": "Telegram",  "emoji": "✈️"},
    "whatsapp":  {"name": "WhatsApp",  "emoji": "💚"},
    "google":    {"name": "Google",    "emoji": "🔴"},
    "instagram": {"name": "Instagram", "emoji": "📸"},
    "facebook":  {"name": "Facebook",  "emoji": "👤"},
    "twitter":   {"name": "Twitter",   "emoji": "🐦"},
    "discord":   {"name": "Discord",   "emoji": "🎮"},
    "tiktok":    {"name": "TikTok",    "emoji": "🎵"},
    "uber":      {"name": "Uber",      "emoji": "🚕"},
    "amazon":    {"name": "Amazon",    "emoji": "📦"},
    "netflix":   {"name": "Netflix",   "emoji": "🎬"},
    "spotify":   {"name": "Spotify",   "emoji": "🎧"},
    "steam":     {"name": "Steam",     "emoji": "🕹"},
    "vkontakte": {"name": "VK",        "emoji": "🔵"},
    "yandex":    {"name": "Yandex",    "emoji": "🟡"},
    "avito":     {"name": "Avito",     "emoji": "🟢"},
}

COUNTRIES = {
    "russia":      {"name": "Россия",     "flag": "🇷🇺"},
    "ukraine":     {"name": "Украина",    "flag": "🇺🇦"},
    "kazakhstan":  {"name": "Казахстан",  "flag": "🇰🇿"},
    "belarus":     {"name": "Беларусь",   "flag": "🇧🇾"},
    "indonesia":   {"name": "Индонезия",  "flag": "🇮🇩"},
    "philippines": {"name": "Филиппины",  "flag": "🇵🇭"},
    "vietnam":     {"name": "Вьетнам",    "flag": "🇻🇳"},
    "india":       {"name": "Индия",      "flag": "🇮🇳"},
    "england":     {"name": "Англия",     "flag": "🇬🇧"},
    "usa":         {"name": "США",        "flag": "🇺🇸"},
    "germany":     {"name": "Германия",   "flag": "🇩🇪"},
    "netherlands": {"name": "Нидерланды", "flag": "🇳🇱"},
    "france":      {"name": "Франция",    "flag": "🇫🇷"},
    "spain":       {"name": "Испания",    "flag": "🇪🇸"},
    "poland":      {"name": "Польша",     "flag": "🇵🇱"},
    "turkey":      {"name": "Турция",     "flag": "🇹🇷"},
    "china":       {"name": "Китай",      "flag": "🇨🇳"},
    "japan":       {"name": "Япония",     "flag": "🇯🇵"},
}

DIV = "━━━━━━━━━━━━━━━━━━━━"
DIV2 = "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈"

BANNER = (
    "╔══════════════════════╗\n"
    "║  📱 <b>PARLAMENT SHOP</b>  ║\n"
    "║   <i>виртуальные номера</i>  ║\n"
    "║      🟢 🟡 🔴 🟣      ║\n"
    "╚══════════════════════╝"
)

ACHIEVEMENTS = {
    "first_buy":  {"name": "🎯 Первый шаг",  "desc": "Первый заказ"},
    "five_buys":  {"name": "🔥 Постоянный",  "desc": "5 заказов"},
    "ten_buys":   {"name": "⭐ Опытный",     "desc": "10 заказов"},
    "referrer":   {"name": "👥 Друг",        "desc": "Пригласить 1 друга"},
    "referrer_5": {"name": "👑 Лидер",       "desc": "Пригласить 5 друзей"},
    "lucky":      {"name": "🍀 Счастливчик", "desc": "Выиграть в рулетку"},
    "daily_7":    {"name": "📅 Верный",      "desc": "7 дней подряд"},
}

# =======================================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ==================== БАЗА ====================
async def init_db():
    async with aiosqlite.connect("shop.db") as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                balance REAL DEFAULT 0,
                username TEXT,
                referrer_id INTEGER,
                total_spent REAL DEFAULT 0,
                orders_count INTEGER DEFAULT 0,
                cashback_earned REAL DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                daily_streak INTEGER DEFAULT 0,
                last_daily TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                service TEXT,
                country TEXT,
                status TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS promos (
                code TEXT PRIMARY KEY,
                bonus REAL,
                max_uses INTEGER DEFAULT 100,
                uses INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS promo_uses (
                user_id INTEGER,
                code TEXT,
                UNIQUE(user_id, code)
            );
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                text TEXT,
                status TEXT DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS achievements (
                user_id INTEGER,
                code TEXT,
                PRIMARY KEY (user_id, code)
            );
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                type TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await db.commit()


async def get_user(user_id, username=None, referrer_id=None):
    async with aiosqlite.connect("shop.db") as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as c:
            row = await c.fetchone()
            if row:
                return dict(row)
            await db.execute("INSERT INTO users (user_id, username, referrer_id) VALUES (?, ?, ?)",
                             (user_id, username, referrer_id))
            await db.commit()
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as c:
                return dict(await c.fetchone())


async def change_balance(user_id, amount, type_="adjust", desc=""):
    async with aiosqlite.connect("shop.db") as db:
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        if type_ == "cashback":
            await db.execute("UPDATE users SET cashback_earned = cashback_earned + ? WHERE user_id = ?",
                             (amount, user_id))
        await db.execute("INSERT INTO transactions (user_id, amount, type, description) VALUES (?, ?, ?, ?)",
                         (user_id, amount, type_, desc))
        await db.commit()


async def notify_user(user_id, text, kb=None):
    try:
        await bot.send_message(user_id, text, parse_mode="HTML", reply_markup=kb)
    except Exception:
        pass


async def give_ach(user_id, code):
    async with aiosqlite.connect("shop.db") as db:
        try:
            await db.execute("INSERT INTO achievements (user_id, code) VALUES (?, ?)", (user_id, code))
            await db.commit()
            a = ACHIEVEMENTS[code]
            await notify_user(user_id, f"🏆 <b>Новое достижение!</b>\n\n{a['name']}\n<i>{a['desc']}</i>")
        except aiosqlite.IntegrityError:
            pass


def level_name(spent):
    if spent >= 10000: return "💎 VIP"
    if spent >= 5000: return "🥇 Голд"
    if spent >= 1000: return "🥈 Серебро"
    if spent >= 100: return "🥉 Бронза"
    return "🆕 Новичок"


# ==================== КЛАВИАТУРЫ ====================
def main_kb(uid):
    rows = [
        [InlineKeyboardButton(text="🛒 Купить номер", callback_data="services")],
        [
            InlineKeyboardButton(text="💰 Баланс", callback_data="balance"),
            InlineKeyboardButton(text="📦 Мои заказы", callback_data="my_orders"),
        ],
        [
            InlineKeyboardButton(text="💳 Пополнить", callback_data="topup"),
            InlineKeyboardButton(text="🎟 Промокод", callback_data="promo"),
        ],
        [
            InlineKeyboardButton(text="🎁 Ежедневный бонус", callback_data="daily"),
            InlineKeyboardButton(text="🎰 Рулетка", callback_data="roulette"),
        ],
        [
            InlineKeyboardButton(text="👥 Рефералка", callback_data="ref"),
            InlineKeyboardButton(text="🏆 Топ", callback_data="top_refs"),
        ],
        [
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="stats"),
        ],
        [
            InlineKeyboardButton(text="🏅 Ачивки", callback_data="achv"),
            InlineKeyboardButton(text="💎 Избранное", callback_data="favs"),
        ],
        [
            InlineKeyboardButton(text="💬 Поддержка", callback_data="support"),
            InlineKeyboardButton(text="❓ FAQ", callback_data="faq"),
        ],
        # ⭐ Кнопка отзывов — ведёт в канал
        [InlineKeyboardButton(
            text=REVIEWS_CHANNEL_NAME,
            url=f"https://t.me/{REVIEWS_CHANNEL}"
        )],
        # ✍️ Написать продавцу
        [InlineKeyboardButton(
            text=f"✍️ Написать {SELLER_NAME}",
            url=f"https://t.me/{SELLER_USERNAME}"
        )],
    ]
    if uid in ADMIN_IDS:
        rows.append([InlineKeyboardButton(text="🛡 Админ-панель", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def services_kb():
    rows = []
    row = []
    for code, s in SERVICES.items():
        row.append(InlineKeyboardButton(text=f"{s['emoji']} {s['name']}", callback_data=f"serv_{code}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="🏠 Меню", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def countries_kb(service):
    rows = []
    row = []
    for code, c in COUNTRIES.items():
        row.append(InlineKeyboardButton(text=f"{c['flag']} {c['name']}", callback_data=f"c_{service}_{code}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="« Назад", callback_data="services")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="a_stats"),
            InlineKeyboardButton(text="📢 Рассылка", callback_data="a_broadcast"),
        ],
        [
            InlineKeyboardButton(text="📋 Заявки", callback_data="a_requests"),
            InlineKeyboardButton(text="👥 Юзеры", callback_data="a_users"),
        ],
        [
            InlineKeyboardButton(text="🎟 Промокоды", callback_data="a_promos"),
            InlineKeyboardButton(text="🎁 Начислить", callback_data="a_add_balance"),
        ],
        [
            InlineKeyboardButton(text="🚫 Бан/Разбан", callback_data="a_ban"),
        ],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="back")],
    ])


# ==================== FSM ====================
class Promo(StatesGroup): code = State()
class Support(StatesGroup): msg = State()
class Broadcast(StatesGroup): text = State()
class AdminPromo(StatesGroup):
    code = State(); bonus = State(); uses = State()
class AdminBalance(StatesGroup):
    user_id = State(); amount = State()
class AdminBan(StatesGroup): user_id = State()
class RouletteState(StatesGroup): bet = State()


# ==================== СТАРТ ====================
@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    ref_id = None
    parts = message.text.split()
    if len(parts) > 1:
        try:
            r = int(parts[1])
            if r != message.from_user.id:
                ref_id = r
        except Exception:
            pass

    u = await get_user(message.from_user.id, message.from_user.username, ref_id)
    if u.get("is_banned"):
        await message.answer("🚫 Вы заблокированы.")
        return

    text = (
        f"{BANNER}\n\n"
        f"👋 <b>Привет, {message.from_user.first_name}!</b>\n\n"
        f"Здесь ты можешь заказать виртуальный номер\n"
        f"для регистрации в любом сервисе.\n\n"
        f"{DIV}\n"
        f"💰 Баланс: <b>{u['balance']:.0f} ₽</b>\n"
        f"📦 Заказов: <b>{u['orders_count']}</b>\n"
        f"🏆 Уровень: {level_name(u['total_spent'])}\n"
        f"{DIV}\n\n"
        f"💡 <b>Как купить?</b>\n"
        f"1. Выбери сервис и страну\n"
        f"2. Нажми «Заказать»\n"
        f"3. Напиши продавцу — он выдаст номер\n"
        f"4. Оплати и получи SMS-код\n\n"
        f"Выбери действие 👇"
    )
    await message.answer(text, reply_markup=main_kb(message.from_user.id), parse_mode="HTML")


@dp.callback_query(F.data == "back")
async def back(cb: CallbackQuery):
    u = await get_user(cb.from_user.id)
    text = (
        f"{BANNER}\n\n"
        f"🏠 <b>Главное меню</b>\n\n"
        f"{DIV}\n"
        f"💰 Баланс: <b>{u['balance']:.0f} ₽</b>\n"
        f"📦 Заказов: <b>{u['orders_count']}</b>\n"
        f"🏆 Уровень: {level_name(u['total_spent'])}\n"
        f"{DIV}"
    )
    try:
        await cb.message.edit_text(text, reply_markup=main_kb(cb.from_user.id), parse_mode="HTML")
    except Exception:
        await cb.message.answer(text, reply_markup=main_kb(cb.from_user.id), parse_mode="HTML")


# ==================== КАТАЛОГ ====================
@dp.callback_query(F.data == "services")
async def services(cb: CallbackQuery):
    await cb.message.edit_text(
        f"🛍 <b>Выбери сервис</b>\n\n"
        f"{DIV2}\n"
        f"💵 Цена: от <b>{PRICE_PER_NUMBER} ₽</b>\n"
        f"{DIV2}",
        reply_markup=services_kb(),
        parse_mode="HTML"
    )


@dp.callback_query(F.data.startswith("serv_"))
async def choose_country(cb: CallbackQuery):
    svc = cb.data[5:]
    s = SERVICES.get(svc, {})
    await cb.message.edit_text(
        f"{s.get('emoji','')} <b>{s.get('name', svc)}</b>\n\n🌍 Выбери страну:",
        reply_markup=countries_kb(svc),
        parse_mode="HTML"
    )


@dp.callback_query(F.data.startswith("c_"))
async def show_price(cb: CallbackQuery):
    _, svc, country = cb.data.split("_")
    name = COUNTRIES.get(country, {}).get("name", country)
    flag = COUNTRIES.get(country, {}).get("flag", "")
    s = SERVICES.get(svc, {})

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Заказать номер", callback_data=f"order_{svc}_{country}")],
        [InlineKeyboardButton(text="✍️ Написать продавцу", url=f"https://t.me/{SELLER_USERNAME}")],
        [InlineKeyboardButton(text="« Назад", callback_data=f"serv_{svc}")],
    ])

    await cb.message.edit_text(
        f"{DIV}\n"
        f"{s.get('emoji','')} <b>{s.get('name', svc)}</b>\n"
        f"{flag} {name}\n"
        f"{DIV}\n\n"
        f"💵 Стоимость: от <b>{PRICE_PER_NUMBER} ₽</b>\n"
        f"⏱ Срок выдачи: <b>1-15 минут</b>\n"
        f"✅ Гарантия: <b>есть</b>\n\n"
        f"{DIV}\n\n"
        f"💬 После нажатия кнопки <b>напиши продавцу</b> — "
        f"он выдаст тебе номер и пришлёт SMS-код.\n\n"
        f"📌 Цена может меняться в зависимости от спроса.",
        reply_markup=kb,
        parse_mode="HTML"
    )


@dp.callback_query(F.data.startswith("order_"))
async def create_order(cb: CallbackQuery):
    _, svc, country = cb.data.split("_")
    uid = cb.from_user.id
    async with aiosqlite.connect("shop.db") as db:
        cur = await db.execute(
            "INSERT INTO requests (user_id, username, service, country) VALUES (?, ?, ?, ?)",
            (uid, cb.from_user.username, svc, country)
        )
        req_id = cur.lastrowid
        await db.commit()

    s = SERVICES.get(svc, {})
    c = COUNTRIES.get(country, {})

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Написать продавцу", url=f"https://t.me/{SELLER_USERNAME}")],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="back")],
    ])

    await cb.message.edit_text(
        f"✅ <b>Заявка #{req_id} создана!</b>\n\n"
        f"{DIV2}\n"
        f"{s.get('emoji','')} <b>{s.get('name', svc)}</b>\n"
        f"{c.get('flag','')} {c.get('name', country)}\n"
        f"{DIV2}\n\n"
        f"📱 Твой ID: <code>{uid}</code>\n\n"
        f"⚠️ <b>Что делать дальше:</b>\n\n"
        f"1. Нажми кнопку ниже — откроется чат с продавцом\n"
        f"2. Напиши: <code>Заказ #{req_id}</code>\n"
        f"3. Продавец выдаст номер и пришлёт SMS\n"
        f"4. Оплатишь после получения\n\n"
        f"💬 <b>{SELLER_NAME}</b> ответит в течение 15 минут.",
        reply_markup=kb,
        parse_mode="HTML"
    )

    for a in ADMIN_IDS:
        await notify_user(
            a,
            f"🔔 <b>НОВАЯ ЗАЯВКА #{req_id}</b>\n\n"
            f"{DIV2}\n"
            f"👤 Покупатель: <b>{cb.from_user.full_name}</b>\n"
            f"🔗 @{cb.from_user.username or '—'}\n"
            f"🆔 <code>{uid}</code>\n"
            f"{DIV2}\n"
            f"📦 Сервис: {s.get('name', svc)}\n"
            f"🌍 Страна: {c.get('name', country)}\n"
            f"{DIV2}",
            InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✍️ Написать", url=f"tg://user?id={uid}")]
            ])
        )


# ==================== БАЛАНС ====================
@dp.callback_query(F.data == "balance")
async def balance(cb: CallbackQuery):
    u = await get_user(cb.from_user.id)
    await cb.message.edit_text(
        f"💰 <b>Твой баланс</b>\n\n"
        f"{DIV}\n"
        f"💵 Доступно: <b>{u['balance']:.0f} ₽</b>\n"
        f"💎 Потрачено: <b>{u['total_spent']:.0f} ₽</b>\n"
        f"🎁 Кэшбэк: <b>{u['cashback_earned']:.0f} ₽</b>\n"
        f"📦 Заказов: <b>{u['orders_count']}</b>\n"
        f"🏆 Уровень: {level_name(u['total_spent'])}\n"
        f"{DIV}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📜 История", callback_data="transactions")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="back")],
        ]),
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "transactions")
async def transactions(cb: CallbackQuery):
    async with aiosqlite.connect("shop.db") as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY id DESC LIMIT 15",
                              (cb.from_user.id,)) as c:
            rows = [dict(r) for r in await c.fetchall()]
    text = "📜 <b>История транзакций</b>\n\n"
    if not rows:
        text += "<i>Пока пусто</i>"
    else:
        for t in rows:
            sign = "➕" if t["amount"] > 0 else "➖"
            text += f"{sign} <b>{abs(t['amount']):.0f} ₽</b> — {t['description'] or t['type']}\n"
    await cb.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="« Назад", callback_data="balance")]
        ]),
        parse_mode="HTML"
    )


# ==================== МОИ ЗАКАЗЫ ====================
@dp.callback_query(F.data == "my_orders")
async def my_orders(cb: CallbackQuery):
    async with aiosqlite.connect("shop.db") as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM requests WHERE user_id = ? ORDER BY id DESC LIMIT 10",
                              (cb.from_user.id,)) as c:
            rows = [dict(r) for r in await c.fetchall()]
    if not rows:
        text = "📦 <b>У тебя пока нет заказов</b>\n\nЗакажи первый номер! 🚀"
    else:
        text = "📦 <b>Твои заявки:</b>\n\n"
        for r in rows:
            st = {"new": "🆕", "in_progress": "⏳", "done": "✅"}.get(r["status"], "⚪️")
            s = SERVICES.get(r["service"], {})
            c_ = COUNTRIES.get(r["country"], {})
            text += f"{st} #{r['id']} — {s.get('emoji','')} {s.get('name', r['service'])} | {c_.get('flag','')} {c_.get('name', r['country'])}\n"
    await cb.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Заказать ещё", callback_data="services")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="back")],
        ]),
        parse_mode="HTML"
    )


# ==================== ПРОМО ====================
@dp.callback_query(F.data == "promo")
async def promo_menu(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Promo.code)
    await cb.message.edit_text(f"🎟 <b>Промокод</b>\n\n{DIV2}\nВведи код:\n{DIV2}")
    await cb.answer()


@dp.message(Promo.code)
async def promo_apply(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    await state.clear()
    async with aiosqlite.connect("shop.db") as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM promos WHERE code = ?", (code,)) as c:
            p = await c.fetchone()
        if not p:
            await message.answer("❌ Такого кода нет", reply_markup=main_kb(message.from_user.id))
            return
        if p["uses"] >= p["max_uses"]:
            await message.answer("❌ Промокод исчерпан", reply_markup=main_kb(message.from_user.id))
            return
        async with db.execute("SELECT 1 FROM promo_uses WHERE user_id = ? AND code = ?",
                              (message.from_user.id, code)) as c:
            if await c.fetchone():
                await message.answer("❌ Ты уже использовал", reply_markup=main_kb(message.from_user.id))
                return
        await db.execute("INSERT INTO promo_uses (user_id, code) VALUES (?, ?)",
                         (message.from_user.id, code))
        await db.execute("UPDATE promos SET uses = uses + 1 WHERE code = ?", (code,))
        await db.commit()
    await change_balance(message.from_user.id, p["bonus"], "promo", f"Промокод {code}")
    u = await get_user(message.from_user.id)
    await message.answer(
        f"🎉 <b>+{p['bonus']:.0f} ₽</b>\n💰 Баланс: <b>{u['balance']:.0f} ₽</b>",
        reply_markup=main_kb(message.from_user.id),
        parse_mode="HTML"
    )


# ==================== РЕФЕРАЛКА ====================
@dp.callback_query(F.data == "ref")
async def ref(cb: CallbackQuery):
    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start={cb.from_user.id}"
    async with aiosqlite.connect("shop.db") as db:
        async with db.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (cb.from_user.id,)) as c:
            count = (await c.fetchone())[0]
    await cb.message.edit_text(
        f"👥 <b>Рефералка</b>\n\n"
        f"{DIV}\n"
        f"💎 Получай <b>{REF_PERCENT}%</b> с заказов друзей\n"
        f"👥 Приглашено: <b>{count}</b>\n"
        f"{DIV}\n\n"
        f"🔗 <code>{link}</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📤 Поделиться",
                                  url=f"https://t.me/share/url?url={link}&text=Крутой%20магазин%20номеров!")],
            [InlineKeyboardButton(text="🏆 Топ", callback_data="top_refs")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="back")],
        ]),
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "top_refs")
async def top_refs(cb: CallbackQuery):
    async with aiosqlite.connect("shop.db") as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT u.username, u.user_id, COUNT(r.user_id) c
            FROM users u JOIN users r ON r.referrer_id = u.user_id
            GROUP BY u.user_id ORDER BY c DESC LIMIT 10
        """) as c:
            rows = await c.fetchall()
    text = "🏆 <b>Топ рефералов</b>\n\n"
    if not rows:
        text += "Пока никого"
    else:
        medals = ["🥇", "🥈", "🥉"]
        for i, r in enumerate(rows):
            m = medals[i] if i < 3 else f"{i+1}."
            text += f"{m} <b>{r['username'] or 'ID'+str(r['user_id'])}</b> — {r['c']} 👥\n"
    await cb.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Меню", callback_data="back")]
        ]),
        parse_mode="HTML"
    )


# ==================== ПРОФИЛЬ ====================
@dp.callback_query(F.data == "profile")
async def profile(cb: CallbackQuery):
    u = await get_user(cb.from_user.id)
    reg = u["created_at"][:10] if u["created_at"] else "—"
    await cb.message.edit_text(
        f"👤 <b>Профиль</b>\n\n"
        f"{DIV}\n"
        f"🆔 <code>{u['user_id']}</code>\n"
        f"📛 {cb.from_user.full_name}\n"
        f"🔗 @{u['username'] or '—'}\n"
        f"📅 {reg}\n"
        f"{DIV}\n"
        f"💰 Баланс: <b>{u['balance']:.0f} ₽</b>\n"
        f"📦 Заказов: <b>{u['orders_count']}</b>\n"
        f"💎 Потрачено: <b>{u['total_spent']:.0f} ₽</b>\n"
        f"🎁 Кэшбэк: <b>{u['cashback_earned']:.0f} ₽</b>\n"
        f"🏆 Уровень: {level_name(u['total_spent'])}\n"
        f"{DIV}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
            [InlineKeyboardButton(text="🏅 Ачивки", callback_data="achv")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="back")],
        ]),
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "stats")
async def user_stats(cb: CallbackQuery):
    u = await get_user(cb.from_user.id)
    async with aiosqlite.connect("shop.db") as db:
        async with db.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (cb.from_user.id,)) as c:
            refs = (await c.fetchone())[0]
    await cb.message.edit_text(
        f"📊 <b>Статистика</b>\n\n"
        f"{DIV2}\n"
        f"📦 Заказов: <b>{u['orders_count']}</b>\n"
        f"💰 Потрачено: <b>{u['total_spent']:.0f} ₽</b>\n"
        f"👥 Друзей: <b>{refs}</b>\n"
        f"🏆 Уровень: {level_name(u['total_spent'])}\n"
        f"{DIV2}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Меню", callback_data="back")]
        ]),
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "achv")
async def achv(cb: CallbackQuery):
    async with aiosqlite.connect("shop.db") as db:
        async with db.execute("SELECT code FROM achievements WHERE user_id = ?", (cb.from_user.id,)) as c:
            got = {r[0] for r in await c.fetchall()}
    text = f"🏅 <b>Достижения</b>\n\n{DIV2}\n"
    for code, a in ACHIEVEMENTS.items():
        mark = "✅" if code in got else "🔒"
        text += f"{mark} {a['name']} — <i>{a['desc']}</i>\n"
    text += DIV2
    await cb.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Меню", callback_data="back")]
        ]),
        parse_mode="HTML"
    )


# ==================== ЕЖЕДНЕВНЫЙ БОНУС ====================
@dp.callback_query(F.data == "daily")
async def daily_bonus(cb: CallbackQuery):
    u = await get_user(cb.from_user.id)
    today = datetime.now().strftime("%Y-%m-%d")
    if u.get("last_daily") == today:
        await cb.answer("⏰ Уже получил сегодня! Приходи завтра.", show_alert=True)
        return
    streak = (u.get("daily_streak") or 0) + 1
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    if u.get("last_daily") != yesterday:
        streak = 1
    bonus = 0.5 + min(streak, 10) * 0.45
    await change_balance(cb.from_user.id, bonus, "daily", f"Ежедневный бонус ({streak} дн.)")
    async with aiosqlite.connect("shop.db") as db:
        await db.execute("UPDATE users SET daily_streak = ?, last_daily = ? WHERE user_id = ?",
                         (streak, today, cb.from_user.id))
        await db.commit()
    if streak >= 7:
        await give_ach(cb.from_user.id, "daily_7")
    await cb.message.edit_text(
        f"🎁 <b>Ежедневный бонус!</b>\n\n"
        f"{DIV}\n"
        f"💵 Получено: <b>+{bonus} ₽</b>\n"
        f"🔥 Серия: <b>{streak} дн.</b>\n"
        f"{DIV}\n\n"
        f"<i>Заходи каждый день — бонус растёт!</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Меню", callback_data="back")]
        ]),
        parse_mode="HTML"
    )


# ==================== РУЛЕТКА ====================
@dp.callback_query(F.data == "roulette")
async def roulette(cb: CallbackQuery, state: FSMContext):
    u = await get_user(cb.from_user.id)
    if u["balance"] < 10:
        await cb.answer("Нужно минимум 10 ₽", show_alert=True)
        return
    await state.set_state(RouletteState.bet)
    await cb.message.edit_text(
        f"🎰 <b>Рулетка</b>\n\n"
        f"{DIV2}\n"
        f"Поставь сумму (мин. 10 ₽):\n"
        f"💰 Баланс: <b>{u['balance']:.0f} ₽</b>\n"
        f"{DIV2}\n\n"
        f"<i>Шанс выиграть ×2 — 45%</i>"
    )
    await cb.answer()


@dp.message(RouletteState.bet)
async def roulette_play(message: Message, state: FSMContext):
    try:
        bet = float(message.text)
        if bet < 10:
            await message.answer("❌ Минимум 10 ₽")
            return
    except ValueError:
        await message.answer("❌ Введи число")
        return
    await state.clear()
    u = await get_user(message.from_user.id)
    if u["balance"] < bet:
        await message.answer("❌ Недостаточно средств", reply_markup=main_kb(message.from_user.id))
        return
    await change_balance(message.from_user.id, -bet, "roulette", "Ставка")
    await message.answer("🎰 Крутим...")
    await asyncio.sleep(2)
    if random.random() < 0.45:
        win = bet * 2
        await change_balance(message.from_user.id, win, "roulette", "Выигрыш ×2")
        await give_ach(message.from_user.id, "lucky")
        await message.answer(
            f"🎉 <b>ПОБЕДА!</b>\n\n💰 +<b>{win:.0f} ₽</b>",
            reply_markup=main_kb(message.from_user.id),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"😢 <b>Проигрыш</b>\n\n💵 -{bet:.0f} ₽",
            reply_markup=main_kb(message.from_user.id),
            parse_mode="HTML"
        )


# ==================== ИЗБРАННОЕ ====================
@dp.callback_query(F.data == "favs")
async def favorites(cb: CallbackQuery):
    await cb.message.edit_text(
        "💎 <b>Избранное</b>\n\nПока пусто.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Меню", callback_data="back")]
        ]),
        parse_mode="HTML"
    )


# ==================== ПОДДЕРЖКА / FAQ ====================
@dp.callback_query(F.data == "support")
async def support(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Support.msg)
    await cb.message.edit_text("💬 Опиши проблему одним сообщением:")
    await cb.answer()


@dp.message(Support.msg)
async def support_msg(message: Message, state: FSMContext):
    await state.clear()
    async with aiosqlite.connect("shop.db") as db:
        cur = await db.execute("INSERT INTO tickets (user_id, text) VALUES (?, ?)",
                               (message.from_user.id, message.text))
        tid = cur.lastrowid
        await db.commit()
    await message.answer(f"✅ Тикет #{tid} отправлен", reply_markup=main_kb(message.from_user.id))
    for a in ADMIN_IDS:
        await notify_user(a, f"💬 <b>Тикет #{tid}</b>\n\n👤 {message.from_user.full_name}\n\n{message.text}")


@dp.callback_query(F.data == "faq")
async def faq(cb: CallbackQuery):
    text = (
        f"❓ <b>FAQ</b>\n\n"
        f"<b>1. Как купить номер?</b>\n"
        f"🛒 Меню → Купить номер → Сервис → Страна → Заказать\n\n"
        f"<b>2. Как я получу номер?</b>\n"
        f"💬 Продавец напишет тебе лично\n\n"
        f"<b>3. Когда придёт SMS?</b>\n"
        f"⏳ Обычно 1-15 минут\n\n"
        f"<b>4. Как оплатить?</b>\n"
        f"💰 Переводом продавцу напрямую\n\n"
        f"<b>5. Кэшбэк?</b>\n"
        f"🎁 {CASHBACK_PERCENT}% с покупок\n\n"
        f"<b>6. Рефералка?</b>\n"
        f"👥 {REF_PERCENT}% с заказов друзей"
    )
    await cb.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Поддержка", callback_data="support")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="back")],
        ]),
        parse_mode="HTML"
    )


# ==================== ОТЗЫВЫ (КОМАНДА) ====================
@dp.message(Command("reviews"))
async def cmd_reviews(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=REVIEWS_CHANNEL_NAME, url=f"https://t.me/{REVIEWS_CHANNEL}")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="back")],
    ])
    await message.answer(
        f"⭐ <b>Отзывы наших клиентов</b>\n\n"
        f"{DIV}\n"
        f"Здесь ты можешь посмотреть:\n"
        f"• ✅ Реальные отзывы покупателей\n"
        f"• 📸 Скриншоты полученных номеров\n"
        f"• 💬 Ответы на вопросы\n"
        f"{DIV}\n\n"
        f"👇 Жми кнопку ниже:",
        reply_markup=kb,
        parse_mode="HTML"
    )


# ==================== АДМИНКА ====================
@dp.callback_query(F.data == "admin")
async def admin_panel(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS:
        await cb.answer("Нет доступа", show_alert=True)
        return
    await cb.message.edit_text("🛡 <b>Админ-панель</b>", reply_markup=admin_kb(), parse_mode="HTML")


@dp.callback_query(F.data == "a_stats")
async def a_stats(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS: return
    async with aiosqlite.connect("shop.db") as db:
        users = (await (await db.execute("SELECT COUNT(*) FROM users")).fetchone())[0]
        reqs = (await (await db.execute("SELECT COUNT(*) FROM requests")).fetchone())[0]
        new_reqs = (await (await db.execute("SELECT COUNT(*) FROM requests WHERE status='new'")).fetchone())[0]
        t = (await (await db.execute("SELECT COUNT(*) FROM tickets WHERE status='open'")).fetchone())[0]
    await cb.message.edit_text(
        f"📊 <b>Статистика</b>\n\n"
        f"{DIV}\n"
        f"👥 Юзеров: <b>{users}</b>\n"
        f"📋 Всего заявок: <b>{reqs}</b>\n"
        f"🆕 Новых: <b>{new_reqs}</b>\n"
        f"💬 Тикетов: <b>{t}</b>\n"
        f"{DIV}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="a_stats")],
            [InlineKeyboardButton(text="« Назад", callback_data="admin")],
        ]),
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "a_requests")
async def a_requests(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS: return
    async with aiosqlite.connect("shop.db") as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM requests ORDER BY id DESC LIMIT 15") as c:
            rows = await c.fetchall()
    text = "📋 <b>Заявки:</b>\n\n"
    for r in rows:
        st = {"new": "🆕", "in_progress": "⏳", "done": "✅"}.get(r["status"], "⚪️")
        s = SERVICES.get(r["service"], {})
        c_ = COUNTRIES.get(r["country"], {})
        text += f"{st} #{r['id']} | {s.get('name', r['service'])} {c_.get('flag','')}\n"
        text += f"👤 {r['username'] or r['user_id']}\n\n"
    if not rows:
        text += "Нет заявок"
    await cb.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="« Назад", callback_data="admin")]
        ]),
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "a_users")
async def a_users(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS: return
    async with aiosqlite.connect("shop.db") as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT 15") as c:
            users = await c.fetchall()
    text = "👥 <b>Юзеры:</b>\n\n"
    for u in users:
        b = "🚫" if u["is_banned"] else "✅"
        text += f"{b} <code>{u['user_id']}</code> | {u['username'] or '—'} | {u['balance']:.0f}₽\n"
    await cb.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="« Назад", callback_data="admin")]
        ]),
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "a_add_balance")
async def a_add_bal(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in ADMIN_IDS: return
    await state.set_state(AdminBalance.user_id)
    await cb.message.edit_text("🎁 Введи ID:")
    await cb.answer()


@dp.message(AdminBalance.user_id)
async def a_add_uid(message: Message, state: FSMContext):
    try:
        uid = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Число")
        return
    await state.update_data(uid=uid)
    await state.set_state(AdminBalance.amount)
    await message.answer("💰 Сумма (+/-):")


@dp.message(AdminBalance.amount)
async def a_add_amt(message: Message, state: FSMContext):
    try:
        amt = float(message.text.strip())
    except ValueError:
        await message.answer("❌ Число")
        return
    d = await state.get_data()
    await state.clear()
    await change_balance(d["uid"], amt, "admin", "Начисление")
    await message.answer(f"✅ {amt:+.0f} ₽", reply_markup=main_kb(message.from_user.id))
    await notify_user(d["uid"], f"🎁 <b>Баланс обновлён!</b>\n{amt:+.0f} ₽")


@dp.callback_query(F.data == "a_promos")
async def a_promos(cb: CallbackQuery):
    if cb.from_user.id not in ADMIN_IDS: return
    async with aiosqlite.connect("shop.db") as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM promos ORDER BY code") as c:
            ps = await c.fetchall()
    text = "🎟 <b>Промокоды:</b>\n\n"
    for p in ps:
        text += f"<code>{p['code']}</code> — +{p['bonus']:.0f}₽ ({p['uses']}/{p['max_uses']})\n"
    if not ps:
        text += "Нет"
    await cb.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Создать", callback_data="a_new_promo")],
            [InlineKeyboardButton(text="« Назад", callback_data="admin")],
        ]),
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "a_new_promo")
async def a_new_promo(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in ADMIN_IDS: return
    await state.set_state(AdminPromo.code)
    await cb.message.edit_text("🎟 Код:")
    await cb.answer()


@dp.message(AdminPromo.code)
async def a_promo_code(message: Message, state: FSMContext):
    await state.update_data(code=message.text.strip().upper())
    await state.set_state(AdminPromo.bonus)
    await message.answer("💰 Бонус (₽):")


@dp.message(AdminPromo.bonus)
async def a_promo_bonus(message: Message, state: FSMContext):
    try:
        b = float(message.text)
    except ValueError:
        await message.answer("❌ Число")
        return
    await state.update_data(bonus=b)
    await state.set_state(AdminPromo.uses)
    await message.answer("📊 Макс. использований:")


@dp.message(AdminPromo.uses)
async def a_promo_uses(message: Message, state: FSMContext):
    try:
        u = int(message.text)
    except ValueError:
        await message.answer("❌ Число")
        return
    d = await state.get_data()
    await state.clear()
    async with aiosqlite.connect("shop.db") as db:
        try:
            await db.execute("INSERT INTO promos (code, bonus, max_uses) VALUES (?, ?, ?)",
                             (d["code"], d["bonus"], u))
            await db.commit()
            await message.answer(f"✅ <code>{d['code']}</code> создан!",
                                 reply_markup=main_kb(message.from_user.id), parse_mode="HTML")
        except Exception:
            await message.answer("❌ Уже существует")


@dp.callback_query(F.data == "a_ban")
async def a_ban(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in ADMIN_IDS: return
    await state.set_state(AdminBan.user_id)
    await cb.message.edit_text("🚫 Введи ID:")
    await cb.answer()


@dp.message(AdminBan.user_id)
async def a_ban_do(message: Message, state: FSMContext):
    try:
        uid = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Число")
        return
    await state.clear()
    u = await get_user(uid)
    if not u:
        await message.answer("❌ Не найден")
        return
    new = 0 if u["is_banned"] else 1
    async with aiosqlite.connect("shop.db") as db:
        await db.execute("UPDATE users SET is_banned = ? WHERE user_id = ?", (new, uid))
        await db.commit()
    await message.answer(f"{'🚫 Забанен' if new else '✅ Разбанен'}: {uid}",
                         reply_markup=main_kb(message.from_user.id))


@dp.callback_query(F.data == "a_broadcast")
async def a_broadcast(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in ADMIN_IDS: return
    await state.set_state(Broadcast.text)
    await cb.message.edit_text("📢 Текст рассылки (или /cancel):")
    await cb.answer()


@dp.message(Broadcast.text, Command("cancel"))
async def bc_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отменено", reply_markup=main_kb(message.from_user.id))


@dp.message(Broadcast.text)
async def bc_do(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS: return
    await state.clear()
    async with aiosqlite.connect("shop.db") as db:
        async with db.execute("SELECT user_id FROM users WHERE is_banned = 0") as c:
            users = await c.fetchall()
    st = await message.answer(f"📢 0/{len(users)}...")
    ok, fail = 0, 0
    for i, (uid,) in enumerate(users, 1):
        try:
            await bot.send_message(uid, message.html_text or message.text, parse_mode="HTML")
            ok += 1
        except Exception:
            fail += 1
        if i % 25 == 0:
            try:
                await st.edit_text(f"📢 {i}/{len(users)}...")
            except Exception:
                pass
        await asyncio.sleep(0.05)
    await st.edit_text(f"✅ Готово\n✔️ {ok}\n❌ {fail}")


# ==================== ЗАПУСК ====================
async def main():
    await init_db()
    print("✅ Бот запущен!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())