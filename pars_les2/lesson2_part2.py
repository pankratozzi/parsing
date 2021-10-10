import pandas as pd
import requests
import sys
import re
from tqdm import tqdm
from bs4 import BeautifulSoup as bs

url = 'https://auto.ru/moskva/cars/all/'
params = {
    'page': 1,
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'
}
df = pd.DataFrame(columns=['Model', 'Year', 'Mileage', 'V_engine', 'EngineType', 'HorsePower',
                           'Selector', 'Color', 'CarBodyType', 'Drive', 'Price'])

num_pages = input('Enter the number of pages: ')
num_pages = int(num_pages) if num_pages.isdigit() else None
number_of_owners = {'owners_count_group': ('ONE', 'LESS_THAN_TWO')}  # here by default 'do not matters'

response = requests.get(url, params=params, headers=headers)
if response.ok:
    soup = bs(response.text, 'html.parser')
    try:
        car_links = soup.find_all('a', attrs={'class': 'ListingPagination__page'})
        last_page = car_links[-1].getText()
    except Exception as exc:
        sys.stderr.write(f'Last page not found. {exc}')
    else:
        last_page = int(last_page)
        if last_page and (num_pages > last_page or num_pages is None):
            num_pages = last_page
        for page in tqdm(range(1, num_pages + 1), total=num_pages):
            params['page'] = page
            page_content = requests.get(url, params=params, headers=headers)  # gets random list of cars every time
            if page_content.ok:
                page_content.encoding = 'utf-8'
                soup = bs(page_content.text, 'html.parser')
                items = soup.find_all('div', attrs={'class': 'ListingItem__main'})
                for idx, item in enumerate(items):
                    description = {}
                    description['Model'] = item.find('a', attrs={'class': 'Link ListingItemTitle__link'}).getText()
                    description['Year'] = item.find('div', attrs={'class': 'ListingItem__year'}).getText()
                    mileage = item.find('div', attrs={'class': 'ListingItem__kmAge'}).getText().replace(u'\xa0', u'')
                    try:
                        description['Mileage'] = float(re.search('\d+', mileage).group(0))
                    except Exception as exc:
                        # sys.stderr.write(f'{idx} row error: {exc}')
                        description['Mileage'] = 0.0  # new cars
                    list_t = item.find_all('div', attrs={'class': 'ListingItemTechSummaryDesktop__cell'})
                    list_t = [ls.getText().replace(u'\u2009', u'').replace(u'\xa0', u'').split('/') for ls in list_t]
                    description['EngineType'] = list_t[0][2]
                    # электро и остальные: л.с. и кВТ -> объем и л.с.
                    try:
                        description['V_engine'] = float(list_t[0][0].split()[0])
                    except:
                        description['V_engine'] = float(list_t[0][1].lower().split('к')[0])
                    if not ('электро' in description['EngineType'].lower()):
                        horse = re.search('\d+', list_t[0][1]).group(0)
                        description['HorsePower'] = float(horse)
                    else:
                        horse = re.search('\d+', list_t[0][0]).group(0)
                        description['HorsePower'] = float(horse)
                    description['Selector'], description['CarBodyType'], description['Drive'], description['Color'] = *list_t[1], *list_t[2], *list_t[3], *list_t[4]
                    try:
                        price = item.find('div', attrs={'class': 'ListingItem__columnCellPrice'}).getText()
                        price = re.search('\d+', price.replace(u'\xa0', u'')).group(0)
                        description['Price'] = float(price)
                    except:
                        continue
                    df = df.append(description, ignore_index=True)
else:
    sys.stderr.write('Got 4xx/5xx response')

df.to_csv('autoru.csv', index=False, encoding='utf-8')
