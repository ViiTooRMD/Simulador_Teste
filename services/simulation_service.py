import pandas as pd

from services.cost_service import CostService
from services.discount_service import DiscountService
from services.freight_service import FreightService
from services.financial_service import FinancialService
from services.margin_service import MarginService


class SimulationService:
    def __init__(
        self,
        cost_service: CostService,
        freight_service: FreightService,
        discount_service: DiscountService,
        margin_service: MarginService,
        financial_service: FinancialService,
    ) -> None:
        self.cost_service = cost_service
        self.freight_service = freight_service
        self.discount_service = discount_service
        self.margin_service = margin_service
        self.financial_service = financial_service

    def calculate_batch(
        self,
        shipments: pd.DataFrame,
        cities: pd.DataFrame,
        costs: pd.DataFrame,
        freight_table: pd.DataFrame,
        cost_representations: pd.DataFrame,
        authorities: pd.DataFrame,
        discount_policies: pd.DataFrame,
        user: dict[str, object],
        use_excess_rule: bool = False,
        manual_freight_weight_discount: float | None = None,
        manual_ad_valorem_discount: float | None = None,
        discount_matrix: pd.DataFrame | None = None,
        payment_days: int = 30,
    ) -> pd.DataFrame:
        prepared_shipments = shipments.copy()

        if "ID_EMBARQUE" not in prepared_shipments.columns:
            prepared_shipments["ID_EMBARQUE"] = [
                f"EMB-{index + 1:06d}"
                for index in range(len(prepared_shipments))
            ]

        cost_result = self.cost_service.calculate_batch(
            shipments=prepared_shipments,
            cities=cities,
            costs=costs,
        )

        freight_result = (
            self.freight_service.calculate_batch(
                shipments=prepared_shipments,
                cities=cities,
                freight_table=freight_table,
                use_excess_rule=use_excess_rule,
            )
        )

        freight_columns = [
            column
            for column in freight_result.columns
            if column != "ID_EMBARQUE"
        ]

        combined = cost_result.merge(
            freight_result[
                ["ID_EMBARQUE"] + freight_columns
            ],
            on="ID_EMBARQUE",
            how="left",
            validate="one_to_one",
        )

        discounted = self.discount_service.calculate_batch(
            result=combined,
            authorities=authorities,
            policies=discount_policies,
            user=user,
            manual_freight_weight_discount=(
                manual_freight_weight_discount
            ),
            manual_ad_valorem_discount=(
                manual_ad_valorem_discount
            ),
            discount_matrix=discount_matrix,
        )

        margins = self.margin_service.calculate_batch(
            result=discounted,
            representations=cost_representations,
        )
        return self.financial_service.calculate_batch(
            result=margins,
            payment_days=payment_days,
        )
