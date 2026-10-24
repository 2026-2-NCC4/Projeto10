# src/dashboard/metrics_kpis/terminal_liquidation.py
from dash import html
from ui_elements import card, money, section


def build_terminal_liquidation_section(filtered):
    """Calcula os dados de encerramento da concessão e monta a seção de liquidação terminal."""
    terminal = filtered[filtered.encerramento] if not filtered.empty else filtered
    terminal_children = []

    if not terminal.empty:
        terminal_tiles = [
            card(label, money(terminal[key].median()))
            for label, key in [
                ("Caixa inicial", "saldo_inicial_caixa"),
                ("Geração de caixa", "geracao_caixa"),
                ("Investimentos", "investimentos"),
                ("Distribuição ao acionista", "distribuicao_acionista"),
                ("Caixa final", "saldo_final_caixa"),
            ]
        ]
        terminal_children = [
            section(
                "Liquidação contratual",
                "Ano 12 · encerramento planejado separado da operação recorrente.",
                [
                    html.Div(terminal_tiles, className="metrics-grid"),
                    html.P(
                        "Saldos liquidados não entram nas tendências operacionais. A base não detalha a destinação contratual de cada ativo.",
                        className="notice",
                    ),
                ],
            )
        ]

    return terminal_children
