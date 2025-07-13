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
            # For trusted domains, still do some basic analysis
            text_sim = 0.95
            image_sim = 0.95
            price_dev = 0.1
            known_seller = True
            
            # Extract additional features for display
            try:
                num_reviews = max(0, int(product.get('num_reviews', 0)))
                avg_rating = max(0, min(5, float(product.get('avg_rating', 0))))
                image_count = max(1, int(product.get('image_count', 1)))
                desc_length = len(str(product.get('description', '')))
                
                # Enhanced keyword analysis
                title_desc = (product.get('title', '') + ' ' + product.get('description', '')).lower()
                keyword_original = 1 if any(word in title_desc for word in ['original', 'authentic', 'official']) else 0
                keyword_replica = 1 if any(word in title_desc for word in ['replica', 'copy', 'duplicate', 'fake']) else 0
                keyword_genuine = 1 if any(word in title_desc for word in ['genuine', '100%', 'certified', 'warranty']) else 0
                
                # Adjust score based on content quality
                base_score = 85
                if keyword_replica > 0:
                    base_score -= 20  # Penalty for replica keywords even on trusted sites
                if avg_rating < 3.0 and num_reviews > 20:
                    base_score -= 10  # Penalty for poor ratings
                if keyword_genuine > 0 or keyword_original > 0:
                    base_score += 5  # Bonus for genuine keywords
                    
                score = max(60, min(95, base_score))  # Keep within reasonable range
                
            except Exception as e:
                app.logger.warning(f"Trusted domain feature extraction error: {e}")
                num_reviews = avg_rating = image_count = desc_length = 0
                keyword_original = keyword_replica = keyword_genuine = 0
                score = 80
            
            if score >= 85:
                verdict = "Highly Genuine"
            elif score >= 70:
                verdict = "Likely Genuine"
            else:
                verdict = "Suspicious"
                
            # Determine reference source
            if "amazon" in url.lower():
                ref_source = "Amazon"
            elif "flipkart" in url.lower():
                ref_source = "Flipkart"
            elif "myntra" in url.lower():
                ref_source = "Myntra"
            elif "tatacliq" in url.lower():
                ref_source = "Tata Cliq"
            else:
                ref_source = "Trusted Domain"
            
        else:
            # For non-trusted domains, use ML model
            try:
                # Search trusted sources
                trusted = search_trusted_sources(product['title'])
                ref = trusted[0] if trusted else None
                
                # Calculate similarities
                if ref and ref.get('title'):
                    text_sim = calculate_text_similarity(product.get('title', ''), ref['title'])
                else:
                    text_sim = 0.1  # Low similarity if no reference
                
                if ref and ref.get('image_url') and product.get('image_url'):
                    image_sim = calculate_image_similarity(product.get('image_url', ''), ref['image_url'])
                else:
                    image_sim = 0.1  # Low similarity if no images
                
                # Price deviation
                product_price = product.get('price', 0)
                if ref and ref.get('price') and product_price:
                    try:
                        ref_prices = [float(ref['price'])]
                        price_dev = calculate_price_deviation(float(product_price), ref_prices)
                    except:
                        price_dev = 1.0  # High deviation on error
                else:
                    price_dev = 0.5  # Medium deviation if no reference price
                
                # Seller comparison
                try:
                    known_seller = (product.get('seller', '').lower() == ref.get('seller', '').lower()) if ref else False
                except:
                    known_seller = False
                
                # Extract additional features with better defaults
                try:
                    num_reviews = max(0, int(product.get('num_reviews', 0)))
                    avg_rating = max(0, min(5, float(product.get('avg_rating', 0))))
                    image_count = max(0, int(product.get('image_count', 1)))
                    desc_length = len(str(product.get('description', '')))
                    
                    # Keyword analysis
                    title_desc = (product.get('title', '') + ' ' + product.get('description', '')).lower()
                    keyword_original = 1 if any(word in title_desc for word in ['original', 'authentic', 'official']) else 0
                    keyword_replica = 1 if any(word in title_desc for word in ['replica', 'copy', 'duplicate', 'fake']) else 0
                    keyword_genuine = 1 if any(word in title_desc for word in ['genuine', '100%', 'certified', 'warranty']) else 0
                    
                except Exception as e:
                    app.logger.warning(f"Feature extraction error: {e}")
                    num_reviews = avg_rating = image_count = desc_length = 0
                    keyword_original = keyword_replica = keyword_genuine = 0
                
                # Prepare features for ML classifier
                features = [
                    text_sim, image_sim, price_dev, int(known_seller),
                    num_reviews, avg_rating, image_count, desc_length,
                    keyword_original, keyword_replica, keyword_genuine
                ]
                
                app.logger.info(f"Features for classification: {features}")
                score, verdict = classify_product(*features)
                ref_source = ref.get('source', 'No Reference') if ref else 'No Reference'
                
            except Exception as e:
                app.logger.error(f"ML analysis failed: {str(e)}")
                score = 25  # Very low score for failed analysis
                verdict = "High Risk - Analysis Failed"
                text_sim = image_sim = 0.0
                price_dev = 1.0
                known_seller = False
                ref_source = 'Analysis Failed'
        
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