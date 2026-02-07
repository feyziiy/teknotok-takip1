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
    response = requests.get(XML_URL, timeout=30)
    response.encoding = 'utf-8'
    parser = etree.XMLParser(recover=True, encoding='utf-8')
    root = etree.fromstring(response.content, parser=parser)
    
    # XML yapısını esnek tarama (post, item veya urun olabilir)
    posts = root.xpath('.//post') or root.xpath('.//item') or root.xpath('.//*[local-name()="post"]')
    
    if not posts:
        # Eğer hala bulunamadıysa root altındaki tüm çocukları dene
        posts = list(root.iterchildren())
        if len(posts) < 5: # Çok azsa yanlış yerdir
            send_telegram("⚠️ XML yapısı hala çözülemedi. Lütfen XML linkini kontrol et.")
            return

    if os.path.exists(HAFIZA_FILE) and os.path.getsize(HAFIZA_FILE) > 0:
        with open(HAFIZA_FILE, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
    else:
        old_data = {}

    new_data = {}
    
    for post in posts:
        try:
            # Etiket isimlerini dinamik bul (Sku, stock vb.)
            sku = post.findtext('.//Sku') or post.findtext('.//sku') or post.findtext('.//ID')
            title = post.findtext('.//Title') or post.findtext('.//title') or post.findtext('.//name')
            price = post.findtext('.//Price') or post.findtext('.//price') or "0"
            stock_text = post.findtext('.//Stock') or post.findtext('.//stock') or post.findtext('.//quantity') or "0"
            
            if sku and title:
                stock = int(''.join(filter(str.isdigit, str(stock_text))))
                new_data[sku.strip()] = {"Price": price.strip(), "Stock": stock, "Title": title.strip()}
        except:
            continue

    with open(HAFIZA_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=4)
    
    if not old_data and new_data:
        send_telegram(f"✅ *Başardık!* \n{len(new_data)} adet ürün bulundu ve hafıza oluşturuldu. Artık takibe hazırım.")
    elif not new_data:
        send_telegram("❌ Veri çekildi ama ürün detayları (Sku/Title) eşleşmedi.")

if __name__ == "__main__":
    start_tracking()
