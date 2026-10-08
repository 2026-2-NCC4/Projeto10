"""NOUR financial dashboard, implemented with Python and Dash.

Run from the repository root with ``python src/dashboard/app.py``.
"""

from pathlib import Path
import unicodedata

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html

from petals import petal

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
FONT_STACK = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
COLORS = {
    "ink": "#111111",
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
PERSPECTIVE_SUMMARIES = {
    "tecnica": "Liquidez, endividamento e os controles que sustentam a operação.",
    "gestao": "Receita, margem e os riscos que exigem decisão no próximo ciclo.",
    "investidores": "Retorno, criação de valor e a dispersão entre cenários.",
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


def row(label, control, readout=None):
    """One control-panel line: name on the left, control (and value) on the right."""
    right = [html.Div(control, className="row-control")]
    if readout is not None:
        right.append(readout)
    return html.Div(
        [
            html.Span(label, className="row-label"),
            html.Div(right, className="row-right"),
        ],
        className="row",
    )


def panel(title, children, open_by_default=True):
    return html.Details(
        [html.Summary(title), html.Div(children, className="panel-body")],
        open=open_by_default,
        className="panel",
    )


app.layout = html.Div(
    className="dashboard",
    children=[
        html.Main(
            className="main",
            children=[html.Div(id="dashboard-content", className="content")],
        ),
        html.Aside(
            className="sidebar",
            children=[
                html.Div(
                    [
                        html.Div("NOUR", className="brand"),
                        html.Div(
                            "CTI Global | Concessão 2027–2038",
                            className="brand-caption",
                        ),
                    ],
                    className="brand-lockup",
                ),
                panel(
                    "Perspectiva",
                    [
                        dcc.Tabs(
                            id="perspective",
                            value="gestao",
                            className="segmented",
                            parent_className="segmented-parent",
                            content_className="segmented-content",
                            children=[
                                dcc.Tab(
                                    label=label,
                                    value=key,
                                    className="segment",
                                    selected_className="segment--on",
                                )
                                for key, label in PERSPECTIVES.items()
                            ],
                        ),
                        html.P(
                            PERSPECTIVE_SUMMARIES["gestao"],
                            id="perspective-summary",
                            className="panel-note",
                        ),
                    ],
                ),
                panel(
                    "Recorte",
                    [
                        row(
                            "Anos da concessão",
                            dcc.RangeSlider(
                                id="years",
                                min=min(YEARS),
                                max=max(YEARS),
                                step=1,
                                value=[min(YEARS), max(YEARS)],
                                marks=None,
                                tooltip={"placement": "bottom"},
                            ),
                            html.Output(
                                f"{min(YEARS)}–{max(YEARS)}",
                                id="years-readout",
                                className="readout",
                            ),
                        ),
                        row(
                            "Cenários simulados",
                            dcc.RangeSlider(
                                id="scenarios",
                                min=1,
                                max=len(SCENARIOS),
                                step=1,
                                value=[1, len(SCENARIOS)],
                                marks=None,
                                tooltip={"placement": "bottom"},
                            ),
                            html.Output(
                                f"{len(SCENARIOS):,}".replace(",", "."),
                                id="scenarios-readout",
                                className="readout",
                            ),
                        ),
                    ],
                ),
                panel(
                    "Indicador",
                    [
                        row(
                            "Distribuição",
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
                        )
                    ],
                ),
                panel(
                    "Fonte",
                    [
                        html.Dl(
                            [
                                html.Dt("Base"),
                                html.Dd("Dados formatados CTI"),
                                html.Dt("Atualização"),
                                html.Dd("Leitura direta do arquivo local"),
                                html.Dt("Cobertura"),
                                html.Dd(
                                    f"{len(SCENARIOS)} cenários · {len(YEARS)} anos"
                                ),
                            ],
                            className="meta-list",
                        )
                    ],
                    open_by_default=False,
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


def ratio(value):
    """A coverage multiple, e.g. 1,76x. pt-BR uses the comma as decimal mark."""
    return "—" if pd.isna(value) else f"{value:.2f}x".replace(".", ",")


def card(label, value, delta=None):
    children = [
        html.Div(label, className="metric-label"),
        html.Div(value, className="metric-value"),
    ]
    if delta is not None and not pd.isna(delta):
        children.append(
            html.Div(
                (
                    # ponytail: ratios land under 1 and money never does, so the
                    # magnitude picks the unit. Pass the unit in if that stops holding.
                    f"Variação: {f'{delta * 100:+.1f}'.replace('.', ',')} p.p."
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
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": FONT_STACK, "color": COLORS["ink"], "size": 12},
        title_font={"size": 15, "color": COLORS["ink"]},
        margin={"l": 48, "r": 20, "t": 56, "b": 44},
        legend_title_text="",
        legend={"font": {"size": 12}},
        hoverlabel={"font": {"family": FONT_STACK, "size": 12}},
    )
    figure.update_xaxes(gridcolor="#eeeeee", linecolor="#cfcfcf", zeroline=False)
    figure.update_yaxes(gridcolor="#eeeeee", linecolor="#cfcfcf", zeroline=False)
    return html.Div(
        dcc.Graph(figure=figure, config={"displayModeBar": False}, responsive=True),
        className=class_name,
    )


HOLE = 0.34
PETAL_GAP = 0.30  # share of each slice left empty, so petals read as separate shapes


def radial_figure(scored_labels):
    """Petal chart of relative indicator scores, one rounded petal per metric."""
    figure = go.Figure()
    slice_deg = 360 / len(scored_labels)
    inner = 100 * HOLE / (1 - HOLE)
    for index, (label, score) in enumerate(scored_labels):
        theta, radius = petal(
            center_deg=index * slice_deg,
            width_deg=slice_deg * (1 - PETAL_GAP),
            inner=inner,
            outer=inner + score * (100 - inner) / 100,
            corner=14,
        )
        figure.add_trace(
            go.Scatterpolar(
                theta=theta,
                r=radius,
                mode="lines",
                fill="toself",
                fillcolor=COLORS["plum"],
                line={"width": 0},
                hoveron="fills",
                text=f"{label}<br>Índice relativo {score:.0f}/100",
                hoverinfo="text",
            )
        )
    figure.update_layout(
        showlegend=False,
        margin={"l": 80, "r": 80, "t": 56, "b": 56},
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": FONT_STACK},
        hoverlabel={
            "bgcolor": COLORS["plum"],
            "bordercolor": COLORS["plum"],
            "font": {"color": "#ffffff", "size": 13, "family": FONT_STACK},
        },
        polar={
            "hole": HOLE,
            "bgcolor": "rgba(0,0,0,0)",
            "radialaxis": {
                # Headroom past 100 so the labels clear the longest petal.
                "range": [0, 118],
                "showticklabels": False,
                "showline": False,
                "griddash": "dot",
                "gridcolor": "rgba(80,24,57,.40)",
                "gridwidth": 1,
                "tickvals": [25, 50, 75, 100],
            },
            "angularaxis": {
                "rotation": 90,
                "direction": "clockwise",
                "showline": False,
                "griddash": "dot",
                "gridcolor": "rgba(80,24,57,.40)",
                "gridwidth": 1,
                "linecolor": "rgba(80,24,57,.40)",
                "tickmode": "array",
                "tickvals": [i * slice_deg for i in range(len(scored_labels))],
                "ticktext": [
                    f"<span style='font-size:17px'>{score:.0f}</span><br>{label}"
                    for label, score in scored_labels
                ],
                "tickfont": {"color": COLORS["plum"], "size": 12},
            },
        },
    )
    return figure


def page(figure, subtitle, sections):
    """Full-bleed radial hero, then the perspective's sections."""
    return [
        html.Section(
            [
                html.Div(
                    [html.H1("Painel financeiro"), html.P(subtitle)],
                    className="hero-copy",
                ),
                dcc.Graph(
                    figure=figure,
                    config={"displayModeBar": False},
                    responsive=True,
                    className="hero-chart",
                    # Inline, not in the sheet: dcc.Graph sets its own inline
                    # `height: 100%`, which no stylesheet rule can outrank. That
                    # 100% resolves against an auto-height parent, so on every
                    # callback remount Plotly measures 0 and falls back to 700x450.
                    style={"height": "clamp(500px, 64vh, 700px)", "width": "100%"},
                ),
            ],
            className="hero",
        ),
        html.Div(sections, className="stack"),
    ]


def render_content(
    years, scenarios, selected_metric="margem_ebitda", perspective="gestao"
):
    year_from, year_to = years or [min(YEARS), max(YEARS)]
    scenario_from, scenario_to = scenarios or [1, len(SCENARIOS)]
    perspective = perspective if perspective in PERSPECTIVES else "gestao"
    allowed_metrics = PERSPECTIVE_METRICS[perspective]
    selected_metric = (
        selected_metric if selected_metric in allowed_metrics else allowed_metrics[0]
    )
    chosen_scenarios = SCENARIOS[scenario_from - 1 : scenario_to]
    filtered = DATA[
        DATA.ano_num.between(year_from, year_to)
        & DATA["Cenário"].isin(chosen_scenarios)
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
        card("Liquidez corrente", ratio(latest.liquidez_corrente.median())),
        card("Liquidez geral", ratio(latest.liquidez_geral.median())),
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
    # Short labels: these sit outside the ring and are clipped at phone widths
    # if they run long. The sections below carry the full indicator names.
    radar_metrics = [
        ("Margem", "margem_ebitda"),
        ("ROE", "roe"),
        ("Liquidez", "liquidez_corrente"),
        ("EVA", "eva"),
        ("Caixa", "geracao_caixa"),
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
    index_fig = radial_figure(radar_values)
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
    risk_fig = px.area(
        risk_long,
        x="ano_calendario",
        y="Probabilidade",
        color="Evento",
        title="Mapa de risco · probabilidade por ano",
        labels={"ano_calendario": "Ano calendário"},
        color_discrete_map={
            risk_labels["prejuizo"]: "#501839",
            risk_labels["caixa_negativo"]: "#55a9e8",
            risk_labels["liquidez_critica"]: "#7a4b69",
            risk_labels["eva_negativo"]: "#2e7fb9",
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
            f"No ano mais recente, os 80% centrais de {METRIC_LABELS[selected_metric].lower()} "
            f"vão de {percent(p10) if selected_metric in {'participacao_capital_terceiros', 'composicao_endividamento'} else ratio(p10)} "
            f"a {percent(p90) if selected_metric in {'participacao_capital_terceiros', 'composicao_endividamento'} else ratio(p90)}.",
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
        labels={
            "ano_calendario": "Ano calendário",
            "value": "Valor",
            "eva": "EVA",
            "geracao_caixa": "Geração de caixa",
        },
        color_discrete_sequence=[COLORS["plum"], COLORS["sky"]],
    )
    value_fig.for_each_trace(
        lambda trace: trace.update(
            name={"eva": "EVA", "geracao_caixa": "Geração de caixa"}[trace.name]
        )
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
    # Non-breaking space before each separator so a wrap never starts a line with "·".
    subtitle = " · ".join(
        [
            PERSPECTIVES[perspective],
            f"Ano {latest_year} ({2026 + latest_year})",
            f"{len(chosen_scenarios):,} cenários".replace(",", "."),
            "Mediana do Recorte",
        ]
    )

    if perspective == "tecnica":
        return page(
            index_fig,
            subtitle,
            [
                section(
                    "Saúde financeira e controles",
                    "Cobertura de curto prazo, estrutura de capital e retorno sobre o ativo.",
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
            ],
        )

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
        return page(
            index_fig,
            subtitle,
            [
                section(
                    "Retorno ao investidor",
                    "Resultado, caixa e criação de valor no último ano do recorte.",
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
            ],
        )

    return page(
        index_fig,
        subtitle,
        [
            section(
                "Resumo operacional",
                "Receita, resultado e caixa no último ano do recorte.",
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
        ],
    )


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
    Output("perspective-summary", "children"),
    Input("perspective", "value"),
)
def describe_perspective(perspective):
    return PERSPECTIVE_SUMMARIES.get(perspective, PERSPECTIVE_SUMMARIES["gestao"])


@app.callback(Output("years-readout", "children"), Input("years", "value"))
def show_year_range(years):
    first, last = years
    return str(first) if first == last else f"{first}–{last}"


@app.callback(Output("scenarios-readout", "children"), Input("scenarios", "value"))
def show_scenario_count(scenarios):
    first, last = scenarios
    return f"{last - first + 1:,}".replace(",", ".")


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
                f"Não foi possível montar os gráficos: {type(error).__name__}: {error}",
                className="empty-state",
            )
        ]


# Serve the first dashboard view in the initial HTML response. The callback
# replaces it whenever the user changes a filter.
app.layout.children[0].children[0].children = render(
    [min(YEARS), max(YEARS)], [1, len(SCENARIOS)], "margem_ebitda", "gestao"
)


if __name__ == "__main__":
    app.run(debug=False)
