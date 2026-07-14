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
    BASE_COLUMN_BY_RANGE = {
        "0 A 10 KG": "TABELA_0_10",
        "10 A 20 KG": "TABELA_10_20",
        "20 A 30 KG": "TABELA_20_30",
        "30 A 50 KG": "TABELA_30_50",
        "50 A 75 KG": "TABELA_50_75",
        "75 A 100 KG": "TABELA_75_100",
        "ACIMA DE 100 KG": "TABELA_ACIMA_100",
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

    def apply_to_uf(
        self,
        matrix: pd.DataFrame,
        state: str,
        weight_discount: float,
        fv_discount: float,
    ) -> pd.DataFrame:
        updated = matrix.copy()
        mask = updated["UF_DESTINO"].map(normalize_text) == normalize_text(state)
        updated.loc[
            mask,
            list(self.RANGE_DISCOUNT_COLUMNS.values()),
        ] = float(weight_discount)
        updated.loc[mask, "DESC_FV"] = float(fv_discount)
        return updated

    def to_vertical_view(
        self,
        matrix: pd.DataFrame,
        state: str,
    ) -> pd.DataFrame:
        selected = matrix[
            matrix["UF_DESTINO"].map(normalize_text) == normalize_text(state)
        ]
        records: list[dict[str, object]] = []
        for _, route in selected.iterrows():
            for weight_range, discount_column in (
                self.RANGE_DISCOUNT_COLUMNS.items()
            ):
                table_value = to_number(
                    route.get(self.BASE_COLUMN_BY_RANGE[weight_range])
                )
                discount = to_number(route.get(discount_column))
                records.append({
                    "ROTA": route.get("ROTA", ""),
                    "DESTINO": route.get("DESTINO", ""),
                    "UF": route.get("UF_DESTINO", ""),
                    "FAIXA": weight_range,
                    "UNIDADE": (
                        "R$/kg"
                        if weight_range == "ACIMA DE 100 KG"
                        else "R$/CTRC"
                    ),
                    "VALOR_TABELA": table_value,
                    "DESCONTO_PCT": discount,
                    "VALOR_PROPOSTO": table_value * (1 - discount / 100),
                })

            fv_table = to_number(route.get("TABELA_FV")) * 100
            fv_discount = to_number(route.get("DESC_FV"))
            records.append({
                "ROTA": route.get("ROTA", ""),
                "DESTINO": route.get("DESTINO", ""),
                "UF": route.get("UF_DESTINO", ""),
                "FAIXA": "FV / AD VALOREM",
                "UNIDADE": "% NF",
                "VALOR_TABELA": fv_table,
                "DESCONTO_PCT": fv_discount,
                "VALOR_PROPOSTO": fv_table * (1 - fv_discount / 100),
            })
        return pd.DataFrame(records)

    def update_from_vertical_view(
        self,
        matrix: pd.DataFrame,
        vertical_view: pd.DataFrame,
    ) -> pd.DataFrame:
        updated = matrix.copy()
        for _, item in vertical_view.iterrows():
            route_mask = (
                updated["ROTA"].map(normalize_text)
                == normalize_text(item.get("ROTA"))
            )
            weight_range = normalize_text(item.get("FAIXA"))
            discount_column = self.RANGE_DISCOUNT_COLUMNS.get(weight_range)
            if weight_range == "FV / AD VALOREM":
                discount_column = "DESC_FV"
            if discount_column:
                updated.loc[route_mask, discount_column] = to_number(
                    item.get("DESCONTO_PCT")
                )
        return updated

    def to_commercial_table(
        self,
        matrix: pd.DataFrame,
        state: str,
    ) -> pd.DataFrame:
        selected = matrix[
            matrix["UF_DESTINO"].map(normalize_text) == normalize_text(state)
        ]
        records: list[dict[str, object]] = []
        for _, route in selected.iterrows():
            record: dict[str, object] = {
                "ROTA": route.get("ROTA", ""),
                "UF": route.get("UF_DESTINO", ""),
                "DESTINO": route.get("DESTINO", ""),
            }
            weight_discounts: list[float] = []
            for weight_range, discount_column in (
                self.RANGE_DISCOUNT_COLUMNS.items()
            ):
                discount = to_number(route.get(discount_column))
                weight_discounts.append(discount)
                table_value = to_number(
                    route.get(self.BASE_COLUMN_BY_RANGE[weight_range])
                )
                record[self._commercial_column(weight_range)] = (
                    table_value * (1 - discount / 100)
                )

            fv_discount = to_number(route.get("DESC_FV"))
            record["FV (% NF)"] = (
                to_number(route.get("TABELA_FV"))
                * 100
                * (1 - fv_discount / 100)
            )
            record["DESCONTO FRETE PESO (%)"] = max(
                weight_discounts,
                default=0.0,
            )
            record["DESCONTO FV (%)"] = fv_discount
            records.append(record)
        return pd.DataFrame(records)

    def update_from_commercial_table(
        self,
        matrix: pd.DataFrame,
        commercial_table: pd.DataFrame,
    ) -> pd.DataFrame:
        updated = matrix.copy()
        for _, item in commercial_table.iterrows():
            route_mask = (
                updated["ROTA"].map(normalize_text)
                == normalize_text(item.get("ROTA"))
            )
            weight_discount = to_number(
                item.get("DESCONTO FRETE PESO (%)")
            )
            fv_discount = to_number(item.get("DESCONTO FV (%)"))
            updated.loc[
                route_mask,
                list(self.RANGE_DISCOUNT_COLUMNS.values()),
            ] = weight_discount
            updated.loc[route_mask, "DESC_FV"] = fv_discount
        return updated

    def apply_editor_changes(
        self,
        matrix: pd.DataFrame,
        routes: list[str],
        states: list[str],
        edited_rows: dict[object, dict[str, object]],
    ) -> pd.DataFrame:
        updated = matrix.copy()
        for raw_index, changes in edited_rows.items():
            index = int(raw_index)
            if index < 0 or index >= len(routes):
                continue
            if index < len(states):
                route_mask = (
                    updated["UF_DESTINO"].map(normalize_text)
                    == normalize_text(states[index])
                )
            else:
                route_mask = (
                    updated["ROTA"].map(normalize_text)
                    == normalize_text(routes[index])
                )
            if "DESCONTO FRETE PESO (%)" in changes:
                updated.loc[
                    route_mask,
                    list(self.RANGE_DISCOUNT_COLUMNS.values()),
                ] = to_number(changes["DESCONTO FRETE PESO (%)"])
            if "DESCONTO FV (%)" in changes:
                updated.loc[route_mask, "DESC_FV"] = to_number(
                    changes["DESCONTO FV (%)"]
                )
        return updated

    @staticmethod
    def _commercial_column(weight_range: str) -> str:
        labels = {
            "0 A 10 KG": "0–10 kg (R$/CTRC)",
            "10 A 20 KG": "10–20 kg (R$/CTRC)",
            "20 A 30 KG": "20–30 kg (R$/CTRC)",
            "30 A 50 KG": "30–50 kg (R$/CTRC)",
            "50 A 75 KG": "50–75 kg (R$/CTRC)",
            "75 A 100 KG": "75–100 kg (R$/CTRC)",
            "ACIMA DE 100 KG": "> 100 kg (R$/kg)",
        }
        return labels[weight_range]

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
