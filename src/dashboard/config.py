

# ==============================================================================
# DESIGN SYSTEM TOKENS (TYPOGRAPHY & PALETTE)
# ==============================================================================
# System font stack prioritizing native OS rendering for clean modern typography
FONT_STACK = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'

# Semantic color palette used across charts, badges, and indicator cards:
# - ink: Primary text, axis lines, titles
# - teal / sky: Positive trends, revenue, available cash, liquid assets
# - plum / amber / red: Deep accents, EBITDA, equity, risk highlights, debt
COLORS = {
    "ink": "#111111",
    "teal": "#55a9e8",
    "blue": "#55a9e8",
    "amber": "#501839",
    "red": "#501839",
    "plum": "#501839",
    "sky": "#55a9e8",
}


# Human-readable labels for metric keys (used in dropdowns, tooltips, and axis titles)
METRIC_LABELS = {
    "margem_ebitda": "Margem EBITDA",
    "roa": "ROA",
    "roe": "ROE",
    "liquidez_corrente": "Liquidez corrente",
    "liquidez_seca": "Liquidez seca",
    "liquidez_imediata": "Liquidez imediata",
    "liquidez_geral": "Liquidez geral",
    "participacao_capital_terceiros": "Participação de capital de terceiros",
    "composicao_endividamento": "Composição do endividamento",
    "imobilizacao_pl": "Imobilização do PL",
    "eva": "EVA",
}

# The three executive perspectives tailored for different stakeholder groups
PERSPECTIVES = {
    "tecnica": "Técnica",           # Controllership, Treasury, Risk & Compliance
    "gestao": "Gestão",             # Executive Committee, Operations, C-Level
    "investidores": "Investidores", # Shareholders, Board of Directors, Lenders
}

# Explanatory subtitles shown beneath the perspective selector in the sidebar
PERSPECTIVE_SUMMARIES = {
    "tecnica": "Liquidez, endividamento e os controles que sustentam a operação.",
    "gestao": "Receita, margem e os riscos que exigem decisão no próximo ciclo.",
    "investidores": "Retorno, criação de valor e a dispersão entre cenários.",
}

# Defines which metrics are available in the distribution dropdown for each perspective
PERSPECTIVE_METRICS = {
    "tecnica": [
        "liquidez_corrente",
        "liquidez_seca",
        "liquidez_imediata",
        "liquidez_geral",
        "participacao_capital_terceiros",
        "composicao_endividamento",
        "imobilizacao_pl",
    ],
    "gestao": ["margem_ebitda", "liquidez_corrente", "roa", "eva"],
    "investidores": ["margem_ebitda", "roa", "roe", "eva"],
}