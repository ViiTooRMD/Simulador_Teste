import hashlib
import hmac

import pandas as pd


class AuthService:
    ITERATIONS = 200_000

    def authenticate(
        self,
        email: str,
        password: str,
        users: pd.DataFrame,
        authorities: pd.DataFrame,
    ) -> dict[str, object] | None:
        normalized_email = email.strip().lower()
        matched = users[
            (users["EMAIL"] == normalized_email)
            & (users["ATIVO"] == "S")
        ]

        if matched.empty:
            return None

        user = matched.iloc[0]
        calculated_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            str(user["SENHA_SALT"]).encode("utf-8"),
            self.ITERATIONS,
        ).hex()

        if not hmac.compare_digest(
            calculated_hash,
            str(user["SENHA_HASH"]),
        ):
            return None

        authority = authorities[
            (authorities["COD_PERFIL"] == user["COD_PERFIL"])
            & (authorities["ATIVO"] == "S")
        ]
        if authority.empty:
            return None

        authority_row = authority.iloc[0]
        return {
            "ID_USUARIO": user["ID_USUARIO"],
            "NOME": user["NOME"],
            "EMAIL": user["EMAIL"],
            "COD_PERFIL": user["COD_PERFIL"],
            "PERFIL": authority_row["PERFIL"],
            "ORDEM_ALCADA": authority_row["ORDEM"],
            "LIMITE_FRETE_PESO": authority_row[
                "DESCONTO_MAX_FRETE_PESO"
            ],
            "LIMITE_AD_VALOREM": authority_row[
                "DESCONTO_MAX_AD_VALOREM"
            ],
            "REGIAO": user["REGIAO"],
            "UF": user["UF"],
            "FILIAL": user["FILIAL"],
            "ADMIN": user["ADMIN"] == "S",
        }
