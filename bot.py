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
TOKEN = "8563043264:AAFgqebPqB_OFtksfOD3AKqdPrQBqEksIpM"  # вставь сюда токен
ADMIN_ID = 1140430618      # твой Telegram ID
MANAGER_USERNAME = "@sweeeqx"
CHANNEL_LINK = "https://t.me/+hB6FqQfllpQ4MDMx"
CATALOG_FILE = "catalog.json"

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

# =======================
# ФАЙЛ КАТАЛОГА
# =======================
def load_catalog():
    if not os.path.exists(CATALOG_FILE) or os.path.getsize(CATALOG_FILE) == 0:
        with open(CATALOG_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(CATALOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_catalog(data):
    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# =======================
# КЛАВИАТУРЫ
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

def back_button(callback):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=callback)]
    ])

# =======================
# СТАРТ
# =======================
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("🔥 <b>Добро пожаловать!</b>\nВыберите раздел:", reply_markup=main_menu())

# =======================
# ГЛАВНОЕ МЕНЮ
# =======================
@dp.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery):
    await call.answer()
    await call.message.edit_text("🔥 <b>Главное меню</b>", reply_markup=main_menu())

@dp.callback_query(F.data == "manager")
async def manager(call: CallbackQuery):
    await call.answer()
    await call.message.edit_text(f"👤 Менеджер: {MANAGER_USERNAME}", reply_markup=back_button("back_main"))

# =======================
# КАТЕГОРИИ
# =======================
@dp.callback_query(F.data == "assortment")
async def show_categories(call: CallbackQuery):
    await call.answer()
    catalog = load_catalog()
    if not catalog:
        await call.message.edit_text("❌ Каталог пуст.", reply_markup=back_button("back_main"))
        return
    buttons = [[InlineKeyboardButton(text=f"📦 {cat}", callback_data=f"cat|{cat}")] for cat in catalog]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")])
    await call.message.edit_text("🛍 <b>Категории:</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("cat|"))
async def show_brands(call: CallbackQuery):
    await call.answer()
    category = call.data.split("|")[1]
    catalog = load_catalog()
    brands = catalog.get(category, {})
    if not brands:
        await call.message.answer("❌ В этой категории нет брендов.")
        return
    buttons = [[InlineKeyboardButton(text=f"🏷 {b}", callback_data=f"brand|{category}|{b}")] for b in brands]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="assortment")])
    await call.message.edit_text(f"📦 <b>{category}</b>\nВыберите бренд:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

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
        await call.message.answer("❌ Товаров нет.")
        return

    for pid, item in products.items():
        name = item.get("name", "Без названия")
        desc = item.get("description", "Описание отсутствует")
        price = item.get("price", "Цена не указана")
        photo = item.get("photo", None)

        if photo:
            await call.message.answer_photo(
                photo=photo,
                caption=f"🔥 <b>{name}</b>\n\n{desc}\n💰 Цена: {price} ₽"
            )
        else:
            await call.message.answer(f"🔥 <b>{name}</b>\n\n{desc}\n💰 Цена: {price} ₽")

    await call.message.answer("⬅️ Назад", reply_markup=back_button(f"cat|{category}"))

# =======================
# АДМИНКА
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
# ДОБАВЛЕНИЕ
# =======================
@dp.callback_query(F.data == "add_product")
async def add_start(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.set_state(AddProduct.category)
    await call.message.answer("Введите категорию:")

@dp.message(AddProduct.category)
async def add_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    await state.set_state(AddProduct.brand)
    await message.answer("Введите бренд:")

@dp.message(AddProduct.brand)
async def add_brand(message: Message, state: FSMContext):
    await state.update_data(brand=message.text)
    await state.set_state(AddProduct.name)
    await message.answer("Введите название товара:")

@dp.message(AddProduct.name)
async def add_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddProduct.description)
    await message.answer("Введите описание товара:")

@dp.message(AddProduct.description)
async def add_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AddProduct.price)
    await message.answer("Введите цену:")

@dp.message(AddProduct.price)
async def add_price(message: Message, state: FSMContext):
    await state.update_data(price=message.text)
    await state.set_state(AddProduct.photo)
    await message.answer("Отправьте фото товара:")

@dp.message(AddProduct.photo)
async def add_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    catalog = load_catalog()
    category = data["category"]
    brand = data["brand"]
    name = data["name"]
    product_id = str(uuid.uuid4())[:8]  # короткий ID

    catalog.setdefault(category, {}).setdefault(brand, {})[product_id] = {
        "name": name,
        "description": data["description"],
        "price": data["price"],
        "photo": message.photo[-1].file_id
    }

    save_catalog(catalog)
    await message.answer("✅ Товар добавлен!")
    await state.clear()

# =======================
# УДАЛЕНИЕ
# =======================
@dp.callback_query(F.data == "delete_product")
async def delete_product(call: CallbackQuery):
    await call.answer()
    catalog = load_catalog()
    buttons = []
    for c in catalog:
        for b in catalog[c]:
            for pid, p in catalog[c][b].items():
                buttons.append([InlineKeyboardButton(text=f"❌ {p.get('name','Без названия')}", callback_data=f"del|{pid}")])
    if not buttons:
        await call.message.answer("❌ Товаров нет.")
        return
    await call.message.answer("Выберите товар для удаления:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("del|"))
async def confirm_delete(call: CallbackQuery):
    await call.answer()
    product_id = call.data.split("|")[1]
    catalog = load_catalog()
    for c in list(catalog):
        for b in list(catalog[c]):
            if product_id in catalog[c][b]:
                del catalog[c][b][product_id]
                if not catalog[c][b]:
                    del catalog[c][b]
                if not catalog[c]:
                    del catalog[c]
                save_catalog(catalog)
                await call.message.answer("✅ Товар удалён")
                return

# =======================
# РЕДАКТИРОВАНИЕ
# =======================
@dp.callback_query(F.data == "edit_product")
async def edit_product(call: CallbackQuery, state: FSMContext):
    await call.answer()
    catalog = load_catalog()
    buttons = []
    for c in catalog:
        for b in catalog[c]:
            for pid, p in catalog[c][b].items():
                buttons.append([InlineKeyboardButton(text=f"✏️ {p.get('name','Без названия')}", callback_data=f"edit|{pid}")])
    if not buttons:
        await call.message.answer("❌ Товаров нет.")
        return
    await call.message.answer("Выберите товар для редактирования:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("edit|"))
async def choose_edit(call: CallbackQuery, state: FSMContext):
    await call.answer()
    product_id = call.data.split("|")[1]
    await state.update_data(product_id=product_id)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Описание", callback_data="field_desc")],
        [InlineKeyboardButton(text="Цена", callback_data="field_price")],
        [InlineKeyboardButton(text="Фото", callback_data="field_photo")]
    ])
    await call.message.answer("Что изменить?", reply_markup=keyboard)
    await state.set_state(EditProduct.field)

@dp.callback_query(F.data.in_(["field_desc", "field_price", "field_photo"]))
async def set_field(call: CallbackQuery, state: FSMContext):
    await call.answer()
    field_map = {"field_desc": "description", "field_price": "price", "field_photo": "photo"}
    field = field_map[call.data]
    await state.update_data(edit_field=field)
    await call.message.answer("Отправьте новое значение (текст или фото):")

@dp.message(EditProduct.field)
async def save_edit(message: Message, state: FSMContext):
    data = await state.get_data()
    catalog = load_catalog()
    product_id = data["product_id"]
    field = data["edit_field"]

    for c in catalog:
        for b in catalog[c]:
            if product_id in catalog[c][b]:
                if field == "photo":
                    catalog[c][b][product_id]["photo"] = message.photo[-1].file_id
                else:
                    catalog[c][b][product_id][field] = message.text
                save_catalog(catalog)
                await message.answer("✅ Изменения сохранены")
                await state.clear()
                return

# =======================
# ЗАПУСК
# =======================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    