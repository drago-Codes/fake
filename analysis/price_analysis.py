import numpy as np

def compute_price_deviation(product_price, reference_prices):
    """
    Analyzes a product's price relative to a set of reference prices.

    This function computes the percentage deviation of the product price from the
    mean of the reference prices. It also performs statistical analysis on the
    reference prices, including calculating the mean, median, and standard deviation.
    Furthermore, it identifies if the product price is an outlier compared to the
    reference prices using a Z-score approach (specifically, checking if it's
    more than 2 standard deviations away from the mean).

    Args:
        product_price (float): The price of the product to analyze.
        reference_prices (list): A list of numerical reference prices (floats or integers).
                                 Handles None values and converts valid entries to floats.

    Returns:
        dict: A dictionary containing the analysis results:
              - "deviation" (float): The percentage deviation of the product price
                                     from the mean of reference prices (0.0 if mean is 0).
              - "mean" (float): The mean of the reference prices (0.0 if no reference prices).
              - "median" (float): The median of the reference prices (0.0 if no reference prices).
              - "std_dev" (float): The standard deviation of the reference prices (0.0 if no reference prices or only one reference price).
              - "is_outlier" (bool): True if the product price is considered an outlier
                                     (more than 2 standard deviations from the mean),
                                     False otherwise.
                                     Returns False if standard deviation is 0 (e.g., all reference prices are the same).
              Returns a dictionary with all values as 0.0 or False in case of errors or empty reference prices.
    Raises:
        ValueError: If product_price or reference_prices cannot be converted to float.
        TypeError: If input types are not compatible for conversion.
    """
    try:
        product_price = float(product_price)
        reference_prices = [float(p) for p in reference_prices if p is not None] # Ensure prices are floats and handle None

        if not reference_prices:
            return {"deviation": 0.0, "mean": 0.0, "median": 0.0, "std_dev": 0.0, "is_outlier": False}

        # Statistical analysis
        mean_price = np.mean(reference_prices)
        median_price = np.median(reference_prices)
        # Calculate standard deviation of the reference prices.
        # np.std computes the population standard deviation by default (delta degrees of freedom = 0).
        std_dev_price = np.std(reference_prices)

        # Outlier detection (using Z-score, a common method)
        # A price is considered an outlier if it's more than 2 standard deviations from the mean
        # Check if std_dev_price is greater than 0 to avoid division by zero or incorrect outlier detection
        # when all reference prices are the same.
        is_outlier = abs(product_price - mean_price) > (2 * std_dev_price) if std_dev_price > 0 else False

        # Calculate the percentage deviation of the product price from the mean.
        # Avoid division by zero if the mean is 0.
        deviation = (product_price - mean_price) / mean_price if mean_price > 0 else 0.0

        # Return the dictionary containing all the computed analysis results.
        # The deviation is returned as a percentage relative to the mean.
        # The statistical measures (mean, median, std_dev) provide context for the reference prices.
        # is_outlier indicates if the product price is significantly different from the reference prices.

        return {"deviation": deviation, "mean": mean_price, "median": median_price, "std_dev": std_dev_price, "is_outlier": is_outlier}
    except (ValueError, TypeError) as e:
        print(f"Error in price analysis: {e}")
        return {"deviation": 0.0, "mean": 0.0, "median": 0.0, "std_dev": 0.0, "is_outlier": False}