import random
import string

DEFAULT_ENCODING = 'utf-8'

RANDOM_CHARSET = [
    *string.ascii_letters,
    *string.digits,
]

def random_str(l: int) -> str:
    return ''.join(random.choice(RANDOM_CHARSET) for _ in range(l))
