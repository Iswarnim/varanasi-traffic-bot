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

# 1. SETUP THE BASELINES (Your Exact Observations)
ROUTES = [
    {
        "name": "Maidagin -> Vishwanath", 
        "origin": "Maidagin Crossing, Varanasi", 
        "dest": "Kashi Vishwanath Gate 4, Varanasi",
        "baseline": 7  # Observed Min: 7 min
    },
    {
        "name": "Godowlia -> Maidagin", 
        "origin": "Godowlia Crossing, Varanasi", 
        "dest": "Maidagin Crossing, Varanasi",
        "baseline": 5  # Observed Min: 5 min
    },
    {
        "name": "Maidagin -> Kaal Bhairav", 
        "origin": "Maidagin Crossing, Varanasi", 
        "dest": "Kaal Bhairav Mandir, Varanasi",
        "baseline": 3  # Observed Min: 3 min
    },
    {
        "name": "Godowlia -> Sankat Mochan", 
        "origin": "Godowlia Crossing, Varanasi", 
        "dest": "Sankat Mochan Hanuman Mandir, Varanasi",
        "baseline": 12 # Observed Min: 12 min
    },
    {
        "name": "Godowlia -> Dashashwamedh", 
        "origin": "Godowlia Crossing, Varanasi", 
        "dest": "Dashashwamedh Ghat, Varanasi",
        "baseline": 5  # Observed Min: 5 min
    }
]

def get_ist_time():
    # Convert UTC to Indian Standard Time (+5:30)
    utc_now = datetime.utcnow()
    ist_now = utc_now + timedelta(hours=5, minutes=30)
    return ist_now.strftime("%Y-%m-%d %H:%M:%S")

def run_bot():
    print("--- ☁️ Starting Math-Based Robot ---")
    
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    # Masking as a real browser to prevent Google hiding data
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    
    driver = webdriver.Chrome(options=options)
    
    current_data = []
    
    try:
        for route in ROUTES:
            origin = route['origin'].replace(" ", "+")
            dest = route['dest'].replace(" ", "+")
            
            # Force CAR mode (!3e0) to ensure consistent baselines
            url = f"https://www.google.com/maps/dir/{origin}/{dest}/data=!4m2!4m1!3e0"
            
            driver.get(url)
            time.sleep(3)
            
            current_min = 0
            
            try:
                # 1. EXTRACT TIME TEXT
                time_text = ""
                try:
                    # Look for the main time display
                    el = driver.find_element(By.XPATH, "//div[contains(@class, 'Fk3sm') or contains(@class, 'Os01j')]")
                    time_text = el.text
                except:
                    # Backup method: Find any text with 'min'
                    els = driver.find_elements(By.XPATH, "//div[contains(text(), 'min')]")
                    for e in els:
                        # Ensure it's a short duration string (e.g. "5 min") not a sentence
                        if len(e.text) < 12 and any(c.isdigit() for c in e.text):
                            time_text = e.text
                            break
                
                # 2. EXTRACT NUMBER
                # Converts "5 min" -> 5
                numbers = re.findall(r'\d+', time_text)
                if numbers:
                    current_min = int(numbers[0])
                    
            except Exception as e:
                print(f"Error reading {route['name']}: {e}")

            # 3. CALCULATE DELAY AND STATUS
            baseline = route['baseline']
            delay = 0
            status = "Unknown"
            
            if current_min > 0:
                delay = current_min - baseline
                
                # If Google is faster than your baseline, set delay to 0
                if delay < 0: 
                    delay = 0
                
                # --- STATUS LOGIC ---
                # Pure Math. No scraping "Red" text.
                if delay == 0:
                    status = "🟢 Clear"
                elif delay >= 2 and delay >= (baseline * 0.3): 
                    # If delay is 2+ mins AND 30% slower than normal
                    status = "🔴 Heavy"
                else:
                    status = "🟡 Moderate"
            
            print(f"📍 {route['name']}: {current_min} min (Base: {baseline}) -> Delay: {delay}")
            
            current_data.append({
                "timestamp": get_ist_time(),
                "route_name": route['name'],
                "total_time_min": current_min,  # The total time Google shows
                "delay_min": delay,             # The traffic delay (Current - Baseline)
                "status": status                # Calculated mathematically
            })
            
    finally:
        driver.quit()
        
    if current_data:
        df = pd.DataFrame(current_data)
        # Check if file exists to write headers only once
        header = not os.path.exists(FILE_NAME)
        df.to_csv(FILE_NAME, mode='a', header=header, index=False)
        print("✅ Data saved.")

if __name__ == "__main__":
    run_bot()
