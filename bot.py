import asyncio
import aiosqlite
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import F

TELEGRAM_TOKEN = "8738922116:AAF2vzIuZElJoXe3UU7D5z7blS1SMBSs48g"
DATAMART_API_KEY = "a111b61fa2a193dd33a8aa00169251db7379534662c3b06d6e67f9d6b4c93dbe"
PAYSTACK_SECRET_KEY = "sk_test_469bdcc01314bcabc90888fcf63260644e355d4a"   

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

user_states = {}

def detect_network(phone: str):
    p = phone.strip().replace("+233", "0").replace(" ", "")
    if p.startswith(("024", "054", "055", "056", "057", "059")): return "MTN"
    elif p.startswith(("020", "050")): return "Telecel"
    elif p.startswith(("027", "057", "026", "056")): return "AirtelTigo"
    return None

MTN_PRICES = "✅ <b>MTN Price List</b>\n\n1GB = ₵4.69\n2GB = ₵9.83\n3GB = ₵13.99\n4GB = ₵19.88\n5GB = ₵24.91\n6GB = ₵27.79\n8GB = ₵36.86\n10GB = ₵44.96\n15GB = ₵64.99\n20GB = ₵84.89\n25GB = ₵110.58\n30GB = ₵135.16\n40GB = ₵176.49\n50GB = ₵223.40"
TELECEL_PRICES = "✅ <b>Telecel Price List</b>\n\n10GB = ₵39.19\n12GB = ₵45.89\n15GB = ₵58.19\n20GB = ₵78.89\n25GB = ₵94.19\n30GB = ₵119.59\n35GB = ₵133.59\n40GB = ₵155.79\n45GB = ₵165.78\n50GB = ₵182.67\n100GB = ₵400"
AIRTELTIGO_PRICES = "✅ <b>AirtelTigo Price List</b>\n\n1GB = ₵4.41\n2GB = ₵9.33\n3GB = ₵14.80\n4GB = ₵18.43\n5GB = ₵21.89\n6GB = ₵26.25\n8GB = ₵34.07\n10GB = ₵43.29\n12GB = ₵50.82\n25GB = ₵106.11\n30GB = ₵128.46\n40GB = ₵168.67\n50GB = ₵212.23"

async def init_db():
    async with aiosqlite.connect("datavibes.db") as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS orders (...)""")
        await db.commit()

@dp.message(Command("start"))
async def start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="📦 Buy Data Bundle")],
                  [types.KeyboardButton(text="🔑 AFA Registration")],
                  [types.KeyboardButton(text="🌍 Foreign Numbers")],
                  [types.KeyboardButton(text="🛒 Other Services")],
                  [types.KeyboardButton(text="💼 Become Reseller")],
                  [types.KeyboardButton(text="📦 Track My Order")]],
        resize_keyboard=True
    )
    await message.answer(
        "🚀 <b>Welcome to Data Vibes GH Bot!</b>\n\n"
        "Buy data directly from our Mini App here 👇\n"
        "https://www.cheapdata.shop/shop/data-vide-2026-1767031990414\n\n"
        "Or choose below 👇",
        parse_mode="HTML",
        reply_markup=keyboard
    )

# Auto network detection
@dp.message(F.text.startswith(("0", "+233")))
async def auto_detect_phone(message: types.Message):
    network = detect_network(message.text)
    if network:
        user_states[message.from_user.id] = {"network": network, "phone": message.text}
        if network == "MTN":
            await message.answer(MTN_PRICES, parse_mode="HTML")
        elif network == "Telecel":
            await message.answer(TELECEL_PRICES, parse_mode="HTML")
        else:
            await message.answer(AIRTELTIGO_PRICES, parse_mode="HTML")
        await message.answer(f"✅ Detected **{network}** number **{message.text}**\n\nType GB amount (e.g. 5, 10, 2)")
        return
    await fallback(message)

# Guided data bundle
@dp.message(F.text.isdigit() | F.text.contains("GB"))
async def process_gb(message: types.Message):
    user_id = message.from_user.id
    state = user_states.get(user_id)
    if not state or "network" not in state:
        return await fallback(message)

    text = message.text.upper().replace("GB", "").strip()
    try:
        gb = int(text)
    except:
        return await message.answer("❌ Enter a number like 5 or 10")

    valid_gb = {"MTN": [1,2,3,4,5,6,8,10,15,20,25,30,40,50],
                "Telecel": [10,12,15,20,25,30,35,40,45,50,100],
                "AirtelTigo": [1,2,3,4,5,6,8,10,12,25,30,40,50]}
    if gb not in valid_gb.get(state["network"], []):
        await message.answer(f"❌ {gb}GB is not available for {state['network']}. Choose from the price list.")
        return

    state["capacity"] = str(gb)
    user_states[user_id] = state

    await message.answer(
        f"✅ **Order Summary**\n"
        f"Network: {state['network']}\n"
        f"Phone: {state['phone']}\n"
        f"Data: {gb}GB\n\n"
        f"Pay securely with MTN MoMo via Paystack below:"
    )

    link = await create_paystack_link(message.from_user.id, f"{state['network']} {gb}GB", 0)
    if link:
        await message.answer(f"Pay here: {link}")
    else:
        await message.answer("❌ Failed to generate link.")

# Paystack link generator
async def create_paystack_link(telegram_id: int, service: str, amount_ghs: float):
    payload = {
        "email": f"user{telegram_id}@datavibesgh.com",
        "amount": int(amount_ghs * 100) if amount_ghs > 0 else 1000,
        "currency": "GHS",
        "metadata": {"telegram_id": telegram_id, "service": service}
    }
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}", "Content-Type": "application/json"}
    try:
        r = requests.post("https://api.paystack.co/transaction/initialize", json=payload, headers=headers, timeout=15)
        data = r.json()
        return data["data"]["authorization_url"] if data.get("status") else None
    except:
        return None

# Clear responses for all services
@dp.message(F.text == "🔑 AFA Registration")
async def afa_registration(message: types.Message):
    await message.answer(
        "🔑 **AFA Registration**\n\n"
        "Pay **₵25** securely with MTN MoMo via Paystack.\n"
        "Registration takes **24 hours** to activate.\n\n"
        "After payment reply with **/paid** + Transaction ID"
    )

@dp.message(F.text == "🌍 Foreign Numbers")
async def foreign_numbers(message: types.Message):
    await message.answer(
        "🌍 **Foreign Numbers + Instant OTP**\n\n"
        "Price: **₵50** (with Refund Policy)\n\n"
        "Pay securely with MTN MoMo via Paystack.\n"
        "After payment reply with **/paid** + Transaction ID"
    )

@dp.message(F.text == "🛒 Other Services")
async def other_services(message: types.Message):
    await message.answer(
        "🛒 **Other Services**\n\n"
        "• WAEC Results Checker – ₵25\n"
        "• Smoke / Fugu / Batakali – ₵435 (Ghanaian) / $120 (Foreign)\n"
        "• Crypto P2P (USDT, TON, Telegram Stars, OKX, Binance)\n"
        "• Fast MoMo (Crypto → Cedis at current rate)\n"
        "• French Online Lessons\n"
        "• Affiliate Marketing\n"
        "• Original Italian Leather Shoes\n"
        "• Gold Coast Roasted Coffee\n\n"
        "Reply with the service name or choose from menu."
    )

@dp.message(F.text == "💼 Become Reseller")
async def become_reseller(message: types.Message):
    await message.answer(
        "💼 **Become a Reseller**\n\n"
        "Reseller account going for **¢55** from next month.\n\n"
        "Join here: https://www.cheapdata.shop/shop/data-vide-2026-1767031990414/join\n\n"
        "All resellers must join our WhatsApp Channel."
    )

@dp.message(F.text == "📦 Track My Order")
async def track_order(message: types.Message):
    await message.answer(
        "📦 **Track My Order**\n\n"
        "For data bundles: Use the orderReference from your receipt or check DataMart dashboard.\n"
        "For AFA: Registration takes up to **24 hours** after payment.\n\n"
        "Reply with your phone number or order reference to check status."
    )

@dp.message()
async def fallback(message: types.Message):
    await message.answer("Type /start to see the main menu 👇")

async def main():
    await init_db()
    print("🚀 SUPERB Data Vibes GH Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())