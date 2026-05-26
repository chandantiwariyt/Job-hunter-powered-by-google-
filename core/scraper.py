from playwright.sync_api import sync_playwright

def crawl_job_page(url: str):
    """Spins up a headless browser to pull live data. Returns dict on success, None on failure."""
    print(f"🌐 [Playwright] Launching headless browser to crawl: {url}")
    
    browser = None
    company_name = "Target Enterprise"
    if "lever.co" in url:
        company_name = url.split("lever.co/")[1].split("/")[0]
    elif "greenhouse.io" in url:
        company_name = url.split("greenhouse.io/")[1].split("/")[0]
    elif "ashbyhq.com" in url:
        company_name = url.split("ashbyhq.com/")[1].split("/")[0]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.goto(url, wait_until="commit", timeout=15000)
            page.wait_for_selector("body", timeout=10000)
            page.wait_for_timeout(2000)
            
            page_title = page.title()
            full_body_text = page.locator("body").inner_text()
            
            if not page_title or not full_body_text:
                print(f"⚠️ No content retrieved from {url}")
                return None
            
            return {
                "title": page_title.split("-")[0].strip(),
                "company": company_name.capitalize(),
                "url": url,
                "description": full_body_text
            }
    except Exception as e:
        print(f"❌ Playwright rendering failed for {url}. Error: {e}")
        return None
