import requests
from lxml import etree
import json
import os

# --- AYARLARIN ---
BOT_TOKEN = "8591872798:AAH-WNlXVF01knmB6q_iRpQkpHp4oyZvo1w"
CHAT_ID = "7798613067"
XML_URL = "https://teknotok.com/wp-content/uploads/teknotok-feeds/teknotokxml.xml"
HAFIZA_FILE = "urun_takip_hafiza.json"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram Hatası: {e}")

def start_tracking():
    try:
        # 1. XML Çekme
        response = requests.get(XML_URL, timeout=30)
        response.encoding = 'utf-8'
        
        # XML'i çok daha esnek bir şekilde (tamir ederek) oku
        parser = etree.XMLParser(recover=True, encoding='utf-8', remove_comments=True)
        try:
            root = etree.fromstring(response.content, parser=parser)
        except Exception as xml_err:
            send_telegram(f"❌ XML Okuma Hatası: {str(xml_err)}")
            return

        # 2. Hafıza Dosyası Kontrolü
        if os.path.exists(HAFIZA_FILE) and os.path.getsize(HAFIZA_FILE) > 0:
            with open(HAFIZA_FILE, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
        else:
            old_data = {}

        new_data = {}
        updates = []

        # 3. Ürünleri Tara
        posts = root.xpath('.//post')
        if not posts:
            send_telegram("⚠️ XML içinde hiç ürün (post) bulunamadı!")
            return

        for post in posts:
            try:
                sku_el = post.find('Sku')
                title_el = post.find('Title')
                if sku_el is not None and title_el is not None:
                    sku = sku_el.text.strip()
                    title = title_el.text.strip()
                    price = post.find('Price').text.strip() if post.find('Price') is not None else "0"
                    stock_text = post.find('Stock').text if post.find('Stock') is not None else "0"
                    stock = int(''.join(filter(str.isdigit, stock_text)))
                    
                    new_data[sku] = {"Price": price, "Stock": stock, "Title": title}

                    # Değişiklik Kontrolü
                    if old_data and sku in old_data:
                        old = old_data[sku]
                        if stock < old['Stock']:
                            updates.append(f"📉 *STOK AZALDI*\n{title}\nKalan: {stock}")
                        elif sku not in old_data:
                            updates.append(f"🆕 *YENİ ÜRÜN*\n{title}")
            except:
                continue

        # 4. Dosyaya Yaz
        with open(HAFIZA_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=4)
        
        # 5. Mesaj Gönderimi
        if not old_data:
            send_telegram(f"✅ *Hafıza Oluşturuldu!*\nToplam {len(new_data)} ürün takibe alındı.")
        
        if updates:
            for msg in updates[:5]:
                send_telegram(msg)

    except Exception as genel_hata:
        send_telegram(f"🚨 Sistemde Kritik Hata: {str(genel_hata)}")

if __name__ == "__main__":
    start_tracking()
