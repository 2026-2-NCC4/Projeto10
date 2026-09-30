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
# Arquivo de entrada: troque esta linha para apontar o dashboard a outra base.
DATA_PATH = ROOT / "data" / "raw" / "Dados_Originais_CTI.csv"
# Folha de estilos ao lado deste script, para separar apresentação da lógica.
STYLE_PATH = Path(__file__).with_name("style.css")

# Configuração global do Streamlit. page_title aparece na aba do navegador,
# page_icon controla o ícone e layout="wide" usa toda a largura disponível.
st.set_page_config(page_title="NOUR | Painel financeiro", page_icon="◒", layout="wide")


@st.cache_data(show_spinner="Preparando a base analítica...")
def load_data(path: str) -> pd.DataFrame:
    """Lê a base longa, padroniza contas e calcula os índices validados."""
    # O CSV vem separado por ponto e vírgula, sem cabeçalho, com números no
    # padrão brasileiro. Altere sep/encoding/decimal/thousands se a origem mudar.
    raw = pd.read_csv(
        path,
        sep=";",
        header=None,
        names=["Ano", "Cenário", "Conta", "Valor"],
        encoding="latin-1",
        decimal=",",
        thousands=".",
    )
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
    passivo_lp = col("BAL Exigível a Longo Prazo")
    patrimonio = col("BAL Patrimônio Líquido")
    ativo_total = col("BAL Total do Ativo")
    caixa = col("BAL Disponível")
    estoque = col("BAL Estoques Diversos")
    realizavel_lp = col("BAL Realizável a Longo Prazo")
    permanente = col("BAL Permanente")

    # Fórmulas reproduzem a aba "Índices" da Planilha de Validação KPIs.
    # Cada linha abaixo cria uma nova coluna derivada que pode ser usada nas
    # métricas, gráficos, filtros ou no CSV baixado.
    wide["receita"] = receita
    # Custos são multiplicados por -1 via abs() para exibir despesas negativas
    # como valores positivos no resumo, preservando a convenção apresentada.
    wide["custos_variaveis"] = col("DRE Custos").abs()
    wide["ebitda"] = col("DRE EBITDA")
    wide["resultado_liquido"] = col("DRE Resultado Líquido")
    wide["margem_ebitda"] = wide["ebitda"].div(receita)
    wide["margem_liquida"] = wide["resultado_liquido"].div(receita)
    wide["roa"] = wide["resultado_liquido"].div(ativo_total)
    wide["roe"] = wide["resultado_liquido"].div(patrimonio.abs())
    wide["liquidez_corrente"] = ativo_circulante.div(passivo_circulante).abs()
    wide["liquidez_seca"] = (ativo_circulante - estoque).div(passivo_circulante).abs()
    wide["liquidez_imediata"] = caixa.div(passivo_circulante).abs()
    wide["liquidez_geral"] = (ativo_circulante + realizavel_lp).div(
        passivo_circulante + passivo_lp
    ).abs()
    wide["participacao_capital_terceiros"] = (passivo_circulante + passivo_lp).div(
        patrimonio
    ).abs()
    wide["composicao_endividamento"] = passivo_circulante.div(
        passivo_circulante + passivo_lp
    ).abs()
    wide["imobilizacao_pl"] = (realizavel_lp + permanente).div(patrimonio).abs()
    wide["caixa"] = caixa
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


try:
    # Streamlit guarda o resultado em cache para evitar reler e recalcular a
    # base em cada interação. O decorador usa o caminho como chave do cache.
    data = load_data(str(DATA_PATH))
except (FileNotFoundError, KeyError, pd.errors.ParserError) as error:
    st.error(f"Não foi possível preparar a base de dados: {error}")
    st.stop()

# Cabeçalho principal: textos e descrição podem ser editados diretamente aqui.
st.title("NOUR")
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
    st.caption("Atualização: leitura direta da base bruta.")

# Aplica os filtros: escolher "Todos" mantém todos os valores daquela dimensão.
# .copy() cria um recorte independente para agregações e exportação posteriores.
filtered = data[
    (data["ano_num"].isin(anos) if "Todos" in anos_selecionados else data["ano_num"].isin(anos_selecionados))
    & (data["Cenário"].isin(cenario_options[1:]) if "Todos" in cenarios_selecionados else data["Cenário"].isin(cenarios_selecionados))
].copy()

if filtered.empty:
    st.warning("Escolha ao menos um ano e um cenário.")
    st.stop()

latest_year = filtered["ano_num"].max()
# Compara o período mais recente selecionado com o período imediatamente anterior.
latest = filtered[filtered["ano_num"].eq(latest_year)]
previous = filtered[filtered["ano_num"].eq(latest_year - 1)]

def variation(metric: str, percentage: bool = False) -> str | None:
    # A variação é diferença entre medianas dos grupos, não taxa de crescimento
    # relativa. percentage controla apenas a formatação do valor resultante.
    if previous.empty:
        return None
    current = latest[metric].median()
    before = previous[metric].median()
    if percentage:
        return f"{(current - before):+.1%}".replace(".", ",")
    return f"{(current - before):+.2f}".replace(".", ",")

# Cinco cartões em colunas iguais; troque st.columns(5) e os índices para mudar
# quantidade ou ordem dos indicadores exibidos.
st.subheader(f"Resumo — Ano {latest_year} ({2026 + latest_year})")
st.caption("Cartões mostram a mediana dos cenários filtrados; a variação é versus o ano anterior.")
cards = st.columns(5)
cards[0].metric("Receita", brl(latest["receita"].median()), variation("receita"))
cards[1].metric("Custos variáveis", brl(latest["custos_variaveis"].median()), variation("custos_variaveis"))
cards[2].metric("Margem EBITDA", pct(latest["margem_ebitda"].median()), variation("margem_ebitda", True))
cards[3].metric("ROE", pct(latest["roe"].median()), variation("roe", True))
cards[4].metric("Liquidez corrente", f"{latest['liquidez_corrente'].median():.2f}", variation("liquidez_corrente"))

# Para as linhas de tendência, reduz cada ano a uma mediana entre os cenários
# atualmente filtrados. Inclua novas agregações aqui para plotá-las em seguida.
by_year = (
    filtered.groupby(["ano_num", "ano_calendario"], as_index=False)
    .agg(
        receita=("receita", "median"),
        ebitda=("ebitda", "median"),
        margem_ebitda=("margem_ebitda", "median"),
        liquidez_corrente=("liquidez_corrente", "median"),
        capital_terceiros=("participacao_capital_terceiros", "median"),
    )
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
    st.plotly_chart(fig, use_container_width=True)
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
    st.plotly_chart(fig, use_container_width=True)

# Boxplot permite comparar a dispersão entre os cenários por ano. A lista define
# quais indicadores o seletor oferece e os textos amigáveis que aparecem na UI.
st.subheader("Distribuição entre cenários")
metric_labels = {
    "margem_ebitda": "Margem EBITDA",
    "roe": "ROE",
    "liquidez_corrente": "Liquidez corrente",
    "participacao_capital_terceiros": "Participação de capital de terceiros",
}
selected_metric = st.selectbox("Indicador", list(metric_labels), format_func=metric_labels.get)
distribution = px.box(
    filtered, x="ano_calendario", y=selected_metric, points=False,
    labels={"ano_calendario": "Ano calendário", selected_metric: metric_labels[selected_metric]},
    color_discrete_sequence=["#1f7a72"],
)
if selected_metric in {"margem_ebitda", "roe"}:
    distribution.update_yaxes(tickformat=".0%")
st.plotly_chart(distribution, use_container_width=True)

# Conteúdo recolhível para deixar a tela principal mais enxuta sem ocultar
# definições metodológicas e avisos sobre a interpretação dos indicadores.
with st.expander("Metodologia, fórmulas e limitações"):
    st.markdown(
        """
        Os valores são projeções simuladas, não histórico realizado. A fonte é a base bruta da CTI,
        transformada para uma linha por combinação de ano e cenário. As fórmulas foram conferidas
        contra a aba **Índices** da Planilha de Validação KPIs.

        - Margem EBITDA = EBITDA / Receita; ROE = Resultado Líquido / |Patrimônio Líquido|.
        - Liquidez corrente = |Ativo Circulante / Passivo Circulante|; liquidez seca exclui estoques.
        - Participação de capital de terceiros = |(Passivo Circulante + Exigível a Longo Prazo) / PL|.
        - Custos são apresentados em módulo positivo, pois a base registra despesas com sinal negativo.

        No Ano 12 ocorre o encerramento da concessão. Índices que dividem pelo passivo circulante
        podem ficar extremos e não devem ser comparados diretamente aos anos anteriores.
        """
    )

# Colunas e ordem do arquivo exportado. Adicione/remova nomes aqui para mudar
# exatamente o conteúdo disponibilizado no botão de download.
export_columns = ["Cenário", "Ano", "ano_calendario", "receita", "custos_variaveis", "ebitda", "margem_ebitda", "roe", "liquidez_corrente"]
st.download_button(
    # O BOM (utf-8-sig) melhora a abertura do CSV com acentos no Excel.
    "Baixar recorte em CSV",
    filtered[export_columns].to_csv(index=False).encode("utf-8-sig"),
    file_name="nour_recorte_kpis.csv",
    mime="text/csv",
)
