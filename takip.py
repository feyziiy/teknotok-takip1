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
    requests.post(url, json=payload, timeout=10)

def start_tracking():
    print("XML çekiliyor...")
    response = requests.get(XML_URL, timeout=30)
    response.encoding = 'utf-8'
    parser = etree.XMLParser(recover=True, encoding='utf-8')
    root = etree.fromstring(response.content, parser=parser)
    
    # Hafızayı oku
    if os.path.exists(HAFIZA_FILE) and os.path.getsize(HAFIZA_FILE) > 0:
        with open(HAFIZA_FILE, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
    else:
        old_data = {}

    new_data = {}
    updates = []

    # XML içindeki TÜM elemanları tara (post, item, product ayrımı yapmaksızın)
    # İçinde 'sku' veya 'ID' geçen her bloğu bir ürün kabul et
    all_elements = root.xpath("//*[sku or Sku or ID or id]")
    
    for item in all_elements:
        try:
            # En yaygın etiket isimlerini dene
            sku = (item.findtext('Sku') or item.findtext('sku') or item.findtext('ID') or item.findtext('id') or "").strip()
            title = (item.findtext('Title') or item.findtext('title') or item.findtext('Name') or item.findtext('name') or "").strip()
            stock_text = (item.findtext('Stock') or item.findtext('stock') or item.findtext('quantity') or "0")
            price = (item.findtext('Price') or item.findtext('price') or "0")

            if sku and title:
                # Stok bilgisini sayıya çevir
                s_digits = "".join(filter(str.isdigit, str(stock_text)))
                stock = int(s_digits) if s_digits else 0
                
                new_data[sku] = {"Stock": stock, "Title": title, "Price": price}

                # Kıyaslama (Hafıza doluysa)
                if old_data and sku in old_data:
                    if stock < old_data[sku]['Stock']:
                        updates.append(f"📉 *STOK AZALDI*\n{title}\nKalan: {stock}")
                    elif stock > old_data[sku]['Stock']:
                        updates.append(f"📈 *STOK ARTTI*\n{title}\nYeni: {stock}")
                elif old_data and sku not in old_data:
                    updates.append(f"🆕 *YENİ ÜRÜN*\n{title}")
        except:
            continue

    # Hafızayı güncelle
    with open(HAFIZA_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=4)
    
    # Rapor ver
    if not old_data:
        send_telegram(f"✅ *Başarılı!* \n{len(new_data)} ürün takibe alındı. Artık sadece değişim olunca mesaj atacağım.")
    
    if updates:
        for msg in updates[:5]:
            send_telegram(msg)

if __name__ == "__main__":
    start_tracking()
