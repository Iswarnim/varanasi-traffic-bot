from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
import os
import re
from datetime import datetime, timedelta

# ================= CONFIGURATION =================
FILE_NAME = "varanasi_traffic_data.csv"

ROUTES = [
    {
        "name": "Maidagin -> Vishwanath", 
        "origin": "Maidagin Crossing, Varanasi", 
        "dest": "Kashi Vishwanath Gate 4, Varanasi"
    },
    {
        "name": "Godowlia -> Maidagin", 
        "origin": "Godowlia Crossing, Varanasi", 
        "dest": "Maidagin Crossing, Varanasi"
    },
    {
        "name": "Maidagin -> Kaal Bhairav", 
        "origin": "Maidagin Crossing, Varanasi", 
        "dest": "Kaal Bhairav Mandir, Varanasi"
    },
    {
        "name": "Godowlia -> Sankat Mochan", 
        "origin": "Godowlia Crossing, Varanasi", 
        "dest": "Sankat Mochan Hanuman Mandir, Varanasi"
    },
    {
        "name": "Godowlia -> Dashashwamedh", 
        "origin": "Godowlia Crossing, Varanasi", 
        "dest": "Dashashwamedh Ghat, Varanasi"
    }
]

def get_ist_time():
    utc_now = datetime.utcnow()
    ist_now = utc_now + timedelta(hours=5, minutes=30)
    return ist_now.strftime("%Y-%m-%d %H:%M:%S")

def run_bot():
    print("--- ☁️ Starting Cloud Robot (Forced CAR Mode) ---")
    
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    # Faking User-Agent to look like a real browser, not a bot
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    
    driver = webdriver.Chrome(options=options)
    
    current_data = []
    
    try:
        for route in ROUTES:
            origin = route['origin'].replace(" ", "+")
            dest = route['dest'].replace(" ", "+")
            
            # --- THE FIX: NEW URL STRUCTURE ---
            # /dir/Origin/Dest/data=!4m2!4m1!3e0
            # !3e0 = Driving (Car)
            # !3e1 = Two-Wheeler (Bike) - GitHub US servers might ignore this, so we use CAR for consistency.
            url = f"https://www.google.com/maps/dir/{origin}/{dest}/data=!4m2!4m1!3e0"
            
            driver.get(url)
            time.sleep(5) # Give the new heavy URL more time to load
            
            found_time = "Error"
            found_dist = "Error"
            status = "Unknown"
            
            try:
                # 1. EXTRACT TIME (Updated for new UI)
                # In the new URL view, the time is often in a specific 'h1' or large div
                try:
                    # Look for the large bold time
                    time_el = driver.find_element(By.XPATH, "//div[contains(@class, 'Fk3sm') or contains(@class, 'Os01j')]")
                    found_time = time_el.text
                except:
                    # Backup: finding the first minute marker
                    els = driver.find_elements(By.XPATH, "//div[contains(text(), 'min')]")
                    for e in els:
                         # Filter: Must be short, have digits, and not be part of a sentence
                        if len(e.text) < 12 and any(c.isdigit() for c in e.text):
                            found_time = e.text
                            break
                
                # 2. EXTRACT DISTANCE
                try:
                    # Look for distance near the time
                    summary_el = driver.find_element(By.XPATH, "//div[contains(@id, 'section-directions-trip-0')]")
                    text_content = summary_el.text
                    dist_match = re.search(r'(\d+[\.,]?\d*\s?(km|m))', text_content)
                    if dist_match:
                        found_dist = dist_match.group(0)
                except:
                    pass
                    
            except Exception as e:
                print(f"Extraction Error: {e}")

            # 3. CAPTURE TRAFFIC STATUS
            src = driver.page_source.lower()
            if "heavy traffic" in src or "red" in src: status = "🔴 Heavy"
            elif "light traffic" in src or "orange" in src: status = "🟡 Moderate"
            else: status = "🟢 Clear"
            
            print(f"📍 {route['name']}: {found_time} | {found_dist} | {status}")
            
            current_data.append({
                "timestamp": get_ist_time(),
                "route_name": route['name'],
                "duration": found_time,
                "distance": found_dist,
                "status": status
            })
            
    finally:
        driver.quit()
        
    if current_data:
        df = pd.DataFrame(current_data)
        header = not os.path.exists(FILE_NAME)
        df.to_csv(FILE_NAME, mode='a', header=header, index=False)
        print("✅ Data saved with Consistent Car Mode.")

if __name__ == "__main__":
    run_bot()
