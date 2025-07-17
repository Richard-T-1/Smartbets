import logging
import os
import json
import asyncio
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
import time

# Vypnutie verbose logov
logging.basicConfig(level=logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Konfigurácia
BOT_TOKEN = os.environ.get('BOT_TOKEN', '7511593743:AAGsPG2FG9_QC-ynD85hHHptE29-P5KiBMQ')
CHANNEL_ID = os.environ.get('CHANNEL_ID', '-1002827606573')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '7626888184'))
PORT = int(os.environ.get('PORT', 10000))
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', 'https://smartbets.onrender.com')

# Flask aplikácia
app = Flask(__name__)

# Globálne premenné
bot_app = None
start_time = time.time()
webhook_info_cache = {}

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

async def send_ticket(context: ContextTypes.DEFAULT_TYPE, chat_id: str, match_data: dict):
    """Odošle tiket do kanála"""
    try:
        image_path = f"images/{match_data.get('sport', 'Futbal - sablona')}.png"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎯 STAV TERAZ!", url=match_data['betting_url'])],
            [InlineKeyboardButton("📊 ANALÝZA", url=f"https://t.me/smartbets_tikety_bot?start=analysis")]
        ])
        
        caption = (f"🏆 {match_data['team1']} vs {match_data['team2']}\n"
                  f"⚽ {match_data['tournament']}\n"
                  f"🕘 {match_data['time']}\n\n"
                  f"🎯 {match_data['pick']}\n"
                  f"💰 Kurz: {match_data['odds']}")
        
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

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Obsluha kliknutí na buttony"""
    query = update.callback_query
    user_name = query.from_user.first_name
    
    if query.data == "user_analysis":
        await query.answer("📊 Načítavam analýzu...")
        
        # Vaše upravené texty - zachované presne tak, ako sú
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
            await query.message.reply_text(current_analysis)
            
    elif query.data == "user_vip":
        await query.answer("💎 VIP informácie...")
        
        # Vaše upravené VIP texty - zachované presne tak, ako sú
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
        
        try:
            await query.message.reply_text(vip_promo, parse_mode='Markdown')
        except Exception as e:
            print(f"Error sending VIP info: {e}")
            await query.message.reply_text(vip_promo)

def is_admin(user_id):
    return user_id == ADMIN_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Obsluha príkazu /start"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    print(f"Start command from user {user_id}: {update.message.text}")
    
    if update.message.text and "analysis" in update.message.text:
        try:
            await update.message.reply_text(
                f"📊 **ANALÝZA ZÁPASU**\n\n{analysis_text}",
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"Error sending analysis: {e}")
            await update.message.reply_text(f"📊 ANALÝZA ZÁPASU\n\n{analysis_text}")
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 ANALÝZA", callback_data="user_analysis")],
            [InlineKeyboardButton("💎 VIP", callback_data="user_vip")]
        ])
        
        try:
            await update.message.reply_text(
                f'🏆 **SMART BETS** - Váš expert na športové stávky\n\n'
                '📊 **ANALÝZA** - Získajte podrobné analýzy zápasov\n'
                '💎 **VIP** - Prémium tipy s vyššími kurzmi\n\n'
                '🎯 Vyberte si možnosť:',
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"Error sending menu: {e}")
            await update.message.reply_text(
                'SMART BETS - Váš expert na športové stávky\n\n'
                'ANALÝZA - Získajte podrobné analýzy zápasov\n'
                'VIP - Prémium tipy s vyššími kurzmi\n\n'
                'Vyberte si možnosť:',
                reply_markup=keyboard
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
    
    uptime = time.time() - start_time
    await update.message.reply_text(
        f"🤖 **Bot Status**\n"
        f"🔄 Mode: Webhook\n"
        f"🌐 Port: {PORT}\n"
        f"⏰ Uptime: {round(uptime/3600, 1)} hodín\n"
        f"🔗 Webhook: {WEBHOOK_URL}/webhook\n"
        f"✅ Status: Running",
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

# Flask routes
@app.route('/')
def health_check():
    """Health check endpoint"""
    uptime = time.time() - start_time
    return jsonify({
        'status': 'ok',
        'service': 'telegram-bot',
        'mode': 'webhook',
        'uptime_hours': round(uptime / 3600, 2),
        'port': PORT,
        'webhook_url': f"{WEBHOOK_URL}/webhook",
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/debug')
def debug_info():
    """Debug informácie"""
    return jsonify({
        'bot_token': BOT_TOKEN[:10] + "..." if BOT_TOKEN else "NOT SET",
        'webhook_url': WEBHOOK_URL,
        'bot_initialized': bot_app is not None,
        'webhook_endpoint': f"{WEBHOOK_URL}/webhook"
    })

@app.route('/test_webhook', methods=['POST'])
def test_webhook():
    """Test webhook endpoint"""
    data = request.get_json()
    print(f"🧪 Test webhook received: {data}")
    return jsonify({'status': 'test_ok', 'received': data})
def webhook_info():
    """Informácie o webhook od Telegram"""
    if not bot_app:
        return jsonify({'error': 'Bot not initialized'})
    
    # Vrátime cache ak je k dispozícii
    if webhook_info_cache:
        return jsonify(webhook_info_cache)
    
    return jsonify({
        'error': 'Webhook info not available yet',
        'suggestion': 'Check logs for webhook setup details'
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint pre Telegram"""
    global bot_app
    
    if not bot_app:
        print("❌ Bot not initialized")
        return jsonify({'error': 'Bot not initialized'}), 500
    
    try:
        update_data = request.get_json()
        
        if not update_data:
            print("❌ No JSON data received")
            return jsonify({'error': 'No data received'}), 400
        
        print(f"📨 Received update: {update_data.get('update_id', 'unknown')}")
        
        # Spracovanie správ
        if 'message' in update_data:
            message = update_data['message']
            chat_id = message['chat']['id']
            text = message.get('text', '')
            user_name = message['from'].get('first_name', 'Unknown')
            user_id = message['from']['id']
            
            print(f"📝 Message from {user_name} (ID: {chat_id}): {text}")
            
            # Handle /start command
            if text.startswith('/start'):
                handle_start_command(chat_id, user_id, user_name, text)
            elif text == '/tiket' and is_admin(user_id):
                handle_tiket_command(chat_id)
            elif text == '/status' and is_admin(user_id):
                handle_status_command(chat_id)
            elif text == '/help' and is_admin(user_id):
                handle_help_command(chat_id)
                
        # Spracovanie callback queries (buttony)
        elif 'callback_query' in update_data:
            callback = update_data['callback_query']
            chat_id = callback['message']['chat']['id']
            user_name = callback['from'].get('first_name', 'Unknown')
            data = callback['data']
            callback_query_id = callback['id']
            
            print(f"🔘 Button clicked: {data} by {user_name}")
            
            # Answer callback query
            answer_callback_query(callback_query_id)
            
            if data == "user_analysis":
                send_analysis(chat_id)
            elif data == "user_vip":
                send_vip_info(chat_id)
        
        return jsonify({'status': 'ok'})
        
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def send_telegram_message(chat_id, text, reply_markup=None, parse_mode=None):
    """Pošle správu cez Telegram API"""
    import requests
    
    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text
    }
    
    if reply_markup:
        payload['reply_markup'] = reply_markup
    if parse_mode:
        payload['parse_mode'] = parse_mode
    
    try:
        resp = requests.post(telegram_url, json=payload)
        print(f"📤 Message sent: {resp.status_code}")
        return resp.status_code == 200
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False

def answer_callback_query(callback_query_id, text=""):
    """Odpovie na callback query"""
    import requests
    
    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
    payload = {
        'callback_query_id': callback_query_id,
        'text': text
    }
    
    try:
        resp = requests.post(telegram_url, json=payload)
        return resp.status_code == 200
    except Exception as e:
        print(f"❌ Error answering callback: {e}")
        return False

def handle_start_command(chat_id, user_id, user_name, text):
    """Spracuje /start príkaz"""
    
    if "analysis" in text:
        # Pošle analýzu
        send_telegram_message(
            chat_id, 
            f"📊 **ANALÝZA ZÁPASU**\n\n{analysis_text}",
            parse_mode='Markdown'
        )
        
        # Potom menu
        keyboard = {
            "inline_keyboard": [
                [{"text": "📊 ANALÝZA", "callback_data": "user_analysis"}],
                [{"text": "💎 VIP", "callback_data": "user_vip"}]
            ]
        }
        
        send_telegram_message(
            chat_id,
            '🏆 **SMART BETS** - Váš expert na športové stávky\n\n'
            '📊 **ANALÝZA** - Získajte podrobné analýzy zápasov\n'
            '💎 **VIP** - Prémium tipy s vyššími kurzmi\n\n'
            '🎯 Vyberte si možnosť:',
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    elif is_admin(user_id):
        send_telegram_message(
            chat_id,
            f'Vitajte v Sports Tips Bot! 🏆\n'
            f'Vaše ID: {user_id}\n\n'
            'Príkazy:\n'
            '/tiket - Odoslať tiket do kanála\n'
            '/status - Stav bota\n'
            '/help - Zobrazí nápovedu'
        )
    else:
        keyboard = {
            "inline_keyboard": [
                [{"text": "📊 ANALÝZA", "callback_data": "user_analysis"}],
                [{"text": "💎 VIP", "callback_data": "user_vip"}]
            ]
        }
        
        send_telegram_message(
            chat_id,
            f'Vitajte {user_name}! 👋\n\n'
            '🏆 **SMART BETS** - Váš expert na športové stávky\n\n'
            '📊 **ANALÝZA** - Získajte podrobné analýzy zápasov\n'
            '💎 **VIP** - Prémium tipy s vyššími kurzmi\n\n'
            '🎯 Vyberte si možnosť:',
            reply_markup=keyboard,
            parse_mode='Markdown'
        )

def send_analysis(chat_id):
    """Pošle analýzu"""
    analysis = """📊 *ANALÝZA ZÁPASU: CHELSEA vs PSG*

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
    
    send_telegram_message(chat_id, analysis, parse_mode='Markdown')

def send_vip_info(chat_id):
    """Pošle VIP informácie"""
    vip_text = """💎 *SMART BETS VIP* 

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
    
    send_telegram_message(chat_id, vip_text, parse_mode='Markdown')

def handle_tiket_command(chat_id):
    """Spracuje /tiket príkaz"""
    # Tu by ste implementovali odoslanie tiketu do kanála
    send_telegram_message(chat_id, "✅ Tiket bol odoslaný do kanála!")

def handle_status_command(chat_id):
    """Spracuje /status príkaz"""
    uptime = time.time() - start_time
    status_text = f"""🤖 **Bot Status**
🔄 Mode: Webhook
🌐 Port: {PORT}
⏰ Uptime: {round(uptime/3600, 1)} hodín
🔗 Webhook: {WEBHOOK_URL}/webhook
✅ Status: Running"""
    
    send_telegram_message(chat_id, status_text, parse_mode='Markdown')

def handle_help_command(chat_id):
    """Spracuje /help príkaz"""
    help_text = """Dostupné príkazy:
/start - Spustenie bota
/tiket - Odoslanie tiketu do kanála
/status - Stav bota
/help - Nápoveda"""
    
    send_telegram_message(chat_id, help_text)

async def setup_bot():
    """Nastavenie bota"""
    global bot_app, webhook_info_cache
    
    try:
        # Vytvorenie aplikácie
        bot_app = Application.builder().token(BOT_TOKEN).build()
        
        # Registrácia handlerov
        bot_app.add_handler(CommandHandler("start", start))
        bot_app.add_handler(CommandHandler("tiket", tiket))
        bot_app.add_handler(CommandHandler("status", status))
        bot_app.add_handler(CommandHandler("help", help_command))
        bot_app.add_handler(CallbackQueryHandler(button_handler))
        
        # Najprv zrušíme existujúci webhook
        await bot_app.bot.delete_webhook(drop_pending_updates=True)
        print("🗑️ Old webhook deleted")
        
        # Krátke čakanie
        import asyncio
        await asyncio.sleep(1)
        
        # Nastavenie nového webhooku
        webhook_url = f"{WEBHOOK_URL}/webhook"
        result = await bot_app.bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True,
            max_connections=40
        )
        
        print(f"✅ Bot initialized")
        print(f"✅ Webhook set: {webhook_url}")
        print(f"✅ Webhook result: {result}")
        
        # Overenie webhook a uloženie do cache
        try:
            webhook_info = await bot_app.bot.get_webhook_info()
            webhook_info_cache = {
                'webhook_url': webhook_info.url,
                'has_custom_certificate': webhook_info.has_custom_certificate,
                'pending_update_count': webhook_info.pending_update_count,
                'last_error_date': str(webhook_info.last_error_date) if webhook_info.last_error_date else None,
                'last_error_message': webhook_info.last_error_message,
                'max_connections': webhook_info.max_connections,
                'status': 'success'
            }
            
            print(f"🔍 Webhook verification:")
            print(f"   URL: {webhook_info.url}")
            print(f"   Pending updates: {webhook_info.pending_update_count}")
            if webhook_info.last_error_message:
                print(f"   ⚠️ Last error: {webhook_info.last_error_message}")
                
        except Exception as e:
            print(f"⚠️ Could not verify webhook: {e}")
            webhook_info_cache = {'error': str(e), 'status': 'verification_failed'}
        
        return True
        
    except Exception as e:
        print(f"❌ Bot setup error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Spustenie aplikácie"""
    print("🚀 Starting Telegram Bot with Webhook...")
    
    # Nastavenie event loopu pre async operácie
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Spustenie bot setup
    success = loop.run_until_complete(setup_bot())
    
    if not success:
        print("❌ Failed to setup bot")
        return
    
    print(f"✅ Starting Flask server on port {PORT}")
    print(f"✅ Webhook URL: {WEBHOOK_URL}/webhook")
    print("✅ Bot ready for requests")
    
    # Spustenie Flask servera
    app.run(host='0.0.0.0', port=PORT)

if __name__ == '__main__':
    main()
