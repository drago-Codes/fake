def compute_price_deviation(product_price, reference_prices):
    # Placeholder: compute deviation from average
    try:
        product_price = float(product_price)
        avg_price = sum(reference_prices) / len(reference_prices)
        deviation = (product_price - avg_price) / avg_price
        return deviation
    except Exception:
        return 0.0 