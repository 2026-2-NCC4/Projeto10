# src/dashboard/metrics_kpis/balance_metrics.py
import pandas as pd

def compute_balance_structure(latest):
    """Prepara o DataFrame para o gráfico de barras da estrutura financeira."""
    if latest.empty:
        return pd.DataFrame(columns=["Componente", "Valor"])

    balance = pd.DataFrame(
        {
            "Componente": ["Dívida total", "Caixa disponível", "Patrimônio líquido"],
            "Valor": [
                latest.divida_total.median(),
                latest.caixa.median(),
                latest.patrimonio_liquido.median(),
            ],
        }
    )
    return balance