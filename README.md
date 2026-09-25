<h1 align="center">Fundação de Comércio Álvares Penteado</h1>

<div align="center">
<a href="https://www.fecap.br/"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRhZPrRa89Kma0ZZogxm0pi-tCn_TLKeHGVxywp-LXAFGR3B1DPouAJYHgKZGV0XTEf4AE&usqp=CAU" alt="FECAP - Fundação de Comércio Álvares Penteado" border="0"></a>

<h1>Nome do Projeto: Nour</h1>
</div>
<br/>

## Integrantes do Grupo

[Analice Coimbra Carneiro](https://github.com/AnaliceCoimbra)  
[Mariah Alice Pimentel Lôbo Pereira](https://github.com/alicelobwp)  
[Sofia Botechia Hernandes](https://github.com/sofiahernandes)  
[Victória Duarte Vieira Azevedo](https://github.com/victoria-azevedo)

## Professores Orientadores

[Eduardo Savino Gomes](https://www.linkedin.com/in/eduardo-savino-gomes-77833a10/)  
[Luis Fernando dos Santos Pires](https://www.linkedin.com/in/luisspires/)  
[Mauricio Lopes da Cunha](https://www.linkedin.com/in/mauricio-lopes-da-cunha-5630492a/)  
[Rodnil da Silva Moreira Lisbôa](https://www.linkedin.com/in/professorrodnil/)  
<br/>

## Entregas das Disciplinas

|          Disciplina          |                                                                   Entrega 1                                                                   | Entrega 2 |
| :--------------------------: | :-------------------------------------------------------------------------------------------------------------------------------------------: | :-------: |
| Análise Inferencial de Dados | [entrega-1/analise-inferencial-dados/](<https://github.com/2026-2-NCC4/Projeto10/tree/main/(documentos)/entrega-1/analise-inferencial-dados>) |     -     |
|        Contabilidade         |             [entrega-1/contabilidade/](<https://github.com/2026-2-NCC4/Projeto10/tree/main/(documentos)/entrega-1/contabilidade>)             |     -     |
|    Engenharia de Software    |    [entrega-1/engenharia-de-software/](<https://github.com/2026-2-NCC4/Projeto10/tree/main/(documentos)/entrega-1/engenharia-de-software>)    |     -     |
|   Projeto Interdisciplinar   |  [entrega-1/projeto-interdisciplinar/](<https://github.com/2026-2-NCC4/Projeto10/tree/main/(documentos)/entrega-1/projeto-interdisciplinar>)  |     -     |
|              -               |                                                                       -                                                                       |     -     |
|              -               |                                                                       -                                                                       |     -     |

<br/>

# Descrição

## Proposta Principal

O projeto Nour tem como objetivo desenvolver, em parceria com a empresa [CTI Global](https://ctiglobal.com/), um pipeline de Ciência de Dados para transformar dados brutos em informações úteis para análise e tomada de decisão. A solução contempla as etapas de coleta e ingestão dos dados, preparação e integração, análise estatística descritiva, análise inferencial e regressão, cálculo de indicadores financeiros, geração de relatórios e disponibilização dos resultados por meio de um dashboard interativo publicado na nuvem.

Sendo que o projeto integra entregas relacionadas às unidades curriculares de Análise Inferencial de Dados, Contabilidade e Finanças, Engenharia de Software e Arquitetura de Sistemas.

O dashboard apresenta, no mínimo, cinco indicadores, permitindo filtros e comparações temporais e segmentadas. Entre os indicadores estão receita, custos variáveis, margem, ticket médio e CAC/LTV simulados. Cada indicador possui sua fórmula, unidade, periodicidade e fonte documentadas.

A solução foi desenvolvida de forma reprodutível e rastreável, utilizando scripts e notebooks versionados no GitHub. Os dados originais estão preservados na camada `data/raw/`, enquanto os dados preparados e processados estão organizados nas camadas `data/staging/` e `data/processed/`.

O projeto também contempla recursos de análise de cenários e sensibilidade, permitindo simular impactos de alterações como descontos, cupons, custos e volume sobre a margem e outros indicadores financeiros.

<br/>

## 🛠 Estrutura de Pastas

```
Projeto10/
├── (documentos)/
├── dashboard/
├── data/
│   ├── raw/
│   ├── staging/
│   └── processed/
├── docs/
├── ES e ML/
├── notebooks/
├── src/
└── README.md
```

<br/>

## 🛠 Instalação

O projeto utiliza Python 3 como linguagem principal e ferramentas de análise e visualização de dados. Para executar o projeto localmente, recomenda-se utilizar um ambiente virtual Python.

```bash
# Clone o repositório
git clone https://github.com/2026-2-NCC4/Projeto10.git
cd Projeto10

# Crie e ative um ambiente virtual
python -m venv .venv

# No Windows
.venv\Scripts\activate

# No Linux/macOS
source .venv/bin/activate

# Instale as dependências do projeto
pip install -r requirements.txt
```

<br/>

## 💻 Configuração para Desenvolvimento

### Pré-requisitos

Para executar e desenvolver o projeto, são necessários:

- Python 3.x
- Git
- Jupyter Notebook ou Google Colab para execução dos notebooks
- VS Code ou outra IDE compatível com Python
- Navegador para acesso ao dashboard
- Dependências listadas em `requirements.txt`

<br/>

As principais tecnologias previstas para o projeto incluem:

- Python
- Pandas
- NumPy
- SciPy
- Statsmodels
- Matplotlib
- Plotly
- Streamlit
- Jupyter Notebook

<br/>

### Passo-a-passo de execução local

1. Clone o repositório:

```bash
git clone https://github.com/2026-2-NCC4/Projeto10.git
```

2. Acesse a pasta do projeto:

```bash
cd Projeto10
```

3. Crie e ative o ambiente virtual:

```bash
python -m venv .venv

# No Windows
.venv\Scripts\activate

# No Linux/macOS
source .venv/bin/activate
```

4. Instale as dependências:

```bash
pip install -r requirements.txt
```

5. Configure as variáveis de ambiente, caso sejam necessárias para fontes externas de dados. Utilize o arquivo `.env.example` como referência e mantenha informações sensíveis fora do repositório.

```bash
...
```

6. Execute os notebooks de análise conforme a sequência do projeto:

```text
notebooks/
...
```

7. Para executar o dashboard, acesse a pasta correspondente:

```bash
cd dashboard
```

8. Execute o aplicativo utilizando Streamlit:

```bash
streamlit run <arquivo_principal>.py
```

9. Acesse o endereço informado pelo Streamlit no navegador, normalmente:

```bash
http://localhost:8501
```

<br/>

### Organização dos dados

Os dados utilizados pelo projeto devem respeitar a seguinte organização:

```text
data/
├── raw/        # Dados originais, preservados sem alterações
├── staging/    # Dados em preparação e tratamento
└── processed/  # Base analítica final
```

Os arquivos originais fornecidos pela CTI devem permanecer na pasta `raw/` sem alterações. Dados complementares utilizados no projeto devem possuir sua origem, data de coleta, licença e justificativa documentadas.

<br/>

### Reprodução dos resultados

Os resultados devem ser reproduzíveis a partir dos notebooks, scripts, dados autorizados e documentação presentes no repositório. O fluxo previsto é:

```text
Dados brutos
↓
Ingestão e perfilamento
↓
Preparação e integração
↓
Análise descritiva
↓
Regressão
↓
Cálculo dos KPIs
↓
Análises de cenários e sensibilidade
↓
Dashboard e relatórios
```

O dashboard deverá disponibilizar pelo menos cinco indicadores, filtros e comparações temporais ou segmentadas, além de informações metodológicas como fonte, fórmula e data de atualização.

<br/>

## 📋 Licença/License

[Lumière](https://github.com/2026-1-NCC3/Projeto8) © 2026 by [Analice Coimbra Carneiro](https://github.com/analicecoimbra), [Mariah Alice Pimentel Lôbo Pereira](https://github.com/alicelobwp), [Sofia Botechia Hernandes](https://github.com/sofiahernandes), [Victória Duarte Vieira](https://github.com/viick04) and [FECAP - Fundação de Comércio Álvares Penteado](https://www.fecap.br) is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) <img src="https://mirrors.creativecommons.org/presskit/icons/cc.svg" height="20" width="20" style="margin-left: 0.2em;"><img src="https://mirrors.creativecommons.org/presskit/icons/by.svg" height="20" width="20" style="margin-left: 0.2em;"><img src="https://mirrors.creativecommons.org/presskit/icons/sa.svg" height="20" width="20" style="margin-left: 0.2em;">

<br/><br/>

## 🎓 Referências

[Creative Commons](https://creativecommons.org/share-your-work/)
[Template PI FECAP](https://github.com/fecaphub/Template_PI)
