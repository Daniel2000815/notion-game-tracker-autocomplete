"""
HLTB module. Fetches the time to beat value for all styles playthroughs.
"""

from howlongtobeatpy import HowLongToBeat

def hltb(title):
    """
    Fetches the time to beat value for all styles playthroughs of title. If not found, returns 0.
    """
    results = HowLongToBeat().search(title)
    if results is not None and len(results) > 0:
        best_element = max(results, key=lambda element: element.similarity)
        return best_element.all_styles

    return 0
