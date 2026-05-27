import os
import time
import pickle
import json
import random
import logging
import threading
import sys
import io
import requests
import argparse
import csv
import undetected_chromedriver as uc
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# --- constants ---
COOKIES_FILE = "cookies.pkl"
LOCAL_FILE = "local_storage.json"
URL = "https://www.target.com/"
CONFIG_FILE = "config.json"
CSV_PATH = "sku.csv"
TOOL_NAME = "Bot1"
PASSWORD = "Hacktanha"


# --- global vars ---
driver_instance = None
running = False

# ===== Core Bot Logic =====

def save_session(driver, profile_dir):
    cookies_file = os.path.join(profile_dir, "cookies.json")
    pickle_file = os.path.join(profile_dir, "session.pkl")

    # Save cookies
    with open(cookies_file, "w") as f:
        json.dump(driver.get_cookies(), f)

    # Save pickle (optional if you want redundancy)
    with open(pickle_file, "wb") as f:
        pickle.dump(driver.get_cookies(), f)

    print("[+] Login session saved successfully.")


def load_session(driver, profile_dir):
    cookies_file = os.path.join(profile_dir, "cookies.json")
    if not os.path.exists(cookies_file):
        return False

    with open(cookies_file, "r") as f:
        cookies = json.load(f)

    for cookie in cookies:
        try:
            driver.add_cookie(cookie)
        except Exception:
            pass
    print("[+] Cookies loaded.")
    return True

def read_config(path=CONFIG_FILE):
    """Read configuration from JSON file and return dict with defaults.

    Returns: {'CVE': str, 'SPEND_LIMIT': float, 'BUY_LIMIT': int}
    """
    defaults = {
        'CVE': '123',
        'SPEND_LIMIT': 120.00,
        'BUY_LIMIT': 3
    }
    try:
        if not os.path.exists(path):
            # create default config file
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(defaults, f, indent=2)
            return defaults
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # sanitize/validate
        cfg = {}
        cfg['CVE'] = str(data.get('CVE', defaults['CVE']))
        try:
            cfg['SPEND_LIMIT'] = float(data.get('SPEND_LIMIT', defaults['SPEND_LIMIT']))
        except Exception:
            cfg['SPEND_LIMIT'] = defaults['SPEND_LIMIT']
        try:
            cfg['BUY_LIMIT'] = int(data.get('BUY_LIMIT', defaults['BUY_LIMIT']))
        except Exception:
            cfg['BUY_LIMIT'] = defaults['BUY_LIMIT']
        return cfg
    except Exception:
        return defaults
    
cfg = read_config()
CVE = cfg.get('CVE', '123')
SPEND_LIMIT = cfg.get('SPEND_LIMIT', 120.00)
BUY_LIMIT = cfg.get('BUY_LIMIT', 3)


def get_price(driver):
    try:
        price_elem = driver.find_element(By.CSS_SELECTOR, "span[data-test='product-price']")
        price_text = price_elem.text.replace('$', '').replace(',', '').strip()
        return float(price_text)
    except Exception:
        return 0.0

def load_skus():
    skus = []
    if not os.path.exists(CSV_PATH):
        return skus
    with open(CSV_PATH, newline='', encoding='utf-8') as cf:
        reader = csv.DictReader(cf)
        for row in reader:
            sku = (row.get('sku') or row.get('SKU') or '').strip()
            qty = row.get('quantity') or row.get('Quantity') or row.get('qty') or ''
            if not sku:
                continue
            try:
                q = int(qty) if qty else 1
            except:
                q = 1
            skus.append({'sku': sku, 'quantity': q})
    return skus


def is_logged_in(driver):
    # Give it a moment to load and settle
    time.sleep(2)
    
    # We check if any element represents "not logged in" (the Account sign in link)
    # Target uses a link with id="account-sign-in" or aria-label="Account, sign in" for guests.
    not_logged_in_selectors = [
        "a#account-sign-in",
        "a[data-test='@web/AccountLink'][aria-label*='sign in']",
        "a[data-test='@web/AccountLink'][aria-label*='Sign in']",
        "//a[contains(@aria-label, 'sign in')]",
        "//a[contains(@aria-label, 'Sign in')]",
        "//span[text()='Account']"
    ]
    
    for selector in not_logged_in_selectors:
        try:
            if selector.startswith("//"):
                driver.find_element(By.XPATH, selector)
            else:
                driver.find_element(By.CSS_SELECTOR, selector)
            print(f"[debug] Detected guest/sign-in element matching: {selector}")
            return False  # Guest sign-in element found -> Not logged in!
        except NoSuchElementException:
            continue
            
    # Default to logged in if none of the sign-in/guest elements are found
    return True



def js_click(driver, element):
    driver.execute_script('arguments[0].click();', element)


def select_quantity(driver, quantity='1'):
    try:
        wait = WebDriverWait(driver, 5)
        dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.sc-10a3dac3-3.fGQZRy")))
        js_click(driver, dropdown)
        time.sleep(0.3)
        try:
            option = wait.until(EC.element_to_be_clickable((By.XPATH, f"//a[@aria-label='{quantity}']")))
            js_click(driver, option)
        except:
            available = driver.find_elements(By.XPATH, "//a[@aria-label]")
            if available:
                max_q = max([int(a.get_attribute("aria-label")) for a in available if a.get_attribute("aria-label").isdigit()])
                js_click(driver, driver.find_element(By.XPATH, f"//a[@aria-label='{max_q}']"))
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

def main(sku_input, quantity, task_id, chrome_version="auto"):
    global driver_instance, running
    print("=========================================")
    print(f"       TARGET BOT STARTED (Task: {task_id})")
    print("=========================================")
    
    # Report task start to backend
    try:
        requests.post(f"http://localhost:8000/tasks/{task_id}/log", json={}, params={"message": "Bot browser starting...", "level": "info"})
        requests.post(f"http://localhost:8000/tasks/{task_id}/status", params={"status": "running"})
    except:
        pass

    resolved_version = resolve_chrome_version(chrome_version)
    print(f"Starting browser for Target task {task_id} with Chrome version {resolved_version or 'Auto'}...")

    options = uc.ChromeOptions()
    if resolved_version:
        options.browser_version = str(resolved_version)
    # Use unique user-data-dir per task to prevent profile locking
    options.user_data_dir = f"c:\\temp\\profile_{task_id}"
    options.add_argument('--no-first-run')
    options.add_argument('--no-service-autorun')
    options.add_argument('--password-store=basic')

    if resolved_version:
        driver_instance = uc.Chrome(options=options, version_main=resolved_version)
    else:
        driver_instance = uc.Chrome(options=options)
    driver_instance.set_window_size(1280, 720)
    driver_instance.get(URL)
    time.sleep(2)

    # Check login status and pause if not logged in
    print("Checking login status...")
    if not is_logged_in(driver_instance):
        print("[!] Not logged in. Pausing for manual login...")
        try:
            requests.post(f"http://localhost:8000/tasks/{task_id}/log", json={}, params={"message": "Manual login required. Solve it in the browser, then click Resume.", "level": "error"})
            requests.post(f"http://localhost:8000/tasks/{task_id}/status", params={"status": "paused"})
        except Exception as e:
            print(f"Failed to post status/log to backend: {e}")
            
        print(">> BROWSER PAUSED <<")
        print("Please log in to your Target account in the browser window.")
        input("Press ENTER here to continue bot execution after logging in...")
        
        try:
            requests.post(f"http://localhost:8000/tasks/{task_id}/status", params={"status": "running"})
        except Exception as e:
            print(f"Failed to update status to backend: {e}")
    else:
        print("[+] Already logged in!")

    # Note: Session loading logic would need adjustment to match the dynamic profile directory
    
    sku = sku_input
    print(f"Searching for SKU {sku} like a human...")
    driver_instance.get("https://www.target.com/")
    time.sleep(random.randint(2, 4))
    
    try:
        wait = WebDriverWait(driver_instance, 10)
        search_box = wait.until(EC.presence_of_element_located((By.ID, "search")))
        search_box.clear()
        for char in sku:
            search_box.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))
        time.sleep(1)
        search_box.send_keys(Keys.ENTER)
        
        time.sleep(random.randint(3, 5))
        # Wait for product grid and click first item link
        first_product_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-test='@web/site-top-of-funnel/ProductCardWrapper'] a")))
        js_click(driver_instance, first_product_link)
        print(f"Navigated to first search result for SKU {sku}")
        time.sleep(random.randint(2, 4))
    except Exception as e:
        print(f"Error checking stock/adding to cart: {str(e)}")
        try:
            requests.post(f"http://localhost:8000/tasks/{task_id}/log", json={}, params={"message": f"Error or Captcha detected. Waiting for manual intervention: {str(e)}", "level": "error"})
            requests.post(f"http://localhost:8000/tasks/{task_id}/status", params={"status": "paused"})
        except:
            pass
        print(">> BROWSER PAUSED <<")
        print("If there is a Captcha or error, please solve it manually in the browser window.")
        input("Press ENTER here to continue bot execution after solving...")
        try:
            requests.post(f"http://localhost:8000/tasks/{task_id}/status", params={"status": "running"})
        except:
            pass
            
    while True:
                driver_instance.refresh()
                print(f"[+] Refreshing page for SKU {sku}...")
                try:
                    button_text = None
                    try:
                        btn = driver_instance.find_element(By.XPATH, "//button[contains(text(),'Add to cart')]")
                        button_text = 'Add to cart'
                    except:
                        btn = driver_instance.find_element(By.XPATH, "//button[text()='Preorder']")
                        button_text = 'Preorder'
                    js_click(driver_instance, btn)
                    if button_text:
                        print(f"[+] Clicked {button_text} for SKU {sku}")
                except:
                    print(f"[!] Add to cart/Preorder button not found for SKU {sku}, retrying...")
                    time.sleep(1)
                    pass
                try:
                    element = driver_instance.find_element(By.CSS_SELECTOR, 'button[data-test="custom-quantity-picker"]')
                    if 'in cart' in element.text.lower():
                        break
                except:
                    pass
                time.sleep(random.randint(3,5))
                
                
    print(f"[+] Added SKU {sku} (x{quantity}) to cart.")
    driver_instance.get('https://www.target.com/checkout')
    time.sleep(2)
    wait = WebDriverWait(driver_instance, 5)
    
    # ... (Checkout logic remains largely the same) ...

    print(f"Done.")
    input('Press Enter to close browser...')
    driver_instance.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Target Auto Checkout Bot")
    parser.add_argument("--sku", type=str, required=True, help="SKU to monitor")
    parser.add_argument("--quantity", type=int, default=1, help="Quantity to buy")
    parser.add_argument("--task_id", type=int, required=True, help="Backend Task ID")
    parser.add_argument("--chrome-version", type=str, default="auto", help="Chrome major version")
    
    args = parser.parse_args()
    
    running = True
    main(args.sku, args.quantity, args.task_id, args.chrome_version)
    running = False
    if driver_instance:
        try:
            driver_instance.quit()
        except Exception:
            pass
