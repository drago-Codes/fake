from flask import Flask, render_template, request, jsonify
from scraping.extract_product import extract_product_details
from scraping.trusted_sources import search_trusted_sources
from analysis.text_similarity import compute_text_similarity as calculate_text_similarity
from analysis.image_similarity import compute_image_similarity as calculate_image_similarity
from analysis.price_analysis import compute_price_deviation as calculate_price_deviation
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
def analyze():
    url = request.form.get('url', '').strip()
    if not url:
        return jsonify({'error': 'Please provide a valid URL'})
    
    app.logger.info(f"Starting analysis for URL: {url}")
    
    try:
        # Initialize all feature variables to default values to avoid UnboundLocalError
        num_reviews = 0
        avg_rating = 0.0
        image_count = 0
        desc_length = 0
        keyword_original = 0
        keyword_replica = 0
        keyword_genuine = 0
        
        # 1. Extract product details
        try:
            product = extract_product_details(url)
            app.logger.info(f"Extracted product details for URL: {url}")
        except Exception as e:
            app.logger.error(f"Failed to extract product details: {str(e)}")
            return jsonify({'error': f'Failed to extract product details: {str(e)}'})
        
        # 2. Check if URL is from trusted domain
        trusted_domains = [
            'amazon.com', 'amazon.in', 'flipkart.com', 'tatacliq.com', 
            'reliancedigital.in', 'snapdeal.com', 'myntra.com', 'nykaa.com', 
            'adidas.co.in', 'nike.com', 'puma.com', 'reebok.in', 'ajio.com'
        ]
        
        is_trusted_domain = any(domain in url.lower() for domain in trusted_domains)
        
        if is_trusted_domain:
            # For trusted domains, return high confidence result
            text_sim = 1.0
            image_sim = 1.0
            price_dev = 0.0
            known_seller = True
            
            # Extract additional features for display
            try:
                num_reviews = int(product.get('num_reviews', 0))
                avg_rating = float(product.get('avg_rating', 0))
                image_count = int(product.get('image_count', 0))
                desc_length = len(product.get('description', ''))
                
                # Keyword analysis
                title_lower = product.get('title', '').lower()
                keyword_original = 1 if 'original' in title_lower else 0
                keyword_replica = 1 if 'replica' in title_lower else 0
                keyword_genuine = 1 if 'genuine' in title_lower or '100%' in title_lower else 0
            except:
                pass
            
            score = 85  # High score for trusted domains
            verdict = "Likely Genuine"
            ref_source = "amazon.in" if "amazon.in" in url.lower() else "flipkart.com" if "flipkart.com" in url.lower() else "Trusted Source"
            
        else:
            # For non-trusted domains, use ML model
            try:
                # Search trusted sources
                trusted = search_trusted_sources(product['title'])
                ref = trusted[0] if trusted else None
                
                # Calculate similarities
                if ref and ref.get('title'):
                    text_sim = calculate_text_similarity(product['title'], ref['title'])
                else:
                    text_sim = 0.0
                
                if ref and ref.get('image_url'):
                    image_sim = calculate_image_similarity(product.get('image_url', ''), ref['image_url'])
                else:
                    image_sim = 0.0
                
                # Price deviation
                if ref and ref.get('price'):
                    price_dev = calculate_price_deviation(float(product.get('price', 0)), [float(ref['price'])])
                else:
                    price_dev = 0.0
                
                known_seller = product['seller'].lower() == ref['seller'].lower() if ref else False
                
                # Extract additional features
                try:
                    num_reviews = int(product.get('num_reviews', 0))
                    avg_rating = float(product.get('avg_rating', 0))
                    image_count = int(product.get('image_count', 0))
                    desc_length = len(product.get('description', ''))
                    
                    title_lower = product.get('title', '').lower()
                    keyword_original = int(product.get('keyword_flags', {}).get('original', 0))
                    keyword_replica = int(product.get('keyword_flags', {}).get('replica', 0))
                    keyword_genuine = int(product.get('keyword_flags', {}).get('100% genuine', 0))
                except:
                    pass
                
                # Prepare features for ML classifier
                features = [
                    text_sim, image_sim, price_dev, int(known_seller),
                    num_reviews, avg_rating, image_count, desc_length,
                    keyword_original, keyword_replica, keyword_genuine
                ]
                
                score, verdict = classify_product(*features)
                ref_source = ref.get('source', 'N/A') if ref else 'N/A'
                
            except Exception as e:
                app.logger.error(f"ML analysis failed: {str(e)}")
                score = 30  # Low score for failed analysis
                verdict = "High Risk"
                text_sim = image_sim = price_dev = 0.0
                known_seller = False
                ref_source = 'N/A'
        
        # Build response
        result = {
            'verdict': verdict,
            'score': score,
            'details': {
                'product_title': product.get('title', ''),
                'product_price': product.get('price', 0),
                'seller': product.get('seller', ''),
                'num_reviews': num_reviews,
                'avg_rating': avg_rating,
                'image_count': image_count,
                'desc_length': desc_length,
                'title_similarity': f"{text_sim * 100:.0f}%",
                'image_similarity': f"{image_sim * 100:.0f}%",
                'price_deviation': f"{price_dev:.0f}%",
                'known_seller': known_seller,
                'reference_source': ref_source,
                'keyword_original': keyword_original,
                'keyword_replica': keyword_replica,
                'keyword_genuine': keyword_genuine
            }
        }
        
        app.logger.info(f"Analysis complete for URL {url}. Result: {verdict}")
        return jsonify(result)
        
    except Exception as e:
        app.logger.error(f"Analysis failed: {str(e)}")
        return jsonify({'error': f'Analysis failed: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=True) 