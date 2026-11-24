from app.geo import is_us_location

US = [
    "New York, NY",
    "Austin, TX",
    "austin, tx",
    "Brooklyn",
    "San Francisco, CA",
    "Washington, DC",
    "USA",
    "U.S.A.",
    "United States",
    "Seattle 🇺🇸",
    "🇺🇸",
    "Bay Area",
    "PNW",
    "Columbus, OH 43215",
    "TX",
    "Georgia",
    # US namesakes of foreign cities — the state must win.
    "London, Kentucky",
    "Paris, TX",
    "Vancouver, WA",
    "Birmingham, Alabama",
    "Manchester, NH",
    "Ontario, California",
]

NOT_US = [
    None,
    "",
    "   ",
    "London",
    "London, UK",
    "Toronto",
    "Toronto, CA",
    "Vancouver BC",
    "Mumbai, India",
    "Bengaluru",
    "Tbilisi, Georgia",
    "Berlin, DE",
    "Paris, France",
    "Lagos, Nigeria",
    "Dubai",
    "Sydney, Australia",
    "São Paulo, Brasil",
    "Seoul 🇰🇷",
    "earth",
    "ur mom's house",
    "localhost",
]


def test_us_locations():
    for value in US:
        assert is_us_location(value), f"expected US: {value!r}"


def test_non_us_locations():
    for value in NOT_US:
        assert not is_us_location(value), f"expected non-US: {value!r}"


def test_non_us_flag_overrides_us_text():
    # An explicit flag is a self-declaration and beats ambiguous text.
    assert not is_us_location("Georgia 🇬🇪")
