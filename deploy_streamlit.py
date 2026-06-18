"""
Deploy automatico a Streamlit Community Cloud usando Microsoft Edge.
"""
import os
import time
from playwright.sync_api import sync_playwright

REPO = "umberto022/logianalytics-pro"
BRANCH = "master"
MAIN_FILE = "app.py"
EDGE_EXE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
EDGE_USER_DATA = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data")

def wait_and_click(page, selectors, timeout=5000, label="elemento"):
    for sel in selectors:
        try:
            el = page.locator(sel).first
            el.wait_for(state="visible", timeout=timeout)
            el.click()
            print(f"Click en {label}: {sel}")
            return True
        except Exception:
            continue
    return False

def wait_and_fill(page, selectors, value, label="campo"):
    for sel in selectors:
        try:
            el = page.locator(sel).first
            el.wait_for(state="visible", timeout=3000)
            el.fill(value)
            print(f"Rellenado {label}: {value}")
            return True
        except Exception:
            continue
    return False

def run():
    with sync_playwright() as p:
        print("Abriendo Edge con tu perfil existente...")
        # Cerrar Edge si esta abierto
        os.system("taskkill /f /im msedge.exe >nul 2>&1")
        time.sleep(1)

        try:
            ctx = p.chromium.launch_persistent_context(
                user_data_dir=EDGE_USER_DATA,
                executable_path=EDGE_EXE,
                headless=False,
                args=["--profile-directory=Default", "--no-sandbox"],
                timeout=60000
            )
            page = ctx.new_page()
            browser = None
        except Exception as e:
            print(f"Error con perfil persistente: {e}")
            print("Intentando Edge sin perfil...")
            browser = p.chromium.launch(
                channel="msedge",
                headless=False
            )
            ctx = browser.new_context()
            page = ctx.new_page()

        try:
            print("\n1. Navegando a Streamlit Cloud...")
            page.goto("https://share.streamlit.io", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=20000)
            time.sleep(2)

            # Login si es necesario
            try:
                page.locator("text=Sign in with GitHub").first.wait_for(state="visible", timeout=5000)
                print("2. Iniciando sesion con GitHub...")
                page.locator("text=Sign in with GitHub").first.click()
                page.wait_for_load_state("networkidle", timeout=30000)
                time.sleep(3)

                # Autorizar si GitHub lo pide
                try:
                    page.locator("text=Authorize streamlit").first.wait_for(state="visible", timeout=5000)
                    page.locator("text=Authorize streamlit").first.click()
                    page.wait_for_load_state("networkidle", timeout=15000)
                    time.sleep(2)
                except Exception:
                    pass
            except Exception:
                print("2. Ya hay sesion activa en Streamlit Cloud.")

            print("3. Buscando boton para nueva app...")
            time.sleep(2)
            page.screenshot(path="paso1_dashboard.png")

            clicked = wait_and_click(page, [
                "button:has-text('New app')",
                "a:has-text('New app')",
                "text=New app",
                "button:has-text('Create app')",
                "text=Create app",
                "[data-testid='new-app-button']",
            ], timeout=8000, label="New app")

            if not clicked:
                print("No encontre el boton. Mira la pantalla y haz click en 'New app' manualmente.")
                input("Presiona Enter cuando hayas clickeado 'New app'...")

            time.sleep(3)
            page.wait_for_load_state("networkidle", timeout=10000)
            page.screenshot(path="paso2_new_app.png")

            print("4. Configurando repositorio...")

            # Seleccionar desde GitHub
            wait_and_click(page, [
                "text=From existing repo",
                "text=GitHub",
                "button:has-text('GitHub')",
            ], timeout=5000, label="From GitHub")
            time.sleep(2)

            # Campo de repo
            if not wait_and_fill(page, [
                "input[placeholder*='owner/repo']",
                "input[placeholder*='repository']",
                "input[placeholder*='repo']",
                "input[name='repository']",
                "input[name='repoUrl']",
            ], REPO, "repositorio"):
                print(f"Escribe el repo manualmente: {REPO}")

            time.sleep(1)
            # Seleccionar del dropdown si aparece
            try:
                page.locator(f"text={REPO}").first.click(timeout=3000)
            except Exception:
                pass

            # Branch
            wait_and_fill(page, [
                "input[placeholder*='branch']",
                "input[name='branch']",
            ], BRANCH, "branch")

            # Main file
            wait_and_fill(page, [
                "input[placeholder*='file']",
                "input[placeholder*='path']",
                "input[name='mainModule']",
                "input[name='mainFile']",
            ], MAIN_FILE, "main file")

            time.sleep(2)
            page.screenshot(path="paso3_config.png")
            print("5. Iniciando deploy...")

            if not wait_and_click(page, [
                "button:has-text('Deploy!')",
                "button:has-text('Deploy')",
                "text=Deploy!",
                "[data-testid='deploy-button']",
            ], timeout=5000, label="Deploy"):
                print("No encontre Deploy. Hazlo manualmente en la pantalla.")
                input("Presiona Enter cuando el deploy haya iniciado...")

            print("\nDeploy en proceso (3-5 minutos). No cierres el navegador.")
            time.sleep(30)
            page.screenshot(path="paso4_deploying.png")

            # Esperar URL de la app
            for i in range(24):  # hasta 4 minutos
                try:
                    url_elem = page.locator("a[href*='.streamlit.app']").first
                    url_elem.wait_for(state="visible", timeout=10000)
                    app_url = url_elem.get_attribute("href")
                    print(f"\n{'='*50}")
                    print(f"APP DESPLEGADA EXITOSAMENTE!")
                    print(f"URL: {app_url}")
                    print(f"{'='*50}\n")
                    break
                except Exception:
                    print(f"Esperando... ({(i+1)*10}s)")
                    time.sleep(10)
            else:
                print("Deploy en curso. Revisa el navegador para ver la URL.")

            input("\nPresiona Enter para cerrar el navegador...")

        finally:
            if browser:
                browser.close()
            elif ctx:
                ctx.close()

if __name__ == "__main__":
    run()
