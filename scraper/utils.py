from decimal import Decimal
from statistics import mean

def calculate_min_target_price(cost_price, margin_percent):
    """
    Ensures tenant achieves their desired profit.
    """
    return cost_price * (1 + Decimal(margin_percent) / 100)


def calculate_competitor_midpoint(prices):
    """
    Averages the lowest and highest competitor price to get a market reference point.
    """
    if not prices:
        return None
    return (min(prices) + max(prices)) / 2


def recommend_optimal_price(cost_price, margin_percent, competitor_prices):
    """
    Core pricing logic:
    - Uses margin to calculate minimum acceptable price.
    - Uses competitor data to find a balanced pricing point.
    """
    if not competitor_prices:
        # No competitors → use only margin-based price
        return round(calculate_min_target_price(cost_price, margin_percent), 2), "No competitors, used margin only"

    min_target_price = calculate_min_target_price(cost_price, margin_percent)
    competitor_mid = calculate_competitor_midpoint(competitor_prices)
    highest_cp = max(competitor_prices)

    if min_target_price <= highest_cp:
        suggested_price = min(max(min_target_price, competitor_mid), highest_cp)
        reason = f"Within market range: Target price {min_target_price:.2f} SAR, competitor midpoint {competitor_mid:.2f} SAR"
    else:
        suggested_price = min_target_price
        reason = "Above market, positioned as premium due to high cost or high margin requirement"

    return round(suggested_price, 2), reason


# utils.py
def calculate_recommended_price(cost_price, competitor_prices, target_margin):
    if not competitor_prices:
        return None, "No competitor prices available."

    min_target_price = cost_price * (1 + (target_margin / 100))
    competitor_mid = (min(competitor_prices) + max(competitor_prices)) / 2

    if min_target_price <= max(competitor_prices):
        optimal_price = min(max(min_target_price, competitor_mid), max(competitor_prices))
        reason = "Recommended based on competitor price range and target margin."
    else:
        optimal_price = min_target_price
        reason = "Target margin not met by competitors; positioned as premium."

    return round(optimal_price, 2), reason
