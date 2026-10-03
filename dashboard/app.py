"""Dashboard financeiro inicial do projeto NOUR / CTI Global.

Executar a partir da raiz do repositório:
    python -m streamlit run dashboard/app.py
"""

from pathlib import Path
import unicodedata

import pandas as pd
import plotly.express as px
import streamlit as st


# Caminho raiz do repositório, calculado com base na localização deste arquivo.
# Se a estrutura de pastas mudar, ajuste parents[1] (dashboard/app.py -> raiz).
ROOT = Path(__file__).resolve().parents[1]
# Arquivo já padronizado para consumo pelo dashboard.
DATA_PATH = ROOT / "data" / "processed" / "Dados_Formatados_CTI.csv"
# Folha de estilos ao lado deste script, para separar apresentação da lógica.
STYLE_PATH = Path(__file__).with_name("style.css")

# Configuração global do Streamlit. page_title aparece na aba do navegador,
# page_icon controla o ícone e layout="wide" usa toda a largura disponível.
st.set_page_config(page_title="NOUR | Painel financeiro", page_icon="◒", layout="wide")


@st.cache_data(show_spinner="Preparando a base analítica...")
def load_data(path: str) -> pd.DataFrame:
    """Lê a base formatada, padroniza contas e calcula índices validados."""
    # CSV formatado usa cabeçalho e números no padrão brasileiro.
    raw = pd.read_csv(
        path,
        sep=";",
        encoding="latin-1",
        decimal=",",
        thousands=".",
    ).rename(columns={"Cenario": "Cenário"})
    # Uniformiza espaços em nomes de contas; isso evita colunas duplicadas por
    # diferenças de formatação invisíveis na planilha original.
    raw["Conta"] = raw["Conta"].str.replace(r"\s+", " ", regex=True).str.strip()
    contas = raw.dropna(subset=["Conta"])
    # Converte o formato longo (uma conta por linha) para uma linha por ano e
    # cenário, com cada conta em sua própria coluna. aggfunc="first" é usado
    # quando a origem contém mais de uma linha para a mesma combinação.
    wide = contas.pivot_table(
        index=["Ano", "Cenário"], columns="Conta", values="Valor", aggfunc="first"
    ).reset_index()
    # Extrai o número do período (por exemplo, "Ano 1" -> 1). O deslocamento
    # 2026 converte o período em ano calendário para os gráficos e rótulos.
    wide["ano_num"] = wide["Ano"].str.extract(r"(\d+)").astype(int)
    wide["ano_calendario"] = wide["ano_num"] + 2026
    wide["encerramento"] = wide["ano_num"].eq(12)

    def col(name: str) -> pd.Series:
        # A planilha e o CSV divergem pontualmente no hífen e nos acentos.
        # A normalização abaixo faz a busca tolerante a acentos e a " - ";
        # a coluna retornada continua sendo a original, com os valores intactos.
        def normalize(label: object) -> str:
            label = str(label).replace(" - ", " ")
            return "".join(
                char for char in unicodedata.normalize("NFD", label)
                if unicodedata.category(char) != "Mn"
            )

        exact = [c for c in wide.columns if normalize(c) == normalize(name)]
        if not exact:
            raise KeyError(f"Conta não encontrada: {name}")
        return wide[exact[0]]

    # Atalhos para as colunas da demonstração de resultados e do balanço.
    # Se os nomes na origem mudarem, ajuste os textos enviados a col().
    receita = col("DRE Receita")
    ativo_circulante = col("BAL Ativo Circulante")
    passivo_circulante = col("BAL Passivo Circulante")
    patrimonio = col("BAL Patrimônio Líquido")
    ativo_total = col("BAL Total do Ativo")
    caixa = col("BAL Disponível")
    estoque = col("BAL Estoques Diversos")
    realizavel_lp = col("BAL Realizável a Longo Prazo")
    permanente = col("BAL Permanente")
    outros_debitos = col("BAL Outros deb")
    emprestimos = col("BAL Emprést")
    contingencias = col("BAL Prov para Contingências")
    # SUMIFS da planilha trata conta ausente como zero; sum reproduz esse caso
    # no encerramento, quando nem todos os componentes de dívida existem.
    divida_total = pd.concat(
        [passivo_circulante, outros_debitos, emprestimos, contingencias], axis=1
    ).sum(axis=1)

    # Fórmulas reproduzem a aba "Índices" da Planilha de Validação KPIs.
    # Cada linha abaixo cria uma nova coluna derivada que pode ser usada nas
    # métricas, gráficos, filtros ou no CSV baixado.
    wide["receita"] = receita
    # Custos são multiplicados por -1 via abs() para exibir despesas negativas
    # como valores positivos no resumo, preservando a convenção apresentada.
    wide["custos_variaveis"] = col("DRE Custos").abs()
    wide["ebitda"] = col("DRE EBITDA")
    wide["resultado_operacional"] = col("DRE Resultado Operacional")
    wide["resultado_liquido"] = col("DRE Resultado Líquido")
    wide["margem_ebitda"] = wide["ebitda"].div(receita)
    wide["margem_liquida"] = wide["resultado_liquido"].div(receita)
    wide["roa"] = wide["resultado_liquido"].div(ativo_total)
    wide["roe"] = wide["resultado_liquido"].div(patrimonio.abs())
    wide["liquidez_corrente"] = ativo_circulante.div(passivo_circulante).abs()
    wide["liquidez_seca"] = (ativo_circulante - estoque).div(passivo_circulante).abs()
    wide["liquidez_imediata"] = caixa.div(passivo_circulante).abs()
    wide["liquidez_geral"] = (ativo_circulante + realizavel_lp).div(divida_total).abs()
    wide["participacao_capital_terceiros"] = divida_total.div(patrimonio).abs()
    wide["composicao_endividamento"] = passivo_circulante.div(divida_total).abs()
    wide["imobilizacao_pl"] = (realizavel_lp + permanente).div(patrimonio).abs()
    wide["divida_total"] = divida_total.abs()
    wide["ativo_total"] = ativo_total
    wide["patrimonio_liquido"] = patrimonio
    wide["caixa"] = caixa
    wide["geracao_caixa"] = col("FLU Geração de Caixa")
    wide["investimentos"] = col("FLU Investimentos")
    wide["distribuicao_acionista"] = col("FLU Distribuição para Acionista")
    wide["saldo_inicial_caixa"] = col("FLU Saldo Inicial")
    wide["saldo_final_caixa"] = col("FLU Saldo Final")
    wide["eva"] = (wide["resultado_operacional"] * (1 - 0.34)) - (
        (ativo_total - passivo_circulante) * 0.10
    )
    # No encerramento da concessão, saldos de curto prazo são liquidados e
    # tornam denominadores próximos de zero. Razões patrimoniais deixam de ser
    # comparáveis; preservar o valor seria matematicamente válido, mas enganoso.
    ratio_columns = [
        "roa", "roe", "liquidez_corrente", "liquidez_seca", "liquidez_imediata",
        "liquidez_geral", "participacao_capital_terceiros", "composicao_endividamento",
        "imobilizacao_pl",
    ]
    wide.loc[wide["encerramento"], ratio_columns] = float("nan")
    return wide


def brl(value: float) -> str:
    # Converte números para texto em reais e abrevia em milhões ou bilhões.
    # Os limites e casas decimais podem ser alterados aqui para mudar os cartões.
    if pd.isna(value):
        return "—"
    scale, suffix = (1e9, " bi") if abs(value) >= 1e9 else (1e6, " mi")
    return f"R$ {value / scale:,.2f}{suffix}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(value: float) -> str:
    # Formato percentual com vírgula decimal, adequado à apresentação brasileira.
    return "—" if pd.isna(value) else f"{value:.1%}".replace(".", ",")


def ratio(value: float) -> str:
    return "n.a." if pd.isna(value) else f"{value:.2f}"


def style_chart(fig):
    """Aplica identidade visual NOUR aos gráficos, fora do tema padrão Streamlit."""
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font={"color": "#10233f", "family": "Arial, sans-serif"},
        title={"font": {"color": "#10233f", "size": 18}},
        legend={"font": {"color": "#10233f"}, "bgcolor": "rgba(255,255,255,0)"},
        hoverlabel={"bgcolor": "#10233f", "font": {"color": "#ffffff"}},
        margin={"l": 18, "r": 18, "t": 56, "b": 18},
    )
    fig.update_xaxes(
        gridcolor="#e3ebf3", linecolor="#c8d5e3", zerolinecolor="#c8d5e3",
        tickfont={"color": "#526b86"}, title_font={"color": "#526b86"},
    )
    fig.update_yaxes(
        gridcolor="#e3ebf3", linecolor="#c8d5e3", zerolinecolor="#c8d5e3",
        tickfont={"color": "#526b86"}, title_font={"color": "#526b86"},
    )
    return fig


try:
    # Streamlit guarda o resultado em cache para evitar reler e recalcular a
    # base em cada interação. O decorador usa o caminho como chave do cache.
    data = load_data(str(DATA_PATH))
except (FileNotFoundError, KeyError, pd.errors.ParserError) as error:
    st.error(f"Não foi possível preparar a base de dados: {error}")
    st.stop()

# Cabeçalho principal: textos e descrição podem ser editados diretamente aqui.
st.title("Nour Dashboard")
st.caption(
    "Simulação CTI Global · 1.200 cenários financeiros para os anos de 2027 a 2038"
)

# O Streamlit não carrega CSS externo automaticamente. Lemos o arquivo da pasta
# do app e o injetamos no documento; assim as regras ficam editáveis em style.css.
custom_css = STYLE_PATH.read_text(encoding="utf-8")
st.markdown(f"<style>\n{custom_css}\n</style>", unsafe_allow_html=True)
with st.sidebar:
    # Opções de filtro. "Todos" é uma opção especial interpretada abaixo e não
    # corresponde a um valor literal da coluna de dados.
    st.header("Recorte da análise")
    anos = sorted(data["ano_num"].unique())
    ano_options = ["Todos", *anos]
    anos_selecionados = st.multiselect(
        "Ano da concessão", ano_options, default=["Todos"], select_all=False
    )
    cenario_options = ["Todos", *sorted(data["Cenário"].unique())]
    cenarios_selecionados = st.multiselect(
        "Cenários", cenario_options, default=["Todos"], select_all=False
    )
    st.divider()
    st.caption(f"Fonte: `{DATA_PATH.relative_to(ROOT)}`")
    st.caption("Atualização: leitura direta da base formatada.")

# Aplica os filtros: escolher "Todos" mantém todos os valores daquela dimensão.
# .copy() cria um recorte independente para agregações e exportação posteriores.
filtered = data[
    (data["ano_num"].isin(anos) if "Todos" in anos_selecionados else data["ano_num"].isin(anos_selecionados))
    & (data["Cenário"].isin(cenario_options[1:]) if "Todos" in cenarios_selecionados else data["Cenário"].isin(cenarios_selecionados))
].copy()

if filtered.empty:
    st.warning("Escolha ao menos um ano e um cenário.")
    st.stop()

# Ano 12 é liquidação contratual; resumo executivo usa último ano operacional.
operating = filtered.loc[~filtered["encerramento"]].copy()
last_operating_year = operating["ano_num"].max()
latest = operating[operating["ano_num"].eq(last_operating_year)]
previous = operating[operating["ano_num"].eq(last_operating_year - 1)]

def variation(metric: str, percentage: bool = False, currency: bool = False) -> str | None:
    # A variação é diferença entre medianas dos grupos, não taxa de crescimento
    # relativa. percentage controla apenas a formatação do valor resultante.
    if previous.empty:
        return None
    current = latest[metric].median()
    before = previous[metric].median()
    if pd.isna(current) or pd.isna(before):
        return "n.a."
    if percentage:
        return f"{(current - before):+.1%}".replace(".", ",")
    if currency:
        return brl(current - before)
    return f"{(current - before):+.2f}".replace(".", ",")

# Valores da DRE, DFC e balanço, agregados pela mediana dos cenários filtrados.
st.subheader(f"Resumo operacional — Ano {last_operating_year} ({2026 + last_operating_year})")
st.caption("Cartões mostram a mediana dos cenários filtrados; a variação é versus o ano anterior.")
cards = st.columns(5)
cards[0].metric("Receita", brl(latest["receita"].median()), variation("receita", currency=True))
cards[1].metric("EBITDA", brl(latest["ebitda"].median()), variation("ebitda", currency=True))
cards[2].metric("Resultado líquido", brl(latest["resultado_liquido"].median()), variation("resultado_liquido", currency=True))
cards[3].metric("Geração de caixa", brl(latest["geracao_caixa"].median()), variation("geracao_caixa", currency=True))
cards[4].metric("Dívida total", brl(latest["divida_total"].median()), variation("divida_total", currency=True))

st.subheader("Índices financeiros")
indices = st.columns(5)
indices[0].metric("Margem EBITDA", pct(latest["margem_ebitda"].median()), variation("margem_ebitda", True))
indices[1].metric("ROA", pct(latest["roa"].median()), variation("roa", True))
indices[2].metric("ROE", pct(latest["roe"].median()), variation("roe", True))
indices[3].metric("Liquidez corrente", ratio(latest["liquidez_corrente"].median()), variation("liquidez_corrente"))
indices[4].metric("Liquidez geral", ratio(latest["liquidez_geral"].median()), variation("liquidez_geral"))

# Tendências operacionais excluem liquidação planejada do Ano 12.
by_year = (
    operating.groupby(["ano_num", "ano_calendario"], as_index=False)
    .agg(
        receita=("receita", "median"),
        ebitda=("ebitda", "median"),
        margem_ebitda=("margem_ebitda", "median"),
        roe=("roe", "median"),
        liquidez_corrente=("liquidez_corrente", "median"),
        capital_terceiros=("participacao_capital_terceiros", "median"),
    )
)

# Probabilidades empíricas no conjunto de cenários selecionado. Elas mostram
# frequência simulada, não previsão estatística fora desta base.
risk_by_year = (
    operating.assign(
        prejuizo=operating["resultado_liquido"].lt(0).astype(float),
        caixa_negativo=operating["saldo_final_caixa"].lt(0).astype(float),
        liquidez_critica=operating["liquidez_corrente"].lt(1).astype(float),
        eva_negativo=operating["eva"].lt(0).astype(float),
    )
    .groupby(["ano_num", "ano_calendario"], as_index=False)[
        ["prejuizo", "caixa_negativo", "liquidez_critica", "eva_negativo"]
    ]
    .mean()
)
risk_long = risk_by_year.melt(
    id_vars=["ano_num", "ano_calendario"],
    value_vars=["prejuizo", "caixa_negativo", "liquidez_critica", "eva_negativo"],
    var_name="Evento",
    value_name="Probabilidade",
)
operating_latest = operating[operating["ano_num"].eq(last_operating_year)]
operating_previous = operating[operating["ano_num"].eq(last_operating_year - 1)]
risk_latest = risk_by_year[risk_by_year["ano_num"].eq(last_operating_year)].iloc[0]
growth = operating_latest["receita"].median() / operating_previous["receita"].median() - 1 if not operating_previous.empty else None

st.subheader("Leitura executiva")
insight_left, insight_right = st.columns([1.35, 1])
with insight_left:
    if risk_latest["prejuizo"] >= 0.5:
        st.error(f"Risco dominante: {pct(risk_latest['prejuizo'])} dos cenários operacionais terminam Ano {last_operating_year} com resultado líquido negativo. Viabilidade depende de reversão operacional ou financeira.")
    elif risk_latest["liquidez_critica"] >= 0.25:
        st.warning(f"Liquidez exige atenção: {pct(risk_latest['liquidez_critica'])} dos cenários ficam abaixo de 1,0x. Caixa pode não cobrir obrigações de curto prazo.")
    else:
        st.success("Recorte sem risco dominante de resultado ou liquidez. Ainda compare dispersão e cenários extremos antes de concluir viabilidade.")
    if growth is not None:
        direction = "cresce" if growth >= 0 else "recua"
        st.caption(f"Receita mediana {direction} {pct(abs(growth))} versus Ano {last_operating_year - 1}. Crescimento só cria valor quando preserva margem, caixa e EVA.")
with insight_right:
    risk_cards = st.columns(2)
    risk_cards[0].metric("Prob. prejuízo", pct(risk_latest["prejuizo"]))
    risk_cards[1].metric("Prob. caixa negativo", pct(risk_latest["caixa_negativo"]))
    risk_cards[0].metric("Prob. liquidez < 1x", pct(risk_latest["liquidez_critica"]))
    risk_cards[1].metric("Prob. EVA negativo", pct(risk_latest["eva_negativo"]))

with st.expander("Interpretação para decisão", expanded=True):
    revenue_low, revenue_high = operating_latest["receita"].quantile([0.1, 0.9])
    margin_low, margin_high = operating_latest["margem_ebitda"].quantile([0.1, 0.9])
    liquidity_low, liquidity_high = operating_latest["liquidez_corrente"].quantile([0.1, 0.9])
    st.markdown("\n\n".join([
        "**Faixa operacional.** No Ano %s, 80%% dos cenários centrais concentram receita entre **%s** e **%s**. Esta faixa mostra incerteza do modelo; não é intervalo de confiança de dados históricos." % (last_operating_year, brl(revenue_low), brl(revenue_high)),
        "**Eficiência.** Margem EBITDA entre **%s** e **%s** indica quanto da receita permanece antes de depreciação, juros e tributos. Margem alta só sustenta viabilidade se geração de caixa e EVA também permanecerem positivos." % (pct(margin_low), pct(margin_high)),
        "**Liquidez.** Entre percentis 10 e 90, liquidez corrente varia de **%sx** a **%sx**. Abaixo de 1,0x, ativos de curto prazo não cobrem passivos de curto prazo; acima de 1,0x, há cobertura contábil, mas não garantia de caixa disponível no prazo." % (ratio(liquidity_low), ratio(liquidity_high)),
        "**Decisão.** Priorize cenários onde lucro, caixa e EVA são positivos ao mesmo tempo. Receita isolada não prova viabilidade; perda de liquidez ou EVA negativo pode destruir valor mesmo com crescimento operacional.",
    ]))

terminal = filtered[filtered["encerramento"]]
if not terminal.empty:
    terminal_year = int(terminal["ano_num"].iloc[0])
    st.subheader(f"Liquidação contratual — Ano {terminal_year} ({2026 + terminal_year})")
    st.caption("Ano terminal separado da operação recorrente. Valores mostram mediana dos cenários selecionados.")
    terminal_cards = st.columns(5)
    terminal_cards[0].metric("Caixa inicial", brl(terminal["saldo_inicial_caixa"].median()))
    terminal_cards[1].metric("Geração de caixa", brl(terminal["geracao_caixa"].median()))
    terminal_cards[2].metric("Investimentos", brl(terminal["investimentos"].median()))
    terminal_cards[3].metric("Distribuição ao acionista", brl(terminal["distribuicao_acionista"].median()))
    terminal_cards[4].metric("Caixa final", brl(terminal["saldo_final_caixa"].median()))
    st.info(
        "Encerramento planejado não é risco operacional. Saldos patrimoniais e liquidez não entram nas tendências operacionais do Ano 12. "
        "Base não identifica se cada ativo foi vendido, revertido ao poder concedente ou indenizado; estes eventos exigem validação contratual."
    )

# Dois gráficos lado a lado. Os códigos hexadecimais no mapa definem as cores
# das séries; markers=True desenha pontos em cada ano.
left, right = st.columns(2)
with left:
    fig = px.line(
        by_year, x="ano_calendario", y=["receita", "ebitda"], markers=True,
        labels={"value": "R$", "ano_calendario": "Ano calendário", "variable": "Indicador"},
        title="Receita e EBITDA — mediana dos cenários",
        color_discrete_map={"receita": "#1f7a72", "ebitda": "#e9a23b"},
    )
    # Formatação do eixo vertical: prefixo em reais e abreviação de escala.
    fig.update_layout(legend_title_text="", yaxis_tickprefix="R$ ", yaxis_tickformat="~s")
    st.plotly_chart(style_chart(fig), use_container_width=True)
with right:
    fig = px.line(
        by_year, x="ano_calendario", y=["margem_ebitda", "liquidez_corrente"], markers=True,
        labels={"value": "Índice", "ano_calendario": "Ano calendário", "variable": "Indicador"},
        title="Rentabilidade e liquidez — mediana dos cenários",
        color_discrete_map={"margem_ebitda": "#1f7a72", "liquidez_corrente": "#8d5cba"},
    )
    fig.update_layout(legend_title_text="", yaxis_tickformat=".0%")
    # A série de liquidez usa eixo próprio para não ser mostrada como percentual.
    fig.update_traces(selector={"name": "liquidez_corrente"}, yaxis="y2")
    fig.update_layout(yaxis2=dict(overlaying="y", side="right", title="Liquidez corrente", tickformat=".2f"))
    st.plotly_chart(style_chart(fig), use_container_width=True)

st.subheader("Risco e criação de valor")
left, right = st.columns(2)
with left:
    risk_chart = px.line(
        risk_long, x="ano_calendario", y="Probabilidade", color="Evento",
        markers=True,
        labels={"Probabilidade": "Probabilidade entre cenários", "ano_calendario": "Ano"},
        title="Probabilidade de eventos críticos",
        color_discrete_map={"prejuizo": "#d45252", "caixa_negativo": "#d98c3d", "liquidez_critica": "#8d5cba", "eva_negativo": "#315f9b"},
    )
    risk_chart.update_layout(legend_title_text="", yaxis_tickformat=".0%")
    st.plotly_chart(style_chart(risk_chart), use_container_width=True)
with right:
    latest_scatter = operating_latest.copy()
    latest_scatter["situação"] = latest_scatter["resultado_liquido"].ge(0).map({True: "Lucro", False: "Prejuízo"})
    scatter = px.scatter(
        latest_scatter, x="liquidez_corrente", y="margem_ebitda", color="situação",
        size="receita", hover_name="Cenário", size_max=22,
        labels={"liquidez_corrente": "Liquidez corrente", "margem_ebitda": "Margem EBITDA"},
        title=f"Mapa de cenários — Ano {last_operating_year}",
        color_discrete_map={"Lucro": "#1f7a72", "Prejuízo": "#d45252"},
    )
    scatter.add_vline(x=1, line_dash="dot", line_color="#d98c3d")
    scatter.update_yaxes(tickformat=".0%")
    st.plotly_chart(style_chart(scatter), use_container_width=True)

left, right = st.columns(2)
with left:
    value_chart = px.line(
        operating.groupby(["ano_num", "ano_calendario"], as_index=False).agg(eva=("eva", "median"), resultado_liquido=("resultado_liquido", "median")),
        x="ano_calendario", y=["eva", "resultado_liquido"], markers=True,
        labels={"value": "R$", "ano_calendario": "Ano", "variable": "Métrica"},
        title="Valor econômico e resultado líquido",
        color_discrete_map={"eva": "#315f9b", "resultado_liquido": "#1f7a72"},
    )
    value_chart.update_layout(legend_title_text="", yaxis_tickprefix="R$ ", yaxis_tickformat="~s")
    st.plotly_chart(style_chart(value_chart), use_container_width=True)
with right:
    balance = latest[["divida_total", "caixa", "patrimonio_liquido"]].median().rename_axis("Componente").reset_index(name="Valor")
    balance["Componente"] = balance["Componente"].replace({"divida_total": "Dívida total", "caixa": "Caixa disponível", "patrimonio_liquido": "Patrimônio líquido"})
    balance_chart = px.bar(balance, x="Componente", y="Valor", text_auto=".2s", title=f"Estrutura financeira operacional — Ano {last_operating_year}", color="Componente", color_discrete_sequence=["#d45252", "#1f7a72", "#315f9b"])
    balance_chart.update_layout(showlegend=False, yaxis_tickprefix="R$ ", yaxis_tickformat="~s")
    st.plotly_chart(style_chart(balance_chart), use_container_width=True)

# Boxplot permite comparar a dispersão entre os cenários por ano. A lista define
# quais indicadores o seletor oferece e os textos amigáveis que aparecem na UI.
st.subheader("Distribuição entre cenários")
metric_labels = {
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
if operating.empty:
    st.info("Distribuição operacional indisponível: Ano 12 é apresentado na seção de encerramento.")
elif operating["Cenário"].nunique() < 2:
    st.info("Escolha mais de um cenário para observar a distribuição.")
else:
    selected_metric = st.selectbox("Indicador", list(metric_labels), format_func=metric_labels.get)
    distribution = px.box(
        operating, x="ano_calendario", y=selected_metric, points=False,
        labels={"ano_calendario": "Ano calendário", selected_metric: metric_labels[selected_metric]},
        color_discrete_sequence=["#1f7a72"],
    )
    if selected_metric in {"margem_ebitda", "roa", "roe", "composicao_endividamento"}:
        distribution.update_yaxes(tickformat=".0%")
    st.plotly_chart(style_chart(distribution), use_container_width=True)

# Conteúdo recolhível para deixar a tela principal mais enxuta sem ocultar
# definições metodológicas e avisos sobre a interpretação dos indicadores.
with st.expander("Metodologia, fórmulas e limitações"):
    st.markdown(
        """
        Os valores são projeções simuladas, não histórico realizado. A fonte é a base formatada da CTI,
        transformada para uma linha por combinação de ano e cenário. As fórmulas foram conferidas
        contra a aba **Índices** da Planilha de Validação KPIs.

        - Margem EBITDA = EBITDA / Receita; ROA = Resultado Líquido / Ativo Total; ROE = Resultado Líquido / |Patrimônio Líquido|.
        - Liquidez corrente = |Ativo Circulante / Passivo Circulante|; liquidez seca exclui estoques; imediata usa disponível.
        - Dívida total = Passivo Circulante + Outros Débitos + Empréstimos + Provisões para Contingências.
        - Liquidez geral, participação de capital de terceiros, composição do endividamento e imobilização do PL usam esta dívida total.
        - EVA = Resultado Operacional após 34% de imposto − 10% do capital empregado, conforme planilha.
        - Custos são apresentados em módulo positivo, pois a base registra despesas com sinal negativo.

        No Ano 12 ocorre o encerramento da concessão. Índices patrimoniais são marcados como n.a.
        porque saldos liquidados tornam denominadores próximos de zero e inviabilizam comparação econômica.
        """
    )

# Colunas e ordem do arquivo exportado. Adicione/remova nomes aqui para mudar
# exatamente o conteúdo disponibilizado no botão de download.
export_columns = [
    "Cenário", "Ano", "ano_calendario", "receita", "custos_variaveis", "ebitda",
    "resultado_operacional", "resultado_liquido", "geracao_caixa", "investimentos",
    "saldo_final_caixa", "divida_total", "margem_ebitda", "roa", "roe",
    "liquidez_corrente", "liquidez_seca", "liquidez_imediata", "liquidez_geral",
    "participacao_capital_terceiros", "composicao_endividamento", "imobilizacao_pl", "eva",
]
st.download_button(
    # O BOM (utf-8-sig) melhora a abertura do CSV com acentos no Excel.
    "Baixar recorte em CSV",
    filtered[export_columns].to_csv(index=False).encode("utf-8-sig"),
    file_name="nour_recorte_kpis.csv",
    mime="text/csv",
)
