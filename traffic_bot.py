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
    # --- ORIGINAL ROUTES ---
    {
        "name": "Maidagin -> Vishwanath", 
        "origin": "Maidagin Crossing, Varanasi", 
        "dest": "Kashi Vishwanath Gate 4, Varanasi",
        "baseline": 7
    },
    {
        "name": "Godowlia -> Maidagin", 
        "origin": "Godowlia Crossing, Varanasi", 
        "dest": "Maidagin Crossing, Varanasi",
        "baseline": 5
    },
    {
        "name": "Maidagin -> Kaal Bhairav", 
        "origin": "Maidagin Crossing, Varanasi", 
        "dest": "Kaal Bhairav Mandir, Varanasi",
        "baseline": 3
    },
    {
        "name": "Godowlia -> Sankat Mochan", 
        "origin": "Godowlia Crossing, Varanasi", 
        "dest": "Sankat Mochan Hanuman Mandir, Varanasi",
        "baseline": 12
    },
    {
        "name": "Godowlia -> Dashashwamedh", 
        "origin": "Godowlia Crossing, Varanasi", 
        "dest": "Dashashwamedh Ghat, Varanasi",
        "baseline": 5
    },

    # --- NEW ADDED ROUTES ---
    {
        "name": "Cantt -> Godowlia", 
        "origin": "Varanasi Junction railway station", # Cantt Station
        "dest": "Godowlia Crossing, Varanasi",
        "baseline": 15 # Estimated Min: 15 min (Long route)
    },
    {
        "name": "Lanka -> Assi Ghat", 
        "origin": "Lanka Gate, BHU, Varanasi", 
        "dest": "Assi Ghat, Varanasi",
        "baseline": 6 # Estimated Min: 6 min
    },
    {
        "name": "Rathyatra -> Godowlia", 
        "origin": "Rathyatra Crossing, Varanasi", 
        "dest": "Godowlia Crossing, Varanasi",
        "baseline": 8 # Estimated Min: 8 min
    }
]

def get_ist_time():
    utc_now = datetime.utcnow()
    ist_now = utc_now + timedelta(hours=5, minutes=30)
    return ist_now.strftime("%Y-%m-%d %H:%M:%S")

def run_bot():
    print("--- ☁️ Starting Smart Cloud Robot ---")
    
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    
    driver = webdriver.Chrome(options=options)
    
    current_data = []
    
    try:
        for route in ROUTES:
            origin = route['origin'].replace(" ", "+")
            dest = route['dest'].replace(" ", "+")
            
            url = f"https://www.google.com/maps/dir/{origin}/{dest}/data=!4m2!4m1!3e0"
            
            driver.get(url)
            time.sleep(2) # Speed up slightly since we have more routes now
            
            current_min = 0
            
            try:
                # Extract Time
                time_text = ""
                try:
                    el = driver.find_element(By.XPATH, "//div[contains(@class, 'Fk3sm') or contains(@class, 'Os01j')]")
                    time_text = el.text
                except:
                    els = driver.find_elements(By.XPATH, "//div[contains(text(), 'min')]")
                    for e in els:
                        if len(e.text) < 12 and any(c.isdigit() for c in e.text):
                            time_text = e.text
                            break
                
                numbers = re.findall(r'\d+', time_text)
                if numbers:
                    current_min = int(numbers[0])
                    
            except Exception as e:
                print(f"Error on {route['name']}: {e}")

            # Calculate Status
            baseline = route['baseline']
            delay = 0
            status = "Unknown"
            
            if current_min > 0:
                delay = current_min - baseline
                if delay < 0: delay = 0
                
                if delay == 0:
                    status = "🟢 Clear"
                elif delay >= 2 and delay >= (baseline * 0.3): 
                    status = "🔴 Heavy"
                else:
                    status = "🟡 Moderate"
            
            print(f"📍 {route['name']}: {current_min} min (Base: {baseline}) -> Delay: {delay}")
            
            current_data.append({
                "timestamp": get_ist_time(),
                "route_name": route['name'],
                "total_time_min": current_min,
                "delay_min": delay,
                "status_calculated": status
            })
            
    finally:
        driver.quit()
        
    if current_data:
        df = pd.DataFrame(current_data)
        header = not os.path.exists(FILE_NAME)
        df.to_csv(FILE_NAME, mode='a', header=header, index=False)
        print("✅ Data saved.")

if __name__ == "__main__":
    run_bot()
