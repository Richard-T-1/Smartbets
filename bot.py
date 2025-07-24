import logging
import os
import json
import time
import requests
from flask import Flask, request, jsonify

# Vypnutie verbose logov
logging.basicConfig(level=logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Konfigurácia
BOT_TOKEN = os.environ.get('BOT_TOKEN', '7511593743:AAGsPG2FG9_QC-ynD85hHHptE29-P5KiBMQ')
CHANNEL_ID = os.environ.get('CHANNEL_ID', '-1002107685116')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '7626888184'))
PORT = int(os.environ.get('PORT', 10000))
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', 'https://smartbets.onrender.com')

# Flask aplikácia
app = Flask(__name__)

# Globálne premenné
bot_initialized = False
start_time = time.time()

# Príklad dát zápasu
example_match = {
    'sport': 'Evans - Moutet',
    'team1': 'D. Evans',
    'team2': 'C. Moutet',
    'tournament': 'ATP Washington',
    'time': '18:10',
    'pick': 'D. Evans + 4.5 gemu',
    'odds': '1.47',
    'betting_url': 'https://www.tipsport.sk/kurzy/zapas/tenis-evans-daniel-moutet-corentin/7260991/co-sa-tipuje'
}

analysis_text = """📊 *ANALÝZA ZÁPASU: D. Evans - C. Moutet*

Priatelia, dneska tu máme osemfinále turnaja vo Washnigtone. V ňom sa proti sebe stretnú aj Daniel Evans (ATP 144) s Corentinom Moutetom (ATP 59) 🎾

_ Evans, ktorého by som nazval aj "tenisovým šachistom", má výborné defenzíve schopnosti. Hra baseline štýlom (na základnej čiare kurtu) a svoju hru vie pestro variovať - drop shoty, loby, zmeny tempa a uhlov. Mimo basekine štýlu mu nevadí ani vyjsť na sieť a využiť volej. Jeho slabšiu stránkou je sila v uderoch a fyzické limity kvôli veku (35 rokov). Napriek tomu však postupuje v ATP rebríčku 🇬🇧

Corentin Moutet je agresívny baseliner, ktorý sa aj vyznačuje hernou kreativitou. Jeho výhodu spočíva v atletizme a dobrom pohybe po kurte. Ako baseline hráč takisto využíva drop shoty a loby. Jeho hra je niekedy zbrkla a môže mať problémy s mentalitou 🇫🇷

V ich histórii hrali spolu 2 krát - v 2020 a 2021. Oba zápasy vyhrali Moutet, ale vôbec neboli jednostranné. V 2021 vyhral (6:4, 5:7, 6:3) a rok predtým (4:6, 6:3, 7:6, 7:6). Teda oba tieto zápasy boli rozdielom 3 gemov 🙌_

* Verím, že aj tento zápas bude vyrovnaný (s miernou výhodou Mouteta) a prinesie dobrú show aj pre divákov * ✅

Alternatíva: Dá sa aj trocha viac zapisovať s handicapom +3.5 """

vip_text = """💎 *SMART BETS VIP* 

🔥 *Prečo si vybrať VIP?*

💎 1-3 Exkluzívne tipy každý deň
🎯 Denné tipy s kurzom 1.8+
🔔 Prioritná podpora
📊 Profesionálne analýzy
🎁 Bonusové tipy cez víkendy

🚀 *BILANCIA TIKETOV*
• výherné tikety: 19 ✅
• prehraté tikety: 5 ❌

📈 *NAŠA ÚSPEŠNOSŤ*
• Navrátnosť za dané obdobie: 19.19% 
• Zisk za dané obdobie: +11.82u

(1u=250€)

📞 [BLIŽŠIE INFO TU](https://t.me/SmartTipy)"""

def is_admin(user_id):
    """Kontrola admin práv"""
    return user_id == ADMIN_ID

def send_telegram_message(chat_id, text, reply_markup=None, parse_mode=None):
    """Pošle správu cez Telegram API"""
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
        resp = requests.post(telegram_url, json=payload, timeout=10)
        print(f"📤 Message sent: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"❌ Telegram API error: {resp.text}")
            
        return resp.status_code == 200
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False

def send_telegram_photo(chat_id, photo_path, caption, reply_markup=None):
    """Pošle obrázok cez Telegram API"""
    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    
    try:
        with open(photo_path, 'rb') as photo:
            files = {'photo': photo}
            data = {
                'chat_id': chat_id,
                'caption': caption
            }
            
            if reply_markup:
                data['reply_markup'] = json.dumps(reply_markup)
            
            resp = requests.post(telegram_url, files=files, data=data, timeout=15)
            print(f"📤 Photo sent: {resp.status_code}")
            
            if resp.status_code != 200:
                print(f"❌ Photo send error: {resp.text}")
                
            return resp.status_code == 200
            
    except FileNotFoundError:
        print(f"❌ Photo not found: {photo_path}")
        return False
    except Exception as e:
        print(f"❌ Error sending photo: {e}")
        return False

def answer_callback_query(callback_query_id, text=""):
    """Odpovie na callback query"""
    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
    payload = {
        'callback_query_id': callback_query_id,
        'text': text,
        'show_alert': False
    }
    
    try:
        resp = requests.post(telegram_url, json=payload, timeout=10)
        print(f"📤 Callback answered: {resp.status_code}")
        if resp.status_code != 200:
            print(f"❌ Callback answer error: {resp.text}")
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
            analysis_text,
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
    success = send_telegram_message(chat_id, analysis_text, parse_mode='Markdown')
    if not success:
        # Fallback bez markdown
        send_telegram_message(chat_id, analysis_text.replace('*', ''))

def send_vip_info(chat_id):
    """Pošle VIP informácie"""
    success = send_telegram_message(chat_id, vip_text, parse_mode='Markdown')
    if not success:
        # Fallback bez markdown
        send_telegram_message(chat_id, vip_text.replace('*', ''))

def handle_tiket_command(chat_id):
    """Spracuje /tiket príkaz"""
    try:
        send_ticket_to_channel()
        send_telegram_message(chat_id, "✅ Tiket bol odoslaný do kanála!")
    except Exception as e:
        print(f"❌ Error sending ticket: {e}")
        send_telegram_message(chat_id, f"❌ Chyba pri odosielaní tiketu: {str(e)}")

def send_ticket_to_channel():
    """Odošle tiket do kanála"""
    match_data = example_match
    
    # Caption pre tiket
    caption = (f"🏆 {match_data['team1']} vs {match_data['team2']}\n"
              f"🎾 {match_data['tournament']}\n"
              f"🕘 {match_data['time']}\n\n"
              f"🎯 {match_data['pick']}\n"
              f"💰 Kurz: {match_data['odds']}")
    
    # Inline keyboard
    keyboard = {
        "inline_keyboard": [
            [{"text": "🎯 STAV TERAZ!", "url": match_data['betting_url']}],
            [{"text": "📊 ANALÝZA", "url": "https://t.me/smartbets_tikety_bot?start=analysis"}]
        ]
    }
    
    # Skús poslať obrázok
    image_path = f"images/{match_data.get('sport', 'Evans - Moutet')}.png"
    
    if send_telegram_photo(CHANNEL_ID, image_path, caption, keyboard):
        print("✅ Ticket with image sent to channel")
    else:
        # Fallback - pošli len text
        text_message = f"{caption}\n\n🎯 [STAV TERAZ!]({match_data['betting_url']})"
        send_telegram_message(CHANNEL_ID, text_message, parse_mode='Markdown')
        print("✅ Ticket as text sent to channel")

def handle_status_command(chat_id):
    """Spracuje /status príkaz"""
    uptime = time.time() - start_time
    status_text = f"""🤖 **Bot Status**
🔄 Mode: Webhook
🌐 Port: {PORT}
⏰ Uptime: {round(uptime/3600, 1)} hodín
🔗 Webhook: {WEBHOOK_URL}/webhook
✅ Status: Running
🤖 Bot: {'✅ Initialized' if bot_initialized else '❌ Not initialized'}"""
    
    send_telegram_message(chat_id, status_text, parse_mode='Markdown')

def handle_help_command(chat_id):
    """Spracuje /help príkaz"""
    help_text = """Dostupné príkazy:
/start - Spustenie bota
/tiket - Odoslanie tiketu do kanála
/status - Stav bota
/help - Nápoveda"""
    
    send_telegram_message(chat_id, help_text)

def setup_webhook():
    """Nastavenie webhook"""
    global bot_initialized
    
    try:
        # Zruš starý webhook
        delete_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
        requests.post(delete_url, json={'drop_pending_updates': True}, timeout=10)
        print("🗑️ Old webhook deleted")
        
        time.sleep(1)
        
        # Nastav nový webhook
        webhook_url = f"{WEBHOOK_URL}/webhook"
        set_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
        payload = {
            'url': webhook_url,
            'drop_pending_updates': True,
            'max_connections': 40
        }
        
        resp = requests.post(set_url, json=payload, timeout=10)
        print(f"✅ Webhook setup: {resp.status_code}")
        
        if resp.status_code == 200:
            bot_initialized = True
            print(f"✅ Webhook set: {webhook_url}")
            
            # Overenie
            info_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
            info_resp = requests.get(info_url, timeout=10)
            if info_resp.status_code == 200:
                info = info_resp.json().get('result', {})
                print(f"🔍 Webhook verification:")
                print(f"   URL: {info.get('url', 'N/A')}")
                print(f"   Pending: {info.get('pending_update_count', 0)}")
                if info.get('last_error_message'):
                    print(f"   ⚠️ Last error: {info.get('last_error_message')}")
                    
            return True
        else:
            print(f"❌ Webhook setup failed: {resp.text}")
            return False
            
    except Exception as e:
        print(f"❌ Webhook setup error: {e}")
        return False

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
        'bot_initialized': bot_initialized,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/health')
def health():
    """Health endpoint pre monitoring"""
    return jsonify({
        'status': 'healthy',
        'bot_active': bot_initialized,
        'uptime_hours': round((time.time() - start_time) / 3600, 2)
    })

@app.route('/debug')
def debug_info():
    """Debug informácie"""
    return jsonify({
        'bot_token': BOT_TOKEN[:10] + "..." if BOT_TOKEN else "NOT SET",
        'webhook_url': WEBHOOK_URL,
        'bot_initialized': bot_initialized,
        'webhook_endpoint': f"{WEBHOOK_URL}/webhook"
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint pre Telegram"""
    if not bot_initialized:
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
            
            print(f"📝 Message from {user_name} (ID: {user_id}): {text}")
            
            # Handle commands
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
            user_id = callback['from']['id']
            data = callback['data']
            callback_query_id = callback['id']
            
            print(f"🔘 Button clicked: {data} by {user_name} (ID: {user_id})")
            
            # Odpoveď na callback query
            answer_callback_query(callback_query_id, "📊 Načítavam...")
            
            # Spracovanie akcií
            if data == "user_analysis":
                print("📊 Sending analysis...")
                send_analysis(chat_id)
            elif data == "user_vip":
                print("💎 Sending VIP info...")
                send_vip_info(chat_id)
            else:
                print(f"❓ Unknown callback data: {data}")
        
        return jsonify({'status': 'ok'})
        
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def main():
    """Spustenie aplikácie"""
    print("🚀 Starting Telegram Bot with Webhook...")
    
    # Setup webhook
    if setup_webhook():
        print("✅ Bot ready for requests")
    else:
        print("❌ Failed to setup webhook, but starting server anyway...")
    
    print(f"✅ Starting Flask server on port {PORT}")
    print(f"✅ Webhook URL: {WEBHOOK_URL}/webhook")
    print(f"✅ Health check: {WEBHOOK_URL}/")
    
    # Spustenie Flask servera
    app.run(host='0.0.0.0', port=PORT, debug=False)

if __name__ == '__main__':
    main()
