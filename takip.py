import requests
from lxml import etree
import json
import os

BOT_TOKEN = "8591872798:AAH-WNlXVF01knmB6q_iRpQkpHp4oyZvo1w"
CHAT_ID = "7798613067"
XML_URL = "https://teknotok.com/wp-content/uploads/teknotok-feeds/teknotokxml.xml"
HAFIZA_FILE = "urun_takip_hafiza.json"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def start_tracking():
    print("XML Çekiliyor...")
    response = requests.get(XML_URL, timeout=30)
    response.encoding = 'utf-8'
    
    parser = etree.XMLParser(recover=True, encoding='utf-8')
    root = etree.fromstring(response.content, parser=parser)
    
    # Hafızayı oku
    if os.path.exists(HAFIZA_FILE):
        with open(HAFIZA_FILE, 'r', encoding='utf-8') as f:
            try:
                old_data = json.load(f)
            except:
                old_data = {}
    else:
        old_data = {}

    new_data = {}
    updates = []

    # XML içindeki her ürünü (post) tara
    for post in root.xpath('.//post'):
        try:
            sku = post.find('Sku').text.strip()
            title = post.find('Title').text.strip()
            price = post.find('Price').text.strip()
            stock_text = post.find('Stock').text
            stock = int(''.join(filter(str.isdigit, stock_text))) if stock_text else 0

            new_data[sku] = {"Price": price, "Stock": stock, "Title": title}

            if old_data: # Eğer hafıza doluysa kıyasla
                if sku in old_data:
                    old = old_data[sku]
                    if old['Stock'] > 0 and stock <= 0:
                        updates.append(f"❌ *STOK BİTTİ*\n{title}")
                    elif old['Price'] != price:
                        updates.append(f"💰 *FİYAT DEĞİŞTİ*\n{title}\n📉 Eski: {old['Price']}\n📈 Yeni: {price}")
                    elif old['Stock'] <= 0 and stock > 0:
                        updates.append(f"✅ *STOK GELDİ*\n{title}\nFiyat: {price}")
                else:
                    updates.append(f"🆕 *YENİ ÜRÜN EKLENDİ*\n{title}\nFiyat: {price}")
            else:
                # Hafıza bomboşsa (ilk çalışma), sessizce doldur veya test için mesaj at
                pass
        except:
            continue

    # ÖNEMLİ: Yeni veriyi dosyaya yaz
    with open(HAFIZA_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=4)
    
    # Bildirimleri gönder (Çok fazla mesaj gelmemesi için ilk 5 tanesini gönderelim test için)
    if updates:
        for msg in updates[:10]: # Şimdilik sınırı 10 yaptık
            send_telegram(msg)
    else:
        print("Değişiklik yok.")

if __name__ == "__main__":
    start_tracking()
