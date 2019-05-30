# -*- coding: utf-8 -*-
# парсер карточек товара для сайта sportssss.com
import requests
from bs4 import BeautifulSoup
from random import choice, uniform
from time import sleep, time
from multiprocessing import Pool
import csv
import re
import os


BASE_URL = 'http://www.wedaili.com'
ADDITIONAL_URL = '/asics-跑步鞋-c-1330/'
product_hrefs = []


# получение Html начальной страницы
def get_html(url, useragent=None, proxy=None):
	r = requests.get(url, headers=useragent, proxies=proxy)
	return r.text


# получение объекта со списками юзерагентов и прокси
def get_useragents_and_proxies():
    useragents_file = open('useragents.txt')
    proxies_file = open('proxies.txt')
    useragents = useragents_file.read().split('\n')
    proxies = proxies_file.read().split('\n')
    useragents_file.close()
    proxies_file.close()
    useragents_and_proxies = {
        'useragents': useragents,
        'proxies':  proxies
    }
    return useragents_and_proxies


# получение ссылок на категории с выбранной страницы
def get_category_hrefs(html):
    soup = BeautifulSoup(html, 'lxml')
    blocks = soup.find_all('div', class_='categoryListBoxContents')
    hrefs = [a.find('a').get('href') for a in blocks]
    return hrefs


# получение списка ссылок на товары с ОДНОЙ страницы
def get_product_hrefs(html):
    soup = BeautifulSoup(html, 'lxml')
    titles = soup.find_all('h3', class_='itemTitle')
    hrefs = [a.find('a').get('href') for a in titles]
    return hrefs


# получение количества страниц
def get_page_num(html):
    soup = BeautifulSoup(html, 'lxml')
    block = soup.find('div', id='productsListingListingBottomLinks')
    last_page = False
    try:
        page_hrefs = block.find_all('a')
        last_page = int(page_hrefs[-2].text.strip())
        return last_page
    except:
        return last_page


# проверка наличия контента на странице
def is_empty(html):
    soup = BeautifulSoup(html, 'lxml')
    try:
       cell = soup.find('th', id='listCell0-0').text.strip()
       if cell == '本分类中没有商品。':
           return True
    except:
        return False
    return False


#получение списка ссылок на товары с ВСЕХ страниц
def get_all_products_hrefs(category_href):

    useragents_and_proxies = get_useragents_and_proxies()
    useragents = useragents_and_proxies['useragents']
    html = get_html(category_href, useragent={'User-Agent': choice(useragents)})

    if not is_empty(html):
        last_page = get_page_num(html)
        if last_page:
            for page in range(1, last_page):
                url = category_href + '?page=' + str(page)
                html = get_html(url, useragent={'User-Agent': choice(useragents)})
                product_hrefs_page = get_product_hrefs(html)
                for i in product_hrefs_page:
                    get_product_data(i)
        else:
            html = get_html(category_href, useragent={'User-Agent': choice(useragents)})
            product_hrefs_page = get_product_hrefs(html)
            for i in product_hrefs_page:
                get_product_data(i)


# сбор данных с карточки товара
def get_product_data(url):

    try:
        delay = uniform(1, 2)

        useragents_and_proxies = get_useragents_and_proxies()
        useragents = useragents_and_proxies['useragents']
        html = get_html(url, useragent={'User-Agent': choice(useragents)})

        soup = BeautifulSoup(html, 'lxml')

        title_raw = soup.find('h1', id='productName').text.strip()
        TITLE = re.sub('[^0-9aA-zZ \{\}\#\-\.]', '', title_raw)
        directory_name = 'catalog/'+TITLE
        os.mkdir(directory_name)

        IMAGE_HREFS = []
        try:
        	all_imgs = soup.find_all('div', class_='additionalImages')
        	IMAGE_HREFS = [a for a in all_imgs]
        except:
        	pass
        IMAGE_HREFS.append(soup.find('div', id='productMainImage'))
        for img_href in IMAGE_HREFS:
        	img_real_href = get_img_real_href(img_href)
        	save_image(directory_name+'/'+get_name(img_real_href), get_file(BASE_URL + '/' + img_real_href))

        file_path = directory_name + '/' + 'info.txt'
        PRICE = soup.find('h2', class_='productGeneral').text.strip()
        write_file(file_path, PRICE + '\n')

        sizes_html = soup.find('div', class_='wrapperAttribsOptions').find_all('option')
        SIZES = [v.text.strip() for v in sizes_html]
        for size in SIZES:
        	write_file(file_path, size)

        sleep(delay)
    except:
        return False


def get_img_real_href(href):
	b = href.find('script')
	return re.search('(href)=["]?((?:.(?!["]?\s+(?:\S+)=|[>"]))+.)["]?', str(b)).group(2)


# запись в файл
def write_file(path, data):
	with open(path, mode='a', encoding='utf8', errors="ignore") as f:
		f.write(data + '\n')


def get_file(url):
	r = requests.get(url, stream=True)
	return r


def get_name(url):
	name = url.split('/')[-1]
	return name


# сохранение картинок
def save_image(name, file_object):
	with open(name, 'bw') as f:
		for chunk in file_object.iter_content(8192):
			f.write(chunk)




def main():

    useragents_and_proxies = get_useragents_and_proxies()
    useragents = useragents_and_proxies['useragents']
    proxies = useragents_and_proxies['proxies']

    url = BASE_URL + ADDITIONAL_URL
    html = get_html(url, useragent={'User-Agent': choice(useragents)})

    category_hrefs = get_category_hrefs(html)

    with Pool(15) as pool:
        pool.map(get_all_products_hrefs, category_hrefs)




if __name__ == '__main__':
    main()