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

client = MongoClient('127.0.0.1', 27017)
db = client['mails']
collection = db.mails

chromedriver = '/usr/local/bin/chromedriver'

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("start-maximized")

driver = webdriver.Chrome(executable_path=chromedriver, options=chrome_options)
driver.get('https://mail.ru/')

assert 'почта' in driver.title
# enter in mailbox
name_box = \
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'login')))
name_box.send_keys('study.ai_172')
button = \
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,
                                                                    "//button[@data-testid='enter-password']")))
button.click()
checkbox = WebDriverWait(driver,
                         10).until(EC.presence_of_element_located((By.XPATH, "//input[@type='checkbox']")))
checkbox.click()
passwd_box = WebDriverWait(driver,
                           10).until(EC.presence_of_element_located((By.XPATH, "//input[@type='password']")))
passwd_box.send_keys('NextPassword172???')
passwd_box.send_keys(Keys.ENTER)

time.sleep(20)
letter_links, last, sleep_time = set(), '', 5


while True:
    letters = driver.find_elements(By.XPATH, "//div[@class='dataset__items']//a[contains(@tabindex, -1)]")
    try:
        new_last = letters[-1].get_attribute('href')
    except IndexError:
        print('No letters found')
        break
    if new_last != last:
        last = new_last
    else:
        break
    for letter in letters:
        link = letter.get_attribute('href')
        letter_links.add(link)
    actions = ActionChains(driver)
    actions.move_to_element(letters[-1])
    actions.perform()
    time.sleep(sleep_time)

# сбор идет очень нестабильно, не каждый раз собирает все ссылки!

for idx, link in enumerate(list(letter_links)):
    vocab = {}
    driver.get(link)
    vocab['title'] = WebDriverWait(driver,
                                   10).until(EC.presence_of_element_located((By.XPATH,
                                                                             "//h2[@class='thread__subject']"))).text
    date = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,
                                                                           "div.letter__date"))).text

    if date.lower().split(',')[0] == 'сегодня':
        vocab['datetime'] = datetime.datetime.now().strftime('%Y-%m-%d') + ' ' + date.lower().split(',')[1].strip() + ':00'
    elif date.lower().split(',')[0] == 'вчера':
        vocab['datetime'] = (datetime.datetime.now() - datetime.timedelta(1)).strftime('%Y-%m-%d') + \
            ' ' + date.lower().split(',')[1].strip() + ':00'
    else:
        vocab['datetime'] = date

    vocab['from'] = \
        WebDriverWait(driver,
                      10).until(EC.presence_of_element_located((By.XPATH,
                                                                "//span[contains(@class, 'letter-contact')]"))).text
    vocab['content'] = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,
                                                                                       "div.letter-body__body-content"))).text
    collection.insert_one(vocab)
    if idx % 50 == 0:
        print(vocab)

print(collection.count_documents({}))


driver.close()
