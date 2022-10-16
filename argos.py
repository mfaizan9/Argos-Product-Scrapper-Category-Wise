import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import csv
from concurrent.futures import ThreadPoolExecutor
import time
from tqdm.notebook import tqdm
from tqdm import tqdm as tqdm2
from tqdm.contrib.concurrent import thread_map

print('================================================================')
print('\n')
print('WELCOME to ARGOS SCRAPPER')
print('\n')
print('================================================================')


parentURL = 'https://www.argos.co.uk/browse/home-and-furniture/bedroom-furniture/beds/kids-beds/c:29869/'
# total pages

# High Sleeper, Bunk Bed, Mid Sleeper, Cabin Bed, Gaming Bed

Total_Data = []
# get data from product API
def getdata(url):
    product_num = url.split('/')[-1].split('?')[0]
    link = f'https://www.argos.co.uk/product-api/pdp-service/partNumber/{product_num}'

    headers = {
        'user-agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'
    }
    r = requests.get(link, headers=headers).json()
    usefuldata = r['data']
    attributes = usefuldata['attributes']
    included = r['included']
    product_attribs = included[0]['attributes']
    # dimensions
    try:
        for i in range(len(included)):
            id = usefuldata['id']
            type_ = 'dimensions'
            dic = included[i]
            if dic['id'] == id and dic['type'] == type_:
                try:
                    dims = (dic['attributes']['packageSizeOne']).replace('H','').replace('W','').replace('D','').replace('cm','').split(', ')
                    h = float(dims[0])
                    w = float(dims[1])
                    d = float(dims[2])
                    V = round((h * w * d) / (100**3), 2)
                except:
                    try:
                        h = dic['attributes']['bedHeight'].replace('cm' , '')
                    except:
                        h = ''
                    try:
                        w = dic['attributes']['bedWidth'].replace('cm' , '')
                    except:
                        w = ''
                    
                    d = ''
                    V = ''

                break
    except:
        h = ''
        w = ''
        d = ''
        V = ''
    # reviews
    try:
        for i in range(len(included)):
            id = usefuldata['id']
            type_ = 'reviewstatistics'
            dic = included[i]
            if dic['id'] == id and dic['type'] == type_:
                try:
                    reviews_attribs = dic['attributes']
                    reviewcount = reviews_attribs['reviewCount']
                    avgRating = round(float(reviews_attribs['avgRating']), 1)
                    break
                except:
                    pass
    except:
        pass

    # Retailer
    retailer = 'Argos'
    # Category
    category = 'Beds'
    # Sub Category
    subcategory = 'Kids Beds'
    # Product Link
    productlink = url
    # Retailer Number
    RetailerNumber = usefuldata['id']
    # Brand
    Brand = attributes['brand'].replace('Argos', '').strip()
    # SKU Description
    SKUDescription = attributes['name'].replace('Argos','').replace(Brand, '').strip()
    # Sub Sub Category
    if 'bunk' in SKUDescription.lower() and 'bed' in SKUDescription.lower():
        subsubcat = 'Bunk Beds'
    elif 'frame' in SKUDescription.lower() and 'bed' in SKUDescription.lower():
        subsubcat = 'Bed Frames'
    elif 'mid' in SKUDescription.lower() and 'sleeper' in SKUDescription.lower():
        subsubcat = 'Mid Sleeper'
    elif 'high' in SKUDescription.lower() and 'sleeper' in SKUDescription.lower():
        subsubcat = 'High Sleeper'
    elif 'toddler' in SKUDescription.lower():
        subsubcat = 'Toddler Beds'
    elif 'cabin' in SKUDescription.lower() and 'bed' in SKUDescription.lower():
        subsubcat = 'Cabin Beds'
    elif 'trundle' in SKUDescription.lower():
        subsubcat = 'Trundle'
    else:
        subsubcat = ''
    # Color
    try:
        colour = product_attribs['variants'][0]['attributes'][0]['value']
    except:
        try:
            colour = SKUDescription.split('-')
            if len(colour)>1:
                colour = colour[-1].strip()
            else:
                colour = ''
        except:
            colour = ''
    # Material

    # Dimension: L
    # Length = h
    # # Dimension: W
    # Width = w
    # # Dimension: H
    # Height = d
    # # Volume
    # Volume = V
    # Price
    pound = (u"\xA3")
    Price = attributes['price']['now']
    Price2 = attributes['price']['was']
    Promo_Retail = pound + '0'
    if Price2 is None:
        Full_Retail_Price = pound + str(Price)
    else:
        Full_Retail_Price = pound + str(Price2)
        Promo_Retail = pound + str(Price)

    # Average Rating
    AverageRating = avgRating
    # No. of Reviews
    NoofReviews = reviewcount

    my_data = {
        'Retailer': 'Argos',
        'Category': 'Beds',
        'Sub Category': 'Kids Beds',
        'Sub Sub Category': subsubcat,
        'Product Link': url,
        'Retailer No': RetailerNumber,
        'Brand': Brand,
        'SKU Description': SKUDescription,
        'Color': colour,
        'Dims L (cm)': h,
        'Dims W (cm)': w,
        'Dims H (cm)': d,
        'Volume (m3)': V,
        f'Full Retail Price ({pound})': Full_Retail_Price,
        f'Promo Retail ({pound})': Promo_Retail,
        'Star Rating': AverageRating,
        'No. of Reviews': NoofReviews
    }
    Total_Data.append(my_data)
    return



# get product links from a page.
ProductLINKS = []


def itemlinks(url2):
    headers = {
        'user-agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'
    }
    r = requests.get(url2, headers=headers).text
    soup = BeautifulSoup(r, 'lxml')
    atags = soup.find_all('a',
                          class_='ProductCardstyles__Title-h52kot-12 PQnCV')
    pre = 'https://www.argos.co.uk'
    for i in atags:
        pLINK = pre + i['href']
        ProductLINKS.append(pLINK)

    return


def getProds(url):

    headers = {
        'user-agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'
    }
    x = 1
    while x<=5:
        link = url + f'/opt/page:{x}'
        r = requests.get(link, headers=headers).text
        sent = 'Oops, that didn&#x27;t go to plan'
        tf = sent in r
        if tf == True:
            break
        itemlinks(link)
        x = x + 1
    return


getProds(parentURL)

print(f'{len(ProductLINKS)} products found.')
print('\n')
print('Scrapping Products')
print('\n')
try:
    thread_map(getdata , ProductLINKS , max_workers=10)
except:
    print(f'{len(Total_Data)}/{len(ProductLINKS)} products has been scrapped, due to IP Ban (because of too many requests sent.')
    pass


print('\n')

df = pd.DataFrame(Total_Data)
df.to_excel('KidsBeds.xlsx' , index=False)

print('Data stored to EXCEL FILE.')

    
