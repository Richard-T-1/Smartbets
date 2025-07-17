import logging
import os
import threading
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from http.server import HTTPServer, BaseHTTPRequestHandler
import signal
import sys

# Vypnutie verbose logov
logging.basicConfig(level=logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Konfigurácia
BOT_TOKEN = os.environ.get('BOT_TOKEN', '7511593743:AAGsPG2FG9_QC-ynD85hHHptE29-P5KiBMQ')
CHANNEL_ID = os.environ.get('CHANNEL_ID', '-1002827606573')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '7626888184'))
PORT = int(os.environ.get('PORT', 8080))

# Globálne premenné
health_server = None
bot_running = False

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "status": "ok",
            "bot_running": bot_running,
            "port": PORT,
            "time": time.strftime('%Y-%m-%d %H:%M:%S'),
            "message": "Telegram bot is running"
        }
        
        self.wfile.write(str(response).encode())
    
    def log_message(self, format, *args):
        pass  # Vypne HTTP logy

def start_health_server():
    """Spusti HTTP server na porte pre Render"""
    global health_server
    try:
        health_server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
        print(f"✅ Health server started on port {PORT}")
        health_server.serve_forever()
    except Exception as e:
        print(f"❌ Health server error: {e}")

def signal_handler(signum, frame):
    """Graceful shutdown"""
    global bot_running, health_server
    print(f"\n🛑 Received signal {signum}, shutting down...")
    bot_running = False
    if health_server:
        health_server.shutdown()
    sys.exit(0)

# Registrácia signal handlera
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

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
        print(f"Error sending ticket: {e}")
        await context.bot.send_message(chat_id, "Nastala chyba pri odosielaní tiketu.")

# Príklad dát zápasu
example_match = {
    'sport': 'Futbal - sablona',
    'team1': 'CHELSEA',
    'team2': 'PARIS SAINT-GERMAIN',
    'tournament': 'FIFA Club World Cup',
    'time': '21:00',
    'pick': 'PSG To Win + Over 1.5 Total Goals - 1u',
    'odds': '1.93',
    'betting_url': 'https://your-betting-site.com/bet/12345'
}

# Analýza
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

💡 **Confidence:** 8/10"""

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Obsluha kliknutí na buttony"""
    query = update.callback_query
    user_name = query.from_user.first_name
    
    if query.data == "user_analysis":
        await query.answer("📊 Načítavam analýzu...")
        
        current_analysis = f"""📊 *ANALÝZA ZÁPASU: CHELSEA vs PSG*

🔍 *Forma tímov:*
• Chelsea: 3 výhry z posledných 5 zápasov (60%)
• PSG: 4 výhry z posledných 5 zápasov (80%)

⚽ *Ofenzívne štatistiky:*
• Chelsea: 1.8 gólov/zápas (posledných 5)
• PSG: 2.4 gólov/zápas doma
• PSG strelilo 12 gólov v posledných 5 domácich

🛡️ *Defenzívne štatistiky:*
• Chelsea inkasuje 1.2 gólov/zápas vonku
• PSG má čisté konto v 60% domácich zápasov

📈 *Vzájomné zápasy:*
• Posledné 3 zápasy: 2x Over 1.5, 1x Under
• PSG vyhralo 2 z posledných 3 vzájomných

🎯 *Náš tip: PSG Win + Over 1.5*

📈 *Ďalšie faktory:*
• PSG je bez zranených hráčov
• Chelsea cestuje po náročnom zápase
• Domáce prostredie favorizuje PSG
• Oba tímy potrebujú víťazstvo

💡 Confidence: 8/10 """
        
        try:
            await query.message.reply_text(current_analysis, parse_mode='Markdown')
        except Exception as e:
            print(f"Error sending analysis: {e}")
            # Fallback bez markdown
            await query.message.reply_text(current_analysis)
        
    elif query.data == "user_vip":
        await query.answer("💎 VIP informácie...")
        
        vip_promo = """💎 *SMART BETS VIP* 

🔥 *Prečo si vybrať VIP?*

💎 1-3 Exkluzívne tipy každý deň
🎯 Denné tipy s kurzom 1.8+
🔔 Prioritná podpora
📊 Profesionálne analýzy
🎁 Bonusové tipy cez víkendy


🚀 *BILANCIA TIKETOV*
• výherné tikety: 11 ✅
• prehraté tikety: 5 ❌


📈 *NAŠA ÚSPEŠNOSŤ*
• Navrátnosť za dané obdobie: 9.45% 
• Zisk za dané obdobie: +3.44u

(1u=250€)

📞 [BLIŽŠIE INFO TU](https://t.me/SmartTipy) """
        
        await query.message.reply_text(vip_promo, parse_mode='Markdown')

def is_admin(user_id):
    """Kontrola či je užívateľ administrátor"""
    return user_id == ADMIN_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Obsluha príkazu /start"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    if update.message.text and "analysis" in update.message.text:
        await update.message.reply_text(
            f"📊 **ANALÝZA ZÁPASU**\n\n{analysis_text}",
            parse_mode='Markdown'
        )
        
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
            '/status - Stav bota\n'
            '/help - Zobrazí nápovedu'
        )
    else:
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
        await send_ticket(context, CHANNEL_ID, example_match)
        await update.message.reply_text('✅ Tiket bol odoslaný do kanála!')
    except Exception as e:
        print(f"Error sending ticket: {e}")
        await update.message.reply_text(f'❌ Chyba pri odosielaní tiketu: {str(e)}')

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Status bota"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Nemáte oprávnenie používať tohto bota.")
        return
    
    await update.message.reply_text(
        f"🤖 **Bot Status**\n"
        f"🔄 Running: {'✅ Yes' if bot_running else '❌ No'}\n"
        f"🌐 Port: {PORT}\n"
        f"⏰ Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"🏠 Health server: {'✅ Active' if health_server else '❌ Inactive'}",
        parse_mode='Markdown'
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
        '/status - Stav bota\n'
        '/help - Nápoveda'
    )

def main():
    """Spustenie bota"""
    global bot_running
    
    print("🚀 Starting Telegram bot...")
    
    # Spustenie health servera na pozadí
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    # Krátke čakanie na spustenie servera
    time.sleep(1)
    
    try:
        # Vytvorenie aplikácie
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Registrácia handlerov
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("tiket", tiket))
        application.add_handler(CommandHandler("status", status))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CallbackQueryHandler(button_handler))
        
        # Nastavenie stavu
        bot_running = True
        
        print("✅ Bot started in polling mode")
        print(f"✅ Health server running on http://0.0.0.0:{PORT}")
        print("✅ All systems ready")
        
        # Spustenie pollingu (toto má vlastný event loop)
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        bot_running = False
        print("🔄 Cleaning up...")
        if health_server:
            try:
                health_server.shutdown()
                print("✅ Health server stopped")
            except:
                pass

if __name__ == '__main__':
    main()
