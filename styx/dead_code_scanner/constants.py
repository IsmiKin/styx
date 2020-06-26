from fuzzywuzzy import fuzz

IMPORT_REGEX = r"\b(?:import)(?:\s*\(?\s*[`'\"]|[^`'\"]*from\s+[`'\"])([^`'\"]+)"
TRANSLATIONS_REGEX = r"(?:[$t]{2})\(([\'\"\`])((?:[^\\\n]|\\\1|\\\\)*?)\1\)"

DEFAULT_FUZZY_WUZZY_RATIO_TYPE = "RATIO"

FUZZY_WUZZY_RATIO_TYPE = {
    "RATIO": fuzz.ratio,
    "PARTIAL_RATIO": fuzz.partial_ratio,
    "TOKEN_SORT_RATIO": fuzz.token_sort_ratio,
    "TOKEN_SET_RATIO": fuzz.token_set_ratio,
}
