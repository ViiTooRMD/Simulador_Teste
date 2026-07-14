import unittest

import pandas as pd

from services.financial_service import FinancialService
from services.parameter_service import ParameterService
from services.table_discount_service import TableDiscountService


class ParameterAndFinancialTest(unittest.TestCase):
    def setUp(self) -> None:
        self.shipment = pd.DataFrame([{
            "ID_EMBARQUE": "TESTE-001",
            "PESO REAL": 100,
            "PESO CUBADO": 50,
            "M3": 2,
        }])

    def test_paid_cubage_recalculates_existing_weight(self) -> None:
        result = ParameterService().prepare_shipments(
            self.shipment,
            "AJU",
            True,
            168,
            30,
            3,
        )

        self.assertEqual(result.iloc[0]["PESO CUBADO"], 336)
        self.assertEqual(
            result.iloc[0]["FONTE_PESO_CUBADO"],
            "M3_X_DENSIDADE_PARAMETRIZADA",
        )

    def test_unpaid_cubage_preserves_informed_weight(self) -> None:
        result = ParameterService().prepare_shipments(
            self.shipment,
            "AJU",
            False,
            168,
            30,
            3,
        )

        self.assertEqual(result.iloc[0]["PESO CUBADO"], 50)

    def test_unpaid_cubage_uses_300_when_weight_is_missing(self) -> None:
        shipment = self.shipment.copy()
        shipment["PESO CUBADO"] = 0
        result = ParameterService().prepare_shipments(
            shipment,
            "AJU",
            False,
            168,
            30,
            3,
        )

        self.assertEqual(result.iloc[0]["PESO CUBADO"], 600)

    def test_financial_impact_uses_monthly_selic_and_days(self) -> None:
        result = pd.DataFrame([{
            "FRETE_SIMULADO": 1000,
            "LAJIR_RS": 200,
        }])
        service = FinancialService()
        calculated = service.calculate_batch(result, 45).iloc[0]
        expected = 1000 * service.monthly_rate * 1.5

        self.assertAlmostEqual(
            calculated["IMPACTO_FINANCEIRO_RS"],
            expected,
        )
        self.assertAlmostEqual(
            calculated["LAJIR_APOS_FINANCEIRO_RS"],
            200 - expected,
        )

    def test_table_matrix_blocks_discount_above_flat_authority(self) -> None:
        matrix = pd.DataFrame([{
            "DESC_0_10": 35,
            "DESC_10_20": 0,
            "DESC_20_30": 0,
            "DESC_30_50": 0,
            "DESC_50_75": 0,
            "DESC_75_100": 0,
            "DESC_ACIMA_100": 0,
            "DESC_FV": 0,
        }])
        user = {
            "LIMITE_FRETE_PESO": 0.30,
            "LIMITE_AD_VALOREM": 0.0,
            "ORDEM_ALCADA": 1,
        }
        authorities = pd.DataFrame([
            {
                "ATIVO": "S",
                "PODE_APROVAR": "S",
                "ORDEM": 3,
                "DESCONTO_MAX_FRETE_PESO": 0.50,
                "DESCONTO_MAX_AD_VALOREM": 0.0,
                "PERFIL": "SUPERVISOR INTERNO",
            }
        ])

        validation = TableDiscountService().validate_authority(
            matrix,
            user,
            authorities,
        )

        self.assertFalse(validation["APROVADO"])
        self.assertEqual(
            validation["ALCADA_NECESSARIA"],
            "SUPERVISOR INTERNO",
        )

    def test_vertical_discount_shows_effective_range_and_kg_values(self) -> None:
        matrix = pd.DataFrame([{
            "ROTA": "SAOCWB",
            "ORIGEM": "SAO",
            "DESTINO": "CWB",
            "UF_DESTINO": "PR",
            "TABELA_0_10": 100.0,
            "TABELA_10_20": 120.0,
            "TABELA_20_30": 140.0,
            "TABELA_30_50": 160.0,
            "TABELA_50_75": 180.0,
            "TABELA_75_100": 200.0,
            "TABELA_ACIMA_100": 2.0,
            "TABELA_FV": 0.01,
            "DESC_0_10": 30.0,
            "DESC_10_20": 30.0,
            "DESC_20_30": 30.0,
            "DESC_30_50": 30.0,
            "DESC_50_75": 30.0,
            "DESC_75_100": 30.0,
            "DESC_ACIMA_100": 30.0,
            "DESC_FV": 20.0,
        }])

        vertical = TableDiscountService().to_vertical_view(matrix, "PR")
        range_value = vertical.loc[
            vertical["FAIXA"] == "0 A 10 KG",
            "VALOR_PROPOSTO",
        ].iloc[0]
        kg_value = vertical.loc[
            vertical["FAIXA"] == "ACIMA DE 100 KG",
            "VALOR_PROPOSTO",
        ].iloc[0]
        fv_value = vertical.loc[
            vertical["FAIXA"] == "FV / AD VALOREM",
            "VALOR_PROPOSTO",
        ].iloc[0]

        self.assertAlmostEqual(range_value, 70.0)
        self.assertAlmostEqual(kg_value, 1.4)
        self.assertAlmostEqual(fv_value, 0.8)

        commercial = TableDiscountService().to_commercial_table(
            matrix,
            "PR",
        )
        self.assertAlmostEqual(
            commercial.iloc[0]["0–10 kg (R$/CTRC)"],
            70.0,
        )
        self.assertAlmostEqual(
            commercial.iloc[0]["> 100 kg (R$/kg)"],
            1.4,
        )
        self.assertAlmostEqual(
            commercial.iloc[0]["FV (% NF)"],
            0.8,
        )


if __name__ == "__main__":
    unittest.main()
