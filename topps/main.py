import os
import time
import random
import json
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import argparse
import requests

# === Project setup ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
URL = "https://www.topps.com/"

def log_message(task_id, message, level="info"):
    print(f"[{level.upper()}] {message}")
    try:
        requests.post(f"http://localhost:8000/tasks/{task_id}/log", json={}, params={"message": message, "level": level})
    except:
        pass

def update_status(task_id, status):
    try:
        requests.post(f"http://localhost:8000/tasks/{task_id}/status", params={"status": status})
    except:
        pass

def resolve_chrome_version(chrome_version):
    if not chrome_version or chrome_version.lower() == "auto":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
            version, _ = winreg.QueryValueEx(key, "version")
            return int(version.split('.')[0])
        except Exception:
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Google Chrome")
                version, _ = winreg.QueryValueEx(key, "DisplayVersion")
                return int(version.split('.')[0])
            except Exception:
                return None
    try:
        return int(chrome_version)
    except Exception:
        return None

def create_driver(task_id, chrome_version="auto"):
    PROFILE_DIR = f"c:\\temp\\profile_{task_id}"
    os.makedirs(PROFILE_DIR, exist_ok=True)

    resolved_version = resolve_chrome_version(chrome_version)
    print(f"Creating browser with resolved Chrome version: {resolved_version or 'Auto'}")

    options = uc.ChromeOptions()
    if resolved_version:
        options.browser_version = str(resolved_version)
    options.add_argument(f"--user-data-dir={PROFILE_DIR}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_argument('--no-first-run')
    options.add_argument('--no-service-autorun')
    options.add_argument('--password-store=basic')
    options.page_load_strategy = 'normal'
    
    if resolved_version:
        driver = uc.Chrome(options=options, headless=False, use_subprocess=True, version_main=resolved_version)
    else:
        driver = uc.Chrome(options=options, headless=False, use_subprocess=True)
    driver.set_page_load_timeout(60)
    return driver

def close_topps_popups(driver):
    try:
        selectors = [
            "#onetrust-accept-btn-handler",
            ".onetrust-close-btn-handler",
            "button[aria-label='Close']",
            ".kl-private-reset-css-p9660t button",
            "button[id*='close']",
            "div[class*='close']"
        ]
        for sel in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, sel)
                for el in elements:
                    if el.is_displayed():
                        el.click()
            except:
                pass
    except:
        pass

def human_type(element, text, min_delay=0.05, max_delay=0.18, pause_after=0.02, driver=None):
    try:
        element.clear()
        for ch in text:
            element.send_keys(ch)
            time.sleep(random.uniform(min_delay, max_delay))
        time.sleep(pause_after)
    except Exception:
        if driver:
            driver.execute_script("arguments[0].value = arguments[1];", element, text)
            driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", element)


def main(sku, quantity, task_id, chrome_version="auto"):
    log_message(task_id, "Bot browser starting...", "info")
    update_status(task_id, "running")
    
    driver = None
    try:
        driver = create_driver(task_id, chrome_version)
        log_message(task_id, f"Navigating to {URL}...", "info")
        driver.get(URL)
        
        # Check login
        time.sleep(5)
        sign_in_link = driver.find_elements(By.XPATH, "//a[contains(@href, 'customer/account/login')] | //*[contains(text(), 'Sign In')]")
        if any(el.is_displayed() for el in sign_in_link):
            log_message(task_id, "Sign In button detected. Paused for manual login.", "error")
            update_status(task_id, "paused")
            print(">> BROWSER PAUSED <<")
            input("Please login manually in the browser window, then press ENTER here to continue...")
            update_status(task_id, "running")
            log_message(task_id, "Continuing after manual login check...", "info")
            
        log_message(task_id, f"Searching for SKU: {sku}", "info")
        wait = WebDriverWait(driver, 15)
        search_selectors = [
            (By.NAME, "q"),
            (By.CSS_SELECTOR, "input[placeholder='Search']"),
            (By.CSS_SELECTOR, "input[aria-label='Search']"),
            (By.CSS_SELECTOR, "input.no-search-clear")
        ]
        
        search_box = None
        for selector in search_selectors:
            try:
                search_box = wait.until(EC.element_to_be_clickable(selector))
                if search_box: break
            except:
                continue
                
        if not search_box:
            raise Exception("Could not find search box")
            
        search_box.click()
        human_type(search_box, sku, driver=driver)
        search_box.send_keys(Keys.ENTER)
        
        time.sleep(random.randint(3, 5))
        close_topps_popups(driver)
        
        log_message(task_id, "Looking for product results...", "info")
        product_url = None
        for _ in range(3):
            time.sleep(3)
            product_links = driver.find_elements(By.CSS_SELECTOR, 'a.contents[href*="/products/"]')
            if product_links:
                link = product_links[0]
                product_url = link.get_attribute("href")
                if product_url and not product_url.startswith("http"):
                    product_url = "https://www.topps.com" + product_url
                break
            else:
                log_message(task_id, "Waiting for products...", "info")
                time.sleep(5)
                
        if product_url:
            log_message(task_id, f"Found product: {product_url}", "success")
            driver.get(product_url)
            time.sleep(random.randint(3, 5))
            
            try:
                add_to_cart = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-testid="product-add-to-cart"]')))
                if add_to_cart.get_attribute("data-sold-out") == "true":
                    log_message(task_id, "Item is sold out.", "error")
                else:
                    try:
                        qty_input = wait.until(EC.element_to_be_clickable((By.NAME, "quantity")))
                        human_type(qty_input, str(quantity), driver=driver)
                    except:
                        pass
                    driver.execute_script("arguments[0].click();", add_to_cart)
                    log_message(task_id, "Added to cart!", "success")
            except Exception as e:
                log_message(task_id, f"Failed to add to cart: {str(e)}", "error")
        else:
            log_message(task_id, "No products found.", "error")
            
        log_message(task_id, "Task Finished", "success")
        update_status(task_id, "completed")
        print("\nBrowser is now staying open.")
        input("Press Enter here when you are ready to close the browser...")
        
    except Exception as e:
        log_message(task_id, f"Error: {str(e)}", "error")
        update_status(task_id, "failed")
        input("Press Enter to close browser...")
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sku", type=str, required=True)
    parser.add_argument("--quantity", type=int, default=1)
    parser.add_argument("--task_id", type=int, required=True)
    parser.add_argument("--chrome-version", type=str, default="auto")
    args = parser.parse_args()
    
    main(args.sku, args.quantity, args.task_id, args.chrome_version)
