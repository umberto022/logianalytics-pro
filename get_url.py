from playwright.sync_api import sync_playwright
import os, time, re

EDGE_EXE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
EDGE_USER_DATA = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data")

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=EDGE_USER_DATA,
        executable_path=EDGE_EXE,
        headless=True,
        args=["--profile-directory=Default", "--no-sandbox"],
        timeout=30000
    )
    page = ctx.new_page()
    page.goto("https://share.streamlit.io", timeout=20000)
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(3)
    content = page.content()
    urls = re.findall(r"https://[a-z0-9\-]+\.streamlit\.app[^\s\"'<>]*", content)
    if urls:
        print("APP URL:")
        for u in sorted(set(urls)):
            print(u)
    else:
        print("Deploy en proceso, URL no disponible aun.")
        print("Pagina actual:", page.url)
    ctx.close()
