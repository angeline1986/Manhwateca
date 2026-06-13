from manhwateca.shared.titles import normalize_first_letter


GROUPS = {
    "0-9": "0123456789",
    "A": "A",
    "BC": "BC",
    "DE": "DE",
    "FG": "FG",
    "HIJ": "HIJ",
    "KLM": "KLM",
    "NO": "NO",
    "PQR": "PQR",
    "ST": "ST",
    "UVW": "UVW",
    "XYZ": "XYZ",
}


def get_group(name):
    first = normalize_first_letter(name)
    for group, letters in GROUPS.items():
        if first in letters:
            return group
    return "0-9"
