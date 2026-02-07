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
    
    # Adım 1: Tüm olası ürün etiketlerini dene (Büyük/Küçük harf duyarlı)
    items = root.xpath('//post') or root.xpath('//item') or root.xpath('//product') or root.xpath('//urun')
    
    # Eğer yukarıdakiler boşsa, XML'deki tüm hiyerarşiyi tara
    if not items:
        items = root.xpath('//*[sku or Sku or ID]')

    new_data = {}
    
    for item in items:
        try:
            # Sku, Title, Price ve Stock değerlerini her türlü etikette ara
            sku = (item.findtext('Sku') or item.findtext('sku') or 
                   item.findtext('ID') or item.findtext('id') or 
                   item.findtext('product_id'))
            
            title = (item.findtext('Title') or item.findtext('title') or 
                     item.findtext('Name') or item.findtext('name') or 
                     item.findtext('post_title'))
            
            price = (item.findtext('Price') or item.findtext('price') or 
                     item.findtext('Regular_price') or "0")
            
            stock_val = (item.findtext('Stock') or item.findtext('stock') or 
                         item.findtext('Quantity') or item.findtext('stock_quantity') or "0")

            if sku and title:
                # Stok verisindeki sayı olmayan karakterleri temizle
                stock = int(''.join(filter(str.isdigit, str(stock_val)))) if any(c.isdigit() for c in str(stock_val)) else 0
                new_data[sku.strip()] = {
                    "Price": price.strip(),
                    "
