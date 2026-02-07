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
    print("İşlem başlıyor, bozuk karakterler temizleniyor...")
    
    # XML'i indir ve hataları görmezden gelerek oku
    response = requests.get(XML_URL, timeout=30)
    response.encoding = 'utf-8'
    
    # BU KISIM HATAYI ÇÖZER: 'recover=True' bozuk XML'i tamir eder
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

    # XML'deki her postu tara
    for post in root.xpath('.//post'):
        try:
            sku_el = post.find('Sku')
            title_el = post.find('Title')
            price_el = post.find('Price')
            stock_el = post.find('Stock')
            
            if sku_el is not None and title_el is not None:
                sku = sku_el.text.strip()
                title = title_el.text.strip()
                price = price_el.text.strip() if price_el is not None else "0"
                stock_text = stock_el.text if stock_el is not None else "0"
                stock = int(''.join(filter(str.isdigit, stock_text)))
                
                new_data[sku] = {"Price": price, "Stock": stock, "Title": title}

                # Kıyaslama Yap (Eski veri varsa)
                if old_data and sku in old_data:
                    old = old_data[sku]
                    if int(stock) < int(old['Stock']):
                        fark = int(old['Stock']) - int(stock)
                        updates.append(f"📉 *STOK AZALDI (-{fark})*\n{title}\nKalan: {stock}")
        except:
            continue

    # Değişiklik yoksa bile botun çalıştığını anlaman için ilk seferde mesaj at
    if not old_data:
        send_telegram("✅ *Sistem Başlatıldı!* XML başarıyla okundu ve hafıza oluşturuldu.")
    
    # Dosyayı kaydet
    with open(HAFIZA_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=4)
    
    # Mesajları gönder
    for msg in updates[:5]:
        send_telegram(msg)

if __name__ == "__main__":
    start_tracking()
