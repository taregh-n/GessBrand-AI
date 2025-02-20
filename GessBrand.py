import requests
import re
from bs4 import BeautifulSoup
import mysql.connector
from getpass import getpass
from sklearn import tree


# Define Funections -->
def brandCollector(link):
    dataList = list()
    pageRec = requests.get(link)
    pageSoup = BeautifulSoup(pageRec.text, 'html.parser')
    all_title = pageSoup.find_all('h2', attrs={'class': 'product-title'})
    for h in all_title:
        brand = re.search('^\w+', h.text.strip()).group(0)
        GB = re.search('- (\d+)GB *\-' , h.text.strip()) or re.search('- (\d+)GB *$' , h.text.strip()) or None
        if GB != None:
            GB = re.search('\d+' , GB.group(0))
            GB = int(GB.group(0))
        else:
            GB = ''
        dataList.append([brand, GB])
    return dataList

def priceCollector(link):
    dataList = list()
    pageRec = requests.get(link)
    pageSoup = BeautifulSoup(pageRec.text, 'html.parser')
    all_price = pageSoup.find_all('div', attrs={'class': 'product-price'})
    for p in all_price:
        price = re.search('^([\d,]*)', p.text.strip()).group(0)
        price = int(price.replace(',', ''))
        dataList.append(price)
    return dataList

# find number of pages -->
link ='https://gooshishop.com/category/mobile/in-stock/'
rec = requests.get(link)
soup = BeautifulSoup(rec.text, 'html.parser')
lastpageLi = soup.find('li', attrs={'class': 'PagedList-skipToLast'})
lastpageLink = lastpageLi.find('a').get('href')
numberOfPages = int(re.search('(\d*)$', lastpageLink).group(0))

# collect data from pages -->
brands = []
pageCoun = 1
for n in range(numberOfPages):
    link = 'https://gooshishop.com/category/mobile/in-stock/page-%s' % pageCoun
    brandsOfPage = brandCollector(link)
    brands += brandsOfPage
    pageCoun += 1
    print('Brandes data Collected from link: ', link)

prices = []
pageCoun = 1
for n in range(numberOfPages):
    link = 'https://gooshishop.com/category/mobile/in-stock/page-%s' % pageCoun
    pricesOfPage = priceCollector(link)
    prices += pricesOfPage
    pageCoun += 1
    print('Prices data Collected from link: ', link)
print('\nAll data collected successfully.')

# save data in database -->
print('Enter database conecting information to save data.')
db_user = input('database user: ')
db_password = getpass('database password: ')
db_host = input('host (defult: 127.0.0.1): ') or '127.0.0.1'
db_name = input('database name: ')

cnx = mysql.connector.connect(user= db_user, password= db_password, host= db_host, database= db_name)
curser = cnx.cursor()
curser.execute('CREATE TABLE IF NOT EXISTS mobiles (brand TEXT, storage INTEGER, price INTEGER)')
cnx.commit()
for i, j in zip(brands, prices):
    brand = i[0]
    storage = i[1]
    if storage == '':
        storage = 0
    price = j
    curser.execute('INSERT INTO mobiles VALUES (\'%s\', %i, %i);'  %(brand, storage, price))
    cnx.commit()
curser.execute('DELETE FROM mobiles WHERE storage = 0;')
cnx.commit()
cnx.close()


# ML: guess mobile brand from storage size and it's price :| ...!!  -->
cnx = mysql.connector.connect(user= db_user, password= db_password,
                              host= db_host,
                              database= db_name)
cursor = cnx.cursor()
cursor.execute('SELECT storage, price FROM mobiles;')
x = [[storage, price] for storage, price in cursor]
cursor.execute('SELECT brand FROM mobiles;')
y = [brand for brand in cursor]
clf = tree.DecisionTreeClassifier()
clf = clf.fit(x, y)
new_storage = int(input('Enter storage of your mobile: '))
new_price = int(input('Enter price of your mobile (Toman): '))
new = [[new_storage , new_price]]
answer = clf.predict(new)
print('Maybe Your Mobile Brand\'s is: ' , answer[0], '\nMaybe Not...!')
cursor.execute('DELETE FROM mobiles;')
cnx.commit()
cnx.close()
