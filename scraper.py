async def scrape_okru_stream(target_url: str):
    print(f"[*] Hedef URL analiz ediliyor: {target_url}")
    captured_streams = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu"
            ]
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="tr-TR",
            timezone_id="Europe/Istanbul"
        )
        
        page = await context.new_page()

        # Ağ isteklerini yakalama fonksiyonu (Filtreyi genişlettik)
        def handle_request(request):
            url = request.url
            if any(keyword in url for keyword in [".m3u8", ".mpd", "manifest", "video", "metadata", "cmd=video"]):
                if url not in captured_streams:
                    captured_streams.append(url)

        page.on("request", handle_request)

        try:
            print("[*] Sayfaya gidiliyor...")
            await page.goto(target_url, wait_until="networkidle", timeout=60000)
            
            # Oynatıcı butonuna veya video alanına tıklama simülasyonu (Oynatıcıyı tetiklemek için)
            print("[*] Oynatıcı tetikleniyor...")
            try:
                # OK.ru oynatıcı oynat tuşu veya video alanı seçicileri
                await page.click('.html5-video-player, .vid-player_cnt, video', timeout=5000)
            except Exception:
                pass # Eğer doğrudan tıklanamazsa devam et

            # Medya isteklerinin düşmesi için biraz bekleme
            await asyncio.sleep(10)
            
        except Exception as e:
            print(f"[!] Hata oluştu: {e}")

        await browser.close()

    return captured_streams

async def main():
    target_url = "https://ok.ru/live/404041965268" # Kendi canlı yayın linkiniz
    
    streams = await scrape_okru_stream(target_url)
    
    print("\n--- YAKALANAN BAĞLANTILAR ---")
    if streams:
        for s in streams:
            print(f"-> {s}")
            
        with open("streams.txt", "w", encoding="utf-8") as f:
            for stream in streams:
                f.write(stream + "\n")
        print("[*] Bağlantılar streams.txt dosyasına yazıldı.")
    else:
        print("[!] Hiçbir akış bağlantısı yakalanamadı.")

if __name__ == "__main__":
    asyncio.run(main())
