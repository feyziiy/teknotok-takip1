import requests
from lxml import etree
import json
import os

# AYARLAR
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
    print("Sistem baslatildi. XML verisi okunuyor...")
    try:
        response = requests.get(XML_URL, timeout=30)
        response.encoding = 'utf-8'
        parser = etree.XMLParser(recover=True, encoding='utf-8')
        root = etree.fromstring(response.content, parser=parser)
        
        new_data = {}
        # XML icindeki her bir ogeye bak (etiket ismi ne olursa olsun)
        for item in root.xpath("//*"):
            # Eger bu ogenin icinde Sku veya ID varsa, bu bir urundur
            sku = (item.findtext('.//*[local-name()="Sku"]') or 
                   item.findtext('.//*[local-name()="sku"]') or 
                   item.findtext('.//*[local-name()="ID"]'))
            
            title = (item.findtext('.//*[local-name()="Title"]') or 
                     item.findtext('.//*[local-name()="title"]') or 
                     item.findtext('.//*[local-name()="Name"]'))
            
            stock_val = (item.findtext('.//*[local-name()="Stock"]') or 
                         item.findtext('.//*[local-name()="stock"]') or "0")

            if sku and title:
                s_digits = "".join(filter(str.isdigit, str(stock_val)))
                new_data[sku.strip()] = {
                    "Stock": int(s_digits) if s_digits else 0,
                    "Title": title.strip()
                }

        # Hafizayi oku
        if os.path.exists(HAFIZA_FILE) and os.path.getsize(HAFIZA_FILE) > 0:
            with open(HAFIZA_FILE, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
        else:
            old_data = {}

        updates = []
        if old_data:
            for sku, info in new_data.items():
                if sku in old_data:
                    if info['Stock'] < old_data[sku]['Stock']:
                        updates.append(f"📉 *STOK AZALDI*\n{info['Title']}\nKalan: {info['Stock']}")
                else:
                    updates.append(f"🆕 *YENI URUN*\n{info['Title']}")

        # Dosyayi guncelle
        with open(HAFIZA_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=4)

        # Telegram bilgilendirme
        if not old_data and len(new_data) > 0:
            send_telegram(f"✅ *BASARDIK!* \n{len(new_data)} urun hafizaya alindi. Takip pusuya yatti.")
        elif len(new_data) == 0:
            send_telegram("❌ XML icinde urun verisi bulunamadi. Etiket isimleri uyumsuz.")
        
        for msg in updates[:5]:
            send_telegram(msg)
            
        print(f"Bitti. Bulunan urun sayisi: {len(new_data)}")

    except Exception as e:
        print(f"Kritik Hata: {e}")
        send_telegram(f"🚨 Hata: {str(e)}")

if __name__ == "__main__":
    start_tracking()
