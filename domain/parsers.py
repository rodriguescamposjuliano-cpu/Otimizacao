def parse_tempo(tempo_str: str) -> float:
    if not tempo_str:
        return 0.0
    h, m = 0, 0
    if "h" in tempo_str:
        partes = tempo_str.split("h")
        h = int(partes[0])
        if "min" in partes[1]:
            m = int(partes[1].replace("min", "").strip())
    elif "min" in tempo_str:
        m = int(tempo_str.replace("min", "").strip())
    return h + m / 60


def format_tempo_horas(tempo_h: float) -> str:
    h = int(tempo_h)
    m = int(round((tempo_h - h) * 60))
    return f"{h}h {m} min"


def parse_preco(preco_str: str) -> float:
    if not preco_str:
        return 0.0
    preco_str = preco_str.replace("R$", "").replace(".", "").replace(",", "").strip()
    try:
        return float(preco_str)
    except ValueError:
        return 0.0


def format_preco(preco: float) -> str:
    return f"R$ {preco:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
