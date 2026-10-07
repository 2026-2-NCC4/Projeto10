# Entendimento de Negócio

## 1. Compreensão do Problema da CTI
   A CTI Global é uma empresa especializada em gestão corporativa, planejamento e controle financeiro, focada no desenvolvimento de soluções de informação para decisões gerenciais.
   O Problema Central: A empresa necessita de uma solução analítica orientada a dados para resolver um problema de planejamento e desempenho financeiro.
   O objetivo do projeto não é construir um sistema transacional completo, mas sim implementar um pipeline de Ciência de Dados (Data Analytics) capaz de transformar dados brutos financeiros em informações úteis e acionáveis.

## 2. Mapeamento dos Usuários
   Os usuários principais da plataforma analítica serão os tomadores de decisão da CTI Global, englobando gestores que atuam tanto no nível estratégico quanto no nível operacional.

## 3. Decisões a Apoiar
   A solução baseada nos dados deverá apoiar as seguintes ações e decisões:
   - Acompanhamento de Desempenho: Monitorar e compreender o comportamento geral dos dados e a saúde financeira por meio de KPIs.
   - Comparações: Realizar comparações de desempenho financeiro e operacional entre diferentes períodos, segmentos, categorias, produtos ou unidades.
   - Análise de Relações: Avaliar estatisticamente as relações entre variáveis de negócios (como a regressão para explicar uma variável financeira-alvo), tendo sempre a clareza ética de que correlação não implica causalidade.
   - Planejamento e Sensibilidade: Tomar decisões baseadas em cenários simulados, avaliando qual é o impacto de alterações operacionais (como concessão de descontos, cupons, variação de custos ou volume de vendas) sobre a margem de lucro e demais indicadores.

## 4. Escopo do Mínimo Produto Viável (MVP)
   O escopo mínimo que define o MVP para a CTI é a entrega de um pipeline de Ciência de Dados integrado a um Dashboard Interativo na nuvem. O fluxo do MVP abrange:
   - Ingestão e Governança: Coleta e catalogação dos dados brutos preservados, com tratamento de nulos, inconsistências e anonimização de dados sensíveis (LGPD).
   - Tratamento e Integração: Criação de variáveis derivadas a partir das bases originais (ex.: cálculo de margem subtraindo custo da receita) e documentação em um Dicionário de Dados.
   - Modelagem e Análises: Execução de análises descritivas (medidas de dispersão e posição) e inferenciais (modelo de regressão linear compatível) em notebooks (Jupyter/Colab) de forma totalmente reprodutível.
   - Apresentação: Publicação de um dashboard analítico (ex.: Streamlit ou Dash) acessível na nuvem, contendo filtros interativos, notas metodológicas visíveis (fórmulas e fontes) e a funcionalidade de exportação de dados (CSV/PDF/XLSX).

## 5. Indicadores Mínimos Estipulados
   Para que o MVP seja considerado funcional, o painel financeiro deverá exibir no mínimo 5 indicadores (KPIs). Os indicadores financeiros e operacionais exigidos pelo projeto incluem:
   - Receita
   - Custos Variáveis
   - Margem
   - Ticket Médio
   - CAC (Custo de Aquisição de Clientes) simulado
   - LTV (Lifetime Value) simulado
   Cada um desses KPIs deve ter sua fórmula, premissa, unidade, fonte, periodicidade e interpretação gerencial estritamente documentadas em um "Dicionário de KPIs" e previamente validadas em uma planilha de conferência antes da integração ao dashboard.
