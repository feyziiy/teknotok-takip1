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
    except:
        pass

def start_tracking():
    print("Sistem baslatildi. XML okunuyor...")
    try:
        response = requests.get(XML_URL, timeout=30)
        response.encoding = 'utf-8'
        parser = etree.XMLParser(recover=True, encoding='utf-8')
        root = etree.fromstring(response.content, parser=parser)
        
        new_data = {}
        # XML icindeki her bir blogu tek tek tara
        for item in root.iter():
            sku_el = item.find('Sku') if item.find('Sku') is not None else item.find('sku')
            title_el = item.find('Title') if item.find('Title') is not None else item.find('title')
            stock_el = item.find('Stock') if item.find('Stock') is not None else item.find('stock')

            if sku_el is not None and title_el is not None:
                sku = (sku_el.text or "").strip()
                title = (title_el.text or "").strip()
                stock_text = (stock_el.text or "0") if stock_el is not None else "0"
                
                if sku and title:
                    s_digits = "".join(filter(str.isdigit, str(stock_text)))
                    new_data[sku] = {"Stock": int(s_digits) if s_digits else 0, "Title": title}

        # Hafizayi oku
        if os.path.exists(HAFIZA_FILE) and os.path.getsize(HAFIZA_FILE) > 0:
            with open(HAFIZA_FILE, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
        else:
            old_data = {}

        # Degisiklikleri belirle
        updates = []
        if old_data:
            for sku, info in new_data.items():
                if sku in old_data:
                    if info['Stock'] < old_data[sku]['Stock']:
                        updates.append(f"📉 *STOK AZALDI*\n{info['Title']}\nKalan: {info['Stock']}")
                else:
                    updates.append(f"🆕 *YENI URUN*\n{info['Title']}")

        # Hafizayi kaydet
        with open(HAFIZA_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=4)

        # Telegram bilgilendirme
        if not old_data and len(new_data) > 0:
            send_telegram(f"🎯 *BASARDIK!* \n{len(new_data)} urun hafizaya alindi.")
        elif len(new_data) == 0:
            send_telegram("⚠️ XML okundu ama uygun urun bulunamadi.")
        
        for msg in updates[:10]:
            send_telegram(msg)
            
        print(f"Bitti. Bulunan urun: {len(new_data)}")

    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    start_tracking()
