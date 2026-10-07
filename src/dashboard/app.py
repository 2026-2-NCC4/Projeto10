"""NOUR financial dashboard, implemented with Python and Dash.

Run from the repository root with ``python src/dashboard/app.py``.
"""

from pathlib import Path
import unicodedata

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = next(
    (
        path
        for path in (
            ROOT / "data" / "processed" / "Dados_Formatados_CTI.csv",
            ROOT / "src" / "data" / "processed" / "Dados_Formatados_CTI.csv",
        )
        if path.exists()
    ),
    ROOT / "src" / "data" / "processed" / "Dados_Formatados_CTI.csv",
)
COLORS = {
    "ink": "#171717",
    "teal": "#55a9e8",
    "blue": "#55a9e8",
    "amber": "#501839",
    "red": "#501839",
    "plum": "#501839",
    "sky": "#55a9e8",
}


def load_data(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, sep=";", encoding="latin-1", decimal=",", thousands=".")
    raw = raw.rename(columns={"Cenario": "Cenário"})
    raw["Conta"] = raw["Conta"].str.replace(r"\s+", " ", regex=True).str.strip()
    wide = (
        raw.dropna(subset=["Conta"])
        .pivot_table(
            index=["Ano", "Cenário"], columns="Conta", values="Valor", aggfunc="first"
        )
        .reset_index()
    )
    wide["ano_num"] = wide["Ano"].str.extract(r"(\d+)").astype(int)
    wide["ano_calendario"] = wide["ano_num"] + 2026
    wide["encerramento"] = wide["ano_num"].eq(12)

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

    receita, ac, pc = (
        col("DRE Receita"),
        col("BAL Ativo Circulante"),
        col("BAL Passivo Circulante"),
    )
    pl, ativo, caixa = (
        col("BAL Patrimônio Líquido"),
        col("BAL Total do Ativo"),
        col("BAL Disponível"),
    )
    estoque, rlp, permanente = (
        col("BAL Estoques Diversos"),
        col("BAL Realizável a Longo Prazo"),
        col("BAL Permanente"),
    )
    divida = pd.concat(
        [
            pc,
            col("BAL Outros deb"),
            col("BAL Emprést"),
            col("BAL Prov para Contingências"),
        ],
        axis=1,
    ).sum(axis=1)
    wide["receita"] = receita
    wide["custos_variaveis"] = col("DRE Custos").abs()
    wide["ebitda"] = col("DRE EBITDA")
    wide["resultado_operacional"] = col("DRE Resultado Operacional")
    wide["resultado_liquido"] = col("DRE Resultado Líquido")
    wide["margem_ebitda"] = wide.ebitda.div(receita)
    wide["margem_liquida"] = wide.resultado_liquido.div(receita)
    wide["roa"] = wide.resultado_liquido.div(ativo)
    wide["roe"] = wide.resultado_liquido.div(pl.abs())
    wide["liquidez_corrente"] = ac.div(pc).abs()
    wide["liquidez_seca"] = (ac - estoque).div(pc).abs()
    wide["liquidez_imediata"] = caixa.div(pc).abs()
    wide["liquidez_geral"] = (ac + rlp).div(divida).abs()
    wide["participacao_capital_terceiros"] = divida.div(pl).abs()
    wide["composicao_endividamento"] = pc.div(divida).abs()
    wide["imobilizacao_pl"] = (rlp + permanente).div(pl).abs()
    wide["divida_total"] = divida.abs()
    wide["ativo_total"], wide["patrimonio_liquido"], wide["caixa"] = ativo, pl, caixa
    wide["geracao_caixa"] = col("FLU Geração de Caixa")
    wide["investimentos"] = col("FLU Investimentos")
    wide["distribuicao_acionista"] = col("FLU Distribuição para Acionista")
    wide["saldo_inicial_caixa"] = col("FLU Saldo Inicial")
    wide["saldo_final_caixa"] = col("FLU Saldo Final")
    wide["eva"] = wide.resultado_operacional * 0.66 - (ativo - pc) * 0.10
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


DATA = load_data(DATA_PATH)
YEARS = sorted(DATA.ano_num.unique())
SCENARIOS = sorted(DATA["Cenário"].dropna().unique())
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
PERSPECTIVES = {
    "tecnica": "Técnica",
    "gestao": "Gestão",
    "investidores": "Investidores",
}
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
app = Dash(
    __name__,
    title="NOUR | Painel financeiro",
    assets_folder=str(Path(__file__).parent),
    suppress_callback_exceptions=True,
)
server = app.server

app.layout = html.Div(
    className="dashboard",
    children=[
        html.Main(
            className="main",
            children=[
                html.Header(
                    className="page-header",
                    children=[
                        html.H1("Painel financeiro"),
                        html.P("Simulação financeira · 1.200 cenários · 2027–2038"),
                    ],
                ),
                html.Div(id="dashboard-content", className="content"),
            ],
        ),
        html.Aside(
            className="sidebar",
            children=[
                html.Div(
                    [
                        html.Div("N", className="brand-mark"),
                        html.Div(
                            [
                                html.Div("NOUR", className="brand"),
                                html.Div("CTI GLOBAL", className="brand-caption"),
                            ]
                        ),
                    ],
                    className="brand-lockup",
                ),
                html.H2("Sua análise", className="sidebar-title"),
                html.Label("Perspectiva"),
                dcc.Dropdown(
                    id="perspective",
                    options=[
                        {"label": label, "value": key}
                        for key, label in PERSPECTIVES.items()
                    ],
                    value="gestao",
                    clearable=False,
                ),
                html.Label("Anos da concessão", className="filter-label"),
                dcc.Dropdown(
                    id="years",
                    options=[{"label": "Todos", "value": "all"}]
                    + [{"label": f"Ano {y} · {2026+y}", "value": y} for y in YEARS],
                    value=["all"],
                    multi=True,
                    clearable=False,
                ),
                html.Label("Cenários", className="filter-label"),
                dcc.Dropdown(
                    id="scenarios",
                    options=[{"label": "Todos", "value": "all"}]
                    + [{"label": str(x), "value": x} for x in SCENARIOS],
                    value=["all"],
                    multi=True,
                    clearable=False,
                ),
                html.Label("Indicador da distribuição", className="filter-label"),
                dcc.Dropdown(
                    id="distribution-metric",
                    options=[
                        {"label": label, "value": key}
                        for key, label in METRIC_LABELS.items()
                        if key in PERSPECTIVE_METRICS["gestao"]
                    ],
                    value="margem_ebitda",
                    clearable=False,
                ),
                html.Div(
                    className="sidebar-foot",
                    children=[
                        html.Span("FONTE"),
                        html.P("Base formatada CTI"),
                        html.Span("ATUALIZAÇÃO"),
                        html.P("Leitura direta dos dados locais"),
                    ],
                ),
            ],
        ),
    ],
)


def money(value):
    if pd.isna(value):
        return "—"
    scale, suffix = (1e9, "bi") if abs(value) >= 1e9 else (1e6, "mi")
    return (
        f"R$ {value/scale:,.2f} {suffix}".replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def percent(value):
    return "—" if pd.isna(value) else f"{value:.1%}".replace(".", ",")


def card(label, value, delta=None):
    children = [
        html.Div(label, className="metric-label"),
        html.Div(value, className="metric-value"),
    ]
    if delta is not None and not pd.isna(delta):
        children.append(
            html.Div(
                (
                    f"Variação: {delta:+.1%}".replace(".", ",")
                    if abs(delta) < 1
                    else f"Variação: {money(delta)}"
                ),
                className="metric-delta",
            )
        )
    return html.Div(children, className="metric-card")


def insight(title, text, tone="neutral"):
    return html.Div(
        [html.H3(title), html.P(text)], className=f"insight-card insight-{tone}"
    )


def section(title, subtitle, children):
    return html.Section(
        [
            html.Div([html.H2(title), html.P(subtitle, className="section-subtitle")]),
            *children,
        ],
        className="section",
    )


def chart(figure, class_name="chart-card"):
    figure.update_layout(
        template="plotly",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Arial, sans-serif", "color": COLORS["ink"]},
        margin={"l": 45, "r": 25, "t": 55, "b": 45},
        legend_title_text="",
    )
    figure.update_xaxes(gridcolor="#e6e6e6", linecolor="#c9c9c9")
    figure.update_yaxes(gridcolor="#e6e6e6", linecolor="#c9c9c9")
    return html.Div(
        dcc.Graph(figure=figure, config={"displayModeBar": False}, responsive=True),
        className=class_name,
    )


def render_content(
    years, scenarios, selected_metric="margem_ebitda", perspective="gestao"
):
    years, scenarios = years or [], scenarios or []
    perspective = perspective if perspective in PERSPECTIVES else "gestao"
    allowed_metrics = PERSPECTIVE_METRICS[perspective]
    selected_metric = (
        selected_metric if selected_metric in allowed_metrics else allowed_metrics[0]
    )
    chosen_years = YEARS if "all" in years or not years else years
    chosen_scenarios = SCENARIOS if "all" in scenarios or not scenarios else scenarios
    filtered = DATA[
        DATA.ano_num.isin(chosen_years) & DATA["Cenário"].isin(chosen_scenarios)
    ].copy()
    if filtered.empty:
        return [
            html.Div("Escolha ao menos um ano e um cenário.", className="empty-state")
        ]
    operating = filtered[~filtered.encerramento]
    if operating.empty:
        operating = filtered
    latest_year = int(operating.ano_num.max())
    latest = operating[operating.ano_num.eq(latest_year)]
    prev = operating[operating.ano_num.eq(latest_year - 1)]

    def delta(metric):
        return (
            latest[metric].median() - prev[metric].median() if not prev.empty else None
        )

    tiles1 = [
        card("Receita", money(latest.receita.median()), delta("receita")),
        card("EBITDA", money(latest.ebitda.median()), delta("ebitda")),
        card(
            "Resultado líquido",
            money(latest.resultado_liquido.median()),
            delta("resultado_liquido"),
        ),
        card(
            "Geração de caixa",
            money(latest.geracao_caixa.median()),
            delta("geracao_caixa"),
        ),
        card(
            "Dívida total", money(latest.divida_total.median()), delta("divida_total")
        ),
    ]
    tiles2 = [
        card(
            "Margem EBITDA",
            percent(latest.margem_ebitda.median()),
            delta("margem_ebitda"),
        ),
        card("ROA", percent(latest.roa.median()), delta("roa")),
        card("ROE", percent(latest.roe.median()), delta("roe")),
        card("Liquidez corrente", f"{latest.liquidez_corrente.median():.2f}x"),
        card("Liquidez geral", f"{latest.liquidez_geral.median():.2f}x"),
    ]
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
    trend = px.area(
        by_year,
        x="ano_calendario",
        y="receita",
        title="Receita ao longo da concessão",
        color_discrete_sequence=[COLORS["teal"]],
    )
    trend.add_trace(
        go.Scatter(
            x=by_year.ano_calendario,
            y=by_year.ebitda,
            mode="lines+markers",
            name="EBITDA",
            line={"color": COLORS["amber"], "width": 3},
            marker={"size": 7},
        )
    )
    trend.update_yaxes(tickprefix="R$ ", tickformat="~s")
    radar_metrics = [
        ("Margem EBITDA", "margem_ebitda"),
        ("ROE", "roe"),
        ("Liquidez", "liquidez_corrente"),
        ("EVA", "eva"),
        ("Geração de caixa", "geracao_caixa"),
        ("Receita", "receita"),
    ]
    radar_values = []
    for label, key in radar_metrics:
        vals, med = operating[key].dropna(), latest[key].median()
        lo, hi = vals.quantile(0.05), vals.quantile(0.95)
        score = (
            50
            if pd.isna(med) or hi == lo
            else max(8, min(100, 12 + 88 * (med - lo) / (hi - lo)))
        )
        radar_values.append((label, score))
    labels, scores = zip(*radar_values)
    index_fig = go.Figure(
        go.Barpolar(
            r=scores,
            theta=labels,
            width=[43] * len(labels),
            marker={
                "color": [
                    COLORS["plum"],
                    COLORS["plum"],
                    COLORS["plum"],
                    COLORS["plum"],
                    COLORS["sky"],
                    COLORS["sky"],
                ],
                "line": {"color": "#fff", "width": 3},
            },
            opacity=0.9,
            hovertemplate="%{theta}<br>Índice relativo: %{r:.0f}/100<extra></extra>",
        )
    )
    index_fig.update_layout(
        title=f"Perfil financeiro radial · Ano {latest_year}",
        polar={
            "hole": 0.38,
            "bgcolor": COLORS["sky"],
            "radialaxis": {
                "range": [0, 100],
                "showticklabels": False,
                "showline": False,
                "gridcolor": "rgba(80,24,57,.35)",
            },
            "angularaxis": {
                "gridcolor": "rgba(80,24,57,.35)",
                "linecolor": "#501839",
                "tickfont": {"color": "#501839"},
            },
        },
        showlegend=False,
    )
    index_fig.add_annotation(
        text="NOUR",
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font={"size": 16, "color": "#501839"},
    )
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
    risk_long = risk.melt(
        "ano_calendario", var_name="Evento", value_name="Probabilidade"
    )
    risk_fig = px.area(
        risk_long,
        x="ano_calendario",
        y="Probabilidade",
        color="Evento",
        title="Mapa de risco · probabilidade por ano",
        color_discrete_map={
            "prejuizo": "#501839",
            "caixa_negativo": "#55a9e8",
            "liquidez_critica": "#7a4b69",
            "eva_negativo": "#2e7fb9",
        },
    )
    risk_fig.update_yaxes(tickformat=".0%")
    latest_risk = risk.loc[risk["ano_calendario"].eq(2026 + latest_year)].iloc[0]
    revenue_change = delta("receita")
    margin_change = delta("margem_ebitda")
    cash_risk = latest_risk["caixa_negativo"]
    liquidity_risk = latest_risk["liquidez_critica"]
    eva_risk = latest_risk["eva_negativo"]
    selected_values = latest[selected_metric].dropna()
    p10, p90 = selected_values.quantile([0.10, 0.90])

    management_insights = [
        insight(
            "Tração de receita",
            (
                f"A mediana da receita variou {revenue_change:+.1%} frente ao ano anterior."
                if revenue_change is not None
                else "Não há ano anterior no recorte para comparar a receita."
            ),
        ),
        insight(
            "Eficiência operacional",
            (
                f"A margem EBITDA mudou {margin_change:+.1%} no período, "
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
    technical_insights = [
        insight(
            "Cobertura de curto prazo",
            f"A liquidez corrente mediana é {latest.liquidez_corrente.median():.2f}x; "
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
            f"No ano mais recente, os 80% centrais de {METRIC_LABELS[selected_metric].lower()} "
            f"vão de {percent(p10) if selected_metric in {'participacao_capital_terceiros', 'composicao_endividamento'} else f'{p10:.2f}x'} "
            f"a {percent(p90) if selected_metric in {'participacao_capital_terceiros', 'composicao_endividamento'} else f'{p90:.2f}x'}.",
        ),
    ]
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
            f"Para {METRIC_LABELS[selected_metric].lower()}, os percentis 10 e 90 no ano são "
            f"{percent(p10) if selected_metric in {'margem_ebitda', 'roa', 'roe'} else money(p10)} e "
            f"{percent(p90) if selected_metric in {'margem_ebitda', 'roa', 'roe'} else money(p90)}.",
        ),
    ]
    scatter = px.scatter(
        latest,
        x="margem_ebitda",
        y="eva",
        color="Cenário",
        size="receita",
        size_max=20,
        opacity=0.72,
        title=f"Cenários · margem EBITDA e EVA · Ano {latest_year}",
        labels={"margem_ebitda": "Margem EBITDA", "eva": "EVA (R$)"},
        color_discrete_sequence=[COLORS["plum"], COLORS["sky"]],
    )
    scatter.update_xaxes(tickformat=".0%")
    value_fig = px.line(
        by_year,
        x="ano_calendario",
        y=["eva", "geracao_caixa"],
        markers=True,
        title="EVA e geração de caixa",
        color_discrete_sequence=[COLORS["plum"], COLORS["sky"]],
    )
    value_fig.update_yaxes(tickprefix="R$ ", tickformat="~s")
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
    balance_fig = px.bar(
        balance,
        x="Componente",
        y="Valor",
        title=f"Estrutura financeira · Ano {latest_year}",
        color="Componente",
        color_discrete_map={
            "Dívida total": "#501839",
            "Caixa disponível": "#55a9e8",
            "Patrimônio líquido": "#7a4b69",
        },
    )
    balance_fig.update_layout(showlegend=False)

    terminal = filtered[filtered.encerramento]
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
    distribution = px.box(
        operating,
        x="ano_calendario",
        y=selected_metric,
        points=False,
        title=f"Distribuição dos cenários · {METRIC_LABELS[selected_metric]}",
        labels={
            "ano_calendario": "Ano calendário",
            selected_metric: METRIC_LABELS[selected_metric],
        },
        color_discrete_sequence=[COLORS["plum"]],
    )
    if selected_metric in {"margem_ebitda", "roa", "roe", "composicao_endividamento"}:
        distribution.update_yaxes(tickformat=".0%")
    if perspective == "tecnica":
        return [
            section(
                "Saúde financeira e controles",
                f"Ano {latest_year} ({2026+latest_year}) · mediana do recorte selecionado",
                [html.Div(tiles2, className="metrics-grid")],
            ),
            section(
                "Leituras para controle",
                "Interpretações calculadas a partir da mediana e da distribuição dos cenários selecionados.",
                [html.Div(technical_insights, className="insights-grid")],
            ),
            section(
                "Risco financeiro",
                "Probabilidade empírica de eventos de liquidez, resultado e criação de valor.",
                [chart(risk_fig)],
            ),
            section(
                "Distribuição de cenários",
                "Dispersão do indicador financeiro selecionado por ano.",
                [chart(distribution)],
            ),
        ]

    if perspective == "investidores":
        investor_tiles = [
            card("EBITDA", money(latest.ebitda.median()), delta("ebitda")),
            card(
                "Resultado líquido",
                money(latest.resultado_liquido.median()),
                delta("resultado_liquido"),
            ),
            card(
                "Geração de caixa",
                money(latest.geracao_caixa.median()),
                delta("geracao_caixa"),
            ),
            card("ROE", percent(latest.roe.median()), delta("roe")),
            card("EVA", money(latest.eva.median()), delta("eva")),
        ]
        return [
            section(
                "Retorno ao investidor",
                f"Ano {latest_year} ({2026+latest_year}) · mediana do recorte selecionado",
                [html.Div(investor_tiles, className="metrics-grid")],
            ),
            section(
                "Leituras para decisão de investimento",
                "O retorno é apresentado com sua incerteza; os textos acompanham o recorte de anos e cenários aplicado.",
                [html.Div(investor_insights, className="insights-grid")],
            ),
            section(
                "Valor e potencial de retorno",
                "Relação entre rentabilidade, criação de valor, caixa e estrutura de capital.",
                [
                    html.Div(
                        [chart(scatter), chart(value_fig), chart(balance_fig)],
                        className="chart-grid",
                    )
                ],
            ),
            *terminal_children,
            section(
                "Distribuição de cenários",
                "Amplitude dos retornos e indicadores observados nos cenários selecionados.",
                [chart(distribution)],
            ),
        ]

    return [
        section(
            "Resumo operacional",
            f"Ano {latest_year} ({2026+latest_year}) · mediana do recorte selecionado",
            [html.Div(tiles1, className="metrics-grid")],
        ),
        section(
            "Leituras para gestão",
            "Sinais que conectam desempenho, margem e risco de execução no recorte selecionado.",
            [html.Div(management_insights, className="insights-grid")],
        ),
        section(
            "Acompanhamento da operação",
            "Evolução de receita, EBITDA e riscos que exigem ação de gestão.",
            [
                html.Div(
                    [chart(trend), chart(value_fig), chart(risk_fig)],
                    className="chart-grid",
                )
            ],
        ),
        *terminal_children,
        section(
            "Distribuição de cenários",
            "Dispersão do indicador operacional selecionado por ano.",
            [chart(distribution)],
        ),
    ]


@app.callback(
    Output("distribution-metric", "options"),
    Output("distribution-metric", "value"),
    Input("perspective", "value"),
)
def set_distribution_metrics(perspective):
    perspective = perspective if perspective in PERSPECTIVE_METRICS else "gestao"
    metrics = PERSPECTIVE_METRICS[perspective]
    return (
        [{"label": METRIC_LABELS[key], "value": key} for key in metrics],
        metrics[0],
    )


@app.callback(
    Output("dashboard-content", "children"),
    Input("years", "value"),
    Input("scenarios", "value"),
    Input("distribution-metric", "value"),
    Input("perspective", "value"),
)
def render(years, scenarios, selected_metric, perspective):
    try:
        return render_content(years, scenarios, selected_metric, perspective)
    except Exception as error:
        app.logger.exception("Dashboard render failed")
        return [
            html.Div(
                f"Could not render charts: {type(error).__name__}: {error}",
                className="empty-state",
            )
        ]


# Serve the first dashboard view in the initial HTML response. The callback
# replaces it whenever the user changes a filter.
try:
    app.layout.children[0].children[1].children = render_content(
        YEARS, SCENARIOS, "margem_ebitda", "gestao"
    )
except Exception as error:
    app.logger.exception("Initial dashboard render failed")
    app.layout.children[0].children[1].children = [
        html.Div(
            f"Could not render charts: {type(error).__name__}: {error}",
            className="empty-state",
        )
    ]


if __name__ == "__main__":
    app.run(debug=False)
