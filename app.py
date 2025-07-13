from flask import Flask, render_template, request, jsonify
from scraping.extract_product import extract_product_details
from scraping.trusted_sources import search_trusted_sources
from analysis.text_similarity import compute_text_similarity
from analysis.image_similarity import compute_image_similarity
from analysis.price_analysis import compute_price_deviation
from ml.classifier import classify_product
import logging
from typing import Any, Dict

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

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
        product = extract_product_details(url)
        # Handle scraping errors and inform the user
        if product.get('scraping_error', False):
            return jsonify({
                'verdict': 'Unable to Analyze',
                'authenticity_score': 0,
                'details': {},
                'recommendation': product.get('scraping_error_message', 'Could not extract product details due to driver or anti-bot issues. Please review manually.'),
                'error': product.get('scraping_error_message', 'Could not extract product details due to driver or anti-bot issues. Please review manually.')
            })
        # 2. Search trusted sources
        trusted_domains = [
            'amazon.in', 'flipkart.com', 'tatacliq.com', 'reliancedigital.in', 'snapdeal.com',
            'myntra.com', 'nykaa.com', 'adidas.co.in', 'nike.com', 'puma.com', 'reebok.in', 'ajio.com'
        ]
        # Compute all features and details as usual
        trusted = search_trusted_sources(product['title'])
        if trusted and trusted[0]['source'] != 'No Match Found':
            ref = trusted[0]
            text_sim = compute_text_similarity(product['title'], ref['title'])
            image_sim = compute_image_similarity(product['images'][0] if product['images'] else '', ref['images'][0] if ref['images'] else '')
            try:
                price_dev = compute_price_deviation(product['price'], [float(ref['price'])])
            except Exception as e:
                logging.warning(f'Price deviation error: {e}')
                price_dev = 0.0
            known_seller = product['seller'].lower() == ref['seller'].lower()
        else:
            text_sim = image_sim = 0.0
            price_dev = 0.0
            known_seller = False
        features = [
            text_sim,
            image_sim,
            price_dev,
            int(known_seller),
            product.get('num_reviews', 0),
            product.get('avg_rating', 0.0),
            product.get('image_count', 0),
            product.get('desc_length', 0),
            int(product.get('keyword_flags', {}).get('original', 0)),
            int(product.get('keyword_flags', {}).get('replica', 0)),
            int(product.get('keyword_flags', {}).get('100% genuine', 0)),
        ]
        score, verdict = classify_product(*features)
        details = {
            'Title Similarity': f'{int(text_sim*100)}%',
            'Image Similarity': f'{int(image_sim*100)}%',
            'Price Deviation': f'{int(price_dev*100)}%',
            'Seller': product['seller'],
            'Reference Source': ref['source'] if trusted and trusted[0]['source'] != 'No Match Found' else 'N/A',
            'Num Reviews': product.get('num_reviews', 0),
            'Avg Rating': product.get('avg_rating', 0.0),
            'Image Count': product.get('image_count', 0),
            'Description Length': product.get('desc_length', 0),
            'Keyword: Original': int(product.get('keyword_flags', {}).get('original', 0)),
            'Keyword: Replica': int(product.get('keyword_flags', {}).get('replica', 0)),
            'Keyword: 100% Genuine': int(product.get('keyword_flags', {}).get('100% genuine', 0)),
        }
        # Strong trusted domain override: always Likely Genuine for big sites if scraping succeeded, but show real details
        if any(domain in url for domain in trusted_domains):
            verdict = 'Likely Genuine'
            score = 95
            result = {
                'verdict': verdict,
                'authenticity_score': score,
                'details': details,
                'recommendation': 'This appears to be a genuine product from a trusted source.'
            }
            return jsonify(result)
        # Handle missing/empty data gracefully
        if (
            product.get('num_reviews', 0) == 0 and
            product.get('avg_rating', 0.0) == 0.0 and
            product.get('desc_length', 0) == 0 and
            not product.get('images')
        ):
            if any(domain in url for domain in trusted_domains):
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
        # Trusted domain override for strong signals
        if (
            any(domain in url for domain in trusted_domains)
            and product.get('avg_rating', 0) >= 4.0
            and product.get('num_reviews', 0) > 100
            and product.get('desc_length', 0) > 100
        ):
            verdict = 'Likely Genuine'
            score = 90
            result = {
                'verdict': verdict,
                'authenticity_score': score,
                'details': {
                    'Title Similarity': 'N/A',
                    'Image Similarity': 'N/A',
                    'Price Deviation': 'N/A',
                    'Seller': product.get('seller', 'Unknown'),
                    'Reference Source': 'N/A',
                    'Num Reviews': product.get('num_reviews', 0),
                    'Avg Rating': product.get('avg_rating', 0.0),
                    'Image Count': product.get('image_count', 0),
                    'Description Length': product.get('desc_length', 0),
                    'Keyword: Original': int(product.get('keyword_flags', {}).get('original', 0)),
                    'Keyword: Replica': int(product.get('keyword_flags', {}).get('replica', 0)),
                    'Keyword: 100% Genuine': int(product.get('keyword_flags', {}).get('100% genuine', 0)),
                },
                'recommendation': 'This appears to be a genuine product from a trusted source.'
            }
            return jsonify(result)
        # Manual trusted source override
        if any(domain in url for domain in trusted_domains) and price_dev == 0 and image_sim > 0.9:
            score = 95
            verdict = 'Likely Genuine'
        else:
            # 4. ML classifier: pass all features in correct order
            features = [
                text_sim,
                image_sim,
                price_dev,
                int(known_seller),
                product.get('num_reviews', 0),
                product.get('avg_rating', 0.0),
                product.get('image_count', 0),
                product.get('desc_length', 0),
                int(product.get('keyword_flags', {}).get('original', 0)),
                int(product.get('keyword_flags', {}).get('replica', 0)),
                int(product.get('keyword_flags', {}).get('100% genuine', 0)),
            ]
            score, verdict = classify_product(*features)
        # 5. Build response
        result = {
            'verdict': verdict,
            'authenticity_score': score,
            'details': details,
            'recommendation': 'Avoid purchasing.' if verdict != 'Likely Genuine' else 'Safe to buy from trusted source.'
        }
        return jsonify(result)
    except Exception as e:
        logging.error(f'Analysis error: {e}', exc_info=True)
        return jsonify({'error': 'An error occurred during analysis. Please try again later.'}), 500

if __name__ == '__main__':
    app.run(debug=True) 