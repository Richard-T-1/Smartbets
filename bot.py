import logging
import asyncio
import os
import threading
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from http.server import HTTPServer, BaseHTTPRequestHandler

# Vypnutie verbose logov
logging.basicConfig(level=logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Konfigurácia
BOT_TOKEN = os.environ.get('BOT_TOKEN', '7511593743:AAGsPG2FG9_QC-ynD85hHHptE29-P5KiBMQ')
CHANNEL_ID = os.environ.get('CHANNEL_ID', '-1002827606573')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '7626888184'))
PORT = int(os.environ.get('PORT', 8080))
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '')

# Jednoduchý HTTP server pre Render
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Bot is running!')
    
    def log_message(self, format, *args):
        pass  # Vypne HTTP logy

def start_health_server():
    """Spusti HTTP server na porte pre Render"""
    server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
    print(f"Health server spustený na porte {PORT}")
    server.serve_forever()

async def send_ticket(context: ContextTypes.DEFAULT_TYPE, chat_id: str, match_data: dict):
    """Odošle tiket do kanála"""
    try:
        # Cesta k obrázkom v priečinku images
        image_path = f"images/{match_data.get('sport', 'Futbal - sablona')}.png"
        
        # Vytvorenie inline klávesnice s buttonom pre analýzu
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎯 STAV TERAZ!", url=match_data['betting_url'])],
            [InlineKeyboardButton("📊 ANALÝZA", url="https://t.me/smartbets_tikety_bot?start=analysis")]
        ])
        
        # Popis tiketu
        caption = (f"🏆 {match_data['team1']} vs {match_data['team2']}\n"
                  f"⚽ {match_data['tournament']}\n"
                  f"🕘 {match_data['time']}\n\n"
                  f"🎯 {match_data['pick']}\n"
                  f"💰 Kurz: {match_data['odds']}")
        
        # Odoslanie obrázka
        with open(image_path, 'rb') as photo:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=caption,
                reply_markup=keyboard
            )
        
    except FileNotFoundError:
        await context.bot.send_message(chat_id, f"❌ Obrázok nebol nájdený: {image_path}")
    except Exception as e:
        print(f"Chyba pri odosielaní tiketu: {e}")
        await context.bot.send_message(chat_id, "Nastala chyba pri odosielaní tiketu.")

# Príklad dát zápasu
example_match = {
    'sport': 'Futbal - sablona',  # názov obrázka bez .png
    'team1': 'CHELSEA',
    'team2': 'PARIS SAINT-GERMAIN',
    'tournament': 'FIFA Club World Cup',
    'time': '21:00',
    'pick': 'PSG To Win + Over 1.5 Total Goals - 1u',
    'odds': '1.93',
    'betting_url': 'https://your-betting-site.com/bet/12345'
}

# Tu si môžete napísať svoju analýzu (až 4096 znakov)
analysis_text = """📊 **PODROBNÁ ANALÝZA**

🔍 **Forma tímov:**
• Chelsea: 3 výhry z posledných 5 zápasov
• PSG: 4 výhry z posledných 5 zápasov

⚽ **Štatistiky:**
• Chelsea strelila 12 gólov v posledných 5 zápasoch
• PSG má priemer 2.3 góla na zápas doma
• Posledné 3 vzájomné zápasy mali Over 2.5 gólov

🎯 **Dôvod tipu:**
PSG má lepšiu ofenzívu a doma sú veľmi silní. Chelsea má problémy v obrane. Očakávame atraktívny zápas s minimálne 2 gólmi.

📈 **Ďalšie faktory:**
• PSG je bez zranených hráčov
• Chelsea cestuje po náročnom zápase
• Domáce prostredie favorizuje PSG
• Oba tímy potrebujú víťazstvo

💡 **Confidence:** 8/10

🎲 **Alternatívne tipy:**
• PSG Win: 1.75
• BTTS Yes: 1.65
• Over 2.5: 1.80"""

async def auto_start_user(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Automaticky pošle /start užívateľovi"""
    try:
        # Simuluje že užívateľ napísal /start
        welcome_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 ANALÝZA", callback_data="user_analysis")],
            [InlineKeyboardButton("💎 VIP", callback_data="user_vip")]
        ])
        
        await context.bot.send_message(
            chat_id=user_id,
            text='👋 **Vitajte v SMART BETS!**\n\n'
                 '📊 **ANALÝZA** - Podrobné analýzy zápasov\n'
                 '💎 **VIP** - Prémium tipy s vyššími kurzmi\n\n'
                 '🎯 Vyberte si možnosť:',
            reply_markup=welcome_keyboard,
            parse_mode='Markdown'
        )
        return True
    except:
        return False

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Obsluha kliknutí na buttony"""
    query = update.callback_query
    user_name = query.from_user.first_name
    
    if query.data == "user_analysis":
        # Konkrétna analýza aktuálneho tiketu pre bežných užívateľov
        await query.answer("📊 Načítavam analýzu...")
        
        # Tu bude konkrétna analýza tiketu (upravte podľa potreby)
        current_analysis = """📊 **ANALÝZA ZÁPASU: CHELSEA vs PSG**

🔍 **Forma tímov:**
• **Chelsea:** 3 výhry z posledných 5 zápasov (60%)
• **PSG:** 4 výhry z posledných 5 zápasov (80%)

⚽ **Ofenzívne štatistiky:**
• Chelsea: 1.8 gólov/zápas (posledných 5)
• PSG: 2.4 gólov/zápas doma
• PSG strelilo 12 gólov v posledných 5 domácich

🛡️ **Defenzívne štatistiky:**
• Chelsea inkasuje 1.2 gólov/zápas vonku
• PSG má čisté konto v 60% domácich zápasov

📈 **Vzájomné zápasy:**
• Posledné 3 zápasy: 2x Over 1.5, 1x Under
• PSG vyhralo 2 z posledných 3 vzájomných

🎯 **Náš tip: PSG Win + Over 1.5**
**Dôvod:** PSG má lepšiu formu, hrá doma a Chelsea má problémy v obrane na cestách.

💡 **Confidence: 8/10**"""
        
        await query.message.reply_text(current_analysis, parse_mode='Markdown')
        
    elif query.data == "user_vip":
        # VIP promo s odkazom na váš chat
        await query.answer("💎 VIP informácie...")
        
        vip_promo = """💎 **SMART BETS VIP** 

🔥 **Prečo si vybrať VIP?**
• **85% úspešnosť** našich VIP tipov
• **Exkluzívne insider info** pred zápasmi
• **Skoršie tipy** - 1 hodinu pred kanálom  
• **Vyššie kurzy** - priemer 2.8+
• **Osobné poradenstvo** pri stávkach

📊 **Posledný mesiac VIP:**
✅ 23 výherných tipov
❌ 4 prehraté tipy  
💰 **ROI: +34%**

🎯 **VIP obsahuje:**
• Denné analýzy TOP zápasov
• Live tipy počas zápasov
• Bankroll management  
• Riziková upozornenia

💬 **Pripojte sa k VIP skupine:**
👉 📞 [BLIŽŠIE INFO TU](https://t.me/SmartTipy) 

💰 **Špeciálna cena:** ~~€49~~ **€29/mesiac**
🎁 **Prvý týždeň ZADARMO!**"""
        
        await query.message.reply_text(vip_promo, parse_mode='Markdown')

def is_admin(user_id):
    """Kontrola či je užívateľ administrátor"""
    return user_id == ADMIN_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Obsluha príkazu /start"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    # Skontrolujeme či užívateľ prišiel pre analýzu
    if update.message.text and "analysis" in update.message.text:
        # Užívateľ prišiel pre analýzu - pošleme ju
        await update.message.reply_text(
            f"📊 **ANALÝZA ZÁPASU**\n\n{analysis_text}",
            parse_mode='Markdown'
        )
        
        # Po analýze automaticky zobrazíme menu
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 ANALÝZA", callback_data="user_analysis")],
            [InlineKeyboardButton("💎 VIP", callback_data="user_vip")]
        ])
        
        await update.message.reply_text(
            f'🏆 **SMART BETS** - Váš expert na športové stávky\n\n'
            '📊 **ANALÝZA** - Získajte podrobné analýzy zápasov\n'
            '💎 **VIP** - Prémium tipy s vyššími kurzmi\n\n'
            '🎯 Vyberte si možnosť:',
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        return
    
    if is_admin(user_id):
        await update.message.reply_text(
            f'Vitajte v Sports Tips Bot! 🏆\n'
            f'Vaše ID: {user_id}\n\n'
            'Príkazy:\n'
            '/tiket - Odoslať tiket do kanála\n'
            '/help - Zobrazí nápovedu'
        )
    else:
        # Pre bežných užívateľov - welcome správa s buttonmi
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 ANALÝZA", callback_data="user_analysis")],
            [InlineKeyboardButton("💎 VIP", callback_data="user_vip")]
        ])
        
        await update.message.reply_text(
            f'Vitajte {user_name}! 👋\n\n'
            '🏆 **SMART BETS** - Váš expert na športové stávky\n\n'
            '📊 **ANALÝZA** - Získajte podrobné analýzy zápasov\n'
            '💎 **VIP** - Prémium tipy s vyššími kurzmi\n\n'
            '🎯 Vyberte si možnosť:',
            reply_markup=keyboard,
            parse_mode='Markdown'
        )

async def tiket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Obsluha príkazu /tiket"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Nemáte oprávnenie používať tohto bota.")
        return
    
    try:
        # Odošle tiket do kanála
        await send_ticket(context, CHANNEL_ID, example_match)
        
        # Potvrdí odoslanie užívateľovi
        await update.message.reply_text('✅ Tiket bol odoslaný do kanála!')
        
    except Exception as e:
        print(f"Chyba pri odosielaní: {e}")
        await update.message.reply_text(f'❌ Chyba pri odosielaní tiketu: {str(e)}')

async def test_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test prístupu do kanála"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Nemáte oprávnenie používať tohto bota.")
        return
    
    try:
        # Pokus o získanie informácií o kanáli
        chat = await context.bot.get_chat(CHANNEL_ID)
        await update.message.reply_text(
            f"✅ Bot má prístup do kanála!\n"
            f"Názov: {chat.title}\n"
            f"ID: {chat.id}"
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Bot nemá prístup do kanála!\n"
            f"Chyba: {str(e)}\n\n"
            f"Skontrolujte:\n"
            f"1. Bot je pridaný do kanála\n"
            f"2. Bot má práva administrátora\n"
            f"3. Bot má právo posielať správy"
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Obsluha príkazu /help"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Nemáte oprávnenie používať tohto bota.")
        return
    
    await update.message.reply_text(
        'Dostupné príkazy:\n'
        '/start - Spustenie bota\n'
        '/tiket - Odoslanie tiketu do kanála\n'
        '/test - Test prístupu do kanála\n'
        '/help - Nápoveda'
    )

def main():
    """Spustenie bota"""
    # Spustenie health servera na pozadí (pre Render)
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    # Vytvorenie aplikácie
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Registrácia handlerov
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("tiket", tiket))
    application.add_handler(CommandHandler("test", test_channel))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_handler))  # Pre buttony
    
    # Spustenie bota v polling režime
    print("Spúšťam polling...")
    application.run_polling()

if __name__ == '__main__':
    main()
