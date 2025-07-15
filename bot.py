import logging
import asyncio
import os
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# Vypnutie verbose logov
logging.basicConfig(level=logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Konfigurácia
BOT_TOKEN = os.environ.get('BOT_TOKEN', '7511593743:AAGsPG2FG9_QC-ynD85hHHptE29-P5KiBMQ')
CHANNEL_ID = os.environ.get('CHANNEL_ID', '-1002827606573')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '7626888184'))
PORT = int(os.environ.get('PORT', 8080))
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '')

async def send_ticket(context: ContextTypes.DEFAULT_TYPE, chat_id: str, match_data: dict):
    """Odošle tiket do kanála"""
    try:
        image_path = 'Volejbal - sablona.png'
        
        # Vytvorenie inline klávesnice s buttonom pre analýzu
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎯 STAV TERAZ!", url=match_data['betting_url'])],
            [InlineKeyboardButton("📊 ANALÝZA", callback_data="show_analysis")]
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
        await context.bot.send_message(chat_id, "❌ Obrázok tiketu nebol nájdený! Uložte obrázok ako 'ticket_image.png'")
    except Exception as e:
        print(f"Chyba pri odosielaní tiketu: {e}")
        await context.bot.send_message(chat_id, "Nastala chyba pri odosielaní tiketu.")

# Príklad dát zápasu
example_match = {
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

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Obsluha kliknutí na button ANALÝZA"""
    query = update.callback_query
    
    if query.data == "show_analysis":
        try:
            # Potvrdí kliknutie
            await query.answer("📊 Analýza sa načítava...")
            
            # Pošle dlhú analýzu ako súkromnú správu
            await context.bot.send_message(
                chat_id=query.from_user.id,
                text=analysis_text,
                parse_mode='Markdown'
            )
            print(f"Analýza odoslaná užívateľovi: {query.from_user.first_name}")
            
        except Exception as e:
            print(f"Chyba pri odosielaní analýzy: {e}")
            await query.answer("❌ Chyba pri načítaní analýzy")

def is_admin(user_id):
    """Kontrola či je užívateľ administrátor"""
    return user_id == ADMIN_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Obsluha príkazu /start"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Nemáte oprávnenie používať tohto bota.")
        return
    
    await update.message.reply_text(
        f'Vitajte v Sports Tips Bot! 🏆\n'
        f'Vaše ID: {user_id}\n\n'
        'Príkazy:\n'
        '/tiket - Odoslať tiket do kanála\n'
        '/help - Zobrazí nápovedu'
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
    # Vytvorenie aplikácie
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Registrácia handlerov
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("tiket", tiket))
    application.add_handler(CommandHandler("test", test_channel))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_handler))  # Pre button ANALÝZA
    
    # Spustenie bota
    if WEBHOOK_URL:
        # Webhook pre Render
        print("Spúšťam webhook...")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"{WEBHOOK_URL}/webhook",
            secret_token="your-secret-token"
        )
    else:
        # Polling pre lokálne testovanie
        print("Bot je spustený...")
        application.run_polling()

if __name__ == '__main__':
    main()
