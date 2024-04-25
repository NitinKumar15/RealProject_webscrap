from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime
import json
import os
import glob
import time
import random
import sys

# Function to check if any downloads are in progress in `download_dir`
def downloads_in_progress(download_dir):
    return any(glob.glob(os.path.join(download_dir, '*.crdownload')))

def fetch_id(id_, file_names_by_id,c):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    download_dir = "./verra-afolu-pdd"
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
    })

    driver = webdriver.Chrome(options=chrome_options)
    full_url = f"https://registry.verra.org/app/projectDetail/VCS/{id_}"
    driver.get(full_url)
    print(id_, flush=True)

    try:
        element_present = EC.presence_of_element_located((By.XPATH, "//div[text()='VCS Pipeline Documents']/.."))
        WebDriverWait(driver, 50).until(element_present)
    except TimeoutException:
        print(f"Timed out waiting for page to load for ID {id_}")
        driver.quit()
        return

    try:
        vcs_card = driver.find_element(By.XPATH, "//div[text()='VCS Pipeline Documents']/..")
        pdf_elements = vcs_card.find_elements(By.XPATH, ".//a[contains(@href, 'FileID')]")
        file_names = []

        # for pdf_element in pdf_elements:
        #     file_name = pdf_element.text
        #     file_names.append(file_name)

        #     pdf_link = pdf_element.get_attribute('href')
        #     driver.get(pdf_link)  # This will download the file
        
        for idx, pdf_element in enumerate(pdf_elements):
            if idx == 0:
            
                # Extracting the date from the HTML
                date_element = driver.find_element(By.XPATH, ".//following-sibling::td[@class='pr-3 text-right']")
                date_str = date_element.text
                # print(date_str)
                date = datetime.strptime(date_str, "%d/%m/%Y")
                # print(date)

                # Check if the date is after 01/08/2023
                if date > datetime(2023, 8, 1):
                    c+=1
                    
                    file_name = pdf_element.text
                    file_names.append(file_name)
                    pdf_link = pdf_element.get_attribute('href')
                    print("pdf_link-",pdf_link)
                    driver.get(pdf_link)  # This will download the file
                    print(f"total={c}")
            


        file_names_by_id[id_] = file_names

        # Wait until all downloads are complete
        while downloads_in_progress(download_dir):
            time.sleep(2)  # Wait for 2 seconds before checking again

    except Exception as e:
        print(f"Could not find or download PDFs for ID {id_}. Error: {e}")

    driver.quit()
    
def save_to_json(data, file_path):
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Data saved to {file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

def read_from_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def start_process():
    try:
        ids = read_from_json('verra_afolu_ids.json')
    except FileNotFoundError:
        print("File 'verra_afolu_ids.json' not found!")
        return
    
    file_names_by_id = {}
    error_log = {}
    c=0
    for count, id_ in enumerate(ids[:], start=1):  # using ids[:] to create a copy of ids
        try:
           
            fetch_id(id_, file_names_by_id,c)
            ids.remove(id_)  # Remove id_ from ids list after successful processing
            save_to_json(ids, 'verra_remaining_ids.json')  # Save remaining ids to json
        except Exception as e:
            error_log[id_] = str(e)  # Log the exception and continue with the next id_
            print(f"Error processing ID {id_}: {e}")
            continue
        
        # After every 50 requests, wait for a random amount of time between 1 to 5 minutes
        if count % 50 == 0:
            wait_time = random.randint(300, 600)
            print(f"Waiting for {wait_time/60:.2f} minutes after processing {count} ids...")
            time.sleep(wait_time)
    
    save_to_json(file_names_by_id, 'file_names_by_id.json')
    save_to_json(error_log, 'verra_error_log.json')  # Save error log to json
    for id_, file_names in file_names_by_id.items():
        print(f"File names for ID {id_}: {file_names}")

if __name__ == "__main__":
    start_process()