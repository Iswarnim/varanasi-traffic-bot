from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
import os
import re
from datetime import datetime

# ================= CONFIGURATION =================
FILE_NAME = "varanasi_traffic_data.csv"

# Updated Route List
ROUTES = [
    # --- OLD ROUTES ---
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
    
    # --- NEW REQUESTED ROUTES ---
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

def run_bot():
    print("--- ☁️ Starting Cloud Robot (Time + Distance) ---")
    
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=options)
    
    current_data = []
    
    try:
        for route in ROUTES:
            origin = route['origin'].replace(" ", "+")
            dest = route['dest'].replace(" ", "+")
            url = f"https://www.google.com/maps/dir/{origin}/{dest}"
            
            driver.get(url)
            time.sleep(3) # Wait for load
            
            found_time = "Error"
            found_dist = "Error"
            status = "Unknown"
            
            try:
                # 1. EXTRACT TIME (Primary Method)
                time_el = driver.find_element(By.XPATH, "//div[contains(@class, 'Fk3sm') or contains(@class, 'Os01j')]")
                found_time = time_el.text
                
                # 2. EXTRACT DISTANCE (New Feature)
                # Distance is usually in a div right next to the time or inside the trip summary
                # We look for any text containing "km" or "m" in the summary card
                summary_el = driver.find_element(By.XPATH, "//div[contains(@id, 'section-directions-trip-0')]")
                text_content = summary_el.text
                
                # Regex to find distance (e.g., "1.2 km" or "850 m")
                dist_match = re.search(r'(\d+[\.,]?\d*\s?(km|m))', text_content)
                if dist_match:
                    found_dist = dist_match.group(0)
                    
            except:
                # Fallback Search
                try:
                    els = driver.find_elements(By.XPATH, "//div")
                    for e in els:
                        txt = e.text
                        # Look for time
                        if "min" in txt and len(txt) < 10 and any(c.isdigit() for c in txt):
                            found_time = txt
                        # Look for distance
                        if ("km" in txt or " m" in txt) and len(txt) < 10 and any(c.isdigit() for c in txt):
                            found_dist = txt
                except:
                    pass

            # 3. CAPTURE TRAFFIC STATUS (Color)
            src = driver.page_source.lower()
            if "heavy traffic" in src or "red" in src: status = "🔴 Heavy"
            elif "light traffic" in src or "orange" in src: status = "🟡 Moderate"
            else: status = "🟢 Clear"
            
            print(f"📍 {route['name']}: {found_time} | {found_dist} | {status}")
            
            current_data.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "route_name": route['name'],
                "duration": found_time,
                "distance": found_dist, # Added this column
                "status": status
            })
            
    finally:
        driver.quit()
        
    # Save Data
    if current_data:
        df = pd.DataFrame(current_data)
        header = not os.path.exists(FILE_NAME)
        df.to_csv(FILE_NAME, mode='a', header=header, index=False)
        print("✅ Data saved.")

if __name__ == "__main__":
    run_bot()
