import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException


def create_driver():
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    options.add_experimental_option("prefs", {
        "download.default_directory": "/tmp",  
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })

    return webdriver.Chrome(
        service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()),
        options=options,
    )

def login_and_navigate(driver):
    driver.get("https://publisher.smallcase.com/login")

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//input[@type='email']")))
    email_input = driver.find_element(By.XPATH, "//input[@type='email']")
    email_input.send_keys('manju@armstrong-cap.com')

    password_input = driver.find_element(By.XPATH, "//input[@type='password']")
    password_input.send_keys('Manju9')

    submit = driver.find_element(By.XPATH, "//input[@type='submit']")
    submit.click()

    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input.login__login-text-pwd__11RBh")))
    inputs = driver.find_elements(By.CSS_SELECTOR, "input.login__login-text-pwd__11RBh")

    inputs[0].send_keys("Vennela")
    inputs[1].send_keys("Bangalore")

    submit = driver.find_element(By.XPATH, "//input[@type='submit']")
    submit.click()

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.LINK_TEXT, "Other smallcases")))
    other_tab = driver.find_element(By.LINK_TEXT, "Other smallcases")
    other_tab.click()


def scrape_smallcase_data(driver, user_input):
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, 'NameHolder__smallcase-title__1FfWo')))
    elements = driver.find_elements(By.CLASS_NAME, 'NameHolder__smallcase-title__1FfWo')

    for element in elements:
        if user_input in element.text:
            element.click()
            break
    else:
        return None, None

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//div[text()='Constituents & Weights']")))
    constituents_tab = driver.find_element(By.XPATH, "//div[text()='Constituents & Weights']")
    constituents_tab.click()

    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, 'StockSegmentTable__segment-header__2JvNB')))
    sectorheader = driver.find_elements(By.CLASS_NAME, 'StockSegmentTable__segment-header__2JvNB')
    stockheader = driver.find_elements(By.CLASS_NAME, "StockSegmentTable__constituent__2k58o")

    sector_data = [sector.text.split('\n') for sector in sectorheader]
    stock_data = [stock.text.split('\n') for stock in stockheader]

    sectordf = pd.DataFrame(sector_data, columns=['SECTOR', 'SR_ALLOCATION'])
    stockdf = pd.DataFrame(stock_data, columns=['STOCK', 'SK_ALLOCATION'])

    if sectordf is not None and stockdf is not None:
        st.session_state.sectordf = sectordf
        st.session_state.stockdf = stockdf

    return sectordf, stockdf

def fetch_data(user_input):
    driver = create_driver()
    try:
        login_and_navigate(driver)
        sectordf, stockdf = scrape_smallcase_data(driver, user_input)
        return sectordf, stockdf
    except WebDriverException as e:
        print(f"An error occurred: {str(e)}")
        return None, None
    finally:
        driver.quit()

def process_list(input_list):
    results_dict = {}
    for user_input in input_list:
        sectordf, stockdf = fetch_data(user_input)
        if sectordf is not None and stockdf is not None:
            results_dict[user_input] = {"sector_data": sectordf, "stock_data": stockdf}
    return results_dict

input_list = ["Gulaq Gear 4 Quant", "Gulaq Gear 5 Quant", "Gulaq Gear 6 Quant"]
# Store results in a dictionary
results_dict = process_list(input_list)

# Display results in Streamlit
for key, value in results_dict.items():
    st.write(f"**{key}**")
    st.write("**Sector Data:**")
    st.write(value["sector_data"])
    st.write("**Stock Data:**")
    st.write(value["stock_data"])
