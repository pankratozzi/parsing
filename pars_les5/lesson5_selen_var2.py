from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
import time, datetime
from pymongo import MongoClient
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common import exceptions as se


date_format = '%Y-%m-%d %H:%M:%S'
timeout = 20

client = MongoClient('127.0.0.1', 27017)
db = client['mails2']
collection = db.mails2
collection.delete_many({})

chromedriver = '/usr/local/bin/chromedriver'

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("start-maximized")

driver = webdriver.Chrome(executable_path=chromedriver, options=chrome_options)
driver.get('https://mail.ru/')

assert 'почта' in driver.title
# enter in mailbox
name_box = \
    WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.NAME, 'login')))
name_box.send_keys('study.ai_172')
button = \
    WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH,
                                                                    "//button[@data-testid='enter-password']")))
button.click()
checkbox = WebDriverWait(driver,
                         timeout).until(EC.presence_of_element_located((By.XPATH, "//input[@type='checkbox']")))
checkbox.click()
passwd_box = WebDriverWait(driver,
                           timeout).until(EC.presence_of_element_located((By.XPATH, "//input[@type='password']")))
passwd_box.send_keys('NextPassword172???')
passwd_box.send_keys(Keys.ENTER)

first_letter = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH,
                                                                               "//a[contains(@class, 'llc')]")))
first_letter.click()

while True:
    vocab = {}
    vocab['title'] = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH,
                                                                             "//h2[@class='thread__subject']"))).text
    date = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR,
                                                                           "div.letter__date"))).text
    if date.lower().split(',')[0] == 'сегодня':
        vocab['datetime'] = datetime.datetime.now().strftime('%Y-%m-%d') + ' ' + date.lower().split(',')[
            1].strip() + ':00'
    elif date.lower().split(',')[0] == 'вчера':
        vocab['datetime'] = (datetime.datetime.now() - datetime.timedelta(1)).strftime('%Y-%m-%d') + \
                            ' ' + date.lower().split(',')[1].strip() + ':00'
    else:
        vocab['datetime'] = date
    vocab['from'] = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH,
                                                                "//span[contains(@class, 'letter-contact')]"))).text
    # vocab['content'] = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR,
    #                                                                                    "div.letter-body__body-content"))).get_attribute('innerHTML')
    vocab['content'] = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH,
                                                                                       "//div[contains(@class, 'letter-body__body-content')]//table"))).get_attribute('innerHTML')

    collection.insert_one(vocab)

    try:
        next_button = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, "//span[contains(@title, 'Следующее')]")))
        next_button.click()
    except se.TimeoutException:
        print('All letters was read')
        break

driver.close()
