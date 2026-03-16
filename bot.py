import asyncio
import logging
import aiosqlite
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ============ СОЗЛАМАЛАР ============
BOT_TOKEN = "8512859375:AAFXnyi0GE3ctdCSuk1fZVoDMC3Io7YOJHo"  # @BotFather дан олган токенингиз
ADMIN_ID = 731696853  # ЎЗИНГИЗНИ ТЕЛЕГРАМ ID РАҚАМИНГИЗНИ ЁЗИНГ!

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ============ БАЗА МАЪЛУМОТЛАРИ ============
DB_NAME = "navbat.db"

async def init_db():
    """Базани тайёрлаш"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS navbatlar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                ism TEXT,
                telefon TEXT,
                mashina_raqam TEXT,
                sana TEXT,
                soat TEXT,
                xizmat TEXT,
                status TEXT DEFAULT 'faol',
                yaratilgan_vaqt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS adminlar (
                user_id INTEGER PRIMARY KEY
            )
        """)
        # Асосий админни қўшиш
        await db.execute("INSERT OR IGNORE INTO adminlar (user_id) VALUES (?)", (ADMIN_ID,))
        await db.commit()

# ============ ХОЛАТЛАР (States) ============
class NavbatState(StatesGroup):
    ism = State()
    telefon = State()
    mashina = State()
    sana = State()
    soat = State()
    xizmat = State()
    tasdiq = State()

class AdminState(StatesGroup):
    xabar = State()

# ============ КЛАВИАТУРАЛАР ============
def asosiy_menu(user_id: int):
    """Асосий меню"""
    buttons = [
        [KeyboardButton(text="📝 Навбат олиш")],
        [KeyboardButton(text="📋 Менинг навбатларим")],
        [KeyboardButton(text="📍 Манзил"), KeyboardButton(text="📞 Телефон")],
    ]
    if user_id == ADMIN_ID:
        buttons.append([KeyboardButton(text="⚙️ Админ панели")])
    
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def xizmatlar_menu():
    """Хизматлар менюси"""
    buttons = [
        [KeyboardButton(text="🚗 Стандарт ювиш"), KeyboardButton(text="🚙 Комплекс ювиш")],
        [KeyboardButton(text="✨ Полировка"), KeyboardButton(text="🧪 Химчистка")],
        [KeyboardButton(text="🔙 Орқага")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def sanalar_menu():
    """Кунлар менюси"""
    today = datetime.now()
    buttons = []
    for i in range(7):  # 7 кунгача
        date = today + timedelta(days=i)
        date_str = date.strftime("%d.%m.%Y")
        buttons.append([KeyboardButton(text=f"📅 {date_str}")])
    buttons.append([KeyboardButton(text="🔙 Орқага")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def soatlar_menu():
    """Соатлар менюси"""
    soatlar = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00"]
    buttons = []
    for soat in soatlar:
        buttons.append([KeyboardButton(text=f"⏰ {soat}")])
    buttons.append([KeyboardButton(text="🔙 Орқага")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def tasdiq_menu():
    """Тасдиқлаш менюси"""
    buttons = [
        [KeyboardButton(text="✅ Тасдиқлаш"), KeyboardButton(text="❌ Бекор қилиш")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# ============ КОМАНДАЛАР ============

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Старт команд"""
    await message.answer(
        f"🚗 <b>Sharq Auto Service</b> га хуш келибсиз!\n\n"
        f"Бу ерда сиз автомойкага онлайн навбат олишингиз мумкин.\n\n"
        f"📍 Манзил: Sharq massivi\n"
        f"📞 Тел: +99893 315 74 74\n\n"
        f"Қуйидаги тугмалардан фойдаланинг:",
        reply_markup=asosiy_menu(message.from_user.id),
        parse_mode="HTML"
    )

@dp.message(F.text == "📍 Манзил")
async def show_manzil(message: Message):
    await message.answer(
        "📍 <b>Манзил:</b> Sharq massivi\n\n"
        "🗺 Яндекс/Гугл харитада кўрсатиб беришимни хоҳлайсизми?",
        parse_mode="HTML"
    )

@dp.message(F.text == "📞 Телефон")
async def show_telefon(message: Message):
    await message.answer(
        "📞 <b>Телефон:</b> +99893 315 74 74\n\n"
        "☎️ Иш вақти: 09:00 - 19:00",
        parse_mode="HTML"
    )

# ============ НАВБАТ ОЛИШ ============

@dp.message(F.text == "📝 Навбат олиш")
async def start_navbat(message: Message, state: FSMContext):
    await state.set_state(NavbatState.ism)
    await message.answer(
        "📝 Исмингизни киритинг:\n\n"
        "Мисол: <b>Алижон</b>",
        parse_mode="HTML"
    )

@dp.message(NavbatState.ism)
async def get_ism(message: Message, state: FSMContext):
    await state.update_data(ism=message.text)
    await state.set_state(NavbatState.telefon)
    
    # Контакт юбориш тугмаси
    contact_btn = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Рақамни юбориш", request_contact=True)]],
        resize_keyboard=True
    )
    await message.answer("📞 Телефон рақамингизни киритинг:", reply_markup=contact_btn)

@dp.message(NavbatState.telefon)
@dp.message(F.contact)
async def get_telefon(message: Message, state: FSMContext):
    if message.contact:
        telefon = message.contact.phone_number
    else:
        telefon = message.text
    
    await state.update_data(telefon=telefon)
    await state.set_state(NavbatState.mashina)
    await message.answer(
        "🚗 Машина рақамини киритинг:\n\n"
        "Мисол: <b>01 A 123 BC</b> ёки <b>90 A 123456</b>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Орқага")]], resize_keyboard=True)
    )

@dp.message(NavbatState.mashina)
async def get_mashina(message: Message, state: FSMContext):
    if message.text == "🔙 Орқага":
        await state.clear()
        await message.answer("Бош меню:", reply_markup=asosiy_menu(message.from_user.id))
        return
    
    await state.update_data(mashina=message.text)
    await state.set_state(NavbatState.sana)
    await message.answer("📅 Қайси кунга навбат оламиз?", reply_markup=sanalar_menu())

@dp.message(NavbatState.sana)
async def get_sana(message: Message, state: FSMContext):
    if message.text == "🔙 Орқага":
        await state.clear()
        await message.answer("Бош меню:", reply_markup=asosiy_menu(message.from_user.id))
        return
    
    sana = message.text.replace("📅 ", "")
    await state.update_data(sana=sana)
    await state.set_state(NavbatState.soat)
    await message.answer("⏰ Қайси соатга?", reply_markup=soatlar_menu())

@dp.message(NavbatState.soat)
async def get_soat(message: Message, state: FSMContext):
    if message.text == "🔙 Орқага":
        await state.clear()
        await message.answer("Бош меню:", reply_markup=asosiy_menu(message.from_user.id))
        return
    
    soat = message.text.replace("⏰ ", "")
    await state.update_data(soat=soat)
    await state.set_state(NavbatState.xizmat)
    await message.answer("🛠 Қандай хизмат керак?", reply_markup=xizmatlar_menu())

@dp.message(NavbatState.xizmat)
async def get_xizmat(message: Message, state: FSMContext):
    if message.text == "🔙 Орқага":
        await state.clear()
        await message.answer("Бош меню:", reply_markup=asosiy_menu(message.from_user.id))
        return
    
    xizmat = message.text.replace("🚗 ", "").replace("🚙 ", "").replace("✨ ", "").replace("🧪 ", "")
    await state.update_data(xizmat=xizmat)
    
    data = await state.get_data()
    
    # Тасдиқлаш хабари
    tasdiq_text = (
        f"📋 <b>Навбат маълумотлари:</b>\n\n"
        f"👤 Исм: <b>{data['ism']}</b>\n"
        f"📞 Телефон: <b>{data['telefon']}</b>\n"
        f"🚗 Машина: <b>{data['mashina']}</b>\n"
        f"📅 Сана: <b>{data['sana']}</b>\n"
        f"⏰ Соат: <b>{data['soat']}</b>\n"
        f"🛠 Хизмат: <b>{xizmat}</b>\n\n"
        f"Тўғрими?"
    )
    
    await state.set_state(NavbatState.tasdiq)
    await message.answer(tasdiq_text, parse_mode="HTML", reply_markup=tasdiq_menu())

@dp.message(NavbatState.tasdiq)
async def tasdiq_navbat(message: Message, state: FSMContext):
    if message.text == "❌ Бекор қилиш":
        await state.clear()
        await message.answer("Навбат бекор қилинди.", reply_markup=asosiy_menu(message.from_user.id))
        return
    
    if message.text == "✅ Тасдиқлаш":
        data = await state.get_data()
        
        # Базага сақлаш
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("""
                INSERT INTO navbatlar (user_id, ism, telefon, mashina_raqam, sana, soat, xizmat)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                message.from_user.id,
                data['ism'],
                data['telefon'],
                data['mashina'],
                data['sana'],
                data['soat'],
                data['xizmat']
            ))
            await db.commit()
        
        # Админга хабар
        admin_text = (
            f"🆕 <b>ЯНГИ НАВБАТ!</b>\n\n"
            f"👤 Исм: {data['ism']}\n"
            f"📞 Телефон: {data['telefon']}\n"
            f"🚗 Машина: {data['mashina']}\n"
            f"📅 {data['sана']} | ⏰ {data['soat']}\n"
            f"🛠 {data['xizmat']}"
        )
        await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML")
        
        # Фойдаланувчига хабар
        await message.answer(
            f"✅ <b>Навбат муваффақиятли олинди!</b>\n\n"
            f"📅 Сана: {data['sana']}\n"
            f"⏰ Соат: {data['soat']}\n"
            f"🛠 Хизмат: {data['xizmat']}\n\n"
            f"⏳ Илтимос, белгиланган вақтда келинг!",
            parse_mode="HTML",
            reply_markup=asosiy_menu(message.from_user.id)
        )
        
        await state.clear()

# ============ МЕНИНГ НАВБАТЛАРИМ ============

@dp.message(F.text == "📋 Менинг навбатларим")
async def my_navbatlar(message: Message):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT id, sana, soat, xizmat, status FROM navbatlar WHERE user_id = ? AND status = 'faol' ORDER BY sana, soat",
            (message.from_user.id,)
        ) as cursor:
            navbatlar = await cursor.fetchall()
    
    if not navbatlar:
        await message.answer("📭 Сизда фаол навбатлар йўқ.", reply_markup=asosiy_menu(message.from_user.id))
        return
    
    text = "📋 <b>Сизнинг навбатларингиз:</b>\n\n"
    for navbat in navbatlar:
        navbat_id, sana, soat, xizmat, status = navbat
        text += f"🆔 ID: {navbat_id}\n"
        text += f"📅 {sana} | ⏰ {soat}\n"
        text += f"🛠 {xizmat}\n"
        text += f"Статус: {'✅ Фаол' if status == 'faol' else '❌ Бекор'}\n"
        text += "➖➖➖➖➖➖➖➖➖\n"
    
    # Бекор қилиш тугмалари
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"❌ ID {n[0]} бекор қилиш", callback_data=f"bekor_{n[0]}")] 
        for n in navbatlar
    ])
    
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("bekor_"))
async def bekor_qilish(callback: CallbackQuery):
    navbat_id = int(callback.data.split("_")[1])
    
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE navbatlar SET status = 'bekor' WHERE id = ?", (navbat_id,))
        await db.commit()
    
    await callback.answer("Навбат бекор қилинди!")
    await callback.message.edit_text("❌ Навбат бекор қилинди.\n\nЯнги навбат олиш учун /start")

# ============ АДМИН ПАНЕЛИ ============

@dp.message(F.text == "⚙️ Админ панели")
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="📋 Барча навбатлар")],
            [KeyboardButton(text="📢 Хабар юбориш"), KeyboardButton(text="🔙 Асосий меню")]
        ],
        resize_keyboard=True
    )
    await message.answer("⚙️ <b>Админ панели</b>", parse_mode="HTML", reply_markup=keyboard)

@dp.message(F.text == "📊 Статистика")
async def admin_stat(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    async with aiosqlite.connect(DB_NAME) as db:
        # Бугунги навбатлар
        today = datetime.now().strftime("%d.%m.%Y")
        async with db.execute("SELECT COUNT(*) FROM navbatlar WHERE sana = ?", (today,)) as cursor:
            bugun = (await cursor.fetchone())[0]
        
        # Жами навбатлар
        async with db.execute("SELECT COUNT(*) FROM navbatlar") as cursor:
            jami = (await cursor.fetchone())[0]
        
        # Фаол навбатлар
        async with db.execute("SELECT COUNT(*) FROM navbatlar WHERE status = 'faol'") as cursor:
            faol = (await cursor.fetchone())[0]
    
    text = (
        f"📊 <b>Статистика:</b>\n\n"
        f"📅 Бугун: {bugun} та\n"
        f"✅ Фаол: {faol} та\n"
        f"📈 Жами: {jami} та"
    )
    await message.answer(text, parse_mode="HTML")

@dp.message(F.text == "📋 Барча навбатлар")
async def admin_all_navbatlar(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    today = datetime.now().strftime("%d.%m.%Y")
    
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT id, ism, telefon, sana, soat, xizmat, status FROM navbatlar WHERE sana >= ? ORDER BY sana, soat",
            (today,)
        ) as cursor:
            navbatlar = await cursor.fetchall()
    
    if not navbatlar:
        await message.answer("Навбатлар йўқ.")
        return
    
    # 10 тадан бўлиб юбориш
    for i in range(0, len(navbatlar), 10):
        batch = navbatlar[i:i+10]
        text = f"📋 <b>Навбатлар ({i+1}-{min(i+10, len(navbatlar))}):</b>\n\n"
        
        for navbat in batch:
            navbat_id, ism, telefon, sana, soat, xizmat, status = navbat
            text += f"🆔 {navbat_id} | 👤 {ism}\n"
            text += f"📞 {telefon}\n"
            text += f"📅 {sana} | ⏰ {soat}\n"
            text += f"🛠 {xizmat} | {'✅' if status == 'faol' else '❌'}\n"
            text += "➖➖➖➖➖➖➖\n"
        
        await message.answer(text, parse_mode="HTML")

@dp.message(F.text == "📢 Хабар юбориш")
async def admin_xabar_start(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.set_state(AdminState.xabar)
    await message.answer("📢 Юбориладиган хабарни ёзинг:")

@dp.message(AdminState.xabar)
async def admin_xabar_send(message: Message, state: FSMContext):
    xabar = message.text
    
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT DISTINCT user_id FROM navbatlar") as cursor:
            users = await cursor.fetchall()
    
    yuborildi = 0
    for user in users:
        try:
            await bot.send_message(user[0], f"📢 <b>Sharq Auto Service дан хабар:</b>\n\n{xabar}", parse_mode="HTML")
            yuborildi += 1
        except:
            pass
    
    await message.answer(f"✅ {yuborildi} та фойдаланувчига хабар юборилди.")
    await state.clear()

@dp.message(F.text == "🔙 Асосий меню")
async def back_to_main(message: Message):
    await message.answer("Бош меню:", reply_markup=asosiy_menu(message.from_user.id))

# ============ ИШГА ТУШИРИШ ============

async def main():
    await init_db()
    print("✅ Бот ишга тушди!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
