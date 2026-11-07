import asyncio
import json
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

async def scrape_okru_stream(target_url: str):
    print(f"[*] Hedef URL analiz ediliyor: {target_url}")
    
    captured_streams = []

    async with async_playwright() as p:
        # GitHub Actions (Linux) ortamı için headless=True zorunludur
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="tr-TR",
            timezone_id="Europe/Istanbul"
        )
        
        page = await context.new_page()

        # Ağ trafiğini dinleyerek m3u8 veya manifest linklerini yakalayalım
        page.on("request", lambda request: check_network_request(request, captured_streams))

        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
            print("[*] Sayfa yüklendi, medya bileşenleri bekleniyor...")
            await asyncio.sleep(7)
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            extracted_metadata = extract_embedded_json(soup)

        except Exception as e:
            print(f"[!] Sayfa yüklenirken hata oluştu: {e}")
            extracted_metadata = None

        await browser.close()

    return captured_streams, extracted_metadata

def check_network_request(request, stream_list):
    url = request.url
    if any(ext in url for ext in [".m3u8", ".mpd", "manifest", "index.fmp4"]):
        if url not in stream_list:
            stream_list.append(url)

def extract_embedded_json(soup: BeautifulSoup):
    metadata = []
    elements = soup.find_all(attrs={"data-options": True})
    for el in elements:
        try:
            raw_data = el.get("data-options")
            parsed = json.loads(raw_data)
            metadata.append(parsed)
        except Exception:
            pass
    return metadata

async def main():
    # Buraya takip etmek istediğiniz OK.ru video veya yayın linkini yazabilirsiniz
    target_url = "https://ok.ru/live/example" 
    
    streams, metadata = await scrape_okru_stream(target_url)
    
    print("\n--- YAKALANAN AKIŞ BAĞLANTILARI (HLS/Manifest) ---")
    if streams:
        for s in streams:
            print(f"-> {s}")
    else:
        print("Ağ trafiğinde doğrudan akış bağlantısı yakalanamadı.")
        
    print("\n--- SAYFADAN AYIKLANAN GÖMÜLÜ METADATA ---")
    if metadata:
        print(json.dumps(metadata[:2], indent=2, ensure_ascii=False))
    else:
        print("Gömülü JSON verisi bulunamadı.")

if __name__ == "__main__":
    asyncio.run(main())
