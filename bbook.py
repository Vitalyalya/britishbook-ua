import requests
from bs4 import BeautifulSoup

import sqlite3

conn = sqlite3.connect('bbooks.db')
curs = conn.cursor()

headers = {
    "accept": "*/*",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36"
    }

def find_links():
    s = requests.Session()
    url = 'https://www.britishbook.ua/sitemap-ru-four.xml'
    r = s.get(url=url, headers=headers)  
    src = r.text
    soup = BeautifulSoup(src, "lxml")
    all_links = soup.find_all('url')

    return all_links
    
def main():

    all_links = find_links()

    total_pages = len(all_links)

    c = 0
            
    for links in all_links:
        
        book_link = links.find('loc').text

        c += 1

        if curs.execute(f"SELECT EXISTS(SELECT 1 FROM bbooks WHERE link = \'{book_link}\')").fetchone() == (1,):
            print(book_link)
            print(f'Book #{c} is in the database already!')

            continue

        s = requests.Session()
        url = book_link
        r = s.get(url=url, headers=headers) 
        src = r.text
        soup = BeautifulSoup(src, "lxml")

        resp = r.status_code
        print(r.status_code)

        if resp != 200:
            continue

        table = soup.find('table', class_ = 'serii_tabs-opisanie_tab')

        if table is None:

            rows = None
            isbn = None
            manuf = None
            pereplet = None
            pages__number = None

        for row in table:

            if 'Тип товара: ' in row.text:
                rows = row.find_all('td')
                rows = rows[1].text.strip()

            elif 'ISBN:' in row.text:
                isbn = row.find_all('td')
                isbn = isbn[1].text.strip()

            elif 'Производитель:' in row.text:
                manuf = row.find_all('td')
                manuf = manuf[1].text.strip()

            elif 'Переплет: ' in row.text:
                    pereplet = row.find_all('td')
                    pereplet = pereplet[1].text.strip()
            
            elif 'Количество страниц: ' in row.text:
                    pages__number = row.find_all('td')
                    pages__number = pages__number[1].text.strip()

        title = soup.find('h1', class_ = 'element_name').text.replace(rows, '').strip()

        avail = soup.find('div', class_ = 'element_nalic-da')
        not_avail = soup.find('div', class_ = 'element_nalic-net')

        if avail is not None:
            availability = 'В наличии'

        elif not_avail is not None:
            availability = 'Нет в наличии'
        
        try:

            price = soup.find('div', class_ = 'element_price-main').text.replace(' грн', '').replace(' ', '').replace(',', '.')
            price = round(float(price), 2)

        except:

            price = None            

        print(f'Book #{c}/{total_pages}')
        print(f'Title: {title}')
        print(f'ISBN: {isbn}')
        print(f'Manufacturer: {manuf}')

        try:
            print(f'Cover: {pereplet}')
        except: 
            pereplet = None
            print(f'Cover: {pereplet}')

        try:
            print(f'Pages_number: {pages__number}')    
        except:
            pages__number = None
            print(f'Pages_number: {pages__number}')

        print(f'Type: {rows}')
        print(f'Price: {price}')
        print(availability)
        print(f'Link: {book_link}')
    
        curs.execute("INSERT INTO bbooks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (title, isbn, manuf, pereplet, pages__number, rows, price, availability, book_link))
        print('Book added to db queue!\n_____________________*************_____________________\n')

        if c % 10 == 0:
            conn.commit()    
            
    conn.commit()    
    conn.close()

if __name__ == "__main__":
    main()