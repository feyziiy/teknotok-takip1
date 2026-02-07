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
    print("XML Verisi okunuyor...")
    try:
        response = requests.get(XML_URL, timeout=30)
        response.encoding = 'utf-8'
        parser = etree.XMLParser(recover=True, encoding='utf-8')
        root = etree.fromstring(response.content, parser=parser)
        
        new_data = {}
        # XML içindeki her bir öğeyi tara
        for item in root.iter():
            sku, title, stock_text = None, None, "0"
            
            # Bu öğenin altındaki tüm etiketleri tek tek kontrol et
            for child in item:
                tag = child.tag.lower() # Etiket adını küçük harfe çevir (sku, Sku, SKU hepsi uyar)
                val = (child.text or "").strip()
                
                if tag in ['sku', 'id', 'product_id', 'kod']:
                    sku = val
                elif tag in ['title', 'name', 'urun_adi', 'post_title', 'baslik']:
                    title = val
                elif tag in ['stock', 'quantity', 'stok', 'stock_quantity', 'adet']:
                    stock_text = val

            # Eğer bir SKU ve Başlık bulunduysa veriyi kaydet
            if sku and title:
                s_digits = "".join(filter(str.isdigit, str(stock_text)))
                new_data[sku] = {
                    "Stock": int(s_digits) if s_digits else 0,
                    "Title": title
                }

        # Hafıza dosyasını yönet
        if os.path.exists(HAFIZA_FILE) and os.path.getsize(HAFIZA_FILE) > 0:
            with open(HAFIZA_FILE, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
        else:
            old_data = {}

        updates = []
        if old_data:
            for s_id, info in new_data.items():
                if s_id in old_data:
                    if info['Stock'] < old_data[s_id]['Stock']:
                        updates.append(f"📉 *STOK AZALDI*\n{info['Title']}\nKalan: {info['Stock']}")
                else:
                    updates.append(f"🆕 *YENİ ÜRÜN*\n{info['Title']}")

        with open(HAFIZA_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=4)

        # Telegram bilgilendirme
        if not old_data and len(new_data) > 0:
            send_telegram(f"🎯 *BAŞARDIK!* \n{len(new_data)} ürün başarıyla takibe alındı.")
        elif len(new_data) == 0:
            send_telegram("⚠️ XML okundu ama ürünler hala tanımlanamadı. Yapı çok farklı görünüyor.")
        
        for msg in updates[:10]:
            send_telegram(msg)
            
        print(f"Bitti. Bulunan: {len(new_data)}")

    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    start_tracking()
