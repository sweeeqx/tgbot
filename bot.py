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
CHANNEL_LINK = "https://t.me/PARekb2"

CATALOG_FILE = "catalog.json"
USERS_FILE = "users.json"

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

# =======================
# FSM
# =======================
class AddProduct(StatesGroup):
    category = State()
    brand = State()
    name = State()
    description = State()
    price = State()
    photo = State()

class NewsState(StatesGroup):
    text = State()
    photo = State()

# =======================
# ФАЙЛЫ
# =======================
def load_catalog():
    if not os.path.exists(CATALOG_FILE):
        return {}
    with open(CATALOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_catalog(data):
    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

# =======================
# КЛАВИАТУРЫ
# =======================
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Каталог", callback_data="catalog")],
        [InlineKeyboardButton(text="📢 Канал", url=CHANNEL_LINK)]
    ])

# =======================
# СТАРТ
# =======================
@dp.message(Command("start"))
async def start(message: Message):
    users = load_users()
    if message.from_user.id not in users:
        users.append(message.from_user.id)
        save_users(users)

    await message.answer("🔥 Добро пожаловать!", reply_markup=main_menu())

# =======================
# КАТАЛОГ
# =======================
@dp.callback_query(F.data == "catalog")
async def show_categories(call: CallbackQuery):
    await call.answer()
    catalog = load_catalog()

    if not catalog:
        await call.message.edit_text("❌ Каталог пуст")
        return

    buttons = []
    for cat in catalog:
        buttons.append([InlineKeyboardButton(text=cat, callback_data=f"cat|{cat}")])

    await call.message.edit_text("📦 Категории:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

# =======================
# БРЕНДЫ
# =======================
@dp.callback_query(F.data.startswith("cat|"))
async def show_brands(call: CallbackQuery):
    await call.answer()
    category = call.data.split("|")[1]
    catalog = load_catalog()

    brands = catalog.get(category, {})

    buttons = []
    for b in brands:
        buttons.append([InlineKeyboardButton(text=b, callback_data=f"brand|{category}|{b}")])

    await call.message.edit_text("🏷 Выберите бренд:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

# =======================
# ТОВАРЫ
# =======================
@dp.callback_query(F.data.startswith("brand|"))
async def show_products(call: CallbackQuery):
    await call.answer()
    _, category, brand = call.data.split("|")

    catalog = load_catalog()
    products = catalog.get(category, {}).get(brand, {})

    for pid, item in products.items():
        text = f"🔥 <b>{item.get('name')}</b>\n\n{item.get('description')}\n💰 {item.get('price')} ₽"

        await call.message.answer_photo(
            photo=item.get("photo"),
            caption=text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🛒 Купить", url=CHANNEL_LINK)]
                ]
            )
        )

# =======================
# АДМИН
# =======================
@dp.message(Command("admin"))
async def admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Товар", callback_data="add")],
        [InlineKeyboardButton(text="📢 Новость", callback_data="news")]
    ])
    await message.answer("⚙️ Админка", reply_markup=kb)

# =======================
# ДОБАВИТЬ ТОВАР
# =======================
@dp.callback_query(F.data == "add")
async def add_start(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.set_state(AddProduct.category)
    await call.message.answer("Категория:")

@dp.message(AddProduct.category)
async def add_cat(msg: Message, state: FSMContext):
    await state.update_data(category=msg.text)
    await state.set_state(AddProduct.brand)
    await msg.answer("Бренд:")

@dp.message(AddProduct.brand)
async def add_brand(msg: Message, state: FSMContext):
    await state.update_data(brand=msg.text)
    await state.set_state(AddProduct.name)
    await msg.answer("Название:")

@dp.message(AddProduct.name)
async def add_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await state.set_state(AddProduct.description)
    await msg.answer("Описание:")

@dp.message(AddProduct.description)
async def add_desc(msg: Message, state: FSMContext):
    await state.update_data(description=msg.text)
    await state.set_state(AddProduct.price)
    await msg.answer("Цена:")

@dp.message(AddProduct.price)
async def add_price(msg: Message, state: FSMContext):
    await state.update_data(price=msg.text)
    await state.set_state(AddProduct.photo)
    await msg.answer("Фото:")

@dp.message(AddProduct.photo)
async def add_photo(msg: Message, state: FSMContext):
    data = await state.get_data()
    catalog = load_catalog()

    catalog.setdefault(data["category"], {}).setdefault(data["brand"], {})[str(uuid.uuid4())[:8]] = {
        "name": data["name"],
        "description": data["description"],
        "price": data["price"],
        "photo": msg.photo[-1].file_id
    }

    save_catalog(catalog)
    await msg.answer("✅ Товар добавлен")
    await state.clear()

# =======================
# НОВОСТИ
# =======================
@dp.callback_query(F.data == "news")
async def news_start(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.set_state(NewsState.text)
    await call.message.answer("Текст новости:")

@dp.message(NewsState.text)
async def news_text(msg: Message, state: FSMContext):
    await state.update_data(text=msg.text)
    await state.set_state(NewsState.photo)
    await msg.answer("Фото новости:")

@dp.message(NewsState.photo)
async def send_news(msg: Message, state: FSMContext):
    data = await state.get_data()
    users = load_users()

    sent = 0

    for user in users:
        try:
            await bot.send_photo(
                user,
                photo=msg.photo[-1].file_id,
                caption=data["text"],
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="🛒 Купить", callback_data="catalog")]
                    ]
                )
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
