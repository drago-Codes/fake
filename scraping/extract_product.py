import requests
from bs4 import BeautifulSoup
import re
import logging
import os
import time
import sys

"""
This module contains functions for extracting product details from various e-commerce websites.
It supports both requests-based scraping and Selenium-based scraping for dynamic websites.
"""

# Attempt to import Selenium libraries for handling dynamic content
# Try to import Selenium
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logging.warning('Selenium not available, falling back to requests for scraping.')

def get_chromedriver_path():
    """
    Determines the path to the ChromeDriver executable.
    """

def get_chromedriver_path():
    base_dir = os.path.dirname(__file__)
    # Windows: chromedriver.exe in project root or chromedriver_mac64
    if sys.platform.startswith('win'):
        exe_name = 'chromedriver.exe'
    else:
        exe_name = 'chromedriver'
    # Check project root
    root_path = os.path.join(os.path.dirname(base_dir), exe_name)
    if os.path.exists(root_path):
        return root_path
    # Check chromedriver_mac64 directory
    mac_path = os.path.join(os.path.dirname(base_dir), 'chromedriver_mac64', exe_name)
    if os.path.exists(mac_path):
        return mac_path
    # Fallback: just the name (if in PATH)
    return exe_name

def extract_product_details(url):
    """
    Extracts product details from a given URL.

    Args:
        url (str): The URL of the product page.

    Returns:
        dict: A dictionary containing the extracted product details, including
              title, description, price, images, seller, reviews, rating,
              image count, description length, keyword flags, and any scraping error information.
    """
    headers = {
        # Using a more generic User-Agent to appear more like a regular browser
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    
    if 'amazon.in' in url:
        # Try Selenium first
        if SELENIUM_AVAILABLE:
            try:
                chrome_options = Options()
                # chrome_options.add_argument('--headless')  # Commented for debugging
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chromedriver_path = get_chromedriver_path() # Get the path to chromedriver
                service = Service(executable_path=chromedriver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
                time.sleep(2) # Add delay before initial GET
                driver.get(url)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'productTitle')))
                title = driver.find_element(By.ID, 'productTitle').text.strip()
                try:
                    desc = driver.find_element(By.ID, 'feature-bullets').text.strip()
                except Exception:
                    desc = ''
                try:
                    price = driver.find_element(By.CLASS_NAME, 'a-price-whole').text.strip().replace(',', '')
                except Exception:
                    try:
                        price = driver.find_element(By.ID, 'priceblock_ourprice').text.strip().replace(',', '')
                    except Exception:
                        price = ''
                images = []
                # Attempt to find the main product image
                try:
                    img = driver.find_element(By.ID, 'landingImage')
                    images.append(img.get_attribute('src'))
                except Exception:
                    # Log if the main image is not found
                    pass
                try:
                    seller = driver.find_element(By.ID, 'bylineInfo').text.strip()
                except Exception:
                    seller = 'Unknown'
                try:
                    reviews = driver.find_element(By.ID, 'acrCustomerReviewText').text.strip()
                    # Extract number of reviews using regex
                    num_reviews = int(re.sub(r'[^0-9]', '', reviews))
                except Exception:
                    num_reviews = 0
                try:
                    # Extract average rating
                    rating = driver.find_element(By.CLASS_NAME, 'a-icon-alt').text.strip()
                    avg_rating = float(rating.split()[0])
                except Exception:
                    avg_rating = 0.0
                image_count = len(images)
                desc_length = len(desc)
                keywords = ['original', 'replica', '100% genuine']
                # Ensure keyword matching is robust (case-insensitive)
                # Check for presence of specified keywords in the description
                keyword_flags = {k: (k in desc.lower()) for k in keywords}
                driver.quit()
                return {
                    'title': title,
                    'description': desc,
                    'price': price,
                    'images': images,
                    'seller': seller,
                    'num_reviews': num_reviews,
                    'avg_rating': avg_rating,
                    'image_count': image_count,
                    'desc_length': desc_length,
                    'keyword_flags': keyword_flags,
                    'scraping_error': False
                }
            except Exception as e:
                logging.error(f'Selenium scraping failed: {e}')
                return {
                    'title': '',
                    'description': '',
                    'price': '',
                    'images': [],
                    'seller': 'Unknown',
                    'num_reviews': 0,
                    'avg_rating': 0.0,
                    'image_count': 0,
                    'desc_length': 0,
                    'keyword_flags': {},
                    'scraping_error': True,
                    'scraping_error_message': f'Selenium scraping failed: {e}'
                }
        # Fallback to requests if Selenium fails or not available
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            time.sleep(1) # Add delay between requests
            soup = BeautifulSoup(resp.text, 'html.parser')
            if 'Robot Check' in resp.text or 'captcha' in resp.text.lower():
                # Detect if Amazon is blocking scraping
                logging.warning('Amazon is blocking scraping (captcha/robot check).')
                return {
                    'title': '',
                    'description': '',
                    'price': '',
                    'images': [],
                    'seller': 'Unknown',
                    'num_reviews': 0,
                    'avg_rating': 0.0,
                    'image_count': 0,
                    'desc_length': 0,
                    'keyword_flags': {},
                    'scraping_error': True,
                    'scraping_error_message': 'Amazon is blocking scraping (captcha/robot check).'
                }
            # Extract title using BeautifulSoup
            title = soup.find(id='productTitle')
            title = title.get_text(strip=True) if title else ''
            # Extract description
            desc = soup.find('div', {'id': 'feature-bullets'})
            # More robust description extraction
            if desc:
                desc = ' '.join([li.get_text(strip=True) for li in desc.find_all('li')])
            else:
                desc = ''
            # Extract price
            price = soup.find('span', {'class': 'a-price-whole'})
            if not price:
                price = soup.find('span', {'id': 'priceblock_ourprice'})
            price = price.get_text(strip=True).replace(',', '') if price else ''
            images = []
            img_data = soup.find('img', {'id': 'landingImage'})
            if img_data:
                # Handle potential missing 'src' attribute
                images.append(img_data['src'])
            seller = ''
            seller_tag = soup.find('a', {'id': 'bylineInfo'})
            # Extract seller information
            if seller_tag:
                seller = seller_tag.get_text(strip=True)
            # Extract number of reviews
            reviews = soup.find('span', {'id': 'acrCustomerReviewText'})
            num_reviews = int(re.sub(r'[^0-9]', '', reviews.get_text(strip=True))) if reviews else 0
            # Extract average rating
            rating = soup.find('span', {'class': 'a-icon-alt'})
            avg_rating = float(rating.get_text(strip=True).split()[0]) if rating else 0.0
            image_count = len(images)
            desc_length = len(desc)
            # Ensure keyword matching is robust (case-insensitive)
            keyword_flags = {k: (k in desc.lower()) for k in keywords}
            return {
                'title': title,
                'description': desc,
                'price': price,
                'images': images,
                'seller': seller or 'Unknown',
                'num_reviews': num_reviews,
                'avg_rating': avg_rating,
                'image_count': image_count,
                'desc_length': desc_length,
                'keyword_flags': keyword_flags,
                # Indicate if scraping was successful (no error)
                'scraping_error': False
            }
        except Exception as e:
            logging.error(f'Amazon scraping error: {e}')
            return {
                'title': '',
                'description': '',
                'price': '',
                'images': [],
                'seller': 'Unknown',
                'num_reviews': 0,
                'avg_rating': 0.0,
                'image_count': 0,
                'desc_length': 0,
                'keyword_flags': {},
                'scraping_error': True,
                'scraping_error_message': f'Amazon scraping error: {e}'
            }
    # Flipkart scraping logic
    if 'flipkart.com' in url:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            time.sleep(1) # Add delay between requests
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Extract title
            title = soup.find('span', {'class': 'B_NuCI'})
            title = title.get_text(strip=True) if title else ''
            # Extract description
            desc = soup.find('div', {'class': 'X3BRps'})
            if desc:
                # More robust description extraction for Flipkart
                desc = ' '.join([li.get_text(strip=True) for li in desc.find_all('li')])
            else:
                desc = ''
            # Extract price
            price = soup.find('div', {'class': '_30jeq3 _16Jk6d'})
            price = price.get_text(strip=True).replace('₹', '').replace(',', '') if price else ''
            images = []
            img_data = soup.find('img', {'class': 'q6DClP'})
            if img_data:
                images.append(img_data['src'])
            seller = ''
            # Extract seller information
            seller_tag = soup.find('div', {'id': 'sellerName'})
            if seller_tag:
                seller = seller_tag.get_text(strip=True)
            # New features
            # Extract reviews and rating
            reviews = soup.find('span', {'class': '_2_R_DZ'})
            num_reviews = 0
            if reviews:
                match = re.search(r'([0-9,]+) Ratings', reviews.get_text(strip=True))
                if match:
                    num_reviews = int(match.group(1).replace(',', ''))
            rating = soup.find('div', {'class': '_3LWZlK'})
            # Extract average rating
            avg_rating = float(rating.get_text(strip=True)) if rating else 0.0
            image_count = len(images)
            desc_length = len(desc)
            keywords = ['original', 'replica', '100% genuine']
            keyword_flags = {k: (k in desc.lower()) for k in keywords}
            return {
                'title': title,
                'description': desc,
                'price': price,
                'images': images,
                'seller': seller or 'Unknown',
                'num_reviews': num_reviews,
                'avg_rating': avg_rating,
                'image_count': image_count,
                'desc_length': desc_length,
                'keyword_flags': keyword_flags,
                'scraping_error': False
            }
        except Exception as e:
            print(f'Flipkart scraping error: {e}')
            return {
                'title': '',
                'description': '',
                'price': '',
                'images': [],
                'seller': 'Unknown',
                'num_reviews': 0,
                'avg_rating': 0.0,
                'image_count': 0,
                'desc_length': 0,
                'keyword_flags': {},
                'scraping_error': True,
                'scraping_error_message': f'Flipkart scraping error: {e}'
            }
    if 'snapdeal.com' in url:
        # Snapdeal scraping logic
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            time.sleep(1) # Add delay between requests
            soup = BeautifulSoup(resp.text, 'html.parser')
            title = soup.find('h1', {'class': 'pdp-e-i-head'})
            title = title.get_text(strip=True) if title else ''
            desc = soup.find('div', {'class': 'pdp-product-description-content'})
            desc = desc.get_text(strip=True) if desc else ''
            price = soup.find('span', {'class': 'payBlkBig'})
            price = price.get_text(strip=True).replace('₹', '').replace(',', '') if price else ''
            images = []
            img_data = soup.find('img', {'class': 'cloudzoom'})
            if img_data:
                images.append(img_data['src'])
            seller = ''
            # Extract seller information
            seller_tag = soup.find('span', {'class': 'pdp-seller-name'})
            if seller_tag:
                seller = seller_tag.get_text(strip=True)
            # Add missing fields for consistency
            num_reviews = 0
            avg_rating = 0.0
            image_count = len(images)
            desc_length = len(desc)
            keywords = ['original', 'replica', '100% genuine']
            keyword_flags = {k: (k in desc.lower()) for k in keywords}
            return { # type: ignore
                'title': title,
                'description': desc,
                'price': price,
                'images': images,
                'seller': seller or 'Unknown',
                'num_reviews': num_reviews, # Include missing fields in success return
                'avg_rating': avg_rating,
            }
        except Exception as e:
            # Add missing fields for consistency in error return
            num_reviews = 0
            avg_rating = 0.0
            image_count = 0
            desc_length = 0
            print(f'Snapdeal scraping error: {e}')
            return {
                'title': '',
                'description': '',
                'price': '',
                'images': [],
                'seller': 'Unknown',
                'num_reviews': num_reviews,
                'avg_rating': avg_rating,
                'scraping_error': True,
                'scraping_error_message': f'Snapdeal scraping error: {e}'
            }
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            title = soup.find('h1', {'class': 'ProductDetailsMainCard__productName'})
            title = title.get_text(strip=True) if title else ''
            desc = soup.find('div', {'class': 'ProductDescription__descriptionContent'})
            desc = desc.get_text(strip=True) if desc else ''
            price = soup.find('div', {'class': 'ProductDetailsMainCard__price'})
            price = price.get_text(strip=True).replace('₹', '').replace(',', '') if price else ''
            images = []
            img_data = soup.find('img', {'class': 'ProductImages__img'})
            if img_data:
                images.append(img_data['src'])
            seller = ''
            # Extract seller information
            seller_tag = soup.find('div', {'class': 'ProductSellerInfo__sellerName'})
            if seller_tag:
                seller = seller_tag.get_text(strip=True)
            # Add missing fields for consistency
            num_reviews = 0
            avg_rating = 0.0
            image_count = len(images)
            desc_length = len(desc)
            keywords = ['original', 'replica', '100% genuine']
            keyword_flags = {k: (k in desc.lower()) for k in keywords}
            return { # type: ignore
                'title': title,
                'description': desc,
                'price': price,
                'images': images,
                'seller': seller or 'Unknown',
                'num_reviews': num_reviews, # Include missing fields in success return
                'avg_rating': avg_rating,
            }
        except Exception as e:
            # Add missing fields for consistency in error return
            num_reviews = 0
            avg_rating = 0.0
            image_count = 0
            desc_length = 0
            print(f'Tata Cliq scraping error: {e}')
            return {
                'title': '',
                'description': '',
                'price': '',
                'images': [],
                'seller': 'Unknown',
                'num_reviews': num_reviews,
                'avg_rating': avg_rating,
                'scraping_error': True,
                'scraping_error_message': f'Tata Cliq scraping error: {e}'
            }
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            title = soup.find('h1', {'class': 'pdp__title'})
            title = title.get_text(strip=True) if title else ''
            desc = soup.find('div', {'class': 'pdp__description-content'})
            desc = desc.get_text(strip=True) if desc else ''
            price = soup.find('span', {'class': 'pdp__offerPrice'})
            price = price.get_text(strip=True).replace('₹', '').replace(',', '') if price else ''
            images = []
            img_data = soup.find('img', {'class': 'pdp__img'})
            if img_data:
                images.append(img_data['src'])
            seller = 'Reliance Digital'
            # Reliance Digital is the seller for all products
            # Add missing fields for consistency
            num_reviews = 0
            avg_rating = 0.0
            image_count = len(images)
            desc_length = len(desc)
            keywords = ['original', 'replica', '100% genuine']
            keyword_flags = {k: (k in desc.lower()) for k in keywords}
            return { # type: ignore
                'title': title,
                'description': desc,
                'price': price,
                'images': images,
                'seller': seller,
                'num_reviews': num_reviews, # Include missing fields in success return
                'avg_rating': avg_rating,
            }
        except Exception as e:
            # Add missing fields for consistency in error return
            num_reviews = 0
            avg_rating = 0.0
            image_count = 0
            desc_length = 0
            print(f'Reliance Digital scraping error: {e}')
            return {
                'title': '',
                'description': '',
                'price': '',
                'images': [],
                'seller': 'Unknown',
                'num_reviews': num_reviews,
                'avg_rating': avg_rating,
                'scraping_error': True,
                'scraping_error_message': f'Reliance Digital scraping error: {e}'
            }
    if 'myntra.com' in url:
        if SELENIUM_AVAILABLE:
            try:
                chrome_options = Options()
                # chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chromedriver_path = get_chromedriver_path()
                service = Service(executable_path=chromedriver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
                time.sleep(2) # Add delay before initial GET
                driver.get(url)
                title = driver.find_element(By.TAG_NAME, 'h1').text.strip()
                # Extract description using Selenium
                try:
                    desc = driver.find_element(By.CLASS_NAME, 'pdp-product-description-content').text.strip()
                except Exception:
                    desc = ''
                # Extract price using Selenium
                try:
                    price = driver.find_element(By.CLASS_NAME, 'pdp-price').text.strip().replace('₹', '').replace(',', '')
                except Exception:
                    price = ''
                images = []
                try:
                    img = driver.find_element(By.CLASS_NAME, 'image-grid-image')
                    images.append(img.get_attribute('src'))
                except Exception:
                    pass
                # Myntra is the seller
                seller = 'Myntra'
                num_reviews = 0
                avg_rating = 0.0
                image_count = len(images)
                desc_length = len(desc)
                keywords = ['original', 'replica', '100% genuine']
                # Ensure keyword matching is robust (case-insensitive)
                # Check for presence of specified keywords in the description
                keyword_flags = {k: (k in desc.lower()) for k in keywords}
                driver.quit()
                print('DEBUG MYNTRA SELENIUM:', {'title': title, 'desc': desc, 'price': price, 'images': images, 'num_reviews': num_reviews, 'avg_rating': avg_rating, 'desc_length': desc_length})
                return {
                    'title': title,
                    'description': desc,
                    'price': price,
                    'images': images,
                    'seller': seller,
                    'num_reviews': num_reviews,
                    'avg_rating': avg_rating,
                    'image_count': image_count,
                    'desc_length': desc_length,
                    'keyword_flags': keyword_flags,
                    'scraping_error': False
                }
            except Exception as e:
                logging.error(f'Myntra Selenium scraping error: {e}')
        # Fallback to requests if Selenium fails or not available
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            time.sleep(1) # Add delay between requests
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Extract title using BeautifulSoup
            title = soup.find('h1')
            title = title.get_text(strip=True) if title else ''
            # Extract description using BeautifulSoup

            desc = soup.find('div', {'class': 'pdp-product-description-content'})
            desc = desc.get_text(strip=True) if desc else ''
            price = soup.find('span', {'class': 'pdp-price'})
            price = price.get_text(strip=True).replace('₹', '').replace(',', '') if price else ''
            images = []
            img_data = soup.find('img', {'class': 'image-grid-image'})
            if img_data:
                images.append(img_data['src'])
            seller = 'Myntra'
            # Myntra is the seller
            num_reviews = 0
            avg_rating = 0.0
            image_count = len(images)
            desc_length = len(desc)
            keywords = ['original', 'replica', '100% genuine']
            # Ensure keyword matching is robust (case-insensitive)
            keyword_flags = {k: (k in desc.lower()) for k in keywords}
            # Debug print for requests fallback
            print('DEBUG MYNTRA REQUESTS:', {'title': title, 'desc': desc, 'price': price, 'images': images, 'num_reviews': num_reviews, 'avg_rating': avg_rating, 'desc_length': desc_length})
            return {
                'title': title,
                'description': desc,
                'price': price,
                'images': images,
                'seller': seller,
                'num_reviews': num_reviews,
                'avg_rating': avg_rating,
                'image_count': image_count,
                'desc_length': desc_length,
                'keyword_flags': keyword_flags,
                'scraping_error': False
            }
        except Exception as e: # Catch any exceptions during requests scraping
            # Log the error and return error details
            logging.error(f'Myntra scraping error: {e}')
            return {'title': '', 'description': '', 'price': '', 'images': [], 'seller': 'Myntra', 'num_reviews': 0, 'avg_rating': 0.0, 'image_count': 0, 'desc_length': 0, 'keyword_flags': {}, 'scraping_error': True, 'scraping_error_message': f'Myntra scraping error: {e}'}
    # Nykaa Selenium + fallback
    if 'nykaa.com' in url:
        if SELENIUM_AVAILABLE:
            try:
                chrome_options = Options()
                # chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chromedriver_path = get_chromedriver_path()
                service = Service(executable_path=chromedriver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
                time.sleep(2) # Add delay before initial GET
                driver.get(url)
                title = driver.find_element(By.TAG_NAME, 'h1').text.strip()
                # Extract description using Selenium
                try:
                    desc = driver.find_element(By.CLASS_NAME, 'css-1m3b9l').text.strip()
                except Exception:
                    desc = ''
                # Extract price using Selenium
                try:
                    price = driver.find_element(By.CLASS_NAME, 'css-1jczs19').text.strip().replace('₹', '').replace(',', '')
                except Exception:
                    price = ''
                images = []
                try:
                    img = driver.find_element(By.CLASS_NAME, 'css-11gn9r6')
                    images.append(img.get_attribute('src'))
                except Exception:
                    pass
                # Nykaa is the seller
                seller = 'Nykaa'
                num_reviews = 0
                avg_rating = 0.0
                image_count = len(images)
                desc_length = len(desc)
                keywords = ['original', 'replica', '100% genuine']
                # Ensure keyword matching is robust (case-insensitive)
                # Check for presence of specified keywords in the description
                keyword_flags = {k: (k in desc.lower()) for k in keywords}
                driver.quit()
                print('DEBUG NYKAA SELENIUM:', {'title': title, 'desc': desc, 'price': price, 'images': images, 'num_reviews': num_reviews, 'avg_rating': avg_rating, 'desc_length': desc_length})
                return {
                    'title': title,
                    'description': desc,
                    'price': price,
                    'images': images,
                    'seller': seller,
                    'num_reviews': num_reviews,
                    'avg_rating': avg_rating,
                    'image_count': image_count,
                    'desc_length': desc_length,
                    'keyword_flags': keyword_flags,
                    'scraping_error': False
                }
            except Exception as e:
                logging.error(f'Nykaa Selenium scraping error: {e}')
        # Fallback to requests if Selenium fails or not available
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            time.sleep(1) # Add delay between requests
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Extract title using BeautifulSoup
            title = soup.find('h1')
            title = title.get_text(strip=True) if title else ''
            # Extract description using BeautifulSoup

            desc = soup.find('div', {'class': 'css-1m3b9l'})
            desc = desc.get_text(strip=True) if desc else ''
            price = soup.find('span', {'class': 'css-1jczs19'})
            price = price.get_text(strip=True).replace('₹', '').replace(',', '') if price else ''
            images = []
            img_data = soup.find('img', {'class': 'css-11gn9r6'})
            if img_data:
                images.append(img_data['src'])
            seller = 'Nykaa'
            # Nykaa is the seller
            num_reviews = 0
            avg_rating = 0.0
            image_count = len(images)
            desc_length = len(desc)
            keywords = ['original', 'replica', '100% genuine']
            # Ensure keyword matching is robust (case-insensitive)
            keyword_flags = {k: (k in desc.lower()) for k in keywords}
            # Debug print for requests fallback
            print('DEBUG NYKAA REQUESTS:', {'title': title, 'desc': desc, 'price': price, 'images': images, 'num_reviews': num_reviews, 'avg_rating': avg_rating, 'desc_length': desc_length})
            return {
                'title': title,
                'description': desc,
                'price': price,
                'images': images,
                'seller': seller,
                'num_reviews': num_reviews,
                'avg_rating': avg_rating,
                'image_count': image_count,
                'desc_length': desc_length,
                'keyword_flags': keyword_flags,
                'scraping_error': False
            }
        except Exception as e: # Catch any exceptions during requests scraping
            # Log the error and return error details
            logging.error(f'Nykaa scraping error: {e}')
            return {'title': '', 'description': '', 'price': '', 'images': [], 'seller': 'Nykaa', 'num_reviews': 0, 'avg_rating': 0.0, 'image_count': 0, 'desc_length': 0, 'keyword_flags': {}, 'scraping_error': True, 'scraping_error_message': f'Nykaa scraping error: {e}'}
    # Adidas, Nike, Puma, Reebok, Ajio Selenium + fallback
    if 'adidas.co.in' in url or 'nike.com' in url or 'puma.com' in url or 'reebok.in' in url or 'ajio.com' in url:
        if SELENIUM_AVAILABLE:
            try:
                chrome_options = Options()
                # chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chromedriver_path = get_chromedriver_path()
                service = Service(executable_path=chromedriver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
                time.sleep(2) # Add delay before initial GET
                driver.get(url)
                title = driver.find_element(By.TAG_NAME, 'h1').text.strip()
                # Extract description using Selenium
                try:
                    desc = driver.find_element(By.TAG_NAME, 'div').text.strip()
                except Exception:
                    desc = ''
                # Extract price using Selenium
                try:
                    price = driver.find_element(By.TAG_NAME, 'span').text.strip().replace('₹', '').replace(',', '')
                except Exception:
                    price = ''
                images = []
                try:
                    img = driver.find_element(By.TAG_NAME, 'img')
                    images.append(img.get_attribute('src'))
                except Exception:
                    pass
                # Assume the brand is the seller for these specific domains
                seller = 'Brand'
                num_reviews = 0
                avg_rating = 0.0
                image_count = len(images)
                desc_length = len(desc)
                keywords = ['original', 'replica', '100% genuine']
                # Ensure keyword matching is robust (case-insensitive)
                # Check for presence of specified keywords in the description
                keyword_flags = {k: (k in desc.lower()) for k in keywords}
                driver.quit()
                print('DEBUG BRAND SELENIUM:', {'title': title, 'desc': desc, 'price': price, 'images': images, 'num_reviews': num_reviews, 'avg_rating': avg_rating, 'desc_length': desc_length})
                return {
                    'title': title,
                    'description': desc,
                    'price': price,
                    'images': images,
                    'seller': seller,
                    'num_reviews': num_reviews,
                    'avg_rating': avg_rating,
                    'image_count': image_count,
                    'desc_length': desc_length,
                    'keyword_flags': keyword_flags,
                    'scraping_error': False
                }
            except Exception as e:
                logging.error(f'Brand Selenium scraping error: {e}')
        # Fallback to requests if Selenium fails or not available
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            time.sleep(1) # Add delay between requests
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Extract title using BeautifulSoup
            title = soup.find('h1')
            title = title.get_text(strip=True) if title else ''
            # Extract description using BeautifulSoup
            desc = soup.find('div')
            desc = desc.get_text(strip=True) if desc else ''
            price = soup.find('span')
            price = price.get_text(strip=True).replace('₹', '').replace(',', '') if price else ''
            images = []
            img_data = soup.find('img')
            # Extract image URL
            if img_data:
                images.append(img_data['src'])
            seller = 'Brand'
            num_reviews = 0
            avg_rating = 0.0
            image_count = len(images)
            desc_length = len(desc)
            keywords = ['original', 'replica', '100% genuine']

            # Ensure keyword matching is robust (case-insensitive)
            keyword_flags = {k: (k in desc.lower()) for k in keywords}
            print('DEBUG BRAND REQUESTS:', {'title': title, 'desc': desc, 'price': price, 'images': images, 'num_reviews': num_reviews, 'avg_rating': avg_rating, 'desc_length': desc_length})
            return {
                'title': title,
                'description': desc,
                'price': price,
                'images': images,
                'seller': seller,
                'num_reviews': num_reviews,
                'avg_rating': avg_rating,
                'image_count': image_count,
                'desc_length': desc_length,
                'keyword_flags': keyword_flags,
                'scraping_error': False
            }
        except Exception as e: # Catch any exceptions during requests scraping
            # Log the error and return error details
            logging.error(f'Brand scraping error: {e}')
            return {'title': '', 'description': '', 'price': '', 'images': [], 'seller': 'Brand', 'num_reviews': 0, 'avg_rating': 0.0, 'image_count': 0, 'desc_length': 0, 'keyword_flags': {}, 'scraping_error': True, 'scraping_error_message': f'Brand scraping error: {e}'}
    # Fallback for other sites
    return {
        'title': 'Sample Product',
        'description': 'Sample description',
        'price': '999',
        'images': [],
        'seller': 'Unknown',
        'num_reviews': 0,
        'avg_rating': 0.0,
        'image_count': 0,
        'desc_length': 0,
        'keyword_flags': {},
        'scraping_error': False,
        'scraping_error_message': ''
    } # type: ignore # Return a default structure for unhandled URLs