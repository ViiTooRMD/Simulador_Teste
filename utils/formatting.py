def format_currency(value: float) -> str:
    formatted = f"{value:,.2f}"
    formatted = (
        formatted
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )
    return f"R$ {formatted}"


def format_number(value: float) -> str:
    formatted = f"{value:,.2f}"
    return (
        formatted
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )
