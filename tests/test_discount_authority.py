import unittest

import pandas as pd

from repositories.discount_repository import DiscountRepository
from repositories.user_repository import UserRepository
from services.auth_service import AuthService
from services.discount_service import DiscountService
from services.margin_service import MarginService


class DiscountAuthorityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        repository = DiscountRepository(
            "data/db_Alcadas_Desconto.csv",
            "data/db_Politicas_Desconto.csv",
        )
        cls.authorities = repository.load_authorities()
        cls.policies = repository.load_policies()
        cls.users = UserRepository(
            "data/db_Usuarios.csv"
        ).load_users()
        cls.service = DiscountService()

    def _user(self, email: str) -> dict[str, object]:
        user = AuthService().authenticate(
            email,
            "Jamef@2026",
            self.users,
            self.authorities,
        )
        self.assertIsNotNone(user)
        return user or {}

    def _result(
        self,
        user: dict[str, object],
        freight_weight_discount: float,
        ad_valorem_discount: float,
    ) -> pd.Series:
        freight = pd.DataFrame(
            [
                {
                    "STATUS_FRETE": "OK",
                    "UF": "PR",
                    "FAIXA_PESO": "50 A 75 KG",
                    "FRETE_PESO": 400.0,
                    "AD_VALOREM": 100.0,
                    "FRETE_PARCIAL": 500.0,
                }
            ]
        )
        return self.service.calculate_batch(
            freight,
            self.authorities,
            self.policies,
            user,
            freight_weight_discount,
            ad_valorem_discount,
        ).iloc[0]

    def test_flat_limits_are_checked_by_component(self) -> None:
        user = self._user("vendedor.interno@jamef.local")
        result = self._result(user, 0.30, 0.00)

        self.assertEqual(result["STATUS_ALCADA"], "APROVADO")
        self.assertAlmostEqual(result["FRETE_SIMULADO"], 380.0)

    def test_fv_above_limit_points_to_capable_authority(self) -> None:
        user = self._user("vendedor.interno@jamef.local")
        result = self._result(user, 0.20, 0.05)

        self.assertEqual(result["STATUS_ALCADA"], "BLOQUEADO")
        self.assertEqual(
            result["ALCADA_NECESSARIA"],
            "GERENTE REGIONAL / GERENTE SP",
        )
        self.assertAlmostEqual(result["FRETE_SIMULADO"], 415.0)

    def test_weight_discount_above_supervisor_points_to_regional(self) -> None:
        user = self._user("SUPERVISOR.INTERNO@JAMEF.LOCAL")
        result = self._result(user, 0.55, 0.00)

        self.assertEqual(result["STATUS_ALCADA"], "BLOQUEADO")
        self.assertEqual(
            result["ALCADA_NECESSARIA"],
            "GERENTE REGIONAL / GERENTE SP",
        )

    def test_margin_uses_simulated_freight_after_discount(self) -> None:
        result = pd.DataFrame(
            [
                {
                    "ROTA_CUSTO": "AJUCWB",
                    "STATUS_CUSTO": "OK",
                    "STATUS_FRETE": "OK",
                    "FRETE_PARCIAL": 500.0,
                    "FRETE_SIMULADO": 400.0,
                    "CUSTO_TOTAL": 100.0,
                }
            ]
        )
        representations = pd.DataFrame(
            [
                {
                    "CHAVE_ROTA_REPRESENTACAO": "AJUCWB",
                    "ROTA_REPRESENTACAO": "AJU_CWB",
                    "PERC_COLETA": 0.20,
                    "PERC_ENTREGA": 0.20,
                    "PERC_TERMINAIS": 0.10,
                    "PERC_FIXO_UNIDADES": 0.10,
                    "PERC_REDESPACHO": 0.10,
                    "PERC_TRANSFERENCIAS": 0.10,
                    "PERC_VAZIOS": 0.00,
                    "PERC_CUSTO_MATRIZ": 0.20,
                }
            ]
        )

        margin = MarginService().calculate_batch(
            result,
            representations,
        ).iloc[0]

        self.assertEqual(margin["STATUS_MARGEM"], "OK")
        self.assertAlmostEqual(margin["MARGEM_BRUTA_RS"], 340.0)


if __name__ == "__main__":
    unittest.main()
