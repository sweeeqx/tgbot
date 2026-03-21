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
MANAGER_USERNAME = "@sweeeqx"
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

class EditProduct(StatesGroup):
    field = State()
    product_id = State()

class NewsState(StatesGroup):
    photo = State()
    text = State()

# =======================
# ФАЙЛЫ
# =======================
def load_catalog():
    if not os.path.exists(CATALOG_FILE):
        with open(CATALOG_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

    with open(CATALOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_catalog(data):
    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump([], f)

    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

# =======================
# КНОПКИ
# =======================
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🛍 Ассортимент", callback_data="assortment"),
            InlineKeyboardButton(text="👤 Менеджер", callback_data="manager")
        ],
        [
            InlineKeyboardButton(text="📢 Канал", url=CHANNEL_LINK)
        ]
    ])

def back_button(cb):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=cb)]
    ])

# =======================
# START
# =======================
@dp.message(Command("start"))
async def start(message: Message):

    users = load_users()

    if message.from_user.id not in users:
        users.append(message.from_user.id)
        save_users(users)

    await message.answer(
        "🔥 <b>Добро пожаловать!</b>\nВыберите раздел:",
        reply_markup=main_menu()
    )

# =======================
# МЕНЮ
# =======================
@dp.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery):
    await call.answer()
    await call.message.edit_text("🔥 <b>Главное меню</b>", reply_markup=main_menu())

@dp.callback_query(F.data == "manager")
async def manager(call: CallbackQuery):
    await call.answer()
    await call.message.edit_text(
        f"👤 Менеджер: {MANAGER_USERNAME}",
        reply_markup=back_button("back_main")
    )

# =======================
# КАТЕГОРИИ
# =======================
@dp.callback_query(F.data == "assortment")
async def show_categories(call: CallbackQuery):
    await call.answer()

    catalog = load_catalog()

    if not catalog:
        await call.message.edit_text("❌ Каталог пуст", reply_markup=back_button("back_main"))
        return

    buttons = []

    for cat in catalog:
        buttons.append([InlineKeyboardButton(text=f"📦 {cat}", callback_data=f"cat|{cat}")])

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")])

    await call.message.edit_text(
        "🛍 <b>Категории</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@dp.callback_query(F.data.startswith("cat|"))
async def show_brands(call: CallbackQuery):
    await call.answer()

    category = call.data.split("|")[1]
    catalog = load_catalog()

    brands = catalog.get(category, {})

    if not brands:
        await call.message.answer("❌ Нет брендов")
        return

    buttons = []

    for b in brands:
        buttons.append([InlineKeyboardButton(text=f"🏷 {b}", callback_data=f"brand|{category}|{b}")])

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="assortment")])

    await call.message.edit_text(
        f"📦 <b>{category}</b>\nВыберите бренд",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

# =======================
# ТОВАРЫ
# =======================
@dp.callback_query(F.data.startswith("brand|"))
async def show_products(call: CallbackQuery):

    await call.answer()

    _, category, brand = call.data.split("|")

    catalog = load_catalog()

    products = catalog.get(category, {}).get(brand, {})

    if not products:
        await call.message.answer("❌ Товаров нет")
        return

    for pid, item in products.items():

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🛒 Купить", url=f"https://t.me/{MANAGER_USERNAME.replace('@','')}")]
            ]
        )

        await call.message.answer_photo(
            photo=item["photo"],
            caption=f"🔥 <b>{item['name']}</b>\n\n{item['description']}\n💰 Цена: {item['price']} ₽",
            reply_markup=keyboard
        )

    await call.message.answer("⬅️ Назад", reply_markup=back_button(f"cat|{category}"))

# =======================
# АДМИН
# =======================
@dp.message(Command("admin"))
async def admin_panel(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить товар", callback_data="add_product")],
        [InlineKeyboardButton(text="✏️ Редактировать товар", callback_data="edit_product")],
        [InlineKeyboardButton(text="❌ Удалить товар", callback_data="delete_product")]
    ])

    await message.answer("⚙️ Админ панель", reply_markup=keyboard)

# =======================
# ДОБАВЛЕНИЕ ТОВАРА
# =======================
@dp.callback_query(F.data == "add_product")
async def add_start(call: CallbackQuery, state: FSMContext):

    await call.answer()

    await state.set_state(AddProduct.category)

    await call.message.answer("Введите категорию")

@dp.message(AddProduct.category)
async def add_category(message: Message, state: FSMContext):

    await state.update_data(category=message.text)

    await state.set_state(AddProduct.brand)

    await message.answer("Введите бренд")

@dp.message(AddProduct.brand)
async def add_brand(message: Message, state: FSMContext):

    await state.update_data(brand=message.text)

    await state.set_state(AddProduct.name)

    await message.answer("Введите название товара")

@dp.message(AddProduct.name)
async def add_name(message: Message, state: FSMContext):

    await state.update_data(name=message.text)

    await state.set_state(AddProduct.description)

    await message.answer("Введите описание")

@dp.message(AddProduct.description)
async def add_desc(message: Message, state: FSMContext):

    await state.update_data(description=message.text)

    await state.set_state(AddProduct.price)

    await message.answer("Введите цену")

@dp.message(AddProduct.price)
async def add_price(message: Message, state: FSMContext):

    await state.update_data(price=message.text)

    await state.set_state(AddProduct.photo)

    await message.answer("Отправьте фото")

@dp.message(AddProduct.photo)
async def add_photo(message: Message, state: FSMContext):

    data = await state.get_data()

    catalog = load_catalog()

    pid = str(uuid.uuid4())[:8]

    catalog.setdefault(data["category"], {}).setdefault(data["brand"], {})[pid] = {
        "name": data["name"],
        "description": data["description"],
        "price": data["price"],
        "photo": message.photo[-1].file_id
    }

    save_catalog(catalog)

    await message.answer("✅ Товар добавлен")
    await state.clear()

# =======================
# НОВОСТИ
# =======================
@dp.message(Command("news"))
async def create_news(message: Message, state: FSMContext):

    if message.from_user.id != ADMIN_ID:
        return

    await message.answer("📸 Отправьте фото новости")

    await state.set_state(NewsState.photo)

@dp.message(NewsState.photo)
async def news_photo(message: Message, state: FSMContext):

    await state.update_data(photo=message.photo[-1].file_id)

    await state.set_state(NewsState.text)

    await message.answer("Введите текст новости")

@dp.message(NewsState.text)
async def preview_news(message: Message, state: FSMContext):

    await state.update_data(text=message.text)

    data = await state.get_data()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Купить", url=f"https://t.me/{MANAGER_USERNAME.replace('@','')}")],
            [
                InlineKeyboardButton(text="✅ Отправить", callback_data="send_news"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_news")
            ]
        ]
    )

    await message.answer_photo(
        photo=data["photo"],
        caption=f"📰 <b>Предпросмотр новости</b>\n\n{data['text']}",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "send_news")
async def send_news(call: CallbackQuery, state: FSMContext):

    data = await state.get_data()

    users = load_users()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Купить", url=f"https://t.me/{MANAGER_USERNAME.replace('@','')}")]
        ]
    )

    for user in users:
        try:
            await bot.send_photo(
                chat_id=user,
                photo=data["photo"],
                caption=f"📰 <b>Новость</b>\n\n{data['text']}",
                reply_markup=keyboard
            )
        except:
            pass

    try:
        await bot.send_photo(
            chat_id=CHANNEL_LINK,
            photo=data["photo"],
            caption=f"📰 <b>Новость</b>\n\n{data['text']}",
            reply_markup=keyboard
        )
    except:
        pass

    await call.message.edit_caption("✅ Новость отправлена")

    await state.clear()

@dp.callback_query(F.data == "cancel_news")
async def cancel_news(call: CallbackQuery, state: FSMContext):

    await state.clear()

    await call.message.edit_caption("❌ Отправка отменена")

# =======================
# ЗАПУСК
# =======================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
