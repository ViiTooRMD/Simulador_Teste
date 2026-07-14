import pandas as pd

from utils.normalization import normalize_text
from utils.number_conversion import to_number


class TableDiscountService:
    RANGE_DISCOUNT_COLUMNS = {
        "0 A 10 KG": "DESC_0_10",
        "10 A 20 KG": "DESC_10_20",
        "20 A 30 KG": "DESC_20_30",
        "30 A 50 KG": "DESC_30_50",
        "50 A 75 KG": "DESC_50_75",
        "75 A 100 KG": "DESC_75_100",
        "ACIMA DE 100 KG": "DESC_ACIMA_100",
    }
    BASE_COLUMNS = {
        "FRETE_FAIXA_10": "TABELA_0_10",
        "FRETE_FAIXA_20": "TABELA_10_20",
        "FRETE_FAIXA_30": "TABELA_20_30",
        "FRETE_FAIXA_50": "TABELA_30_50",
        "FRETE_FAIXA_75": "TABELA_50_75",
        "FRETE_FAIXA_100": "TABELA_75_100",
        "FRETE_KG_ACIMA_100": "TABELA_ACIMA_100",
        "PERCENTUAL_AD_VALOREM": "TABELA_FV",
    }

    def create_matrix(
        self,
        shipments: pd.DataFrame,
        cities: pd.DataFrame,
        freight_table: pd.DataFrame,
        origin: str,
    ) -> pd.DataFrame:
        flow = shipments.copy()
        flow["BUSCA"] = (
            flow["UF"].map(normalize_text)
            + flow["CIDADE DESTINO"].map(normalize_text)
        )
        city_routes = flow[["BUSCA"]].drop_duplicates().merge(
            cities[["BUSCA", "JAMEF"]].drop_duplicates("BUSCA"),
            on="BUSCA",
            how="left",
            validate="one_to_one",
        )
        city_routes["ROTA"] = normalize_text(origin) + city_routes[
            "JAMEF"
        ].fillna("")
        routes = city_routes["ROTA"].loc[lambda value: value != ""].unique()
        matrix = freight_table[freight_table["ROTA"].isin(routes)].copy()

        if matrix.empty:
            raise ValueError(
                "Nenhuma rota da tabela padrão atende ao fluxo informado."
            )

        keep = [
            "ROTA", "ORIGEM", "DESTINO", "UF_DESTINO",
            *self.BASE_COLUMNS.keys(),
        ]
        matrix = matrix[[column for column in keep if column in matrix.columns]]
        matrix = matrix.rename(columns=self.BASE_COLUMNS)
        for column in self.BASE_COLUMNS.values():
            if column in matrix.columns:
                percentage = column == "TABELA_FV"
                matrix[column] = matrix[column].map(
                    lambda value: to_number(value, percentage=percentage)
                )
        for column in self.discount_columns():
            matrix[column] = 0.0
        return matrix.reset_index(drop=True)

    def validate_authority(
        self,
        matrix: pd.DataFrame,
        user: dict[str, object],
        authorities: pd.DataFrame,
    ) -> dict[str, object]:
        weight_columns = list(self.RANGE_DISCOUNT_COLUMNS.values())
        numeric_weight = matrix[weight_columns].apply(
            lambda column: column.map(to_number)
        )
        weight_max = float(numeric_weight.max().max()) / 100
        fv_max = float(matrix["DESC_FV"].map(to_number).max()) / 100
        approved = (
            weight_max <= float(user["LIMITE_FRETE_PESO"]) + 1e-12
            and fv_max <= float(user["LIMITE_AD_VALOREM"]) + 1e-12
        )
        required = ""
        if not approved:
            capable = authorities[
                (authorities["ATIVO"] == "S")
                & (authorities["PODE_APROVAR"] == "S")
                & (authorities["ORDEM"] > float(user["ORDEM_ALCADA"]))
                & (authorities["DESCONTO_MAX_FRETE_PESO"] >= weight_max)
                & (authorities["DESCONTO_MAX_AD_VALOREM"] >= fv_max)
            ].sort_values("ORDEM")
            required = (
                str(capable.iloc[0]["PERFIL"])
                if not capable.empty
                else "FORA DA POLÍTICA / GERENTE NACIONAL"
            )
        return {
            "APROVADO": approved,
            "MAX_FRETE_PESO": weight_max,
            "MAX_FV": fv_max,
            "ALCADA_NECESSARIA": required,
        }

    @classmethod
    def discount_columns(cls) -> list[str]:
        return [*cls.RANGE_DISCOUNT_COLUMNS.values(), "DESC_FV"]
