def compute_yearly_medians(operating):
    """Calcula as medianas anuais detalhadas para as métricas da concessão."""
    if operating.empty:
        return operating

    by_year = operating.groupby(["ano_num", "ano_calendario"], as_index=False).agg(
        receita=("receita", "median"),
        ebitda=("ebitda", "median"),
        margem_ebitda=("margem_ebitda", "median"),
        roe=("roe", "median"),
        liquidez_corrente=("liquidez_corrente", "median"),
        capital_terceiros=("participacao_capital_terceiros", "median"),
        eva=("eva", "median"),
        geracao_caixa=("geracao_caixa", "median"),
    )
    return by_year
