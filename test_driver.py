from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import undetected_chromedriver as uc
uc.install()

WINDOW_SIZE = "1920,1080"
chromedriverPath = "/bin/chromedriver"
chrome_options = uc.ChromeOptions()
#chrome_options.add_argument("--headless")
#chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36")
driver = webdriver.Chrome(executable_path=chromedriverPath, chrome_options = chrome_options,
        service_args=["--verbose","--log-path=logs/webdriver.log"])

driver.get("https://antcpt.com/score_detector")
print(driver.title)
time.sleep(60)
driver.close()
