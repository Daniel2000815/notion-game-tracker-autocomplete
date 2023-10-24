
from howlongtobeatpy import HowLongToBeat

def hltb(title):
    results = HowLongToBeat().search(title)
    if results is not None and len(results) > 0:
        best_element = max(results, key=lambda element: element.similarity)
        return best_element.all_styles
    else:
        return 0