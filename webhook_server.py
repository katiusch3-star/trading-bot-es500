from flask import Flask, request
import requests
import json

app = Flask(__name__)

# I tuoi dati Telegram
TELEGRAM_TOKEN = '8093135745:AAFlLkmT87Aopf5sw47tLQhOR9qnmYYDIY4'
FREE_CHAT_ID = "@es_segnali_free"
PREMIUM_CHAT_ID = "-1002766136972"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Debug: vediamo tutto quello che arriva
        print("=" * 50)
        print(f"Content-Type: {request.content_type}")
        print(f"Raw data: {request.data}")
        
        message_text = ""
        signal_type = "free"  # Default: segnale gratuito
        
        # Prova diversi modi per ottenere il messaggio
        if request.content_type and 'application/json' in request.content_type:
            try:
                data = request.get_json()
                message_text = data.get('message', str(data))
                # Controlla se è specificato il tipo di segnale
                signal_type = data.get('type', 'free')
                print(f"JSON data: {data}")
            except:
                pass
        
        # Se non è JSON, prova come testo raw
        if not message_text:
            message_text = request.get_data(as_text=True)
            print(f"Raw text: {message_text}")
            
            # Controlla se nel messaggio c'è "PREMIUM" per determinare il tipo
            if "PREMIUM" in message_text.upper() or "💎" in message_text:
                signal_type = "premium"
        
        # Se ancora vuoto, prova form data
        if not message_text:
            message_text = request.form.get('message', '')
            signal_type = request.form.get('type', 'free')
            if not message_text:
                # Prova a prendere il primo valore del form
                for key, value in request.form.items():
                    message_text = f"{key}: {value}"
                    break
        
        # Se ancora vuoto, prova query parameters
        if not message_text:
            message_text = request.args.get('message', '')
            signal_type = request.args.get('type', 'free')
        
        # Ultimo tentativo: converti tutto in stringa
        if not message_text:
            message_text = f"Headers: {request.headers}\nForm: {request.form}\nArgs: {request.args}\nData: {request.data}"
        
        print(f"Messaggio ricevuto: {message_text}")
        print(f"Tipo segnale: {signal_type}")
        
        # ==================== FILTRO ANTI-SPAM ====================
        # Ignora messaggi che contengono il placeholder non sostituito
        spam_keywords = [
            "{{strategy.order.alert_message}}",
            "{{alert_message}}",
            "strategy.order.alert_message",
            "alert_message"
        ]
        
        # Controlla se il messaggio contiene parole spam
        message_lower = message_text.lower().strip()
        is_spam = False
        
        for keyword in spam_keywords:
            if keyword.lower() in message_lower:
                is_spam = True
                print(f"🚫 MESSAGGIO SPAM RILEVATO: '{keyword}' trovato nel messaggio")
                break
        
        # Se è spam, logga e ignora
        if is_spam:
            print(f"🗑️ Messaggio ignorato: {message_text}")
            print("=" * 50)
            return "Messaggio spam ignorato", 200
        
        # Se è vuoto o troppo corto, ignora
        if len(message_text.strip()) < 10:
            print(f"🚫 Messaggio troppo corto ignorato: '{message_text}'")
            print("=" * 50)
            return "Messaggio troppo corto ignorato", 200
        
        # ==================== SELEZIONE CHAT ID ====================
        # Scegli il canale in base al tipo di segnale
        if signal_type.lower() == "premium":
            chat_id = PREMIUM_CHAT_ID
            print(f"📡 Invio a canale PREMIUM: {PREMIUM_CHAT_ID}")
        else:
            chat_id = FREE_CHAT_ID
            print(f"📡 Invio a canale FREE: {FREE_CHAT_ID}")
        
        print(f"✅ Messaggio valido, invio a Telegram: {message_text[:100]}...")
        print("=" * 50)
        
        # ==================== AGGIUNGI DISCLAIMER ====================
        # Disclaimer compatto bilingue
        disclaimer_footer = "\n\nIT: I segnali ES sono SOLO educativi - NON consigli d'investimento\nEN: ES signals are ONLY educational - NOT investment advice\nIT: Il trading comporta rischi elevati di perdite\nEN: Trading involves high risks of losses"
        
        # Aggiungi disclaimer al messaggio
        final_message = message_text + disclaimer_footer
        
        # Invia a Telegram
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        
        payload = {
            "chat_id": chat_id,
            "text": final_message[:4096],  # Limite Telegram 4096 caratteri
            "parse_mode": "HTML"
        }
        
        response = requests.post(telegram_url, json=payload)
        
        print(f"Telegram response: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            print("✅ Messaggio inviato con successo!")
            return "Messaggio inviato a Telegram", 200
        else:
            print(f"❌ Errore Telegram: {response.text}")
            return f"Errore Telegram: {response.text}", 500
            
    except Exception as e:
        print(f"💥 Errore generale: {e}")
        import traceback
        traceback.print_exc()
        return f"Errore: {e}", 500

@app.route('/test', methods=['GET'])
def test():
    """Endpoint per testare se il server funziona"""
    return "🟢 Server TradingView->Telegram funzionante!", 200

@app.route('/test-telegram-free', methods=['GET'])
def test_telegram_free():
    """Endpoint per testare l'invio al canale FREE"""
    try:
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": FREE_CHAT_ID,
            "text": "🧪 Test dal server Python - Canale FREE funziona!"
        }
        response = requests.post(telegram_url, json=payload)
        
        if response.status_code == 200:
            return f"✅ Test canale FREE riuscito! Messaggio inviato a {FREE_CHAT_ID}", 200
        else:
            return f"❌ Test canale FREE fallito: {response.text}", 500
    except Exception as e:
        return f"💥 Errore test FREE: {e}", 500

@app.route('/test-telegram-premium', methods=['GET'])
def test_telegram_premium():
    """Endpoint per testare l'invio al canale PREMIUM"""
    try:
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": PREMIUM_CHAT_ID,
            "text": "💎 Test dal server Python - Canale PREMIUM funziona!"
        }
        response = requests.post(telegram_url, json=payload)
        
        if response.status_code == 200:
            return f"✅ Test canale PREMIUM riuscito! Messaggio inviato a {PREMIUM_CHAT_ID}", 200
        else:
            return f"❌ Test canale PREMIUM fallito: {response.text}", 500
    except Exception as e:
        return f"💥 Errore test PREMIUM: {e}", 500

@app.route('/test-webhook-free', methods=['GET'])
def test_webhook_free():
    """Simula un webhook per il canale FREE"""
    try:
        message = "🆓 TEST SEGNALE FREE\n📊 BTCUSD | Score: 8/10\n💰 Entry: 45000\n🎯 TP: 45100\n🛑 SL: 44900"
        
        # Aggiungi disclaimer anche ai test
        disclaimer_footer = "\n\nIT: I segnali ES sono SOLO educativi - NON consigli d'investimento\nEN: ES signals are ONLY educational - NOT investment advice\nIT: Il trading comporta rischi elevati di perdite\nEN: Trading involves high risks of losses"
        message_with_disclaimer = message + disclaimer_footer
        
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": FREE_CHAT_ID,
            "text": message_with_disclaimer,
            "parse_mode": "HTML"
        }
        response = requests.post(telegram_url, json=payload)
        
        if response.status_code == 200:
            return f"✅ Test webhook FREE riuscito! Messaggio inviato a {FREE_CHAT_ID}", 200
        else:
            return f"❌ Test webhook FREE fallito: {response.text}", 500
    except Exception as e:
        return f"💥 Errore: {e}", 500

@app.route('/test-webhook-premium', methods=['GET'])
def test_webhook_premium():
    """Simula un webhook per il canale PREMIUM"""
    try:
        message = "💎 TEST SEGNALE PREMIUM\n📊 BTCUSD | Score: 9/10 ⭐️\n💰 Entry: 45000\n🎯 TP: 45150\n🛑 SL: 44850\n🔥 Analisi: Breakout confermato + Volume surge"
        
        # Aggiungi disclaimer anche ai test
        disclaimer_footer = "\n\nIT: I segnali ES sono SOLO educativi - NON consigli d'investimento\nEN: ES signals are ONLY educational - NOT investment advice\nIT: Il trading comporta rischi elevati di perdite\nEN: Trading involves high risks of losses"
        message_with_disclaimer = message + disclaimer_footer
        
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": PREMIUM_CHAT_ID,
            "text": message_with_disclaimer,
            "parse_mode": "HTML"
        }
        response = requests.post(telegram_url, json=payload)
        
        if response.status_code == 200:
            return f"✅ Test webhook PREMIUM riuscito! Messaggio inviato a {PREMIUM_CHAT_ID}", 200
        else:
            return f"❌ Test webhook PREMIUM fallito: {response.text}", 500
    except Exception as e:
        return f"💥 Errore: {e}", 500

if __name__ == '__main__':
    print("🚀 Avvio server TradingView->Telegram...")
    print(f"📱 Chat ID FREE: {FREE_CHAT_ID}")
    print(f"💎 Chat ID PREMIUM: {PREMIUM_CHAT_ID}")
    print(f"🤖 Bot Token: {TELEGRAM_TOKEN[:10]}...")
    print("🌐 Server disponibile su http://localhost:5000")
    print("📡 Ricorda di avviare ngrok: ngrok http 5000")
    print("🧪 Test endpoints:")
    print("   - http://localhost:5000/test")
    print("   - http://localhost:5000/test-telegram-free")
    print("   - http://localhost:5000/test-telegram-premium")
    print("   - http://localhost:5000/test-webhook-free")
    print("   - http://localhost:5000/test-webhook-premium")
    print("\n✅ DISCLAIMER AUTOMATICO ATTIVO!")
    print("📋 Ogni segnale avrà disclaimer legale bilingue")
    app.run(host='0.0.0.0', port=5000, debug=True)