def compact_number_ranges(numbers: set[int]) -> list[str]:
    if not numbers:
        return []

    ordered = sorted(numbers)
    ranges = []
    start = previous = ordered[0]

    for number in ordered[1:]:
        if number == previous + 1:
            previous = number
            continue

        ranges.append(str(start) if start == previous else f"{start}-{previous}")
        start = previous = number

    ranges.append(str(start) if start == previous else f"{start}-{previous}")
    return ranges
