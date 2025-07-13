from flask import Flask, render_template, request, jsonify
from scraping.extract_product import extract_product_details
from scraping.trusted_sources import search_trusted_sources
from analysis.text_similarity import compute_text_similarity
from analysis.image_similarity import compute_image_similarity
from analysis.price_analysis import compute_price_deviation
from ml.classifier import classify_product
from config import Config  # Import the Config class
import pandas as pd # Import pandas
import time  # Import time for potential delays
import logging
from logging.handlers import RotatingFileHandler
from typing import Any, Dict

app = Flask(__name__)

# Ensure LOG_FILE is set in config, fallback to 'app.log'
if 'LOG_FILE' not in app.config:
    app.config['LOG_FILE'] = 'app.log'

app.config.from_object(Config) # Load configuration from Config object

# Configure logging
handler = RotatingFileHandler(app.config['LOG_FILE'], maxBytes=10000, backupCount=10)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

app.logger.info("Flask application started.")

@app.route('/')
def index() -> str:
    """Render the main index page."""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze() -> Any:
    """Analyze a product URL and return authenticity verdict and details as JSON."""
    data: Dict = request.get_json()
    url: str = data.get('url')
    try:
        # 1. Extract product details
        try:
            product = extract_product_details(url)
            app.logger.info(f"Extracted product details for URL: {url}")
            # Handle scraping errors and inform the user if the extraction failed
            if product.get('scraping_error', False):
                app.logger.error(f"Scraping error for URL {url}: {product.get('scraping_error_message')}")
                return jsonify({
                    'authenticity_score': 0,
                    'details': {},
                    'recommendation': product.get('scraping_error_message', 'Could not extract product details. Please review manually.'),
                    'error': product.get('scraping_error_message', 'Could not extract product details. Please review manually.')
                })
        except Exception as e:
            logging.error(f"Error during product detail extraction for URL {url}: {e}", exc_info=True)
            # Return a generic error if extraction fails unexpectedly
            return jsonify({'error': 'Could not extract product details. Please ensure the URL is correct and try again.'}), 500

        # 2. Search trusted sources
        trusted_domains = [
            'amazon.com',  # Added .com for broader coverage
            'amazon.in', 'flipkart.com', 'tatacliq.com', 'reliancedigital.in', 'snapdeal.com',
            'myntra.com', 'nykaa.com', 'adidas.co.in', 'nike.com', 'puma.com', 'reebok.in', 'ajio.com'
        ]
        # Search for the product on trusted sources using the extracted title
        trusted = search_trusted_sources(product['title'])

        # Initialize comparison variables
        if trusted and trusted[0]['source'] != 'No Match Found':
            ref = trusted[0]
            # Compute similarity scores if a match is found on a trusted source
            text_sim = compute_text_similarity(product['title'], ref['title'])
            image_sim = compute_image_similarity(product['images'][0] if product['images'] else '', ref['images'][0] if ref['images'] else '')
            try:
                # Compute price deviation, handling potential errors during conversion or calculation
                product_price = float(product['price'].replace(',', '').strip()) # Clean price string
                # Safely convert reference price to float as well
                try:
                    ref_price = float(ref['price'].replace(',', '').strip())
                    price_dev = compute_price_deviation(product_price, [ref_price])
                except ValueError:
                    app.logger.warning(f"Could not convert reference price '{ref['price']}' to float.")
                    price_dev = 0.0 # Default to 0 deviation if ref price is invalid
            except Exception as e:
                app.logger.warning(f'Price deviation error for product {product.get("title", "N/A")}: {e}')
                price_dev = 0.0
            known_seller = product['seller'].lower() == ref['seller'].lower()
        else:
            text_sim = image_sim = 0.0
            price_dev = 0.0
            known_seller = False
            # Default values if no trusted source match is found
            num_reviews = product.get('num_reviews', 0)
            avg_rating = product.get('avg_rating', 0.0)
            image_count = product.get('image_count', 0)
            desc_length = product.get('desc_length', 0)
            keyword_original = int(product.get('keyword_flags', {}).get('original', 0))
            keyword_replica = int(product.get('keyword_flags', {}).get('replica', 0))
            keyword_genuine = int(product.get('keyword_flags', {}).get('100% genuine', 0))

        # Define feature names corresponding to the training data
        feature_names = [
            'text_similarity',
            'image_similarity',
            'price_deviation',
            'known_seller',
            'num_reviews',
            'avg_rating',
            'image_count',
            'desc_length',
            'keyword_original',
            'keyword_replica',
            'keyword_100% genuine'
        ]
        # Prepare features for the ML classifier
        features = [
            text_sim,
            image_sim,
            price_dev,
            int(known_seller), # Ensure boolean is converted to int
            num_reviews, avg_rating, image_count, desc_length, keyword_original, keyword_replica, keyword_genuine
        ]
        score, verdict = classify_product(*features)
        app.logger.info(f"ML Classifier result for {url}: Score - {score}, Verdict - {verdict}")

        details = {
            'Product Title': product.get('title', 'N/A'),
            'Product Price': product.get('price', 'N/A'),
            'Title Similarity': f'{int(text_sim*100)}%',
            'Image Similarity': f'{int(image_sim*100)}%',
            'Price Deviation': f'{int(price_dev*100)}%',
            'Seller': product['seller'],
            'Reference Source': ref['source'] if trusted and trusted[0]['source'] != 'No Match Found' else 'N/A', # Handle case where ref might not be defined
            'Num Reviews': num_reviews,
            'Avg Rating': avg_rating,
            'Image Count': image_count,
            'Description Length': product.get('desc_length', 0),
            'Keyword: Original': int(product.get('keyword_flags', {}).get('original', 0)),

            'Keyword: Replica': int(product.get('keyword_flags', {}).get('replica', 0)),
            'Keyword: 100% Genuine': int(product.get('keyword_flags', {}).get('100% genuine', 0))
        }
        # Handle missing/empty data gracefully
        if (
            product.get('num_reviews', 0) == 0 and
            product.get('avg_rating', 0.0) == 0.0 and
            product.get('desc_length', 0) == 0 and
            not product.get('images')
        ):
            if any(domain in url for domain in trusted_domains):
                # If from a trusted domain but no details, mark as Needs Review
                verdict = 'Needs Review'
                score = 50
                recommendation = 'Could not extract product details. Please review manually.'
            else:
                verdict = 'High Risk'
                score = 25
                recommendation = 'Could not extract product details. Avoid purchasing.'
            result = {
                'verdict': verdict,
                'authenticity_score': score,
                'details': {
                    'Product Title': product.get('title', 'N/A'),
                    'Product Price': product.get('price', 'N/A'),
                    'Title Similarity': '0%',
                    'Image Similarity': '0%',
                    'Price Deviation': '0%',
                    'Seller': product.get('seller', 'Unknown'),
                    'Reference Source': 'N/A',
                    'Num Reviews': 0,
                    'Avg Rating': 0.0,
                    'Image Count': 0,
                    'Description Length': 0,
                    'Keyword: Original': 0,
                    'Keyword: Replica': 0,
                    'Keyword: 100% Genuine': 0,
                },
                'recommendation': recommendation
            }
            return jsonify(result)

        # Organize features into a pandas DataFrame with column names
        features_df = pd.DataFrame([features], columns=feature_names)

        # Always use ML classifier for verdict
        score, verdict = classify_product(features_df) # Pass the DataFrame
        # 5. Build response
        result = {
            'verdict': verdict,
            'authenticity_score': score,
            'details': details,
            'recommendation': 'Avoid purchasing.' if verdict != 'Likely Genuine' and verdict != 'Needs Review' else 'Safe to buy from trusted source.' if verdict == 'Likely Genuine' else 'Review details carefully.'
        }

        # Add a note if the product is from a trusted source
        is_trusted = any(domain in url for domain in trusted_domains)
        if is_trusted:
            result['note'] = 'This product is from a trusted source, but the authenticity is still analyzed.'

        app.logger.info(f"Analysis complete for URL {url}. Result: {result['verdict']}")
        return jsonify(result)
    except Exception as e:
        logging.error(f'Unexpected error during analysis for URL {url}: {e}', exc_info=True)
        return jsonify({'error': 'An error occurred during analysis. Please try again later.'}), 500

if __name__ == '__main__':
    app.run(debug=True) 