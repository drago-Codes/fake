import numpy as np

def compute_price_deviation(product_price, reference_prices):
    """
    Computes the percentage deviation of product price from reference prices.
    
    Args:
        product_price (float): The price of the product to analyze.
        reference_prices (list): A list of reference prices.
    
    Returns:
        float: Absolute percentage deviation (0.0 to 1.0+)
    """
    try:
        product_price = float(product_price)
        reference_prices = [float(p) for p in reference_prices if p is not None and p > 0]
        
        if not reference_prices or product_price <= 0:
            return 0.0
        
        mean_price = np.mean(reference_prices)
        if mean_price <= 0:
            return 0.0
            
        # Return absolute percentage deviation
        deviation = abs(product_price - mean_price) / mean_price
        return min(deviation, 2.0)  # Cap at 200% deviation
        
    except (ValueError, TypeError) as e:
        print(f"Error in price analysis: {e}")
        return 0.0