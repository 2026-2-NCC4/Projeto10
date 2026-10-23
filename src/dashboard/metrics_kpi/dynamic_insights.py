# src/dashboard/metrics_kpis/dynamic_insights.py
import pandas as pd
from ui_elements import insight, money, percent, ratio

def compute_dynamic_insights(latest, prev, risk, latest_year, selected_metric, metric_labels):
    """Calcula e monta os insights dinâmicos baseados em limiares para gestores, técnicos e investidores."""
    
    # Tratamento de deltas auxiliares locais
    def delta(metric):
        if prev.empty or metric not in latest.columns or metric not in prev.columns:
            return None
        return latest[metric].median() - prev[metric].median()

    # Filtro de risco para o ano mais recente
    target_year = 2026 + latest_year
    risk_filtered = risk.loc[risk["ano_calendario"].eq(target_year)]
    
    if not risk_filtered.empty:
        latest_risk = risk_filtered.iloc[0]
        cash_risk = latest_risk.get("caixa_negativo", 0.0)
        liquidity_risk = latest_risk.get("liquidez_critica", 0.0)
        eva_risk = latest_risk.get("eva_negativo", 0.0)
    else:
        cash_risk, liquidity_risk, eva_risk = 0.0, 0.0, 0.0

    revenue_change = delta("receita")
    margin_change = delta("margem_ebitda")
    
    # Quartis/Percentis da métrica selecionada
    selected_values = latest[selected_metric].dropna() if not latest.empty and selected_metric in latest.columns else pd.Series([0])
    p10, p90 = selected_values.quantile([0.10, 0.90]) if not selected_values.empty else (0, 0)

    # 1. Management Perspective Insights
    management_insights = [
        insight(
            "Tração de receita",
            (
                f"A mediana da receita variou {money(revenue_change)} frente ao ano anterior."
                if revenue_change is not None
                else "Não há ano anterior no recorte para comparar a receita."
            ),
        ),
        insight(
            "Eficiência operacional",
            (
                f"A margem EBITDA mudou {f'{margin_change * 100:+.1f}'.replace('.', ',')} p.p. no período, "
                f"chegando a {percent(latest.margem_ebitda.median())}."
                if margin_change is not None
                else f"A margem EBITDA mediana é de {percent(latest.margem_ebitda.median())}."
            ),
        ),
        insight(
            "Prioridade de caixa",
            f"{cash_risk:.0%} dos cenários encerram o ano com caixa negativo; "
            "esse é o principal sinal para acompanhar no plano de ação.",
            "alert" if cash_risk >= 0.10 else "positive",
        ),
    ]

    # 2. Technical / Controllership Insights
    metric_label_name = metric_labels.get(selected_metric, "Indicador").lower()
    is_percent_metric = selected_metric in {'participacao_capital_terceiros', 'composicao_endividamento'}
    
    technical_insights = [
        insight(
            "Cobertura de curto prazo",
            f"A liquidez corrente mediana é {ratio(latest.liquidez_corrente.median())}; "
            f"{liquidity_risk:.0%} dos cenários ficam abaixo de 1,0x.",
            "alert" if liquidity_risk >= 0.10 else "positive",
        ),
        insight(
            "Dependência de terceiros",
            f"O capital de terceiros representa, na mediana, "
            f"{percent(latest.participacao_capital_terceiros.median())} do patrimônio líquido.",
        ),
        insight(
            "Faixa de incerteza",
            f"No ano mais recente, os 80% centrais de {metric_label_name} "
            f"vão de {percent(p10) if is_percent_metric else ratio(p10)} "
            f"a {percent(p90) if is_percent_metric else ratio(p90)}.",
        ),
    ]

    # 3. Investor / Shareholder Insights
    is_investor_percent = selected_metric in {'margem_ebitda', 'roa', 'roe'}
    investor_insights = [
        insight(
            "Criação de valor",
            f"O EVA mediano é {money(latest.eva.median())}; "
            f"{eva_risk:.0%} dos cenários apresentam EVA negativo no ano.",
            "alert" if eva_risk >= 0.10 else "positive",
        ),
        insight(
            "Retorno sobre o capital",
            f"O ROE mediano é {percent(latest.roe.median())}. "
            "Leia este indicador junto à estrutura de capital e à dispersão entre cenários.",
        ),
        insight(
            "Assimetria de cenários",
            f"Para {metric_label_name}, os percentis 10 e 90 no ano são "
            f"{percent(p10) if is_investor_percent else money(p10)} e "
            f"{percent(p90) if is_investor_percent else money(p90)}.",
        ),
    ]

    return management_insights, technical_insights, investor_insights