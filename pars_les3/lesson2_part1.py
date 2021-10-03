import pandas as pd
import argparse
import requests
import sys
import re
from tqdm import tqdm
from bs4 import BeautifulSoup as bs


def parse_hh(url, params, headers, num_pages=5, with_df=False):
    if with_df:
        df = pd.DataFrame(columns=['Vacancy', 'Salary_min', 'Salary_max', 'Currency', 'Vac_link', 'Source',
                                   'Employee', 'Area'])
    else:
        vacancies_list_of_dicts = []

    while params['page'] < num_pages:
        print(f'parsing page no {params["page"] + 1}')
        response = requests.get(url, params=params, headers=headers)
        soup = bs(response.text, 'html.parser')

        vacancy_list = soup.find_all('div', attrs={'class': 'vacancy-serp-item'})

        if not vacancy_list or not response.ok:
            break

        for idx, item in enumerate(vacancy_list):
            vacancies = {}
            try:
                item_info = item.find('a', attrs={'class': 'bloko-link'})
                vacancies['Vacancy'] = item_info.getText()
                vacancies['Vac_link'] = item_info['href'].split('?')[0]
                vacancies['Source'] = ''.join(url.split('/')[2])
                vacancies['Employee'] = item.find('a', attrs={'class': 'bloko-link_secondary'}).getText().replace(u'\xa0', u' ')
                vacancies['Area'] = item.find('span', attrs={'class': 'vacancy-serp-item__meta-info'}).getText().split(',')[0]
                salary = item.find('span', attrs={'class': 'bloko-header-section-3_lite', 'data-qa': 'vacancy-serp__vacancy-compensation'})
                if not salary:
                    salary_min, salary_max, currency = None, None, None
                else:
                    salary = salary.getText()
                    salary = salary.split()
                    currency = salary[-1]
                    salary = ''.join(salary)
                    salary_values = re.findall('\d+', salary)
                    if salary.startswith('от'):
                        salary_min = float(salary_values[0])
                        salary_max = None
                    elif salary.startswith('до'):
                        salary_min = None
                        salary_max = float(salary_values[0])
                    else:
                        salary_min = float(salary_values[0])
                        salary_max = float(salary_values[1])
                vacancies['Salary_min'], vacancies['Salary_max'], vacancies['Currency'] = salary_min, salary_max, currency
            except Exception as exc:
                sys.stderr.write(f'An error {exc} was occurred while parsing {idx}\n')
                continue
            if with_df:
                df = df.append(vacancies, ignore_index=True)
            else:
                vacancies_list_of_dicts.append(vacancies)

        params['page'] += 1

    return df if with_df else vacancies_list_of_dicts


def parse_sjob(url, params, headers, num_pages=None, with_df=False):
    if with_df:
        df = pd.DataFrame(columns=['Vacancy', 'Salary_min', 'Salary_max', 'Currency', 'Vac_link', 'Source',
                                   'Employee', 'Area'])
    else:
        vacancies_list_of_dicts = []
    source = url.split('/')[-1]
    global_url = url
    url += '/vacancy/search/'

    response = requests.get(url, params=params, headers=headers)
    if response.ok:
        soup = bs(response.text, 'html.parser')
        next_button_a = soup.find('a', attrs={'class': 'f-test-button-dalshe'})
        if not next_button_a:
            num_pages = 1
        else:
            next_button_a = next_button_a.findParent()
            next_button_a = next_button_a.find_all('a')[-2].getText()
            if num_pages > int(next_button_a) or num_pages is None:
                num_pages = int(next_button_a)
    else:
        sys.stderr.write('An error of type 4xx/5xx occurred.')
        return
    for page in tqdm(range(1, num_pages + 1), total=num_pages):
        # print(f'Parsing from page no {page}.')
        params['page'] = page
        page_content = requests.get(url, params=params, headers=headers)
        if page_content.ok:
            soup = bs(page_content.text, 'html.parser')
            blocks = soup.find_all('div', attrs={'class': 'f-test-vacancy-item'})
            if not blocks: break
            for block in blocks:
                vacancies = {}
                vacancies['Source'] = source
                block_info = block.find('div', attrs={'class': 'jNMYr GPKTZ _1tH7S'})
                block_a = block_info.find('a')
                vacancies['Vac_link'] = global_url + block_a['href']
                vacancies['Vacancy'] = block_a.getText()
                salary = block_info.find('span', attrs={'class': 'f-test-text-company-item-salary'})
                if not salary:
                    salary_min, salary_max, currency = None, None, None
                else:
                    salary = salary.getText()
                    salary_values = salary.split()
                    salary_values = ''.join(salary_values)
                    salary_values = re.findall('\d+', salary_values)
                    if len(salary_values) == 0:
                        salary_min, salary_max, currency = None, None, None  # 'по договоренности' == None
                    else:
                        if salary.startswith('от'):
                            salary_min, salary_max = float(salary_values[0]), None
                        elif salary.startswith('до'):
                            salary_min, salary_max = None, float(salary_values[0])
                        elif len(salary_values) == 1:
                            salary_min, salary_max = float(salary_values[0]), None
                        else:
                            salary_min, salary_max = float(salary_values[0]), float(salary_values[1])
                        currency = salary.split('/')[0].split()[-1]
                vacancies['Salary_min'], vacancies['Salary_max'], vacancies['Currency'] = salary_min, salary_max, currency
                try:
                    vacancies['Employee'] = block.find('span', attrs={'class': 'f-test-text-vacancy-item-company-name'}).getText()
                except Exception as exc:
                    vacancies['Employee'] = None
                location = block.find('span', attrs={'class': 'f-test-text-company-item-location'}) #.getText()
                spans = location.find_all('span')
                vacancies['Area'] = spans[2].getText().split(',')[0]

                if with_df:
                    df = df.append(vacancies, ignore_index=True)
                else:
                    vacancies_list_of_dicts.append(vacancies)
        else:
            sys.stderr.write(f'No page with number {page}.')
            continue

    return df if with_df else vacancies_list_of_dicts

if __name__ == '__main__':

    inputer = argparse.ArgumentParser()
    inputer.add_argument('-v', '--vacancy', required=True, help='set vacancy name to parse')
    inputer.add_argument('-n', '--num_pages', required=True, help='set number of pages')
    args = vars(inputer.parse_args())
    num_pages = int(args['num_pages'])
    vacancy = args['vacancy']

    # https://hh.ru/search/vacancy
    url_hunter = 'https://hh.ru/search/vacancy'
    params_hunter = {
        'text': vacancy,
        'items_on_page': 20,
        'page': 0
    }
    # https://superjob.ru/vacancy/search/
    url_super = 'https://superjob.ru'
    params_super = {
        'keywords': vacancy,
        'page': 1,
        'noGeo': 1
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'}

    df_hunter = parse_hh(url_hunter, params_hunter, headers, num_pages=num_pages)
    df_super = parse_sjob(url_super, params_super, headers, num_pages=num_pages)

    #df_super.to_csv('super.csv', index=False, encoding='utf-8')
    #df_hunter.to_csv('hunter_100.csv', index=False, encoding='utf-8')

    final_df = pd.concat([df_super, df_hunter], axis=0)
    final_df.to_csv('final.csv', index=False, encoding='utf-8')
