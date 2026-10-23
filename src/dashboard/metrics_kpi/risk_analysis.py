

    # Evaluates binary adverse conditions across all simulated scenarios per year:
    # - Net Loss (Resultado Líquido < 0)
    # - Negative Cash (Saldo Final de Caixa < 0)
    # - Critical Liquidity (Liquidez Corrente < 1.0x)
    # - Value Destruction (EVA < 0)

def compute_risk_probabilities(operating):
    """Calcula as probabilidades anuais de eventos adversos baseados nas simulações."""
    if operating.empty:
        return []
    risk = (
        operating.assign(
            prejuizo=operating.resultado_liquido.lt(0).astype(float),
            caixa_negativo=operating.saldo_final_caixa.lt(0).astype(float),
            liquidez_critica=operating.liquidez_corrente.lt(1).astype(float),
            eva_negativo=operating.eva.lt(0).astype(float),
        )
        .groupby("ano_calendario", as_index=False)[
            ["prejuizo", "caixa_negativo", "liquidez_critica", "eva_negativo"]
        ]
        .mean()
    )
    risk_labels = {
        "prejuizo": "Prejuízo no ano",
        "caixa_negativo": "Caixa negativo",
        "liquidez_critica": "Liquidez abaixo de 1,0x",
        "eva_negativo": "EVA negativo",
    }
    risk_long = risk.melt(
        "ano_calendario", var_name="Evento", value_name="Probabilidade"
    )
    risk_long["Evento"] = risk_long["Evento"].map(risk_labels)
    return risk_long, risk_labels