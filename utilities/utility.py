from num2words import num2words
def get_probability(probability):
    """
    Determine the sales opportunity stage based on the probability value.

    :param probability: Integer representing the probability percentage (0 to 100).
    :return: String representing the stage name.
    """
    if 10 <= probability <= 20:
        return "Prospecting"
    elif 21 <= probability <= 40:
        return "Qualification"
    elif 41 <= probability <= 60:
        return "Needs Analysis"
    elif 61 <= probability <= 70:
        return "Value Proposition"
    elif 71 <= probability <= 80:
        return "Decision Makers"
    elif 81 <= probability <= 85:
        return "Perception Analysis"
    elif 86 <= probability <= 90:
        return "Proposal/Price Quote"
    elif 91 <= probability <= 95:
        return "Negotiation/Review"
    elif probability == 100:
        return "Closed Won"
    elif probability == 0:
        return "Closed Lost"
    else:
        raise ValueError("Invalid probability value")


def currency_conversion(amount):
    """
    Convert a given amount from INR to various other currencies using predefined rates.

    :param amount: Amount in INR to be converted.
    :return: Dictionary with the amount converted to various currencies.
    """

    usd_rate = 85
    aus_rate = 60
    cad_rate = 70

    # Perform currency conversions
    usd = amount * usd_rate
    aus = amount * aus_rate
    cad = amount * cad_rate

    # Return a dictionary with all conversions rounded to 2 decimal places
    return {
        'USD': round(usd, 2),
        'AUD': round(aus, 2),
        'CAD': round(cad, 2),
        'INR': round(amount, 2)  # Original amount in INR
    }


def convert_amount_to_word(amount):
    if amount is None:
        return "Zero"
    return num2words(amount, to='currency', lang='en')

