import logging
import os
import json
import time
import requests
from datetime import datetime
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
STATS_FILE = 'user_stats.json'

def log_user_interaction(user_name, user_id, button_type):
    """Zaznamenať kliknutie užívateľa na tlačidlo"""
    try:
        # Načítaj existujúce dáta
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = []
        
        # Pridaj nový záznam
        new_record = {
            'user_name': user_name,
            'user_id': user_id,
            'button': button_type,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        data.append(new_record)
        
        # Ulož späť do súboru
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"📊 Logged: {user_name} clicked {button_type}")
        
    except Exception as e:
        print(f"❌ Error logging interaction: {e}")

def get_user_stats():
    """Získaj štatistiky užívateľov"""
    try:
        if not os.path.exists(STATS_FILE):
            return {
                'total_clicks': 0,
                'analiza_clicks': 0,
                'vip_clicks': 0,
                'start_clicks': 0,
                'analysis_from_channel': 0,
                'unique_users': 0,
                'recent_interactions': []
            }
        
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Spočítaj štatistiky
        total_clicks = len(data)
        analiza_clicks = len([x for x in data if x['button'] == 'ANALÝZA'])
        vip_clicks = len([x for x in data if x['button'] == 'VIP'])
        start_clicks = len([x for x in data if x['button'] == 'ŠTART bota'])
        analysis_from_channel = len([x for x in data if x['button'] == 'ANALÝZA (z kanála)'])
        unique_users = len(set([x['user_id'] for x in data]))
        
        # Posledných 10 interakcií
        recent = sorted(data, key=lambda x: x['timestamp'], reverse=True)[:10]
        
        return {
            'total_clicks': total_clicks,
            'analiza_clicks': analiza_clicks,
            'vip_clicks': vip_clicks,
            'start_clicks': start_clicks,
            'analysis_from_channel': analysis_from_channel,
            'unique_users': unique_users,
            'recent_interactions': recent
        }
        
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        return {'error': str(e)}

# Príklad dát zápasu - odstránená kolónka 'sport'
example_match = {
         'team1': 'T. M. Etcheverry',
         'team2': 'J. Shang',
         'tournament': 'ATP Cincinnati',
         'time': '19:20',
         'pick': 'Etcheverry vyhrá - 1',
         'odds': '1.65'
}

analysis_text = """📊 *ANALÝZA ZÁPASU: T. M. Etcheverry - J. Shang*

V turnaji ATP Cincinnati začína vyraďovacia časť, ktorá nám priniesla aj zápas Tomasa Etcheverryho s Junchengom Shangom  🎾

_Tomas Martin Etcheverry (ATP 60) má klasický antukársky štýl s bohatými skúsenosťami. Jeho štýl je založený na silnej baseline hre s dôrazom na topspin údery a fyzickú odolnosť. Argentínčan dosiahol kariérne maximum ATP 27 a má za sebou tri finále ATP turnajov. Etcheverry má výborný bekhend s oboma rukami a vie hrať dlhé výmeny s vysokou intenzitou. Silnou stránkou je jeho mentálna odolnosť a skúsenosti z veľkých zápasov. Jeho výkony na tvrdom kurte sú horšie ako na antuke, ale už aj tu si zobral pál skalpov - napr. minulý týždeň porazil Griekspoora. Zároveň treba spomenúť, mesiac dozadu porazil Bena Sheltona  🇦🇷
 
Juncheng Shang (ATP 109) reprezentuje novú generáciu čínskych tenistov s veľkým potenciálom.  Jeho herný štýl je all-court s výbornou technikou a rýchlosťou po kurte. Jeho ľavácky herný štýl vytvára problémy súperom a má výborné anticipovanie. Shang je syn bývalého futbalistu a majsterky sveta v stolnom tenise, čo mu dáva športové gény. Problémom je jeho mladý vek a niekedy nedostatočné skúsenosti v kľúčových momentoch, najmä proti skúsenejším súperom. Tento rok však toho neodohral. Zranil sa na začiatku sezóny v Hongkongu a potom aj na Australian open s Fokinou 🇨🇳

Zatiaľ spolu odohrali 2 zápasy a oba vyhrala Shang. Verím však, že teraz je Etcheverry v lepšej forme a Shang nebude po zraneniach hrať tak dobre _

*Tento zápas bude však vyrovnaný, kde môže rozhodnúť Etcheverryho forma a herné skúsenosti * ✅ """               

vip_text = """💎 *SMART BETS VIP* 

*Prečo si vybrať VIP?*

👑 1-3 Exkluzívne tipy každý deň
🎯 Denné tipy s kurzom 1.8+
🔔 Prioritná podpora
📊 Profesionálne analýzy
🎁 Bonusové tipy cez víkendy

🏆 *BILANCIA TIKETOV*
• Výherné tikety: 36✅
• Prehraté tikety: 12 ❌
• Úspešnosť: 75% 

📈 *NAŠA ÚSPEŠNOSŤ*
• Navrátnosť za dané obdobie: 17,68% 
• Zisk za dané obdobie: +19.63u

💰 *CELKOVÝ ZISK V €*
⏩pri vklade 100€ ZISK 393€
⏩pri vklade 200€ ZISK 785€
⏩pri vklade 500€ ZISK 1963€

💰 *CELKOVÝ ZISK V KC*
⏩pri vklade 2500KC ZISK 9815KC
⏩pri vklade 5000KC ZISK 19630KC
⏩pri vklade 12500KC ZISK 49075KC

💬[AK CHCETE AJ VY ZARÁBAŤ TIETO SUMY S NAŠOU VIP](https://t.me/SmartTipy)"""

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
    
    # Rozlíš medzi /start analysis a obyčajným /start
    if text == "/start analysis":
        # Zaznamenaj interakciu keď niekto klikne na ANALÝZA z kanála
        log_user_interaction(user_name, user_id, "ANALÝZA (z kanála)")
        
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
    
    elif text == "/start" and is_admin(user_id):
        # Admin spustil bota
        send_telegram_message(
            chat_id,
            f'Vitajte v Sports Tips Bot! 🏆\n'
            f'Vaše ID: {user_id}\n\n'
            'Príkazy:\n'
            '/tiket - Odoslať tiket do kanála\n'
            '/status - Stav bota\n'
            '/help - Zobrazí nápovedu'
        )
    
    elif text == "/start":
        # Obyčajný používateľ spustil bota
        log_user_interaction(user_name, user_id, "ŠTART bota")
        
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
    
    else:
        # Neznámy /start parameter
        print(f"❓ Unknown start parameter: {text}")
        # Fallback na normálne menu
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
    
    # Inline keyboard - len s tlačidlom ANALÝZA
    keyboard = {
        "inline_keyboard": [
            [{"text": "📊 ANALÝZA", "url": "https://t.me/smartbets_tikety_bot?start=analysis"}]
        ]
    }
    
    # Skús poslať obrázok - odstránené generovanie cesty podľa 'sport'
    image_path = "images/ATP Cincinnati 2.png"
    
    if send_telegram_photo(CHANNEL_ID, image_path, caption, keyboard):
        print("✅ Ticket with image sent to channel")
    else:
        # Fallback - pošli len text
        send_telegram_message(CHANNEL_ID, caption, parse_mode='Markdown')
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

@app.route('/stats')
def user_statistics():
    """Zobrazí štatistiky užívateľov"""
    stats = get_user_stats()
    
    if 'error' in stats:
        return jsonify({'error': stats['error']}), 500
    
    # Vytvor prehľadný HTML výstup
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>User Statistics</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .stat {{ background: #f0f0f0; padding: 20px; margin: 10px 0; border-radius: 8px; }}
            .recent {{ background: #e8f4fd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            h1 {{ color: #333; }}
            h2 {{ color: #666; }}
        </style>
    </head>
    <body>
        <h1>📊 Bot Statistics</h1>
        
        <div class="stat">
            <h2>📈 Celkové štatistiky</h2>
            <p><strong>Celkový počet interakcií:</strong> {stats['total_clicks']}</p>
            <p><strong>Kliknutia na ANALÝZA (v chate):</strong> {stats['analiza_clicks']}</p>
            <p><strong>Kliknutia na ANALÝZA (z kanála):</strong> {stats['analysis_from_channel']}</p>
            <p><strong>Kliknutia na VIP:</strong> {stats['vip_clicks']}</p>
            <p><strong>Spustenia bota (/start):</strong> {stats['start_clicks']}</p>
            <p><strong>Unikátni užívatelia:</strong> {stats['unique_users']}</p>
        </div>
        
        <div class="stat">
            <h2>🔄 Posledné interakcie</h2>
    """
    
    for interaction in stats['recent_interactions']:
        html += f"""
            <div class="recent">
                <strong>{interaction['user_name']}</strong> (ID: {interaction['user_id']}) 
                akcia: <strong>{interaction['button']}</strong><br>
                <small>⏰ {interaction['timestamp']}</small>
            </div>
        """
    
    html += """
        </div>
    </body>
    </html>
    """
    
    return html

@app.route('/stats/json')
def user_statistics_json():
    """Vráti štatistiky v JSON formáte"""
    return jsonify(get_user_stats())

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
                # Preferuj username pred first_name aj pre /start
                display_name = message['from'].get('username', message['from'].get('first_name', 'Unknown'))
                if display_name and not display_name.startswith('@'):
                    display_name = f"@{display_name}"
                handle_start_command(chat_id, user_id, display_name, text)
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
            # Preferuj username pred first_name
            user_name = callback['from'].get('username', callback['from'].get('first_name', 'Unknown'))
            if user_name and not user_name.startswith('@'):
                user_name = f"@{user_name}"
            user_id = callback['from']['id']
            data = callback['data']
            callback_query_id = callback['id']
            
            print(f"🔘 Button clicked: {data} by {user_name} (ID: {user_id})")
            
            # Odpoveď na callback query
            answer_callback_query(callback_query_id, "📊 Načítavam...")
            
            # Spracovanie akcií
            if data == "user_analysis":
                print("📊 Sending analysis...")
                # Zaznamenaj interakciu
                log_user_interaction(user_name, user_id, "ANALÝZA")
                send_analysis(chat_id)
            elif data == "user_vip":
                print("💎 Sending VIP info...")
                # Zaznamenaj interakciu
                log_user_interaction(user_name, user_id, "VIP")
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
