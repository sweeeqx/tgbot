import asyncio
import json
import os
import uuid

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

# =======================
# НАСТРОЙКИ
# =======================
TOKEN = "8563043264:AAFgqebPqB_OFtksfOD3AKqdPrQBqEksIpM"
ADMIN_ID = 1140430618
MANAGER = "@sweeeqx"
CHANNEL_LINK = "https://t.me/PARekb2"

CATALOG_FILE = "catalog.json"
USERS_FILE = "users.json"

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

# =======================
# JSON
# =======================
def load_json(file):
    if not os.path.exists(file):
        return {}
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# =======================
# UI
# =======================
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Ассортимент", callback_data="menu_cat")],
        [InlineKeyboardButton(text="👤 Менеджер", url=f"https://t.me/{MANAGER.replace('@','')}")],
        [InlineKeyboardButton(text="📢 Канал", url=CHANNEL_LINK)]
    ])

def back(btn):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=btn)]
    ])

# =======================
# FSM
# =======================
class Add(StatesGroup):
    cat = State()
    brand = State()
    name = State()
    desc = State()
    price = State()
    photo = State()

class Edit(StatesGroup):
    pid = State()
    field = State()

class News(StatesGroup):
    text = State()
    photo = State()

# =======================
# START
# =======================
@dp.message(Command("start"))
async def start(msg: Message):
    users = load_json(USERS_FILE)
    users[str(msg.from_user.id)] = True
    save_json(USERS_FILE, users)

    await msg.answer("🔥 Добро пожаловать", reply_markup=main_menu())

# =======================
# КАТЕГОРИИ
# =======================
@dp.callback_query(F.data == "menu_cat")
async def categories(call: CallbackQuery):
    await call.answer()

    catalog = load_json(CATALOG_FILE)

    if not catalog:
        await call.message.edit_text("❌ Каталог пуст", reply_markup=back("back_main"))
        return

    kb = [[InlineKeyboardButton(text=c, callback_data=f"cat:{c}")] for c in catalog]
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")])

    await call.message.edit_text("📦 Категории", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery):
    await call.answer()
    await call.message.edit_text("🏠 Главное меню", reply_markup=main_menu())

# =======================
# БРЕНДЫ
# =======================
@dp.callback_query(F.data.startswith("cat:"))
async def brands(call: CallbackQuery):
    await call.answer()
    cat = call.data.split(":")[1]

    catalog = load_json(CATALOG_FILE)

    kb = [[InlineKeyboardButton(text=b, callback_data=f"brand:{cat}:{b}")]
          for b in catalog.get(cat, {})]

    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu_cat")])

    await call.message.edit_text(f"📦 {cat}", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# =======================
# ТОВАРЫ
# =======================
@dp.callback_query(F.data.startswith("brand:"))
async def products(call: CallbackQuery):
    await call.answer()
    _, cat, brand = call.data.split(":")

    catalog = load_json(CATALOG_FILE)

    items = catalog.get(cat, {}).get(brand, {})

    if not items:
        await call.message.answer("❌ Нет товаров")
        return

    for pid, item in items.items():
        await call.message.answer_photo(
            photo=item.get("photo"),
            caption=f"🔥 <b>{item.get('name')}</b>\n\n{item.get('desc')}\n💰 {item.get('price')} ₽",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛒 Купить", url=f"https://t.me/{MANAGER.replace('@','')}")]
            ])
        )

    await call.message.answer("⬅️ Назад", reply_markup=back(f"cat:{cat}"))

# =======================
# АДМИНКА
# =======================
@dp.message(Command("admin"))
async def admin(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить", callback_data="add")],
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit")],
        [InlineKeyboardButton(text="❌ Удалить", callback_data="del")],
        [InlineKeyboardButton(text="📢 Новость", callback_data="news")]
    ])
    await msg.answer("⚙️ Админка", reply_markup=kb)

# =======================
# ДОБАВЛЕНИЕ
# =======================
@dp.callback_query(F.data == "add")
async def add_start(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.set_state(Add.cat)
    await call.message.answer("Категория:")

@dp.message(Add.cat)
async def add_cat(msg: Message, state: FSMContext):
    await state.update_data(cat=msg.text)
    await state.set_state(Add.brand)
    await msg.answer("Бренд:")

@dp.message(Add.brand)
async def add_brand(msg: Message, state: FSMContext):
    await state.update_data(brand=msg.text)
    await state.set_state(Add.name)
    await msg.answer("Название:")

@dp.message(Add.name)
async def add_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await state.set_state(Add.desc)
    await msg.answer("Описание:")

@dp.message(Add.desc)
async def add_desc(msg: Message, state: FSMContext):
    await state.update_data(desc=msg.text)
    await state.set_state(Add.price)
    await msg.answer("Цена:")

@dp.message(Add.price)
async def add_price(msg: Message, state: FSMContext):
    await state.update_data(price=msg.text)
    await state.set_state(Add.photo)
    await msg.answer("Отправь фото:")

@dp.message(Add.photo)
async def add_photo(msg: Message, state: FSMContext):
    data = await state.get_data()
    catalog = load_json(CATALOG_FILE)

    catalog.setdefault(data["cat"], {}).setdefault(data["brand"], {})[str(uuid.uuid4())[:6]] = {
        "name": data["name"],
        "desc": data["desc"],
        "price": data["price"],
        "photo": msg.photo[-1].file_id
    }

    save_json(CATALOG_FILE, catalog)
    await msg.answer("✅ Товар добавлен")
    await state.clear()

# =======================
# УДАЛЕНИЕ
# =======================
@dp.callback_query(F.data == "del")
async def delete(call: CallbackQuery):
    await call.answer()
    catalog = load_json(CATALOG_FILE)

    kb = []
    for c in catalog:
        for b in catalog[c]:
            for pid, p in catalog[c][b].items():
                kb.append([InlineKeyboardButton(text=p["name"], callback_data=f"del:{pid}")])

    await call.message.answer("Выбери товар:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("del:"))
async def delete_item(call: CallbackQuery):
    await call.answer()
    pid = call.data.split(":")[1]

    catalog = load_json(CATALOG_FILE)

    for c in list(catalog):
        for b in list(catalog[c]):
            if pid in catalog[c][b]:
                del catalog[c][b][pid]

    save_json(CATALOG_FILE, catalog)
    await call.message.answer("✅ Удалено")

# =======================
# РЕДАКТИРОВАНИЕ
# =======================
@dp.callback_query(F.data == "edit")
async def edit(call: CallbackQuery):
    await call.answer()
    catalog = load_json(CATALOG_FILE)

    kb = []
    for c in catalog:
        for b in catalog[c]:
            for pid, p in catalog[c][b].items():
                kb.append([InlineKeyboardButton(text=p["name"], callback_data=f"edit:{pid}")])

    await call.message.answer("Выбери товар:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("edit:"))
async def edit_choose(call: CallbackQuery, state: FSMContext):
    await call.answer()
    pid = call.data.split(":")[1]
    await state.update_data(pid=pid)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Описание", callback_data="f:desc")],
        [InlineKeyboardButton(text="Цена", callback_data="f:price")]
    ])
    await call.message.answer("Что изменить?", reply_markup=kb)
    await state.set_state(Edit.field)

@dp.callback_query(F.data.startswith("f:"))
async def edit_field(call: CallbackQuery, state: FSMContext):
    await call.answer()
    field = call.data.split(":")[1]
    await state.update_data(field=field)
    await call.message.answer("Новое значение:")

@dp.message(Edit.field)
async def edit_save(msg: Message, state: FSMContext):
    data = await state.get_data()
    catalog = load_json(CATALOG_FILE)

    for c in catalog:
        for b in catalog[c]:
            if data["pid"] in catalog[c][b]:
                catalog[c][b][data["pid"]][data["field"]] = msg.text

    save_json(CATALOG_FILE, catalog)
    await msg.answer("✅ Обновлено")
    await state.clear()

# =======================
# НОВОСТИ
# =======================
@dp.callback_query(F.data == "news")
async def news_start(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.set_state(News.text)
    await call.message.answer("Текст новости:")

@dp.message(News.text)
async def news_text(msg: Message, state: FSMContext):
    await state.update_data(text=msg.text)
    await state.set_state(News.photo)
    await msg.answer("Отправь фото:")

@dp.message(News.photo)
async def news_send(msg: Message, state: FSMContext):
    data = await state.get_data()
    users = load_json(USERS_FILE)

    sent = 0

    for uid in users:
        try:
            await bot.send_photo(
                uid,
                msg.photo[-1].file_id,
                caption=data["text"],
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🛒 Купить", url=f"https://t.me/{MANAGER.replace('@','')}")]
                ])
            )
            sent += 1
        except:
            pass

    await msg.answer(f"✅ Отправлено: {sent}")
    await state.clear()

# =======================
# ЗАПУСК
# =======================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
