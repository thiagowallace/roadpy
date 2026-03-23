"""
RoadPy - Calculadora de Elementos de Curva Horizontal
Motor de cálculo baseado nas fórmulas do DNIT / IPR-742
"""

import math


# ─────────────────────────────────────────────
#  Helpers de conversão angular
# ─────────────────────────────────────────────

def dms_to_decimal(graus: float, minutos: float, segundos: float) -> float:
    """Converte graus, minutos e segundos para graus decimais."""
    return abs(graus) + abs(minutos) / 60.0 + abs(segundos) / 3600.0


def decimal_to_dms(dec: float):
    """Converte graus decimais para (graus, minutos, segundos)."""
    d = int(dec)
    m_dec = (dec - d) * 60.0
    m = int(m_dec + 1e-9)   # tolerância para evitar 19.9999... → 19
    s = (m_dec - m) * 60.0
    s = max(0.0, round(s, 4))  # evita -0.0 por ponto flutuante
    # normalização
    if s >= 60.0:
        s -= 60.0
        m += 1
    if m >= 60:
        m -= 60
        d += 1
    return d, m, s


def format_dms(dec: float) -> str:
    """Formata graus decimais como string °'\"."""
    d, m, s = decimal_to_dms(dec)
    return f"{d:d}°{m:02d}'{s:05.2f}\""


def format_dms_compact(dec: float) -> str:
    """Formata deflexão como DD°MM'SS.S\"  (sem casas decimais nos segundos)."""
    d, m, s = decimal_to_dms(dec)
    return f"{d:d}°{m:02d}'{s:04.1f}\""


# ─────────────────────────────────────────────
#  Tabela de cordas (padrão DNIT)
# ─────────────────────────────────────────────

def get_corda_dnit(raio: float) -> float:
    """
    Retorna o comprimento de corda máximo conforme tabela DNIT.
    R < 100 m  → corda = 5 m
    100 ≤ R < 600 m → corda = 10 m
    R ≥ 600 m  → corda = 20 m
    """
    if raio < 100.0:
        return 5.0
    elif raio < 600.0:
        return 10.0
    else:
        return 20.0


# ─────────────────────────────────────────────
#  Cálculo principal dos elementos da curva
# ─────────────────────────────────────────────

def calculate_curve(
    raio: float,
    ac_graus: float,
    ac_minutos: float,
    ac_segundos: float,
    estaca_pi: int,
    fracao_pi: float,
    comp_estaca: float = 20.0,
) -> dict:
    """
    Calcula todos os elementos geométricos de uma curva circular simples.

    Parâmetros
    ----------
    raio        : Raio da curva (m)
    ac_graus    : Ângulo central – graus
    ac_minutos  : Ângulo central – minutos
    ac_segundos : Ângulo central – segundos
    estaca_pi   : Número da estaca do PI
    fracao_pi   : Fração métrica da estaca do PI (m)
    comp_estaca : Comprimento padrão de estaca (padrão = 20 m)

    Retorna
    -------
    dict com todos os elementos calculados
    """

    # --- Ângulo central em graus decimais e radianos ---
    ac_dec = dms_to_decimal(ac_graus, ac_minutos, ac_segundos)
    ac_rad = math.radians(ac_dec)

    # --- Corda (tabela DNIT) ---
    corda = get_corda_dnit(raio)

    # --- Elementos geométricos (fórmulas DNIT / IPR-742) ---
    # Tangente externa
    T = raio * math.tan(ac_rad / 2.0)

    # Desenvolvimento da curva (comprimento do arco)
    D = raio * ac_dec * math.pi / 180.0

    # Afastamento (distância PI → curva)
    E = raio * (1.0 / math.cos(ac_rad / 2.0) - 1.0)

    # Corda longa (PC → PT em linha reta)
    corda_longa = 2.0 * raio * math.sin(ac_rad / 2.0)

    # Grau da curva
    Gc_dec = 180.0 * corda / (raio * math.pi)

    # Deflexão por metro
    dm = Gc_dec / (2.0 * corda)

    # --- Localização das estacas PC e PT ---
    pi_metros = estaca_pi * comp_estaca + fracao_pi

    pc_metros = pi_metros - T
    pc_estaca = int(pc_metros / comp_estaca)
    pc_fracao = pc_metros - pc_estaca * comp_estaca

    pt_metros = pc_metros + D
    pt_estaca = int(pt_metros / comp_estaca)
    pt_fracao = pt_metros - pt_estaca * comp_estaca

    # --- Deflexões parciais ---
    # Deflexão parcial para corda padrão
    d_corda = dm * corda

    # Primeira corda (PC → próximo ponto de estaqueamento)
    primeira_corda = corda - pc_fracao
    if primeira_corda <= 0:
        primeira_corda = corda
    d_pc = dm * primeira_corda

    # Última corda (último ponto de estaqueamento → PT)
    ultima_corda = pt_fracao if pt_fracao > 0 else corda
    d_pt = dm * ultima_corda

    return {
        # Entradas processadas
        "ac_dec": ac_dec,
        "ac_fmt": format_dms(ac_dec),
        # Corda
        "corda": corda,
        # Tangente externa
        "T": T,
        # Desenvolvimento
        "D": D,
        # Afastamento
        "E": E,
        # Corda longa
        "corda_longa": corda_longa,
        # Grau da curva
        "Gc_dec": Gc_dec,
        "Gc_fmt": format_dms(Gc_dec),
        # Deflexão por metro
        "dm": dm,
        "dm_fmt": format_dms(dm),
        # Deflexões parciais (graus decimais)
        "d_corda": d_corda,
        "d_corda_fmt": format_dms(d_corda),
        "d_pc": d_pc,
        "d_pc_fmt": format_dms(d_pc),
        "d_pt": d_pt,
        "d_pt_fmt": format_dms(d_pt),
        # Primeira e última corda
        "primeira_corda": primeira_corda,
        "ultima_corda": ultima_corda,
        # Estaca PC
        "pc_metros": pc_metros,
        "pc_estaca": pc_estaca,
        "pc_fracao": pc_fracao,
        "pc_fmt": f"E{pc_estaca}+{pc_fracao:.3f}",
        # Estaca PT
        "pt_metros": pt_metros,
        "pt_estaca": pt_estaca,
        "pt_fracao": pt_fracao,
        "pt_fmt": f"E{pt_estaca}+{pt_fracao:.3f}",
    }


# ─────────────────────────────────────────────
#  Tabela de locação por deflexões
# ─────────────────────────────────────────────

def generate_staking_table(result: dict, comp_estaca: float = 20.0) -> list[dict]:
    """
    Gera a tabela de locação por deflexões acumuladas.

    Retorna lista de dicionários com:
        estaca_inteira, estaca_frac, distancia, deflexao_parcial (dec),
        deflexao_acumulada (dec), leitura_limbo (dec = 45 + acum)
    """
    corda   = result["corda"]
    dm      = result["dm"]
    pc_frac = result["pc_fracao"]
    pt_frac = result["pt_fracao"]
    pc_est  = result["pc_estaca"]
    pt_est  = result["pt_estaca"]
    D       = result["D"]

    rows = []
    acumulada = 0.0
    distancia_total = 0.0

    # Ponto PC
    rows.append({
        "label": f"PC – E{pc_est}",
        "frac": pc_frac,
        "distancia": 0.0,
        "parcial": 0.0,
        "acumulada": 0.0,
        "limbo": format_dms(45.0),
        "acum_dec": 0.0,
    })

    # Primeira corda (PC → próximo ponto)
    primeira = corda - pc_frac
    if primeira > 0.0:
        acumulada += dm * primeira
        distancia_total += primeira
        frac_next = pc_frac + primeira
        est_next = pc_est
        if frac_next >= comp_estaca:
            est_next += 1
            frac_next -= comp_estaca

        rows.append({
            "label": f"E{est_next}",
            "frac": frac_next,
            "distancia": primeira,
            "parcial": dm * primeira,
            "acumulada": acumulada,
            "limbo": format_dms(45.0 + acumulada),
            "acum_dec": acumulada,
        })

    # Cordas intermediárias
    est_atual = pc_est + (1 if pc_frac + corda >= comp_estaca else 0)
    dist_acum_no_arco = primeira

    while dist_acum_no_arco + corda < D - 0.001:
        dist_acum_no_arco += corda
        acumulada += dm * corda
        est_atual_frac = dist_acum_no_arco + pc_frac
        ei = pc_est + int(est_atual_frac / comp_estaca)
        ef = est_atual_frac % comp_estaca

        rows.append({
            "label": f"E{ei}",
            "frac": ef,
            "distancia": corda,
            "parcial": dm * corda,
            "acumulada": acumulada,
            "limbo": format_dms(45.0 + acumulada),
            "acum_dec": acumulada,
        })

    # Ponto PT
    acumulada += dm * pt_frac if pt_frac > 0 else dm * corda
    rows.append({
        "label": f"PT – E{pt_est}",
        "frac": pt_frac,
        "distancia": pt_frac if pt_frac > 0 else corda,
        "parcial": dm * pt_frac if pt_frac > 0 else dm * corda,
        "acumulada": acumulada,
        "limbo": format_dms(45.0 + acumulada),
        "acum_dec": acumulada,
    })

    # Formata ângulos
    for r in rows:
        r["parcial_fmt"] = format_dms(r["parcial"])
        r["acumulada_fmt"] = format_dms(r["acumulada"])

    return rows
