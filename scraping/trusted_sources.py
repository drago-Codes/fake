import requests
from bs4 import BeautifulSoup
import re
from rapidfuzz import fuzz

def search_trusted_sources(query):
    # Collect all products from all sources
    products = []
    # Amazon India search
    try:
        search_url = f'https://www.amazon.in/s?k={requests.utils.quote(query)}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        resp = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        for product in soup.find_all('div', {'data-component-type': 's-search-result'}):
            title = product.h2.get_text(strip=True) if product.h2 else ''
            link = product.h2.a['href'] if product.h2 and product.h2.a else ''
            price = product.find('span', {'class': 'a-price-whole'})
            price = price.get_text(strip=True).replace(',', '') if price else ''
            img = product.find('img', {'class': 's-image'})
            images = [img['src']] if img else []
            seller = 'Amazon Seller'
            products.append({
                'source': 'Amazon India',
                'title': title,
                'description': '',
                'price': price,
                'images': images,
                'seller': seller,
                'url': f'https://www.amazon.in{link}' if link else ''
            })
    except Exception as e:
        print(f'Amazon search error: {e}')
    # Flipkart search
    try:
        search_url = f'https://www.flipkart.com/search?q={requests.utils.quote(query)}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        resp = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        product = soup.find('div', {'class': '_1AtVbE'})
        if product:
            title = product.find('div', {'class': '_4rR01T'})
            title = title.get_text(strip=True) if title else ''
            link = product.find('a', {'class': '_1fQZEK'})
            link = link['href'] if link else ''
            price = product.find('div', {'class': '_30jeq3 _1_WHN1'})
            price = price.get_text(strip=True).replace('₹', '').replace(',', '') if price else ''
            img = product.find('img', {'class': '_396cs4'})
            images = [img['src']] if img else []
            seller = 'Flipkart Seller'
            products.append({
                'source': 'Flipkart',
                'title': title,
                'description': '',
                'price': price,
                'images': images,
                'seller': seller,
                'url': f'https://www.flipkart.com{link}' if link else ''
            })
    except Exception as e:
        print(f'Flipkart search error: {e}')
    # Snapdeal search
    try:
        search_url = f'https://www.snapdeal.com/search?keyword={requests.utils.quote(query)}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        resp = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        product = soup.find('div', {'class': 'product-tuple-listing'})
        if product:
            title = product.find('p', {'class': 'product-title'})
            title = title.get_text(strip=True) if title else ''
            link = product.find('a', {'class': 'dp-widget-link'})
            link = link['href'] if link else ''
            price = product.find('span', {'class': 'lfloat product-price'})
            price = price.get_text(strip=True).replace('₹', '').replace(',', '') if price else ''
            img = product.find('img', {'class': 'product-image'})
            images = [img['src']] if img else []
            seller = 'Snapdeal Seller'
            products.append({
                'source': 'Snapdeal',
                'title': title,
                'description': '',
                'price': price,
                'images': images,
                'seller': seller,
                'url': link
            })
    except Exception as e:
        print(f'Snapdeal search error: {e}')
    # Tata Cliq search
    try:
        search_url = f'https://www.tatacliq.com/search/?searchCategory=all&text={requests.utils.quote(query)}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        resp = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        product = soup.find('div', {'class': 'ProductModule__productModule'})
        if product:
            title = product.find('h2', {'class': 'ProductModule__productName'})
            title = title.get_text(strip=True) if title else ''
            link = product.find('a', {'class': 'ProductModule__productLink'})
            link = 'https://www.tatacliq.com' + link['href'] if link and link.has_attr('href') else ''
            price = product.find('div', {'class': 'ProductModule__price'})
            price = price.get_text(strip=True).replace('₹', '').replace(',', '') if price else ''
            img = product.find('img', {'class': 'ProductModule__img'})
            images = [img['src']] if img else []
            seller = 'Tata Cliq Seller'
            products.append({
                'source': 'Tata Cliq',
                'title': title,
                'description': '',
                'price': price,
                'images': images,
                'seller': seller,
                'url': link
            })
    except Exception as e:
        print(f'Tata Cliq search error: {e}')
    # Reliance Digital search
    try:
        search_url = f'https://www.reliancedigital.in/search?q={requests.utils.quote(query)}:relevance'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        resp = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        product = soup.find('div', {'class': 'sp grid'})
        if product:
            title = product.find('p', {'class': 'sp__name'})
            title = title.get_text(strip=True) if title else ''
            link = product.find('a', {'class': 'sp__product-link'})
            link = 'https://www.reliancedigital.in' + link['href'] if link and link.has_attr('href') else ''
            price = product.find('span', {'class': 'sp__finalPrice'})
            price = price.get_text(strip=True).replace('₹', '').replace(',', '') if price else ''
            img = product.find('img', {'class': 'sp__product-img'})
            images = [img['src']] if img else []
            seller = 'Reliance Digital'
            products.append({
                'source': 'Reliance Digital',
                'title': title,
                'description': '',
                'price': price,
                'images': images,
                'seller': seller,
                'url': link
            })
    except Exception as e:
        print(f'Reliance Digital search error: {e}')
    # Fuzzy match to select best product
    best_score = 0
    best_product = None
    for p in products:
        score = fuzz.token_set_ratio(query, p['title']) / 100.0
        if score > best_score:
            best_score = score
            best_product = p
    if best_product and best_score >= 0.4:
        best_product['fuzzy_score'] = best_score
        return [best_product]
    else:
        return [{'source': 'No Match Found', 'title': '', 'description': '', 'price': '', 'images': [], 'seller': '', 'url': '', 'fuzzy_score': 0.0}] 