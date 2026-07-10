from pathlib import Path
import re
import unicodedata

import numpy as np
import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Validação do Custeio",
    layout="wide",
)


ARQUIVO_CIDADES = Path("CIDADES.csv")
ARQUIVO_CUSTOS = Path("CUSTOS.csv")


def normalizar_texto(valor: object) -> str:
    """Padroniza textos utilizados como chave de cruzamento."""
    if pd.isna(valor):
        return ""

    texto = str(valor).strip().upper()
    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ascii", errors="ignore").decode("utf-8")
    texto = re.sub(r"\s+", " ", texto)

    return texto


def converter_numero(valor: object, percentual: bool = False) -> float:
    """
    Converte números no padrão brasileiro ou internacional.

    Exemplos aceitos:
    1.234,56
    1234,56
    1234.56
    R$ 1,25
    2,50%
    """
    if valor is None or pd.isna(valor):
        return 0.0

    if isinstance(valor, (int, float, np.number)):
        numero = float(valor)
    else:
        texto = str(valor).strip()

        if texto in {"", "-", "NAN", "NONE"}:
            return 0.0

        texto = texto.replace("R$", "")
        texto = texto.replace("%", "")
        texto = texto.replace(" ", "")

        # Padrão brasileiro: 1.234,56
        if "." in texto and "," in texto:
            texto = texto.replace(".", "").replace(",", ".")
        elif "," in texto:
            texto = texto.replace(",", ".")

        numero = float(texto)

    if percentual:
        return numero / 100.0

    return numero


def validar_colunas(
    dataframe: pd.DataFrame,
    obrigatorias: set[str],
    nome_arquivo: str,
) -> None:
    encontradas = set(dataframe.columns)
    ausentes = obrigatorias - encontradas

    if ausentes:
        raise ValueError(
            f"{nome_arquivo}: colunas obrigatórias ausentes: "
            f"{sorted(ausentes)}. "
            f"Colunas encontradas: {sorted(encontradas)}"
        )


def carregar_csv(caminho: Path) -> pd.DataFrame:
    if not caminho.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {caminho.resolve()}"
        )

    tentativas = [
        {"sep": ";", "encoding": "utf-8-sig"},
        {"sep": ";", "encoding": "latin1"},
        {"sep": ",", "encoding": "utf-8-sig"},
        {"sep": ",", "encoding": "latin1"},
    ]

    erros = []

    for parametros in tentativas:
        try:
            dataframe = pd.read_csv(
                caminho,
                dtype=str,
                keep_default_na=False,
                **parametros,
            )

            if len(dataframe.columns) <= 1:
                raise ValueError(
                    "O arquivo foi lido com apenas uma coluna; "
                    "o separador provavelmente está incorreto."
                )

            dataframe.columns = [
                normalizar_texto(coluna)
                for coluna in dataframe.columns
            ]

            return dataframe

        except Exception as erro:
            erros.append(
                f"{parametros}: {type(erro).__name__}: {erro}"
            )

    raise ValueError(
        f"Não foi possível ler {caminho.name}.\n\n"
        + "\n".join(erros)
    )


@st.cache_data(show_spinner=False)
def carregar_referencias() -> tuple[pd.DataFrame, pd.DataFrame]:
    cidades = carregar_csv(ARQUIVO_CIDADES)
    custos = carregar_csv(ARQUIVO_CUSTOS)

    validar_colunas(
        cidades,
        {
            "CIDADE",
            "UF",
            "JAMEF",
            "CAP_INT",
        },
        "CIDADES.csv",
    )

    validar_colunas(
        custos,
        {
            "ROTA",
            "PM",
            "R$_CAPITAL",
            "%_CAPITAL",
            "R$_INTERIOR",
            "%_INTERIOR",
        },
        "CUSTOS.csv",
    )

    return cidades, custos


def preparar_cidades(dataframe: pd.DataFrame) -> pd.DataFrame:
    resultado = dataframe.copy()

    resultado["CHAVE_CIDADE"] = resultado["CIDADE"].map(
        normalizar_texto
    )
    resultado["UF"] = resultado["UF"].map(normalizar_texto)
    resultado["JAMEF"] = resultado["JAMEF"].map(normalizar_texto)
    resultado["CAP_INT"] = resultado["CAP_INT"].map(normalizar_texto)

    def classificar_regiao(valor: str) -> str:
        if valor in {"C", "CAP", "CAPITAL"}:
            return "CAPITAL"

        if valor in {"I", "INT", "INTERIOR"}:
            return "INTERIOR"

        return "NAO_IDENTIFICADA"

    resultado["REGIAO_CALC"] = resultado["CAP_INT"].map(
        classificar_regiao
    )

    return resultado


def preparar_custos(dataframe: pd.DataFrame) -> pd.DataFrame:
    resultado = dataframe.copy()
    resultado["ROTA"] = resultado["ROTA"].map(normalizar_texto)

    return resultado


def calcular_custo_embarque(
    linha: pd.Series,
) -> dict[str, object]:
    rota = linha.get("ROTA_CALC", "")
    regiao = linha.get("REGIAO_CALC", "")

    if not linha.get("JAMEF"):
        return {
            "STATUS": "ERRO",
            "MENSAGEM": "Cidade e UF não encontradas no cadastro.",
            "PESO_CUSTEIO": np.nan,
            "CUSTO_PESO": np.nan,
            "CUSTO_VARIAVEL": np.nan,
            "CUSTO_TOTAL": np.nan,
        }

    if pd.isna(linha.get("PM")) or str(linha.get("PM")).strip() == "":
        return {
            "STATUS": "ERRO",
            "MENSAGEM": f"Rota {rota} não encontrada em CUSTOS.csv.",
            "PESO_CUSTEIO": np.nan,
            "CUSTO_PESO": np.nan,
            "CUSTO_VARIAVEL": np.nan,
            "CUSTO_TOTAL": np.nan,
        }

    if regiao not in {"CAPITAL", "INTERIOR"}:
        return {
            "STATUS": "ERRO",
            "MENSAGEM": (
                f"Classificação Capital/Interior inválida: "
                f"{linha.get('CAP_INT')}"
            ),
            "PESO_CUSTEIO": np.nan,
            "CUSTO_PESO": np.nan,
            "CUSTO_VARIAVEL": np.nan,
            "CUSTO_TOTAL": np.nan,
        }

    peso_real = converter_numero(linha.get("PESO REAL"))
    valor_mercadoria = converter_numero(
        linha.get("VALOR MERCADORIA")
    )
    peso_minimo = converter_numero(linha.get("PM"))

    peso_custeio = max(peso_real, peso_minimo)

    if regiao == "CAPITAL":
        custo_kg = converter_numero(linha.get("R$_CAPITAL"))
        percentual = converter_numero(
            linha.get("%_CAPITAL"),
            percentual=True,
        )
    else:
        custo_kg = converter_numero(linha.get("R$_INTERIOR"))
        percentual = converter_numero(
            linha.get("%_INTERIOR"),
            percentual=True,
        )

    custo_peso = peso_custeio * custo_kg
    custo_variavel = valor_mercadoria * percentual
    custo_total = custo_peso + custo_variavel

    return {
        "STATUS": "OK",
        "MENSAGEM": (
            f"{regiao} | PM={peso_minimo:.2f} | "
            f"Peso custeio={peso_custeio:.2f} | "
            f"R$/kg={custo_kg:.4f} | "
            f"Variável={percentual:.4%}"
        ),
        "PESO_CUSTEIO": peso_custeio,
        "CUSTO_KG": custo_kg,
        "PERCENTUAL_VARIAVEL": percentual,
        "CUSTO_PESO": custo_peso,
        "CUSTO_VARIAVEL": custo_variavel,
        "CUSTO_TOTAL": custo_total,
    }


st.title("Validação do racional de custo")

with st.sidebar:
    st.subheader("Diagnóstico")

    if st.button("Limpar cache dos arquivos"):
        st.cache_data.clear()
        st.rerun()

try:
    df_cidades, df_custos = carregar_referencias()
except Exception as erro:
    st.error("Falha ao carregar os arquivos de referência.")
    st.exception(erro)
    st.stop()

df_cidades = preparar_cidades(df_cidades)
df_custos = preparar_custos(df_custos)

with st.expander("Visualizar diagnóstico dos arquivos"):
    coluna_1, coluna_2 = st.columns(2)

    with coluna_1:
        st.write("CIDADES.csv")
        st.write(f"Linhas: {len(df_cidades):,}")
        st.write("Colunas:")
        st.code("\n".join(df_cidades.columns))
        st.dataframe(df_cidades.head(10), use_container_width=True)

    with coluna_2:
        st.write("CUSTOS.csv")
        st.write(f"Linhas: {len(df_custos):,}")
        st.write("Colunas:")
        st.code("\n".join(df_custos.columns))
        st.dataframe(df_custos.head(10), use_container_width=True)

origens_disponiveis = sorted(
    origem
    for origem in df_custos["ROTA"].str[:3].dropna().unique()
    if origem
)

with st.form("formulario_embarque"):
    st.subheader("Dados do embarque")

    coluna_1, coluna_2, coluna_3 = st.columns(3)

    with coluna_1:
        origem = st.selectbox(
            "Origem",
            options=origens_disponiveis,
        )

        cidade_destino = st.text_input(
            "Cidade de destino",
            value="MACEIÓ",
        )

        uf_destino = st.text_input(
            "UF de destino",
            value="AL",
            max_chars=2,
        )

    with coluna_2:
        peso_real = st.number_input(
            "Peso real",
            min_value=0.0,
            value=84.0,
            step=1.0,
        )

        peso_cubado = st.number_input(
            "Peso cubado",
            min_value=0.0,
            value=193.08,
            step=1.0,
        )

    with coluna_3:
        valor_mercadoria = st.number_input(
            "Valor da mercadoria",
            min_value=0.0,
            value=9178.41,
            step=100.0,
        )

    calcular = st.form_submit_button(
        "Calcular custo",
        type="primary",
    )

if calcular:
    df_embarque = pd.DataFrame(
        [
            {
                "CIDADE DESTINO": cidade_destino,
                "UF": uf_destino,
                "PESO REAL": peso_real,
                "PESO CUBADO": peso_cubado,
                "VALOR MERCADORIA": valor_mercadoria,
            }
        ]
    )

    df_embarque["CHAVE_CIDADE"] = df_embarque[
        "CIDADE DESTINO"
    ].map(normalizar_texto)

    df_embarque["UF"] = df_embarque["UF"].map(
        normalizar_texto
    )

    df_enriquecido = df_embarque.merge(
        df_cidades[
            [
                "CHAVE_CIDADE",
                "UF",
                "CIDADE",
                "JAMEF",
                "CAP_INT",
                "REGIAO_CALC",
            ]
        ],
        on=["CHAVE_CIDADE", "UF"],
        how="left",
        validate="many_to_one",
    )

    df_enriquecido["ROTA_CALC"] = (
        normalizar_texto(origem)
        + df_enriquecido["JAMEF"].fillna("")
    )

    df_resultado = df_enriquecido.merge(
        df_custos,
        left_on="ROTA_CALC",
        right_on="ROTA",
        how="left",
        validate="many_to_one",
    )

    detalhes = df_resultado.apply(
        calcular_custo_embarque,
        axis=1,
        result_type="expand",
    )

    df_resultado = pd.concat(
        [
            df_resultado.reset_index(drop=True),
            detalhes.reset_index(drop=True),
        ],
        axis=1,
    )

    linha = df_resultado.iloc[0]

    if linha["STATUS"] == "OK":
        st.success("Cálculo realizado.")

        card_1, card_2, card_3, card_4 = st.columns(4)

        card_1.metric(
            "Peso de custeio",
            f"{linha['PESO_CUSTEIO']:,.2f} kg",
        )
        card_2.metric(
            "Custo por peso",
            f"R$ {linha['CUSTO_PESO']:,.2f}",
        )
        card_3.metric(
            "Custo variável",
            f"R$ {linha['CUSTO_VARIAVEL']:,.2f}",
        )
        card_4.metric(
            "Custo total",
            f"R$ {linha['CUSTO_TOTAL']:,.2f}",
        )

    else:
        st.error(linha["MENSAGEM"])

    st.subheader("Detalhamento do cruzamento")

    colunas_exibicao = [
        "CIDADE DESTINO",
        "UF",
        "JAMEF",
        "CAP_INT",
        "REGIAO_CALC",
        "ROTA_CALC",
        "PM",
        "R$_CAPITAL",
        "%_CAPITAL",
        "R$_INTERIOR",
        "%_INTERIOR",
        "PESO REAL",
        "PESO_CUBADO",
        "PESO_CUSTEIO",
        "CUSTO_PESO",
        "CUSTO_VARIAVEL",
        "CUSTO_TOTAL",
        "STATUS",
        "MENSAGEM",
    ]

    colunas_existentes = [
        coluna
        for coluna in colunas_exibicao
        if coluna in df_resultado.columns
    ]

    st.dataframe(
        df_resultado[colunas_existentes],
        use_container_width=True,
    )
