import pandas as pd

from services.cost_service import CostService
from services.freight_service import FreightService


class SimulationService:
    def __init__(
        self,
        cost_service: CostService,
        freight_service: FreightService,
    ) -> None:
        self.cost_service = cost_service
        self.freight_service = freight_service

    def calculate_batch(
        self,
        shipments: pd.DataFrame,
        cities: pd.DataFrame,
        costs: pd.DataFrame,
        freight_table: pd.DataFrame,
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

        return combined
