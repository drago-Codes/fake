import requests
from bs4 import BeautifulSoup
import re
from rapidfuzz import fuzz


def search_trusted_sources(query):
    """
    Searches trusted e-commerce sources for a given product query and returns
    the best matching product based on fuzzy title matching.

    Args:
        query (str): The product query string.

    Returns:
        list: A list containing a dictionary of the best matching product
              information, or a list with a "No Match Found" entry if no
              suitable product is found.
    """
    # Collect all products from all sources
    products = []

    # --- Amazon India Search ---
    try:
        # Construct the search URL for Amazon India
        search_url = f'https://www.amazon.in/s?k={requests.utils.quote(query)}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        resp = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        for product in soup.find_all('div', {'data-component-type': 's-search-result'}):
            # Extract product title
            title = product.h2.get_text(strip=True) if product.h2 else ''
            # Extract product link
            link = product.h2.a['href'] if product.h2 and product.h2.a else ''
            # Extract product price
            price = product.find('span', {'class': 'a-price-whole'})
            price = price.get_text(strip=True).replace(',', '') if price else ''
            # Extract product image URL
            img = product.find('img', {'class': 's-image'})
            images = [img['src']] if img else []
            seller = 'Amazon Seller'

            # Append the extracted product information to the products list
            # Note: Description is not easily available on search results, so it's left empty.
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
        # Log any errors encountered during Amazon scraping
        print(f'Amazon search error: {e}')

    # --- Flipkart Search ---
    try:
        # Construct the search URL for Flipkart
        search_url = f'https://www.flipkart.com/search?q={requests.utils.quote(query)}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        resp = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Find the first product listing
        product = soup.find('div', {'class': '_1AtVbE'})
        if product:
            # Extract product title
            title = product.find('div', {'class': '_4rR01T'})
            title = title.get_text(strip=True) if title else ''
            # Extract product link
            link = product.find('a', {'class': '_1fQZEK'})
            link = link['href'] if link else ''
            # Extract product price
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
        # Log any errors encountered during Flipkart scraping
        print(f'Flipkart search error: {e}')

    # --- Snapdeal Search ---
    try:
        # Construct the search URL for Snapdeal
        search_url = f'https://www.snapdeal.com/search?keyword={requests.utils.quote(query)}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        resp = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Find the first product listing
        product = soup.find('div', {'class': 'product-tuple-listing'})
        if product:
            # Extract product title
            title = product.find('p', {'class': 'product-title'})
            title = title.get_text(strip=True) if title else ''
            # Extract product link
            link = product.find('a', {'class': 'dp-widget-link'})
            link = link['href'] if link else ''
            # Extract product price
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
        # Log any errors encountered during Snapdeal scraping
        print(f'Snapdeal search error: {e}')

    # --- Tata Cliq Search ---
    try:
        # Construct the search URL for Tata Cliq
        search_url = f'https://www.tatacliq.com/search/?searchCategory=all&text={requests.utils.quote(query)}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        resp = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Find the first product listing
        product = soup.find('div', {'class': 'ProductModule__productModule'})
        if product:
            # Extract product title
            title = product.find('h2', {'class': 'ProductModule__productName'})
            title = title.get_text(strip=True) if title else ''
            # Extract product link
            link = product.find('a', {'class': 'ProductModule__productLink'})
            link = 'https://www.tatacliq.com' + link['href'] if link and link.has_attr('href') else ''
            # Extract product price
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
        # Log any errors encountered during Tata Cliq scraping
        print(f'Tata Cliq search error: {e}')

    # --- Reliance Digital Search ---
    try:
        # Construct the search URL for Reliance Digital
        search_url = f'https://www.reliancedigital.in/search?q={requests.utils.quote(query)}:relevance'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        resp = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Find the first product listing
        product = soup.find('div', {'class': 'sp grid'})
        if product:
            # Extract product title
            title = product.find('p', {'class': 'sp__name'})
            title = title.get_text(strip=True) if title else ''
            # Extract product link
            link = product.find('a', {'class': 'sp__product-link'})
            link = 'https://www.reliancedigital.in' + link['href'] if link and link.has_attr('href') else ''
            # Extract product price
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
        # Log any errors encountered during Reliance Digital scraping
        print(f'Reliance Digital search error: {e}')

    # Fuzzy match to select best product
    best_score = 0
    best_product = None
    for p in products:
        # Calculate fuzzy similarity score between the query and product title
        score = fuzz.token_set_ratio(query, p['title']) / 100.0
        # Update best product if current product has a higher score
        if score > best_score:
            best_score = score
            best_product = p
    if best_product and best_score >= 0.4:
        best_product['fuzzy_score'] = best_score
        return [best_product]
    # If no match found, but the query is from a trusted domain, return a self-match
    trusted_domains = ['amazon.in', 'flipkart.com', 'tatacliq.com', 'reliancedigital.in', 'snapdeal.com', 'myntra.com', 'nykaa.com', 'adidas.co.in', 'nike.com', 'puma.com', 'reebok.in', 'ajio.com']
    import re
    # If the query looks like a product title from a trusted domain, return a self-match
    for domain in trusted_domains:
        if domain in query.lower():
            return [{
                'source': domain,
                'title': query,
                'description': '',
                'price': '',
                'images': [],
                'seller': 'Trusted Seller',
                'url': '',
                'fuzzy_score': 1.0
            }]
    else:
        # Return "No Match Found" if no product meets the fuzzy score threshold
        return [{'source': 'No Match Found', 'title': '', 'description': '', 'price': '', 'images': [], 'seller': '', 'url': '', 'fuzzy_score': 0.0}] 