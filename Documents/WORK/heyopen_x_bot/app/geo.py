"""Best-effort US gate built on the profile `location` string.

X exposes no account-country field, so this is the only first-party signal
available (see README "US-only gate"). It is user-typed, so it is spoofable and
it rejects US users who leave `location` empty. Treat it as a traffic filter,
not an identity control.

Resolution order matters: an unambiguous US marker wins over a foreign one, so
"London, Kentucky" and "Paris, TX" resolve to US while bare "London" does not.
"""

import re

_REGIONAL_INDICATOR_A = 0x1F1E6

# Wins outright. "georgia" is deliberately absent — it is also a country.
_UNAMBIGUOUS_US = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "hawaii", "idaho", "illinois",
    "indiana", "iowa", "kansas", "kentucky", "louisiana", "maine", "maryland",
    "massachusetts", "michigan", "minnesota", "mississippi", "missouri",
    "montana", "nebraska", "nevada", "new hampshire", "new jersey",
    "new mexico", "new york", "north carolina", "north dakota", "ohio",
    "oklahoma", "oregon", "pennsylvania", "rhode island", "south carolina",
    "south dakota", "tennessee", "texas", "utah", "vermont", "virginia",
    "washington", "west virginia", "wisconsin", "wyoming",
    "puerto rico", "district of columbia",
    "united states", "united states of america", "usa", "u.s.a.", "u.s.",
    "america",
    "new york city", "nyc", "brooklyn", "queens", "manhattan", "bronx",
    "los angeles", "san francisco", "bay area", "silicon valley", "socal",
    "norcal", "san diego", "san jose", "chicago", "houston", "phoenix",
    "philadelphia", "san antonio", "dallas", "austin", "atx", "jacksonville",
    "fort worth", "columbus", "charlotte", "indianapolis", "seattle",
    "denver", "boston", "nashville", "detroit", "memphis", "las vegas",
    "baltimore", "milwaukee", "albuquerque", "tucson", "fresno", "sacramento",
    "kansas city", "omaha", "colorado springs", "raleigh", "long beach",
    "virginia beach", "oakland", "minneapolis", "tulsa", "tampa",
    "new orleans", "wichita", "cleveland", "honolulu", "anaheim",
    "pittsburgh", "st louis", "saint louis", "cincinnati", "salt lake city",
    "washington dc", "washington d.c.", "d.c.", "pnw", "dmv", "new england",
    "midwest", "bama",
}

# Real but weak. Only consulted after foreign markers have had their say.
_AMBIGUOUS_US = {"georgia"}

# Two-letter state codes with no ISO country collision — safe to trust.
_SAFE_ABBREV = {
    "ak", "ct", "fl", "hi", "ia", "id", "ks", "mi", "mn", "nc", "nd", "nh",
    "nj", "nm", "nv", "ny", "oh", "ok", "or", "ri", "tx", "ut", "vt", "wa",
    "wi", "wv", "wy", "dc", "pr",
}

# State codes that double as country codes (CA/Canada, IN/India, DE/Germany...).
_COLLIDING_ABBREV = {
    "al", "ar", "az", "ca", "co", "de", "ga", "il", "in", "ky", "la", "ma",
    "md", "me", "mo", "ms", "mt", "ne", "pa", "sc", "sd", "tn", "va",
}

# Cities with a US namesake are qualified ("vancouver bc") so the bare name
# falls through to a default reject instead of being wrongly excluded.
_FOREIGN = {
    "canada", "mexico", "united kingdom", "uk", "england", "scotland",
    "wales", "ireland", "france", "germany", "deutschland", "spain", "italy",
    "portugal", "netherlands", "holland", "belgium", "switzerland", "austria",
    "sweden", "norway", "denmark", "finland", "iceland", "poland", "czechia",
    "czech republic", "slovakia", "hungary", "romania", "bulgaria", "greece",
    "turkey", "turkiye", "türkiye", "russia", "ukraine", "belarus", "serbia",
    "croatia", "india", "bharat", "pakistan", "bangladesh", "sri lanka",
    "nepal", "china", "taiwan", "hong kong", "japan", "south korea", "korea",
    "vietnam", "thailand", "philippines", "indonesia", "malaysia",
    "singapore", "australia", "new zealand", "nigeria", "kenya", "ghana",
    "south africa", "egypt", "morocco", "algeria", "tunisia", "ethiopia",
    "uganda", "tanzania", "brazil", "brasil", "argentina", "chile",
    "colombia", "peru", "venezuela", "ecuador", "bolivia", "uruguay",
    "paraguay", "israel", "palestine", "saudi arabia", "uae",
    "united arab emirates", "dubai", "abu dhabi", "qatar", "kuwait",
    "bahrain", "oman", "jordan", "lebanon", "iraq", "iran", "afghanistan",
    "kazakhstan", "uzbekistan", "azerbaijan", "armenia", "cyprus", "malta",
    "luxembourg", "estonia", "latvia", "lithuania", "slovenia", "bosnia",
    "albania", "moldova", "jamaica", "cuba", "haiti", "dominican republic",
    "trinidad", "barbados", "bahamas", "panama", "costa rica", "guatemala",
    "honduras", "el salvador", "nicaragua", "belize",
    "london", "toronto", "vancouver bc", "montreal", "ottawa", "calgary",
    "edmonton", "winnipeg", "quebec", "mississauga", "brampton",
    "victoria bc", "paris", "berlin", "munich", "hamburg", "frankfurt",
    "cologne", "madrid", "barcelona", "rome", "milan", "naples", "turin",
    "lisbon", "porto", "amsterdam", "rotterdam", "brussels", "zurich",
    "geneva", "vienna", "stockholm", "oslo", "copenhagen", "helsinki",
    "dublin", "edinburgh", "glasgow", "manchester uk", "birmingham uk",
    "liverpool", "leeds", "bristol", "cardiff", "belfast", "warsaw",
    "krakow", "prague", "budapest", "bucharest", "sofia", "athens",
    "istanbul", "ankara", "moscow", "st petersburg", "kyiv", "kiev", "minsk",
    "belgrade", "zagreb", "mumbai", "bombay", "delhi", "new delhi",
    "bangalore", "bengaluru", "hyderabad", "chennai", "kolkata", "pune",
    "ahmedabad", "jaipur", "lucknow", "karachi", "lahore", "islamabad",
    "dhaka", "colombo", "kathmandu", "beijing", "shanghai", "shenzhen",
    "guangzhou", "chengdu", "taipei", "tokyo", "osaka", "kyoto", "yokohama",
    "seoul", "busan", "hanoi", "ho chi minh", "saigon", "bangkok", "manila",
    "cebu", "jakarta", "surabaya", "kuala lumpur", "sydney", "melbourne",
    "brisbane", "perth", "adelaide", "auckland", "wellington",
    "christchurch", "lagos", "abuja", "nairobi", "accra", "johannesburg",
    "cape town", "durban", "pretoria", "cairo", "casablanca", "tunis",
    "algiers", "addis ababa", "kampala", "dar es salaam", "sao paulo",
    "são paulo", "rio de janeiro", "brasilia", "buenos aires", "santiago",
    "bogota", "bogotá", "lima", "caracas", "quito", "montevideo", "tel aviv",
    "jerusalem", "riyadh", "jeddah", "doha", "kuwait city", "amman",
    "beirut", "baghdad", "tehran", "kabul", "almaty", "tashkent", "baku",
    "yerevan", "tbilisi",
}

_STATE_CODE_RE = re.compile(
    r"(?:,\s*|^)([a-z]{2})\b(?:\s*\d{5}(?:-\d{4})?)?\s*$"
)


def _flag_country_codes(text: str) -> list[str]:
    indicators = [c for c in text if _REGIONAL_INDICATOR_A <= ord(c) <= 0x1F1FF]
    return [
        chr(ord("A") + ord(indicators[i]) - _REGIONAL_INDICATOR_A)
        + chr(ord("A") + ord(indicators[i + 1]) - _REGIONAL_INDICATOR_A)
        for i in range(0, len(indicators) - 1, 2)
    ]


def _mentions_any(normalized: str, phrases: set[str]) -> bool:
    return any(
        re.search(rf"\b{re.escape(p)}(?![a-z0-9])", normalized) for p in phrases
    )


def _trailing_state_code(normalized: str, codes: set[str]) -> bool:
    match = _STATE_CODE_RE.search(normalized)
    return match is not None and match.group(1) in codes


def is_us_location(location: str | None) -> bool:
    if not location or not location.strip():
        return False

    flags = _flag_country_codes(location)
    if "US" in flags:
        return True
    if flags:
        return False

    normalized = re.sub(r"\s+", " ", location.lower().strip())

    if _mentions_any(normalized, _UNAMBIGUOUS_US):
        return True
    if _trailing_state_code(normalized, _SAFE_ABBREV):
        return True
    if _mentions_any(normalized, _FOREIGN):
        return False
    if _mentions_any(normalized, _AMBIGUOUS_US):
        return True
    return _trailing_state_code(normalized, _COLLIDING_ABBREV)
