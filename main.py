# You will need chrome installed and the correct chromedriver for it for this to work (read GitHub page for more)
# To improve reliability, please install buster (read GitHub page for more)

import undetected_chromedriver as uc
uc.install()

import time
from datetime import datetime, timedelta
from datetime import time as time1
from selenium import webdriver
from selenium.webdriver.common.by import By
from configparser import ConfigParser
import requests
import ast
import json
import os
import traceback
import random
import text as text

#########################################
#  Please update details in config.ini  #
#########################################

current_path = str(os.path.dirname(os.path.realpath(__file__))) # Gets current file location
# Grab config data
config = ConfigParser()
config.read(os.path.join(current_path,'config.ini'))

# prefrences json is deprecated, replaced by config.ini
# prefrences = """[
#     {
#         "licence-id": 0,
#         "user-id": 0,
#         "licence": "",
#         "booking": "",
#         "current-test": {
#             "date": "",
#             "center": "",
#             "error": 
#         },
#         "disabled-dates": [
#             ""
#         ],
#         "center": [
#             ""
#         ],
#         "before-date": "",
#         "after-date": ""
#     }
# ]"""

# Use to parse data in config.ini
def parse_config() -> dict:
    def build_dict(**kwargs) -> dict:
        perference = {}
        perference["licence-id"] = 0
        perference["user-id"] = 0
        perference["licence"] = kwargs.get('licence')
        perference["booking"] = kwargs.get('booking')
        perference["current-test"] = {}
        perference["current-test"]["date"] = kwargs.get('current_test_date')
        perference["current-test"]["center"] = kwargs.get('current_test_centre')
        perference["current-test"]["error"] = kwargs.get('current_test_error')
        perference["disabled-dates"] = ast.literal_eval(kwargs.get('disabled_dates'))
        perference["center"] = ast.literal_eval(kwargs.get('centre'))
        perference["before-date"] = kwargs.get('before_date')
        perference["after-date"] = kwargs.get('after_date')

        return perference

    key_dict = {}
    for section in config.sections():
        for key, val in config.items(section):
            key_val = config.get(section,key)
            key_dict[key] = key_val
    
    perference_dict = build_dict(**key_dict)
    return perference_dict

# Grab phone number from config for notification
phone_number = config.get("twilio","phone_number")
# Grab chromedriver version, windows or linux
# chromedriver_version = config.get("chromedriver","driver_verion")
# Change the version of chromedriver for your OS by building path
# chromedriverPath = os.path.join(str(current_path), chromedriver_version)
# Use direct path for linux chromedriver
chromedriverPath = "/bin/chromedriver"
print(f"chrome driver path: {chromedriverPath}")
# Grab auto_book_test
auto_book_test = config.get("preferences","auto_book_test")
# Grab formatted test date
formatted_current_test_date = config.get("preferences","formatted_current_test_date")

# Enable buster to solve captcha
busterEnabled = True
busterPath = str(current_path) + "/buster-chrome.zip"


def test_avaliable(last_date, last_time):
    try:
        message = f"Tests are avaliable on {last_date} at {last_time}."
        text.send_text(phone_number,message)
    except Exception as e:
        print(f"Could not send SMS when tests are avaliable due to: {e}")

def test_found(centre, date, time, shortNotice):
    try:
        message = f"Test has been found in {centre}! Date: {date}, Time: {time}, Short Notice: {shortNotice}."
        text.send_text(phone_number,message)
    except Exception as e:
        print(f"Could not send SMS when test is found due to: {e}.")

######################################################
# You do not need to change anything below this line #
######################################################

print("")
print(f"Time: {datetime.now()}")
print("="*100)
print("START OF SCRIPT")
print("="*100)
print("Input: ")
print([parse_config()])
print("="*100)

# Due to firewall issues this has to be fairly long and up to 10 seconds will be added randomly to reduce the risk of getting blocked
DVSADelay = 60

licence_number = "" # Do NOT change from blank
booking_refrence = "" # Do NOT change from blank
dvsa_queue_url = "https://queue.driverpracticaltest.dvsa.gov.uk/?c=dvsatars&e=ibsredirectprod0915&t=https%3A%2F%2Fdriverpracticaltest.dvsa.gov.uk%2Flogin&cid=en-GB"
dvsa_url = "https://driverpracticaltest.dvsa.gov.uk/login"
checkRunTime = False
proxySystem = False

if not os.path.exists('./error_screenshots'):
    os.makedirs('./error_screenshots')

def is_time_between(begin_time, end_time, check_time=None):
    # If check time is not given, default to current UTC time
    check_time = check_time or datetime.now().time()
    if begin_time < end_time:
        return check_time >= begin_time and check_time <= end_time
    else: # crosses midnight
        return check_time >= begin_time or check_time <= end_time

def input_text_box(box_id, text, currentDriver):
    box = currentDriver.find_element_by_id(box_id)
    for charachter in text:
        box.send_keys(charachter)
        time.sleep(random.randint(1, 5) / 100)

def random_sleep(weight, maxTime):
    maxTime = maxTime * 100
    print(f"Sleeping for {weight} seconds...")
    time.sleep(weight)
    ran_sleep_time = random.randint(0, maxTime) / 100
    print(f"Sleeping for another {ran_sleep_time} seconds...")
    time.sleep(ran_sleep_time)

def wait_for_internet_connection():
    connected = False
    while True:
        online = requests.get("https://www.google.com/")
        if online:
            print("Connected to internet")
            return
        time.sleep(1)

def report_error(error_code, title=None, data=None):
    # Report error to server
    try:
        errorData = json.dumps({
            "title": title,
            "log": data
        });
        # Not currently in use
    except Exception as e:
        print("Unable to log error to server: " + str(e))

def scan_for_preferred_tests(before_date, after_date, unavailable_dates, test_date, formatted_test_date, currentDriver):
    last_date = None
    last_date_element = None
    if before_date != None:
        minDate = datetime.strptime(before_date, "%Y-%m-%d")
    elif "Yes" in test_date:
        minDate = datetime.strptime("2050-12-12", "%Y-%m-%d")
    else:
        minDate = datetime.strptime(test_date, "%A %d %B %Y %I:%M%p") - timedelta(days=1)

    print("Before: " + str(minDate))

    if after_date != "None":
        maxDate = datetime.strptime(after_date, "%Y-%m-%d")
    else:
        maxDate = datetime.strptime("2000-01-01", "%Y-%m-%d")

    print("After: " + str(maxDate))

    available_calendar = currentDriver.find_element_by_class_name("BookingCalendar-datesBody")
    available_days = available_calendar.find_elements_by_xpath(".//td")

    found = False

    if (unavailable_dates is None):
        unavailable_dates= []
    
    for day in available_days:
        if not "--unavailable" in day.get_attribute("class"):
            day_a = day.find_element_by_xpath(".//a")
            if day_a.get_attribute("data-date") not in unavailable_dates and datetime.strptime(day_a.get_attribute("data-date"), "%Y-%m-%d") < minDate and \
                datetime.strptime(day_a.get_attribute("data-date"), "%Y-%m-%d") > maxDate and datetime.strptime(day_a.get_attribute("data-date"), "%Y-%m-%d").weekday() < 5 and \
                    day_a.get_attribute("data-date") != formatted_test_date:
                        last_date_container = day
                        last_date_element = day_a
                        last_date = day_a.get_attribute("data-date")
                        found = True
                        break
    return found, last_date, last_date_element

def solve_captcha(currentDriver,skip=False) -> bool:
    if not skip:
        driver = currentDriver
        driver.switch_to.default_content()
        iframe = driver.find_element_by_id("main-iframe")
        driver.switch_to.frame(iframe)
        iframe1 = driver.find_element_by_css_selector("iframe[name*='a-'][src*='https://www.google.com/recaptcha/api2/anchor?']")
        driver.switch_to.frame(iframe1)
        time.sleep(0.2)
        driver.find_element_by_xpath("//span[@id='recaptcha-anchor']").click()
        driver.switch_to.default_content()
        time.sleep(0.2)
        iframe = driver.find_element_by_id("main-iframe")
        driver.switch_to.frame(iframe)
        if "Why am I seeing this page" in driver.page_source:
            print("Completing captcha 1")
            time.sleep(2)
            iframe1 = driver.find_element_by_css_selector("iframe[title*='recaptcha challenge'][src*='https://www.google.com/recaptcha/api2/bframe?']")
            driver.switch_to.frame(iframe1)
            print("Completing captcha 2")
            time.sleep(2)
            driver.find_elements_by_class_name("help-button-holder")[0].click()
            random_sleep(5, 4)
            attempts2 = 0
            while ("Multiple correct solutions required" in driver.page_source and attempts2 < 4):
                attempts2 += 1
                driver.find_elements_by_class_name("help-button-holder")[0].click()
                random_sleep(5, 4)
            driver.switch_to.default_content()
            print("Completing captcha 3")
            time.sleep(1)
        if "Why am I seeing this page" in driver.page_source:
            return False
        else:
            return True
    else:
        print(f"Solve_captcha() skipped. Solve manually...")
        time.sleep(60)

def enter_credentials(manual=False):
    if not manual:
        input_text_box("driving-licence-number", str(licenceInfo["licence"]), driver)
        input_text_box("application-reference-number", str(licenceInfo["booking"]), driver)
        random_sleep(1, 1)
        driver.find_element_by_id("booking-login").click()
        random_sleep(3, 1)
    else:
        print(f"Enter credentials manually...")
        time.sleep(30)


def send_update_log(licenceIdUpdate):
    # For future use
    print()

def bot_online():
    # For future use
    print()

# Send test error to server
report_error(0)
wait_for_internet_connection()

DVSAdown = False
runningLoop = True
currentLicences = [] # List of dictionaries
previousLicences = "" # Raw data from server
activeDrivers = {} # Dictionary of "licence-id"->driver
allDriversQuit = True
maxLoop = 100
run_on_VM = False
solve_manually = False

# Chrome configuration
chrome_options = uc.ChromeOptions()
if not solve_manually:
    prefs = {"profile.managed_default_content_settings.images": 2} # Hide images (expreimental)
    chrome_options.add_experimental_option("prefs", prefs)

if run_on_VM is True:
# Following code added for running on VM in case VM has no GPU which will cause error in webdriver
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36")
    chrome_options.add_argument("window-size=1400,900")
if busterEnabled:
    chrome_options.add_extension(busterPath) # Use reCAPTCHA buster extension

# Try 4 times when script is run
max_attempt = 4
#### Main Loop ####
# while runningLoop:
for i in range(max_attempt):
    print()
    print("-"*100)
    print(f"Main attempt:{i}")
    print()
    try:
        loopStartTime = time.time()
        if (is_time_between(time1(6,5), time1(23,35))):
            allDriversQuit = False
            # Get list of new licences to check
            # dataRAW = prefrences
            # data = json.loads(dataRAW)
            dataRAW = json.dumps([parse_config()])
            data = [parse_config()]
            # Check for any changes in the array
            if dataRAW != previousLicences:
                # Compare and update lists
                if len(currentLicences) == 0 and len(data) == 0:
                    print("No licences assigned - no change")
                elif len(currentLicences) > 0 and len(data) == 0:
                    print("No licences assigned - quitting all current drivers")
                    currentLicences = data
                    for driver in activeDrivers:
                        # Quit all current drivers
                        try:
                            activeDrivers[driver].quit()
                        except:
                            print("Failed to quit driver")
                    activeDrivers = {}
                else:
                    print("Change in licences - transferring old data")
                    oldActiceDrivers = activeDrivers
                    activeDrivers = {}
                    newLicencesTemp = data
                    oldLicencesTemp = currentLicences
                    for newLicenceInfo in newLicencesTemp:
                        newLicenceInfo["active"] = False
                        newLicenceInfo["current-centre"] = 0
                    for newLicenceInfo in newLicencesTemp:
                        for oldLicenceInfo in oldLicencesTemp:
                            if oldLicenceInfo["licence-id"] == newLicenceInfo["licence-id"]:
                                if newLicenceInfo["licence"] != oldLicenceInfo["licence"] or newLicenceInfo["booking"] != oldLicenceInfo["booking"]:
                                    newLicenceInfo["active"] = False
                                    print(str(newLicenceInfo["licence-id"]) + " -> inactive (change to booking info)")
                                else:
                                    if oldLicenceInfo["active"]:
                                        newLicenceInfo["active"] = True
                                        print(str(newLicenceInfo["licence-id"]) + " -> active")
                                    else:
                                        newLicenceInfo["active"] = False
                                        print(str(newLicenceInfo["licence-id"]) + " -> inactive")
                    currentLicences = newLicencesTemp
                    
                    # Transfer over old active chrome drivers
                    for driver in oldActiceDrivers:
                        transferred = False
                        for newLicenceInfo in newLicencesTemp:
                            if driver == newLicenceInfo["licence-id"]:
                                activeDrivers[newLicenceInfo["licence-id"]] = oldActiceDrivers[driver]
                                transferred = True
                                print("Transferred licence ID " + str(driver))
                        if not transferred:
                            oldActiveDrivers[driver].quit()
                            print("Inactive chrome driver quit")
                previousLicences = dataRAW
            else:
                print("No changes in licence information")
            # Check if need to restart failed sessions
            for licenceInfo in currentLicences:
                bot_online()
                if licenceInfo["active"] == False:
                    licenceInfo["active"] = False
                    try:
                        activeDrivers[licenceInfo["licence-id"]].close()
                    except:
                        print("No browser active to close")
                    print("Relaunching driver for licence " + str(licenceInfo["licence-id"]))
                        
                    activeDrivers[licenceInfo["licence-id"]] = webdriver.Chrome(executable_path=chromedriverPath, chrome_options=chrome_options, service_args=["--verbose","--log-path=logs/webdriver.log"])
                    driver = activeDrivers[licenceInfo["licence-id"]]
                    
                    if run_on_VM:
                        agent = driver.execute_script("return navigator.userAgent")

                    print("Launching queue")
                    driver.get(dvsa_queue_url)
                    try:
                        if ("queue.driverpracticaltest.dvsa.gov.uk" in driver.current_url):
                            print("Queue active on DVSA site, please wait...")
                            loopCount = 0
                            queueComplete = False
                            while not queueComplete and loopCount <= maxLoop:
                                if ("queue.driverpracticaltest.dvsa.gov.uk" in driver.current_url):
                                    loopCount += 1
                                else:
                                    print("Queue complete!")
                                    queueComplete = True
                                time.sleep(2)
                        else:
                            queueComplete = True

                        if ("Request unsuccessful. Incapsula incident ID" in driver.page_source):
                            random_sleep(4, 10)
                            
                            if not solve_manually:
                                driver.refresh()
                            else:
                                random_sleep(30, 10)

                            if ("Request unsuccessful. Incapsula incident ID" in driver.page_source):
                                random_sleep(2,5)
                                captcha_success = solve_captcha(driver,skip=solve_manually)
                                if not captcha_success:
                                    print(f"First captcha attempty unsuccessful.")
                                else:
                                    print(f"Captcha solved!")

                                time.sleep(4)
                                if ("Request unsuccessful. Incapsula incident ID" in driver.page_source):
                                    queueComplete = False
                                    print("Firewall - Extra delay")
                                    random_sleep(180, 10)
                                else:
                                    print("Firewall has been delt with ;)")
                            else:
                                print("Firewall has been delt with ;)")

                        if (queueComplete):
                            enter_credentials(manual=False)

                            if ("Request unsuccessful. Incapsula incident ID" in driver.page_source):
                                random_sleep(5, 10)
                                
                                if not solve_manually:
                                    driver.refresh()
                                else:
                                    random_sleep(30, 10)

                                if ("Request unsuccessful. Incapsula incident ID" in driver.page_source):
                                    random_sleep(2,5)
                                    captcha_success = solve_captcha(driver,skip=solve_manually)
                                    
                                    if not captcha_success:
                                        print(f"First captcha attempty unsuccessful.")
                                    else:
                                        print("Captcha solved!")
                                    
                                    time.sleep(3)

                                    if ("Request unsuccessful. Incapsula incident ID" in driver.page_source):
                                        queueComplete = False
                                        print("Firewall - Extra delay")
                                        random_sleep(20, 10)
                                    else:
                                        print("Firewall has been delt with ;)")
                                else:
                                    print("Firewall has been delt with ;)")

                            if ("loginError=true" in driver.current_url):
                                print("Incorrect Licence/Booking Ref")
                            else:
                                random_sleep(3, 1)
                                
                                contents_container = driver.find_elements_by_class_name("contents")
                                # contents_container = driver.find_element_by_css_selector("div.contents")
                                test_date_temp = contents_container[0].find_element_by_xpath(".//dd").get_attribute('innerHTML')
                                test_center_temp = contents_container[1].find_element_by_xpath(".//dd").get_attribute('innerHTML')
                                print("Test Date: " + test_date_temp)
                                print("Test Center: " + test_center_temp)

                                if ("Your booking has been cancelled. You’ll need to either re-book your test or call the " in driver.find_element_by_id("main").get_attribute('innerHTML')):
                                    print("Test has been cancelled")
                                    licenceInfo["active"] = False
                                else:
                                    newTestInfo = json.dumps({
                                        "date": test_date_temp,
                                        "center": test_center_temp
                                    });
                                
                                if ("The number of allowed changes to your booking has now been exceeded" in driver.find_element_by_id("main").get_attribute('innerHTML')):
                                    print("Maximum number of rebookings has been exceeded")

                                if "Yes" in licenceInfo["current-test"]["date"]:
                                    print("Reserved test login")
                                    driver.find_element_by_id("date-time-change").click()
                                    random_sleep(1, 2)

                                    driver.find_element_by_id("test-choice-earliest").click()

                                    random_sleep(1, 2)

                                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                                    random_sleep(1, 2)

                                    driver.find_element_by_id("driving-licence-submit").click()
                                    
                                    licenceInfo["centre"] = [test_center_temp]
                                    
                                    random_sleep(1, 2)
                                else:
                                    driver.find_element_by_id("test-centre-change").click()
                                    random_sleep(3, 2)
                                    
                                    driver.find_element_by_id("test-centres-input").clear()
                                    input_text_box("test-centres-input", str(licenceInfo["center"][0]), driver)
                                    
                                    driver.find_element_by_id("test-centres-submit").click()
                                    random_sleep(5, 2)

                                    results_container = driver.find_element_by_class_name("test-centre-results")

                                    test_center = results_container.find_element_by_xpath(".//a")

                                    licenceInfo["refresh_url"] = test_center.get_attribute('href')

                                    test_center.click()


                                # Check for tests
                                if "There are no tests available" in driver.page_source:
                                    print("No test available")
                                    licenceInfo["active"] = True
                                elif "Oops" in driver.page_source:
                                    print("Went away")
                                    licenceInfo["active"] = False
                                elif "You are now in the queue to book, change or cancel your driving test." in driver.page_source:
                                    print("Queue")
                                    licenceInfo["active"] = False
                                elif ("Request unsuccessful. Incapsula incident ID" in driver.page_source):
                                    print("Firewall - extra delay")
                                    # licenceInfo["active"] = False
                                    time.sleep(60)
                                elif "Enter details below to access your booking" in driver.page_source:
                                    print("Login required")
                                    licenceInfo["active"] = False
                                else:
                                    licenceInfo["active"] = True
                                    print("Tests available, checking dates...")

                                    # # Notify my phone, disabled as avaliable dates after current test will still notify in this case
                                    # try:
                                    #     text.send_text(phone_number,"Tests avaliable, checking dates now...")
                                    # except Exception as e:
                                    #     print(f"Could not notify after tests avaliable due to: {e}")

                                    found, last_date, last_date_element = scan_for_preferred_tests(licenceInfo["before-date"], licenceInfo["after-date"], licenceInfo["disabled-dates"], licenceInfo["current-test"]["date"], formatted_current_test_date, driver)
                                    if found:
                                        month = datetime.strptime(last_date, "%Y-%m-%d")
                                        attempts = 0
                                        while month.strftime("%B") != driver.find_element_by_class_name("BookingCalendar-currentMonth").get_attribute('innerHTML') and attempts < 12:
                                            try:
                                                driver.find_element_by_class_name("BookingCalendar-nav--prev").click()
                                            except:
                                                print("Booking rev fail")
                                            attempts += 1
                                            random_sleep(0.1, 0.2)
                                        print(last_date)
                                        print("TARGET CAL MONTH: " + month.strftime("%B"))
                                        print("CURRENT CAL MONTH: " + driver.find_element_by_class_name("BookingCalendar-currentMonth").get_attribute('innerHTML'))
                                        print("REVERSE NUM: " + str(attempts))
                                        # time.sleep(0.6)
                                        last_date_element.click()
                                        time_container = driver.find_element_by_id("date-" + last_date)
                                        time_item = int(time_container.find_element_by_xpath(".//label").get_attribute('for').replace("slot-", "")) / 1000
                                        test_time = datetime.fromtimestamp(time_item).strftime("%H:%M")

                                        # Notify my phone
                                        test_avaliable(last_date,test_time)

                                        try:
                                            shortNoticeCheck = time_container.find_element_by_id(time_container.find_element_by_xpath(".//label").get_attribute('for')).get_attribute('data-short-notice')
                                            if shortNoticeCheck == "true":
                                                shortNotice = True
                                                print("Short notice")
                                            else:
                                                shortNotice = False
                                        except:
                                            shortNotice = False

                                        print("Test Found: " + last_date + " at " + test_time)

                                        time_container.find_element_by_xpath(".//label").click()

                                        booking_failed = False
                                        errorPoint = "p0"

                                        try:
                                            licenceInfo["active"] = False
                                            time_container.click()
                                            errorPoint = "p1"
                                            time.sleep(0.1)
                                            driver.find_element_by_id("slot-chosen-submit").click()
                                            errorPoint = "p2"
                                            time.sleep(0.4)
                                            if shortNotice:
                                                driver.find_element_by_xpath("(//button[@id='slot-warning-continue'])[2]").click()
                                            else:
                                                driver.find_element_by_id("slot-warning-continue").click()
                                            errorPoint = "p3"
                                            random_sleep(1, 1)
                                            reserved = False
                                            testTaken = False
                                            iAmCandidateClicked = False
                                            attempts = 0
                                            while not reserved and not testTaken and attempts <= 4:
                                                print("Booking attempt: " + str(attempts))
                                                try:
                                                    if not iAmCandidateClicked:
                                                        driver.find_element_by_id("i-am-candidate").click()
                                                        iAmCandidateClicked = True
                                                    try:
                                                        driver.switch_to.default_content()
                                                        iframe = driver.find_element_by_id("main-iframe")
                                                        driver.switch_to.frame(iframe)
                                                        print("Booking fail - attempting captcha")
                                                        reserved = False
                                                        attempts += 1
                                                        time.sleep(0.2)
                                                        try:
                                                            if "The time chosen is no longer available" not in driver.page_source:
                                                                solve_captcha(driver,skip=solve_manually)
                                                            else:
                                                                print("Time chosen is no longer available...")
                                                                testTaken = True
                                                        except:
                                                            print("Failed recaptcha")
                                                        
                                                    except:
                                                        print("Booking success")
                                                        reserved = True
                                                except:
                                                    attempts += 1
                                                    time.sleep(0.2)
                                                    try:
                                                        if "The time chosen is no longer available" not in driver.page_source:
                                                            solve_captcha(driver,skip=solve_manually)
                                                        else:
                                                            print("Time chosen is no longer available...")
                                                            testTaken = True
                                                    except:
                                                        print("Failed recaptcha")
                                                    if not testTaken:
                                                        try:
                                                            iframe = driver.find_element_by_id("main-iframe")
                                                            driver.switch_to.frame(iframe)
                                                        except:
                                                            print("No captcha iframe")
                                                        random_sleep(2, 2)
                                                        if "Why am I seeing this page" in driver.page_source:
                                                            driver.switch_to.default_content()
                                                            nowFileName = datetime.now()
                                                            dt_string = nowFileName.strftime("%Y-%m-%d %H-%M-%S")
                                                            filename = "./error_screenshots/" + str(dt_string) + ".png"
                                                            driver.get_screenshot_as_file(filename)
                                                            random_sleep(20, 4)
                                                            driver.refresh()
                                            
                                            if reserved == False:
                                                booking_failed = True
                                                if testTaken:
                                                    errorTitle = "Test booking error (test taken): " + str(errorPoint) + ", " + str(licenceInfo["licence-id"])
                                                else:
                                                    errorTitle = "Test booking error: " + str(errorPoint) + ", " + str(licenceInfo["licence-id"])
                                                
                                            errorPoint = "p4"
                                        except:
                                            booking_failed = True
                                        
                                        if booking_failed:
                                            print("Failed to book - test taken by some other goon")

                                            try:
                                                time.sleep(1)
                                                nowFileName = datetime.now()
                                                dt_string = nowFileName.strftime("%Y-%m-%d %H-%M-%S")
                                                filename = "./error_screenshots/" + str(dt_string) + ".png"
                                                driver.get_screenshot_as_file(filename)
                                            except:
                                                print("Error capturing screenshot")
                                        else:
                                            newTestInfo = json.dumps({
                                                "date": last_date,
                                                "time": test_time,
                                                "center": licenceInfo["center"][0],
                                                "short": shortNotice
                                            })

                                            # Notify my phone
                                            test_found(licenceInfo["center"][0], last_date, test_time, shortNotice)

                                            # Put test notification here
                                            print("Centre: " + licenceInfo["center"][0])
                                            print("Date: " + last_date)
                                            print("Time: " + test_time)

                                            # Manual input is disabled here
                                            # validInput = False
                                            # while not validInput:
                                            #     userInput = input("Would you like to book this test? y/n")
                                            #     if userInput == "y":
                                            #         print("Bookig test")
                                            #         test_accept = True
                                            #         validInput = True
                                            #     elif userInput == "n":
                                            #         print("Not booking test")
                                            #         test_accept = False
                                            #         validInput = True
                                            #     else:
                                            #         print("Please either enter y or n")
                                
                                            if auto_book_test == "True":
                                                print("Booking Test...")
                                                
                                                # Notify my phone
                                                try:
                                                    message = "Test accepted. Trying to book test now..."
                                                    text.send_text(phone_number,message)
                                                except Exception as e:
                                                    print(f"Could not send SMS after test accept due to: {e}")

                                                driver.find_element_by_id("confirm-changes").click()
                                                if ("Request unsuccessful. Incapsula incident ID" in driver.page_source):
                                                    print("Firewall - booking error")
                                                    random_sleep(40, 4)
                                                    driver.refresh()
                                                    try:
                                                        if ("Request unsuccessful. Incapsula incident ID" in driver.page_source):
                                                            solve_captcha(driver,skip=solve_manually)
                                                        else:
                                                            print("Recaptcha Bypassed")
                                                    except:
                                                        print("Failed Recaptcha")
                                                        if ("Request unsuccessful. Incapsula incident ID" in driver.page_source):
                                                            print("Attempting refresh")
                                                            random_sleep(10, 4)
                                                            driver.refresh()
                                                        if "Incapsula" not in driver.page_source:
                                                            print("Recaptcha bypassed")
                                                if "Incapsula" not in driver.page_source:
                                                    print("Test Booked")
                                                else:
                                                    print("Test failed to book")
                                                    try:
                                                        time.sleep(1)
                                                        nowFileName = datetime.now()
                                                        dt_string = nowFileName.strftime("%Y-%m-%d %H-%M-%S")
                                                        filename = "./error_screenshots/" + str(dt_string) + ".png"
                                                        driver.get_screenshot_as_file(filename)
                                                    except:
                                                        print("Error capturing screenshot")
                                                
                                            else:
                                                print("Test not booked")
                                        
                                    else:
                                        print("No test found")
                                
                            random_sleep(20, 30)
                        else:
                            err = True
                            print("Queue max time exceeded")
                    except Exception as e:
                        print("A login error occured")

                        print(traceback.format_exc())

                        try:
                            driver.quit();
                        except:
                            print("No driver to close")
                        licenceInfo["active"] = False


                        try:
                            time.sleep(1)
                            nowFileName = datetime.now()
                            dt_string = nowFileName.strftime("%Y-%m-%d %H-%M-%S")
                            filename = "./error_screenshots/" + str(dt_string) + ".png"
                            driver.get_screenshot_as_file(filename)
                        except:
                            print("Error capturing screenshot")
                        
                        err = True

            # Continue to check licences
            print("Checking licences")
            for licenceInfo in currentLicences:
                print("Checking licence " + str(licenceInfo["licence-id"]))
                if not licenceInfo["active"]:
                    print("Licence " + str(licenceInfo["licence-id"]) + " not active")
                else:
                    if len(licenceInfo["center"]) > 1 or True:
                        try:
                            moveBack = 0
                            search_centre_id = licenceInfo["current-centre"] = licenceInfo["current-centre"] + 1
                            if licenceInfo["current-centre"] > len(licenceInfo["center"]) - 1:
                                search_centre_id = licenceInfo["current-centre"] - len(licenceInfo["center"])
                            licenceInfo["current-centre"] = search_centre_id

                            driver = activeDrivers[licenceInfo["licence-id"]]
                            
                            search_centre = licenceInfo["center"][search_centre_id]
                            
                            driver.find_element_by_id("change-test-centre").click()
                            moveBack = 1
                            random_sleep(2, 2)
                            
                            driver.find_element_by_id("test-centres-input").clear()
                            input_text_box("test-centres-input", str(search_centre), driver)
                            
                            driver.find_element_by_id("test-centres-submit").click()
                            moveBack = 2
                            random_sleep(5, 2)

                            results_container = driver.find_element_by_class_name("test-centre-results")

                            test_center = results_container.find_element_by_xpath(".//a")

                            test_center.click()
                            moveBack = 3
                        except:
                            print("Error updating checking...")
                            try:
                                if "Oops" in driver.page_source:
                                    print("Went away")
                                    licenceInfo["active"] = False
                                elif "You are now in the queue to book, change or cancel your driving test." in driver.page_source:
                                    print("Queue")
                                    licenceInfo["active"] = False
                                elif ("Request unsuccessful. Incapsula incident ID" in driver.page_source):
                                    print("Firewall - extra delay")
                                    # licenceInfo["active"] = False
                                    time.sleep(60)
                                    if moveBack != 3:
                                        for i in range(0, moveBack):
                                            driver.back()
                                elif "Enter details below to access your booking" in driver.page_source:
                                    print("Login required")
                                    licenceInfo["active"] = False
                                else:
                                    print("Unknown error with checks - restart")
                                    licenceInfo["active"] = False
                            except:
                                print("Error running checks")
                                licenceInfo["active"] = False
                    else:
                        search_centre = licenceInfo["center"][0]
                        driver.get(licenceInfo["refresh_url"])

                    if licenceInfo["active"]:
                        send_update_log(licenceInfo["licence-id"])

                        # Check for tests
                        if "There are no tests available" in driver.page_source:
                            print("No test available")
                        elif "Oops" in driver.page_source:
                            print("Went away")
                            licenceInfo["active"] = False
                        elif "You are now in the queue to book, change or cancel your driving test." in driver.page_source:
                            print("Queue")
                            licenceInfo["active"] = False
                        elif ("Request unsuccessful. Incapsula incident ID" in driver.page_source):
                            print("Firewall - extra delay")
                            # licenceInfo["active"] = False
                            time.sleep(60)
                        elif "Enter details below to access your booking" in driver.page_source:
                            print("Login required")
                            licenceInfo["active"] = False
                        else:
                            print("Tests available, checking dates...")

                            # # Notify my phone, disabled as avaliable test after current test will still count
                            # try:
                            #     text.send_text(phone_number,"Tests avaliable, checking dates now...")
                            # except Exception as e:
                            #     print(f"Could not notify after tests avaliable due to: {e}")

                            found, last_date, last_date_element = scan_for_preferred_tests(licenceInfo["before-date"], licenceInfo["after-date"], licenceInfo["disabled-dates"], licenceInfo["current-test"]["date"], formatted_current_test_date, driver)
                            if found:
                                month = datetime.strptime(last_date, "%Y-%m-%d")
                                attempts = 0
                                while month.strftime("%B") != driver.find_element_by_class_name("BookingCalendar-currentMonth").get_attribute('innerHTML') and attempts < 12:
                                    try:
                                        driver.find_element_by_class_name("BookingCalendar-nav--prev").click()
                                    except:
                                        print("Booking rev fail")
                                    attempts += 1
                                    random_sleep(0.1, 0.2)
                                print(last_date)
                                print("TARGET CAL MONTH: " + month.strftime("%B"))
                                print("CURRENT CAL MONTH: " + driver.find_element_by_class_name("BookingCalendar-currentMonth").get_attribute('innerHTML'))
                                print("REVERSE NUM: " + str(attempts))
                                # time.sleep(0.6)
                                last_date_element.click()
                                time_container = driver.find_element_by_id("date-" + last_date)
                                time_item = int(time_container.find_element-by_xpath(".//label").get_attribute('for').replace("slot-", "")) / 1000
                                test_time = datetime.fromtimestamp(time_item).strftime("%H:%M")

                                try:
                                    shortNoticeCheck = time_container.find_element_by_id(time_container.find_element_by_xpath(".//label").get_attribute('for')).get_attribute('data-short-notice')
                                    if shortNoticeCheck == "true":
                                        shortNotice = True
                                        print("Short notice")
                                    else:
                                        shortNotice = False
                                except:
                                    shortNotice = False

                                print("Test Found: " + last_date + " at " + test_time)
                                
                                time_container.find_element_by_xpath(".//label").click()

                                booking_failed = False
                                errorPoint = "p0"

                                try:
                                    licenceInfo["active"] = False
                                    time_container.click()
                                    errorPoint = "p1"
                                    time.sleep(0.1)
                                    driver.find_element_by_id("slot-chosen-submit").click()
                                    errorPoint = "p2"
                                    time.sleep(0.4)
                                    if shortNotice:
                                        driver.find_element_by_xpath("(//button[@id='slot-warning-continue'])[2]").click()
                                    else:
                                        driver.find_element_by_id("slot-warning-continue").click()
                                    errorPoint = "p3"
                                    random_sleep(1, 1)
                                    reserved = False
                                    testTaken = False
                                    iAmCandidateClicked = False
                                    attempts = 0
                                    while not reserved and not testTaken and attempts <= 4:
                                        print("Booking attempt: " + str(attempts))
                                        try:
                                            if not iAmCandidateClicked:
                                                driver.find_element_by_id("i-am-candidate").click()
                                                iAmCandidateClicked = True
                                            try:
                                                driver.switch_to.default_content()
                                                iframe = driver.find_element_by_id("main-iframe")
                                                driver.switch_to.frame(iframe)
                                                print("Booking fail - attempting captcha")
                                                reserved = False
                                                attempts += 1
                                                time.sleep(0.2)
                                                try:
                                                    if "The time chosen is no longer available" not in driver.page_source:
                                                        solve_captcha(driver,skip=solve_manually)
                                                    else:
                                                        print("Time chosen is no longer available...")
                                                        testTaken = True
                                                except:
                                                    print("Failed recaptcha")
                                                
                                            except:
                                                print("Booking success")
                                                reserved = True
                                        except:
                                            attempts += 1
                                            time.sleep(0.2)
                                            try:
                                                if "The time chosen is no longer available" not in driver.page_source:
                                                    solve_captcha(driver,skip=solve_manually)
                                                else:
                                                    print("Time chosen is no longer available...")
                                                    testTaken = True
                                            except:
                                                print("Failed recaptcha")
                                            if not testTaken:
                                                try:
                                                    iframe = driver.find_element_by_id("main-iframe")
                                                    driver.switch_to.frame(iframe)
                                                except:
                                                    print("No captcha iframe")
                                                random_sleep(2, 2)
                                                if "Why am I seeing this page" in driver.page_source:
                                                    driver.switch_to.default_content()
                                                    nowFileName = datetime.now()
                                                    dt_string = nowFileName.strftime("%Y-%m-%d %H-%M-%S")
                                                    filename = "./error_screenshots/" + str(dt_string) + ".png"
                                                    driver.get_screenshot_as_file(filename)
                                                    random_sleep(20, 4)
                                                    driver.refresh()
                                    
                                    if reserved == False:
                                        booking_failed = True
                                        # Time to diagnose
                                        if (errorPoint == "p2"):
                                            time.sleep(60)
                                        
                                    errorPoint = "p4"
                                except:
                                    booking_failed = True
                                
                                if booking_failed:
                                    print("Failed to book - test taken by some other goon")

                                    try:
                                        time.sleep(1)
                                        nowFileName = datetime.now()
                                        dt_string = nowFileName.strftime("%Y-%m-%d %H-%M-%S")
                                        filename = "./error_screenshots/" + str(dt_string) + ".png"
                                        driver.get_screenshot_as_file(filename)
                                    except:
                                        print("Error capturing screenshot")
                                else:
                                    newTestInfo = json.dumps({
                                        "date": last_date,
                                        "time": test_time,
                                        "center": search_centre,
                                        "short": shortNotice
                                    })

                                    # Notify my phone
                                    test_found(licenceInfo["center"][0], last_date, test_time, shortNotice)
                                    
                                    # Put test notification here
                                    print("Centre: " + licenceInfo["center"][0])
                                    print("Date: " + last_date)
                                    print("Time: " + test_time)

                                    # Manual input is disabled here 
                                    # validInput = False
                                    # while not validInput:
                                    #     userInput = input("Would you like to book this test? y/n")
                                    #     if userInput == "y":
                                    #         print("Bookig test")
                                    #         test_accept = True
                                    #         validInput = True
                                    #     elif userInput == "n":
                                    #         print("Not booking test")
                                    #         test_accept = False
                                    #         validInput = True
                                    #     else:
                                    #         print("Please either enter y or n")
                                    
                                    if auto_book_test == "True":
                                        print("Booking Test...")

                                        # Notify my phone
                                        try:
                                            message = "Test accepted. Trying to book test now..."
                                            text.send_text(phone_number,message)
                                        except Exception as e:
                                            print(f"Could not send SMS after test accept due to: {e}")

                                        driver.find_element_by_id("confirm-changes").click()
                                        if ("Request unsuccessful. Incapsula incident ID" in driver.page_source):
                                            print("Firewall - booking error")
                                            random_sleep(40, 4)
                                            driver.refresh()
                                            try:
                                                if ("Request unsuccessful. Incapsula incident ID" in driver.page_source):
                                                    solve_captcha(driver,skip=solve_manually)
                                                else:
                                                    print("Recaptcha Bypassed")
                                            except:
                                                print("Failed Recaptcha")
                                                if ("Request unsuccessful. Incapsula incident ID" in driver.page_source):
                                                    print("Attempting refresh")
                                                    random_sleep(10, 4)
                                                    driver.refresh()
                                                if "Incapsula" not in driver.page_source:
                                                    print("Recaptcha bypassed")
                                        if "Incapsula" not in driver.page_source:
                                            print("Test Booked")
                                        else:
                                            print("Test failed to book")
                                            try:
                                                time.sleep(1)
                                                nowFileName = datetime.now()
                                                dt_string = nowFileName.strftime("%Y-%m-%d %H-%M-%S")
                                                filename = "./error_screenshots/" + str(dt_string) + ".png"
                                                driver.get_screenshot_as_file(filename)
                                            except:
                                                print("Error capturing screenshot")
                                    else:
                                        print("Test not booked")
                                
                            else:
                                print("No test found")
                random_sleep(DVSADelay, 10)
        else:
            print("Site offline")
            if not allDriversQuit:
                for driver in activeDrivers:
                    # Quit all current drivers
                    try:
                        activeDrivers[driver].quit()
                    except:
                        print("No driver to quit")
                    allDriversQuit = True
                currentLicences = {}
                previousLicences = {}
                activeDrivers = {}
        # Check run length and restart if longer than 15 minutes
        try:
            if float("%s" % (time.time() - loopStartTime)) > 1800 and checkRunTime:
                # Run length exceeded
                print("System delay - restarting")
                for driver in activeDrivers:
                    # Quit all current drivers
                    try:
                        activeDrivers[driver].quit()
                    except:
                        print("Error quitting driver")
                runningLoop = False
        except:
            print("Error checking run time")
    except Exception as e:
        print("Unknown error occurred: " + str(traceback.format_exc()))

        try:
            time.sleep(1)
            nowFileName = datetime.now()
            dt_string = nowFileName.strftime("%Y-%m-%d %H-%M-%S")
            filename = "./error_screenshots/" + str(dt_string) + ".png"
            driver.get_screenshot_as_file(filename)
        except:
            print("Error capturing screenshot")

        try:
            if ("Request unsuccessful. Incapsula incident ID" in driver.page_source):
                print("Firewall - Extra delay")
                random_sleep(50, 10)
        except:
            print("Failed firewall check")
        
        time.sleep(30)
        
        try:
            driver.quit()
        except:
            print("No browser active to close")
        
        try:
            licenceInfo["active"] = False
        except:
            print("Unable to deactivate licence info")
    random_sleep(10, 5)

    # Check if it is end of script, quit drivers
    if i == (max_attempt-1):
        for driver in activeDrivers:
            # Quit all current drivers
            try:
                activeDrivers[driver].quit()
            except:
                print("Failed to quit driver")

print("="*100)
print("END OF SCRIPT")
print("="*100)
