import re
from typing import Optional, Union


def parse_price(text: Union[str, int, float]) -> Optional[int]:
    if type(text) in (int, float):
        return text
    text = text.replace(",", ".")
    text = re.sub(r"[^\d.]", "", text)
    text = text.split(".")[0]
    if not text:
        return None
    return int(text)
