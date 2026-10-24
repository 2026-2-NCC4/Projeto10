# src/dashboard/data_loader.py
from pathlib import Path
import unicodedata
import pandas as pd


def load_data(path: Path) -> pd.DataFrame:
    """Load, cleanse, pivot, and calculate financial indicators from raw CSV ledger.

    Parameters:
        path (Path): Path to the processed CTI CSV data file.

    Returns:
        pd.DataFrame: Wide-format dataframe containing all original accounts plus
                      derived financial ratios, indices, and calendar dimensions.

    Processing Steps:
        1. Reads Brazilian CSV formatting (semicolon delimiter, comma decimal).
        2. Pivots accounting accounts ('Conta') into individual columns per Year and Scenario.
        3. Normalizes Portuguese column names to allow accent-insensitive lookups.
        4. Calculates DRE (Income Statement), BAL (Balance Sheet), and FLU (Cash Flow) KPIs.
        5. Computes liquidity, debt structure, profitability, and EVA metrics.
        6. Sets ratios to NaN for Year 12 (terminal liquidation year).
    """
    # Read the CSV with Brazilian locale formatting:
    # - sep=";": Semicolon separates columns
    # - decimal=",": Comma is used as the decimal mark (e.g. 10,50)
    # - thousands=".": Dot is used as thousands separator (e.g. 1.000.000)
    # - encoding="latin-1": Handles Portuguese accented characters (é, ã, ç, etc.)
    raw = pd.read_csv(path, sep=";", encoding="latin-1", decimal=",", thousands=".")

    # Standardize column naming
    raw = raw.rename(columns={"Cenario": "Cenário"})

    # Strip excess whitespace inside account names for cleaner matching
    raw["Conta"] = raw["Conta"].str.replace(r"\s+", " ", regex=True).str.strip()

    # PIVOT OPERATION:
    # The original file is in long format (each row is a single account value).
    # We pivot so that each unique (Ano, Cenário) is a single row, and each
    # financial account ('Conta') becomes a distinct column.
    wide = (
        raw.dropna(subset=["Conta"])
        .pivot_table(
            index=["Ano", "Cenário"], columns="Conta", values="Valor", aggfunc="first"
        )
        .reset_index()
    )

    # FEATURE ENGINEERING: CONCESSION TIMELINE
    # Extract the numeric year (e.g. "Ano 1" -> 1, "Ano 12" -> 12)
    wide["ano_num"] = wide["Ano"].str.extract(r"(\d+)").astype(int)

    # Map concession year to actual calendar year:
    # Concession starts in 2027 (Ano 1 = 1 + 2026 = 2027, Ano 12 = 12 + 2026 = 2038)
    wide["ano_calendario"] = wide["ano_num"] + 2026

    # Flag Year 12 as the contractual termination/handback year
    wide["encerramento"] = wide["ano_num"].eq(12)

    # ACCENT-INSENSITIVE COLUMN RESOLVER
    # Portuguese accounting labels often vary between sources (e.g., "Patrimônio Líquido" vs
    # "Patrimonio Liquido" or with/without hyphens). This helper performs NFD Unicode
    # normalization to safely locate the matching column regardless of accents or spacing.
    def col(name):
        def normalize(value):
            value = str(value).replace(" - ", " ")
            return "".join(
                c
                for c in unicodedata.normalize("NFD", value)
                if unicodedata.category(c) != "Mn"
            )

        found = [c for c in wide.columns if normalize(c) == normalize(name)]
        if not found:
            raise KeyError(f"Conta não encontrada: {name}")
        return wide[found[0]]

    # --------------------------------------------------------------------------
    # 1. EXTRACT RAW BASE ACCOUNTS (BALANÇO & DRE)
    # --------------------------------------------------------------------------
    receita, ac, pc = (
        col("DRE Receita"),  # Gross Revenue
        col("BAL Ativo Circulante"),  # Current Assets (short-term)
        col("BAL Passivo Circulante"),  # Current Liabilities (short-term)
    )
    pl, ativo, caixa = (
        col("BAL Patrimônio Líquido"),  # Shareholders' Equity
        col("BAL Total do Ativo"),  # Total Assets
        col("BAL Disponível"),  # Cash and Cash Equivalents
    )
    estoque, rlp, permanente = (
        col("BAL Estoques Diversos"),  # Inventory
        col(
            "BAL Realizável a Longo Prazo"
        ),  # Long-Term Receivables / Non-current Assets
        col("BAL Permanente"),  # Fixed / Permanent Assets (PPE)
    )

    # Total Debt Calculation: Current Liabilities + Other Debts + Loans + Contingency Provisions
    divida = pd.concat(
        [
            pc,
            col("BAL Outros deb"),
            col("BAL Emprést"),
            col("BAL Prov para Contingências"),
        ],
        axis=1,
    ).sum(axis=1)

    # --------------------------------------------------------------------------
    # 2. DRE METRICS (INCOME STATEMENT)
    # --------------------------------------------------------------------------
    wide["receita"] = receita
    wide["custos_variaveis"] = col("DRE Custos").abs()
    wide["ebitda"] = col("DRE EBITDA")
    wide["resultado_operacional"] = col("DRE Resultado Operacional")  # EBIT
    wide["resultado_liquido"] = col("DRE Resultado Líquido")  # Net Profit/Loss

    # Margins: operational efficiency relative to gross revenue
    wide["margem_ebitda"] = wide.ebitda.div(receita)
    wide["margem_liquida"] = wide.resultado_liquido.div(receita)

    # --------------------------------------------------------------------------
    # 3. PROFITABILITY & RETURN RATIOS
    # --------------------------------------------------------------------------
    # ROA (Return on Assets): Net Profit / Total Assets
    wide["roa"] = wide.resultado_liquido.div(ativo)

    # ROE (Return on Equity): Net Profit / Shareholders' Equity
    wide["roe"] = wide.resultado_liquido.div(pl.abs())

    # --------------------------------------------------------------------------
    # 4. LIQUIDITY INDICATORS (SHORT-TERM SOLVENCY)
    # --------------------------------------------------------------------------
    # Current Liquidity: Current Assets / Current Liabilities (> 1.0 indicates safety)
    wide["liquidez_corrente"] = ac.div(pc).abs()

    # Quick Liquidity: (Current Assets - Inventory) / Current Liabilities
    wide["liquidez_seca"] = (ac - estoque).div(pc).abs()

    # Immediate Liquidity: Cash / Current Liabilities (instant coverage)
    wide["liquidez_imediata"] = caixa.div(pc).abs()

    # General Liquidity: (Current Assets + Long-Term Receivables) / Total Debt
    wide["liquidez_geral"] = (ac + rlp).div(divida).abs()

    # --------------------------------------------------------------------------
    # 5. CAPITAL STRUCTURE & INDEBTEDNESS
    # --------------------------------------------------------------------------
    # Debt-to-Equity Ratio: Total Debt / Equity
    wide["participacao_capital_terceiros"] = divida.div(pl).abs()

    # Debt Composition: Share of total debt maturing in the short term (PC / Debt)
    wide["composicao_endividamento"] = pc.div(divida).abs()

    # Fixed Assets to Equity: (RLP + Permanent Assets) / Equity
    wide["imobilizacao_pl"] = (rlp + permanente).div(pl).abs()

    # Absolute Balances
    wide["divida_total"] = divida.abs()
    wide["ativo_total"], wide["patrimonio_liquido"], wide["caixa"] = ativo, pl, caixa

    # --------------------------------------------------------------------------
    # 6. CASH FLOW STATEMENT (FLU)
    # --------------------------------------------------------------------------
    wide["geracao_caixa"] = col("FLU Geração de Caixa")  # Operating Cash Flow
    wide["investimentos"] = col("FLU Investimentos")  # Capex / Investments
    wide["distribuicao_acionista"] = col(
        "FLU Distribuição para Acionista"
    )  # Dividends / Equity returns
    wide["saldo_inicial_caixa"] = col("FLU Saldo Inicial")  # Beginning cash balance
    wide["saldo_final_caixa"] = col("FLU Saldo Final")  # Ending cash balance

    # --------------------------------------------------------------------------
    # 7. ECONOMIC VALUE ADDED (EVA)
    # --------------------------------------------------------------------------
    # Formula: NOPAT - (Invested Capital * Cost of Capital)
    # - resultado_operacional * 0.66: Net Operating Profit After Tax (assuming 34% corporate tax)
    # - (ativo - pc): Invested Capital (Total Assets minus Non-interest Bearing Current Liabilities)
    # - 0.10: 10% Weighted Average Cost of Capital (WACC) hurdle rate
    wide["eva"] = wide.resultado_operacional * 0.66 - (ativo - pc) * 0.10

    # --------------------------------------------------------------------------
    # 8. TERMINAL YEAR ADJUSTMENTS
    # --------------------------------------------------------------------------
    # In Year 12 (concession handback/liquidation), traditional financial ratios
    # are distorted by contractual asset transfers. We mask them as NaN so they
    # do not skew ongoing operational trends.
    ratios = [
        "roa",
        "roe",
        "liquidez_corrente",
        "liquidez_seca",
        "liquidez_imediata",
        "liquidez_geral",
        "participacao_capital_terceiros",
        "composicao_endividamento",
        "imobilizacao_pl",
    ]
    wide.loc[wide.encerramento, ratios] = float("nan")
    return wide
