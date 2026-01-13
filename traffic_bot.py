from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
import os
from datetime import datetime

# Routes Configuration
ROUTES = [
    {"name": "Maidagin -> Vishwanath", "origin": "Maidagin Crossing, Varanasi", "dest": "Kashi Vishwanath Gate 4, Varanasi"},
    {"name": "Lanka -> Sankat Mochan", "origin": "Lanka Gate, BHU, Varanasi", "dest": "Sankat Mochan Hanuman Mandir, Varanasi"},
    {"name": "Godowlia -> Maidagin", "origin": "Godowlia Crossing, Varanasi", "dest": "Maidagin Crossing, Varanasi"}
]

FILE_NAME = "varanasi_traffic_data.csv"

def run_bot():
    print("--- ☁️ Starting Cloud Robot ---")
    
    # Cloud-Optimized Chrome Options
    options = Options()
    options.add_argument("--headless=new") # Must be headless in cloud
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage") # Overcome limited resource problems
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
            
            # Extract Time
            found_time = "Error"
            status = "Unknown"
            try:
                # Primary Strategy
                el = driver.find_element(By.XPATH, "//div[contains(@class, 'Fk3sm') or contains(@class, 'Os01j')]")
                found_time = el.text
            except:
                # Fallback
                try:
                    els = driver.find_elements(By.XPATH, "//div[contains(text(), 'min')]")
                    for e in els:
                        if any(c.isdigit() for c in e.text):
                            found_time = e.text
                            break
                except:
                    pass

            # Status Check
            src = driver.page_source.lower()
            if "heavy traffic" in src or "red" in src: status = "🔴 Heavy"
            elif "light traffic" in src or "orange" in src: status = "🟡 Moderate"
            else: status = "🟢 Clear"
            
            print(f"📍 {route['name']}: {found_time}")
            
            current_data.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "route_name": route['name'],
                "duration": found_time,
                "status": status
            })
            
    finally:
        driver.quit()
        
    # Save Data (Append Mode)
    if current_data:
        df = pd.DataFrame(current_data)
        # Check if file exists to determine header
        header = not os.path.exists(FILE_NAME)
        df.to_csv(FILE_NAME, mode='a', header=header, index=False)
        print("✅ Data saved locally (ready for git push)")

if __name__ == "__main__":
    run_bot()