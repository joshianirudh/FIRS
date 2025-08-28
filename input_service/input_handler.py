
def validate_stock_sticker(ticker: str):

    if not ticker:
        raise ValueError("Stock ticker is required")

    # No validation for now, can add validation later
    # expected value is stock ticker
    return ticker