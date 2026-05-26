import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import csv
from bs4 import BeautifulSoup
import json
import undetected_chromedriver as uc
import argparse
import requests

# # Credentials
# username = "Blake.Cecil18@gmail.com"
# password = "bozkoQ-zaqpaj-dudka5"
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
    # Report task start to backend
    try:
        requests.post(f"http://localhost:8000/tasks/{task_id}/log", json={}, params={"message": "Bot browser starting...", "level": "info"})
        requests.post(f"http://localhost:8000/tasks/{task_id}/status", params={"status": "running"})
    except:
        pass

    # Load config
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Warning: Could not load config.json: {e}")
        config = {"card_number": "", "expiry": "", "cvv": ""}

    resolved_version = resolve_chrome_version(chrome_version)
    print(f"Starting browser for BestBuy task {task_id} with Chrome version {resolved_version or 'Auto'}...")
    
    options = uc.ChromeOptions()
    if resolved_version:
        options.browser_version = str(resolved_version)
    options.user_data_dir = f"c:\\temp\\profile_{task_id}"
    options.add_argument('--no-first-run')
    options.add_argument('--no-service-autorun')
    options.add_argument('--password-store=basic')
    
    if resolved_version:
        driver = uc.Chrome(options=options, version_main=resolved_version)
    else:
        driver = uc.Chrome(options=options)
    driver.get("https://www.bestbuy.com")
    print("Browser opened.")
    # Handle country selector if it appears
    try:
        us_link = driver.find_elements(By.CSS_SELECTOR, "a.us-link")
        if us_link:
            print("Clicking US country selector...")
            us_link[0].click()
            time.sleep(random.uniform(2, 4))
    except Exception as e:
        print(f"Note: Country selector handling skipped: {e}")

    # Check for 'Sign in' or 'Account' to determine if manual login is needed
    # Using find_elements to avoid NoSuchElementException if the element isn't present
    print("Checking login status...")
    login_elements = driver.find_elements(By.XPATH, "//span[contains(text(), 'Sign in') or contains(text(), 'Sign In') or contains(text(), 'Account')]")
    
    if login_elements:
        # If 'Account' is found, we might still need to check if it's already logged in
        # For simplicity, if we see 'Sign in', we definitely need login.
        needs_login = any("Sign in" in el.text or "Sign In" in el.text for el in login_elements)
        if needs_login:
            try:
                requests.post(f"http://localhost:8000/tasks/{task_id}/log", json={}, params={"message": "Manual login required. Solve it in the browser, then click Resume.", "level": "error"})
                requests.post(f"http://localhost:8000/tasks/{task_id}/status", params={"status": "paused"})
            except:
                pass
            input('Please login manually and click enter here...')
            try:
                requests.post(f"http://localhost:8000/tasks/{task_id}/status", params={"status": "running"})
            except:
                pass
    
    print('Login check complete.')
    
    # --- Search Functionality ---
    sku = sku_input
    if sku:
        try:
            print(f"Searching for: {sku}")
            # Use WebDriverWait to ensure the search bar is ready
            wait = WebDriverWait(driver, 15)
            search_bar = wait.until(EC.presence_of_element_located((By.ID, "autocomplete-search-bar")))
            
            search_bar.clear()
            search_bar.send_keys(sku)
            
            # Click the search button
            search_button = driver.find_element(By.ID, "autocomplete-search-button")
            search_button.click()
            
            print("Search submitted. Waiting for results...")
            time.sleep(random.uniform(3, 6))
            
            # --- Add to Cart Logic ---
            initial_url = driver.current_url
            print("Looking for 'Add to cart' buttons. Will keep clicking until URL changes or success message appears (Unlimited attempts)...")
            
            attempt = 0
            success = False
            
            while not success:
                attempt += 1
                try:
                    # 1. Check for "Added to cart" success message (H2 element)
                    success_elements = driver.find_elements(By.XPATH, "//h2[contains(@class, 'large') and contains(text(), 'Added to cart')]")
                    if any(el.is_displayed() for el in success_elements):
                        print("SUCCESS: 'Added to cart' message detected!")
                        success = True
                        break
                    
                    # 2. Check if URL changed
                    if driver.current_url != initial_url:
                        print(f"SUCCESS: URL changed to {driver.current_url}")
                        success = True
                        break

                    # 3. Find 'Add to cart' buttons
                    # Prioritize buttons with 'add-to-cart' in data-testid or ID
                    buttons = driver.find_elements(By.XPATH, "//button[contains(@data-testid, 'add-to-cart') or contains(@id, 'add-to-cart') or contains(., 'Add to cart')]")
                    
                    # Filter to only visible buttons to avoid clicking hidden elements or dozens of recommendations
                    visible_buttons = []
                    for b in buttons:
                        try:
                            if b.is_displayed():
                                visible_buttons.append(b)
                        except:
                            continue
                    
                    if not visible_buttons:
                        print(f"Attempt {attempt}: No visible 'Add to cart' buttons found. Waiting...")
                        time.sleep(2)
                        continue
                    
                    # Focus on the first 1-2 buttons found (usually the main ones)
                    # This prevents the script from clicking 50+ recommendation buttons
                    target_buttons = visible_buttons[:2]
                    print(f"Attempt {attempt}: Found {len(visible_buttons)} visible button(s). Trying top {len(target_buttons)}.")
                    
                    for i, btn in enumerate(target_buttons):
                        try:
                            print(f"Trying to click button at index {i}...")
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                            time.sleep(1)
                            
                            driver.execute_script("arguments[0].click();", btn)
                            print(f"Clicked button at index {i}. Checking status...")
                            
                            time.sleep(3) # Wait for page to update
                            
                            # Check for success immediately after click
                            if driver.current_url != initial_url:
                                success = True
                                break
                            
                            success_elements = driver.find_elements(By.XPATH, "//h2[contains(text(), 'Added to cart')]")
                            if any(el.is_displayed() for el in success_elements):
                                success = True
                                break
                        except Exception as inner_e:
                            print(f"Failed to click button at index {i}: {inner_e}")
                            continue
                    
                    if success:
                        break 
                except Exception as e:
                    print(f"Error during interaction loop: {e}")
                    time.sleep(2)
            
            if success:
                print("Item successfully added to cart! Proceeding to checkout...")
                driver.get("https://www.bestbuy.com/checkout/r/payment")
                time.sleep(5) 
                
                try:
                    print("Filling in payment details...")
                    wait_checkout = WebDriverWait(driver, 20)
                    
                    # Card Number
                    card_input = wait_checkout.until(EC.presence_of_element_located((By.ID, "number")))
                    card_input.send_keys(config['card_number'])
                    
                    # Expiration Date
                    exp_input = driver.find_element(By.ID, "expirationDate")
                    exp_input.send_keys(config['expiry'])
                    
                    # Security Code (CVV)
                    cvv_input = driver.find_element(By.ID, "cvv")
                    cvv_input.send_keys(config['cvv'])
                    
                    print("Payment details filled.")
                    
                    # Agree to terms (dynamic ID, so we use the label text)
                    try:
                        print("Agreeing to terms...")
                        terms_label = driver.find_element(By.XPATH, "//label[contains(., 'I agree to enroll in automatic renewal')]")
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", terms_label)
                        time.sleep(1)
                        terms_label.click()
                    except Exception as e:
                        print(f"Note: Terms checkbox not found or already checked: {e}")
                    
                    # Scroll and Click 'Place Your Order'
                    try:
                        print("Looking for 'Place Your Order' button. Will keep clicking until it's gone or URL changes...")
                        initial_checkout_url = driver.current_url
                        
                        while True:
                            # Re-find buttons to handle re-renders
                            place_order_buttons = driver.find_elements(By.XPATH, "//button[contains(., 'Place Your Order')]")
                            
                            # Filter to visible ones
                            visible_place_buttons = [b for b in place_order_buttons if b.is_displayed()]
                            
                            if not visible_place_buttons:
                                print("'Place Your Order' button is no longer visible or available.")
                                break
                            
                            # Check if URL changed (indicates success)
                            if driver.current_url != initial_checkout_url:
                                print(f"URL changed to {driver.current_url}. Assuming order placed.")
                                break
                            
                            try:
                                btn = visible_place_buttons[0]
                                print("Clicking 'Place Your Order'...")
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                time.sleep(1)
                                driver.execute_script("arguments[0].click();", btn)
                                
                                # Wait to see reaction
                                time.sleep(4)
                            except Exception as inner_e:
                                print(f"Failed to interact with 'Place Your Order' button: {inner_e}")
                                time.sleep(2)
                                
                        print("Order placement process finished.")
                    except Exception as e:
                        print(f"Could not find or click 'Place Your Order' button: {e}")
                        
                except Exception as e:
                    print(f"Error during checkout flow: {e}")
            else:
                print("Finished attempts. Item may not have been added.")
            # -------------------------
        except Exception as e:
            print(f"Error during search: {e}")
            try:
                requests.post(f"http://localhost:8000/tasks/{task_id}/log", json={}, params={"message": f"Error or Captcha detected. Waiting for manual intervention: {str(e)}", "level": "error"})
                requests.post(f"http://localhost:8000/tasks/{task_id}/status", params={"status": "paused"})
            except:
                pass
            print(">> BROWSER PAUSED <<")
            input("If there is a Captcha or error, please solve it manually in the browser window. Press ENTER here to continue...")
            try:
                requests.post(f"http://localhost:8000/tasks/{task_id}/status", params={"status": "running"})
            except:
                pass
    
    try:
        requests.post(f"http://localhost:8000/tasks/{task_id}/log", json={}, params={"message": "Task Finished", "level": "success"})
        requests.post(f"http://localhost:8000/tasks/{task_id}/status", params={"status": "completed"})
    except:
        pass
    print("\nBrowser is now staying open.")
    input("Press Enter here when you are ready to close the browser...")
    
    print("Closing browser...")
    driver.quit()
    print("Browser closed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BestBuy Auto Checkout Bot")
    parser.add_argument("--sku", type=str, required=True, help="SKU to monitor")
    parser.add_argument("--quantity", type=int, default=1, help="Quantity to buy")
    parser.add_argument("--task_id", type=int, required=True, help="Backend Task ID")
    parser.add_argument("--chrome-version", type=str, default="auto", help="Chrome major version")
    
    args = parser.parse_args()
    main(args.sku, args.quantity, args.task_id, args.chrome_version)