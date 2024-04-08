"""
Tests for `esg.utils.jwt`

Copyright 2024 FZI Research Center for Information Technology

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

SPDX-FileCopyrightText: 2024 FZI Research Center for Information Technology
SPDX-License-Identifier: Apache-2.0
"""

from datetime import datetime
from datetime import timedelta
from datetime import timezone

import json

import jwt
from pydantic import ValidationError
import pytest

from esg.utils.jwt import AccessTokenChecker

# Relevant stuff for tests that keycloak returns with default settings for the
# `realms/<realm>/.well-known/openid-configuration` URL.`
OPEN_ID_CONFIGURATION_TEMPLATE = """{
  "jwks_uri": "$ISSUER/protocol/openid-connect/certs",
  "id_token_signing_alg_values_supported": [
    "PS384",
    "RS384",
    "EdDSA",
    "ES384",
    "HS256",
    "HS512",
    "ES256",
    "RS256",
    "HS384",
    "ES512",
    "PS256",
    "PS512",
    "RS512"
  ]
}
"""

# A demo output from Keycloak's JWKS endpoint, i.e. from
# /realms/<realm>/protocol/openid-connect/certs
# The RSA256 key is decoupled to make access in tests simpler.
# spell-checker: disable
RSA256_KEY = {
    "kid": "6EMd1mmMI8msdSG3YJ-4k-PkqYbwFXRCPJx--Rlop6A",
    "kty": "RSA",
    "alg": "RS256",
    "use": "sig",
    "n": (
        "tXzYQI3KNRie9nb5S-urutl7hZudw0TpPEfdNm7Cb7vilbS43iBVQD8w276iMJ8-xu7fUz"
        "xchWthmSBZay8mytHpstWVHLWy5yGDtLMxKf_Di8FRG7d4V2BK6F4Tuhdju05Nf00O7RtW"
        "wRyumv1OnqcOKTPPCCcGYgFmJDrd2Q04Xa3jlOy5tnFrg26CP3IfkPfFXsJUs8eqB4C6zZ"
        "uuZeloj-jYRxoPTRu4jCegy8Jb-5ISpPpRWvzUULFr8f1dJcTtgQhlfxe8VD2MT5sLdnqM"
        "dl5jaiWTLZy-VZnfRYY5tyjGXF5dl4uJUUvXb_izsj5BAmwMQ7XIaSkimGAW8Q"
    ),
    "e": "AQAB",
    "x5c": [
        "MIICmzCCAYMCBgGOpVd4MDANBgkqhkiG9w0BAQsFADARMQ8wDQYDVQQDDAZtYXN0ZXIwHh"
        "cNMjQwNDAzMTkwMDU2WhcNMzQwNDAzMTkwMjM2WjARMQ8wDQYDVQQDDAZtYXN0ZXIwggEi"
        "MA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQC1fNhAjco1GJ72dvlL66u62XuFm53DRO"
        "k8R902bsJvu+KVtLjeIFVAPzDbvqIwnz7G7t9TPFyFa2GZIFlrLybK0emy1ZUctbLnIYO0"
        "szEp/8OLwVEbt3hXYEroXhO6F2O7Tk1/TQ7tG1bBHK6a/U6epw4pM88IJwZiAWYkOt3ZDT"
        "hdreOU7Lm2cWuDboI/ch+Q98VewlSzx6oHgLrNm65l6WiP6NhHGg9NG7iMJ6DLwlv7khKk"
        "+lFa/NRQsWvx/V0lxO2BCGV/F7xUPYxPmwt2eox2XmNqJZMtnL5Vmd9Fhjm3KMZcXl2Xi4"
        "lRS9dv+LOyPkECbAxDtchpKSKYYBbxAgMBAAEwDQYJKoZIhvcNAQELBQADggEBALC21zcH"
        "a3ZDNtXj8R/8339ULQcor9xOWJeqK6r24LClwXfef8XxgZ0jyvn6fbqzj0K1IuI6KgzuJQ"
        "wcNsP/tGAlobGiwoZiUaOmR+p8FPCaXIDYcF2eIgSHrJUjEov7bAR71c9mBazqKlZtif9N"
        "fVBF0ZCPBuADBal2Gl86TCtnG3vHbG6PivWAl6mP4ugdFmmfck36tMDJk97bYpFZ3Lw2Gs"
        "0fedWOb21gObxlT//y6EvM9qW+AsAixV7CHoduqZmpk3CoB68VCd5PAvoxLkFuhXx4O197"
        "4BX5GZFECSpLT3k9FsPpV0wTgKCwoRRizTKJGNzy1ygyaW2CVHOpMBE="
    ],
    "x5t": "0Sdn5KZ2KsLO-tjfXCQhohNFKjU",
    "x5t#S256": "eTq3o_w-_RwVuobPTyWKZYKXqjcycJ8F3SOcSEYlJDY",
}
# spell-checker:enable

# This is the corresponding private key to RSA public key above.
# It can be used to generate valid JWT signatures for testing.
RSA256_PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEogIBAAKCAQEAtXzYQI3KNRie9nb5S+urutl7hZudw0TpPEfdNm7Cb7vilbS4
3iBVQD8w276iMJ8+xu7fUzxchWthmSBZay8mytHpstWVHLWy5yGDtLMxKf/Di8FR
G7d4V2BK6F4Tuhdju05Nf00O7RtWwRyumv1OnqcOKTPPCCcGYgFmJDrd2Q04Xa3j
lOy5tnFrg26CP3IfkPfFXsJUs8eqB4C6zZuuZeloj+jYRxoPTRu4jCegy8Jb+5IS
pPpRWvzUULFr8f1dJcTtgQhlfxe8VD2MT5sLdnqMdl5jaiWTLZy+VZnfRYY5tyjG
XF5dl4uJUUvXb/izsj5BAmwMQ7XIaSkimGAW8QIDAQABAoIBAApDKM/0VJVOXZrD
3SfuXR5qiCy6FnXWvTY5PWiDuH9B9Azmvwy3GQBSMmySlIWZqPPtyPdiHTyMIbow
v+2q07o58XQ5Kz6IMGQXxeSfZ1h1IR++IDHS3OgFRrxp/sU8kllNPbOaQ2L5SJ1l
26JhpXhHgP+nxtKysOPffrZDao0Iihx4eeoWvWtg/NkKmPfId4gxEvtnt8IQAJhY
ZzHDjT14smOdSVNP9QrhSxEC+EXR82Uj5KvcZlCRC1QmpzAxFEi3nWQyY6tPRK9H
YuuGYJeFTM1UJnHwhThMdVc859Plu7ItK+Drf9aNPOK+mVhy2gCRhaVIs3MouCUn
6UxqKjkCgYEA/3Xk+NjVO3LD7Wm/mq/zc3F9S0HzXn+jgaMKLt1Rko5TnTPdqlma
GiROf75rJ9LZ/t3I0bcPJ+2YRdriL2cGVyKqIJNpD8RTLkQDCXYjHGtT1q0klkRg
ErmvREZiY3vtmT1TosQuMJ+oeJ/APdkt7wqiLsYBbo0Sa7dcIbZ+pZ0CgYEAtd71
pJFU+V5lKVBUWeWJ7wcb2Rlux3l617eZ758XdgxAbqq2x2rTk+258M/9hsqV3fTQ
KcUZSKdoLc2rXELrM29ZVWu7aev69L969fdk7boAOLr2yT0CBD9bU+zSHX64cYHv
hh6jaxRXwfRqhAtRHwddYKrCgSt/ryOSdggPwGUCgYB8ygx1+wX+qktHWFb+q2DT
TecUsjy+Nr+afhhlWDuWyevSaRmpM2fxyTaHdG9H3toahCCrQS8oJAo0ZX4EBeG1
Avv0Oc4io5a2jQamwozYPx2PSrkKpo//1bDmOzOowUsJhkmqwwaFPhjAA9mW3NZx
ZNJg4tykMkmDUOiyl0E6iQKBgBda6nCXuTHMzXDgv/RLZcssPodCnNdA4mWRTlNX
OswOBrgvdAlnzoPQo3ApRYVpvpUiOxkiFn0eAmLfZoISleGlCvPNQeP4SeHkNQYh
HvToTd77I3X0P64L9M5yOwlOnKD27qtqg9HcauidWpBaY7B4YaVoSFIOI/d5ufUu
U9eBAoGAYeDkOrzH3vRlsMkj8ghyjryJac9HM2c5w19AX2e3U+wB3UJPV1cX6XuG
SZ0yTU4pvCv+Zl63iOCWFHOy1dynIscIc+NJ1Y91tn3WOwdsmnkM9ukI0/IYzNWI
biEmrKSVxwxRJt+K3zxKeWw5y8R7Xp2bJjUlsuzq4J4z7uZ72dY=
-----END RSA PRIVATE KEY-----"""

INVALID_RSA_PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
MIICeAIBADANBgkqhkiG9w0BAQEFAASCAmIwggJeAgEAAoGBAL1TMnOPMo0cFaet
uFJvBHZHRoGOp9nu8/eZzqpjL3gsMx5PLLSNmOSc1y8dBF5bCEg4Ad2LcOtQmQO8
ZLCoc1dl712femZOWpWSObpJElTLD0uGxhFqP7NempjquuXJ1enHy9d6Dipsjlmn
pmgOBV7Us4nd+1JeKQVBPRlsWgZpAgMBAAECgYBfIEtsNtoefqr+ylGf0bo7N8rc
U/JQlTiuAvENObLjPcodg4ih27ejvo58VKcaRcEekE2XpHWDNsb7UpCBFtKEjFPt
BbXKzlh9fUId35dCeGIVRvlDJKj3pjJFS8du3Cz7zriDS2tTAgC/irAwIGn0u3pm
/siF53UlcmjFtTQSAQJBAPBZs7+FSoDVSEG9ErO17HYIKNNTR5Dt1mXBHMNWcFsm
ua7R4/ctSohsmfve4cDlZSz765xZ53UttSzoLjnLRykCQQDJpvlmqA2w/pcWMsJE
Yf8uARz0j88c2rI+RFTG0nfIgoRRogwMJvjeD98RajoF3XEMrF12wY8bfa5KuBI/
fO1BAkEAj1RO9sVb+pw17M392yGAE5smDW+6W9kZY7DXoD1p31GmpXQRSBPAQL7S
zPrLEac6wKqyhJiwiJZrVo5XEqwAkQJBAKyF5L7FbOFPD+h4COkEhpPPc/xwxRvE
p9bKE1X/X2f28kn9QB1tgmJKZei6X2YBLOVQ2q3tsAgvINzgWwxiT4ECQQCI5c6M
9tQq9rFfe1zfjvds7hNdEPTcOH0eu3wapMRy2IXtNcklRlAht/b1gMidym0WX27M
KFYkaQtm5jQr27ai
-----END PRIVATE KEY-----
"""

# spell-checker: disable
JWKS_CERTS = {
    "keys": [
        {
            "kid": "xkPobP_zKoZL3y_AofSgQ2LE4R1TqOc_dFKnwmgshzY",
            "kty": "RSA",
            "alg": "RSA-OAEP",
            "use": "enc",
            "n": (
                "lCOkgbgVn_wm6TIkoOQ27Ezpj7534la4DJhFA8_8PF8ffxYQ2ARf5B4Vd7xbOE"
                "ymi4_7lvNIHc_9knGLpya9rfgj2NpN5uJRpv-x4BryeDHRDR-ChykM4cYNnW55"
                "Rkqylx216YmOZS3iBvQGmpKxAN9QwGq2ZVoT6dHPN5nS7BxpxhMCxRK4l0x_9N"
                "LJUxgCuxu9JucIXwxBa3P36w5qbov61bqy3dglpHmLyw6kYCH4lNvVgDvbqVtp"
                "T2x5e86hdpsOCyoO9ooYji59d2z1dARaUU1q9tB4Gozkwcc_RfEKA9GrDY2GIt"
                "w_KYqj5I-X6VMNDkvoOotTX05mtVlp8w"
            ),
            "e": "AQAB",
            "x5c": [
                "MIICmzCCAYMCBgGOEr2okDANBgkqhkiG9w0BAQsFADARMQ8wDQYDVQQDDAZtYX"
                "N0ZXIwHhcNMjQwMzA2MDc0ODIzWhcNMzQwMzA2MDc1MDAzWjARMQ8wDQYDVQQD"
                "DAZtYXN0ZXIwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQCUI6SBuB"
                "Wf/CbpMiSg5DbsTOmPvnfiVrgMmEUDz/w8Xx9/FhDYBF/kHhV3vFs4TKaLj/uW"
                "80gdz/2ScYunJr2t+CPY2k3m4lGm/7HgGvJ4MdENH4KHKQzhxg2dbnlGSrKXHb"
                "XpiY5lLeIG9AaakrEA31DAarZlWhPp0c83mdLsHGnGEwLFEriXTH/00slTGAK7"
                "G70m5whfDEFrc/frDmpui/rVurLd2CWkeYvLDqRgIfiU29WAO9upW2lPbHl7zq"
                "F2mw4LKg72ihiOLn13bPV0BFpRTWr20HgajOTBxz9F8QoD0asNjYYi3D8piqPk"
                "j5fpUw0OS+g6i1NfTma1WWnzAgMBAAEwDQYJKoZIhvcNAQELBQADggEBAG/hW6"
                "Bk6AdERD0mtk/XMfE0piD5Ywj/b/VDXi47SkjVNBM8O+/CcGgqQFq2+/YOvn38"
                "qwmbameiOLPclefrFb0u5V7N9e2FnHyT6Wf1nRIUoiHeOqH7kmjSpVTO+VYPPf"
                "N1FXxmcCNHNH/41IdLIik2mqjKVr+5zbpNwKIYtZ2vxcvzbEJCU5nhhqyIL/V3"
                "7hiuRFZsrRmTtL73jfIm64/hH8CPDQp65qFBnhNIo4cuIZ74NN3jM5KrpddDoM"
                "gHEJgEt+6i5RVpkKzLjpd8XAxT3A8ZyZ0tS9IoTSBCf7q/Pt004P6C576sJ07I"
                "0ljKa3UsiJD5SRxjUiy1dBhQOrY="
            ],
            "x5t": "SqaCuidwtIa8SWk_j75GtUfeEVs",
            "x5t#S256": "tm-YoQTnZ__8l6Fka6kEJfAIBN52qnXzeJwh04MkdMI",
        },
        RSA256_KEY,
    ]
}
# spell-checker: enable

# Sane default kwargs for testing `AccessTokenChecker`.
ATC_DEFAULT_KWARGS = {
    "expected_issuer": "http://localhost/realms/test",
    "expected_audience": "some_client_id",
}


@pytest.fixture
def openid_like_test_idp(httpserver):
    realm_url = "/realms/test-atc"
    openid_config_url = f"{realm_url}/.well-known/openid-configuration"

    # Handle the request to OpenID Connect discovery endpoint.
    issuer = httpserver.url_for(realm_url)
    open_id_config = json.loads(
        OPEN_ID_CONFIGURATION_TEMPLATE.replace("$ISSUER", issuer)
    )
    expected_request = httpserver.expect_oneshot_request(
        openid_config_url,
    )
    expected_request.respond_with_json(open_id_config)

    # Handle request to JWKS endpoint.
    jwks_uri = json.loads(OPEN_ID_CONFIGURATION_TEMPLATE)["jwks_uri"]
    jwks_uri = jwks_uri.split("$ISSUER")[-1]
    jwks_uri = f"{realm_url}{jwks_uri}"
    expected_request = httpserver.expect_oneshot_request(
        jwks_uri,
    )
    expected_request.respond_with_json(JWKS_CERTS)

    return httpserver, issuer


class TestAccessTokenCheckerInit:
    """
    Tests for `esg.utils.jwt.AccessTokenChecker.__init__`
    """

    def test_attributes_available(self, openid_like_test_idp):
        """
        Verify that the relevant arguments are stored as attributes.
        """
        issuer = openid_like_test_idp[1]
        atc_kwargs = ATC_DEFAULT_KWARGS | {
            "expected_issuer": issuer,
            "expected_role_claim": ["test"],
            "expected_roles": ["test:ro", "test:rw"],
        }

        # For now just a copy, might become more complex in future.
        expected_attrs_values = atc_kwargs.copy()

        atc = AccessTokenChecker(**atc_kwargs)

        for expected_attr, expected_value in expected_attrs_values.items():
            actual_value = getattr(atc, expected_attr)
            assert actual_value == expected_value

    def test_is_checked_that_issuer_is_URL(self):
        """
        We will use the `expected_issuer` to retrieve the public certificates
        used for JWT checking. Hence `expected_issuer` must be a URL.
        """
        atc_kwargs = ATC_DEFAULT_KWARGS | {"expected_issuer": "not a url"}
        with pytest.raises(ValidationError):
            _ = AccessTokenChecker(**atc_kwargs)

    def test_jwks_client_created(self, openid_like_test_idp):
        """
        This validates that init creates the JWKS client required
        later for retrieving the keys for validating the JWTs.
        """
        issuer = openid_like_test_idp[1]

        atc_kwargs = ATC_DEFAULT_KWARGS | {"expected_issuer": issuer}
        atc = AccessTokenChecker(**atc_kwargs)

        # Check that we can fetch the RSA public key from using the JWKS client.
        atc.jwks_client.get_signing_key(kid=RSA256_KEY["kid"])

    def test_expected_roles_cannot_be_empty(self):
        """
        Verify that `expected_roles` cannot be empty if `expected_role_claim`
        is set.
        """
        atc_kwargs = ATC_DEFAULT_KWARGS | {
            "expected_role_claim": ["resource_access"],
            "expected_roles": [],
        }
        with pytest.raises(ValueError):
            _ = AccessTokenChecker(**atc_kwargs)

    def test_expected_roles_cannot_be_none_if_role_claims_used(self):
        """
        Verify that `expected_roles` cannot be `None` if `expected_role_claim`
        is set.
        """
        atc_kwargs = ATC_DEFAULT_KWARGS | {
            "expected_role_claim": ["resource_access"],
        }
        with pytest.raises(ValueError):
            _ = AccessTokenChecker(**atc_kwargs)


class TestAccessTokenCheckerCheckToken:
    """
    Tests for `esg.utils.jwt.AccessTokenChecker.check_token`
    """

    def _generate_payload(self, issuer):
        """
        Helper function. Generates the expected content of the JWT.
        """
        payload = {
            "iss": issuer,
            "aud": [ATC_DEFAULT_KWARGS["expected_audience"], "some other aud"],
            "iat": datetime.now(tz=timezone.utc) - timedelta(seconds=60),
            "exp": datetime.now(tz=timezone.utc) + timedelta(seconds=60),
            "sub": "18e72351-7d97-4c56-b593-038be8e00d2b",
        }
        return payload

    def test_valid_token_passes(self, openid_like_test_idp):
        """
        Check that a valid JWT is checked as OK, i.e. `check_token` does not
        raise.
        """
        issuer = openid_like_test_idp[1]

        token = jwt.encode(
            self._generate_payload(issuer),
            algorithm="RS256",
            key=RSA256_PRIVATE_KEY,
            headers={"kid": RSA256_KEY["kid"]},
        )

        atc_kwargs = ATC_DEFAULT_KWARGS | {"expected_issuer": issuer}
        atc = AccessTokenChecker(**atc_kwargs)
        _ = atc.check_token(token=token)

    def test_sub_returned(self, openid_like_test_idp):
        """
        Check that the sub value is extracted from the token.
        """
        issuer = openid_like_test_idp[1]
        payload = self._generate_payload(issuer)
        expected_sub_value = payload["sub"]

        token = jwt.encode(
            payload,
            algorithm="RS256",
            key=RSA256_PRIVATE_KEY,
            headers={"kid": RSA256_KEY["kid"]},
        )

        atc_kwargs = ATC_DEFAULT_KWARGS | {"expected_issuer": issuer}
        atc = AccessTokenChecker(**atc_kwargs)
        actual_sub_value, _ = atc.check_token(token=token)

        assert actual_sub_value == expected_sub_value

    def test_token_with_invalid_signature_raises(self, openid_like_test_idp):
        """
        Verify that a access token signed with the wrong key is detected.
        """
        issuer = openid_like_test_idp[1]
        token = jwt.encode(
            self._generate_payload(issuer),
            algorithm="RS256",
            key=INVALID_RSA_PRIVATE_KEY,
            headers={"kid": RSA256_KEY["kid"]},
        )

        atc_kwargs = ATC_DEFAULT_KWARGS | {"expected_issuer": issuer}
        atc = AccessTokenChecker(**atc_kwargs)

        with pytest.raises(jwt.exceptions.InvalidSignatureError):
            atc.check_token(token=token)

    def test_token_reusing_RSA_public_key_raises(self, openid_like_test_idp):
        """
        One hacking trick to fake valid JWT signatures is to sign a JWT with a
        valid kid of and the public key of a RS256 algorithm but with HS256.
        See here for details:
        https://auth0.com/blog/critical-vulnerabilities-in-json-web-token-libraries/
        """
        issuer = openid_like_test_idp[1]
        token = jwt.encode(
            self._generate_payload(issuer),
            algorithm="HS256",
            key=RSA256_KEY["x5c"][0],
            headers={"kid": RSA256_KEY["kid"]},
        )

        atc_kwargs = ATC_DEFAULT_KWARGS | {"expected_issuer": issuer}
        atc = AccessTokenChecker(**atc_kwargs)

        with pytest.raises(Exception):
            # NOTE: This raises no clean exception but some internal of PyJWT
            # seems to fail once requested to load a RSA key with the mechanism
            # for a symmetric key. Beyond that there seems no checking if the
            # KID actually matches the algorithm.
            atc.check_token(token=token)

    def test_missing_claims_raise(self, openid_like_test_idp):
        """
        We require the presence of some claims. Check here that the absence
        of these raises an error.
        """
        issuer = openid_like_test_idp[1]

        atc_kwargs = ATC_DEFAULT_KWARGS | {"expected_issuer": issuer}
        atc = AccessTokenChecker(**atc_kwargs)

        expected_claims = ["iss", "iat", "exp", "aud", "sub"]
        for expected_claim in expected_claims:
            print(f"Checking claim {expected_claim}")

            payload = self._generate_payload(issuer)
            if expected_claim in payload:
                del payload[expected_claim]

            token = jwt.encode(
                payload,
                algorithm="RS256",
                key=RSA256_PRIVATE_KEY,
                headers={"kid": RSA256_KEY["kid"]},
            )

            with pytest.raises(jwt.exceptions.MissingRequiredClaimError):
                atc.check_token(token=token)

    def test_invalid_claim_values_raise(self, openid_like_test_idp):
        """
        Check that incorrect claim values raise an error.
        """
        issuer = openid_like_test_idp[1]

        incorrect_claim_values = {
            "iss": issuer + "/nope",
            "aud": ATC_DEFAULT_KWARGS["expected_audience"] + "-definitely-not",
            "iat": datetime.now(tz=timezone.utc) + timedelta(seconds=60),
            "exp": datetime.now(tz=timezone.utc) - timedelta(seconds=60),
        }

        expected_exceptions = {
            "iss": jwt.exceptions.InvalidIssuerError,
            "aud": jwt.exceptions.InvalidAudienceError,
            # NOTE: As of PyJWT 2.8.0 the docs state that this error should be
            #       be named `InvalidIssuedAtError`. However interacting with
            #       pyjwt indicates this is the actually thrown exception.
            "iat": jwt.exceptions.ImmatureSignatureError,
            "exp": jwt.exceptions.ExpiredSignatureError,
        }

        atc_kwargs = ATC_DEFAULT_KWARGS | {"expected_issuer": issuer}
        atc = AccessTokenChecker(**atc_kwargs)

        for claim, value in incorrect_claim_values.items():
            print(f"Checking claim {claim} with value {value}")

            payload = self._generate_payload(issuer)
            payload[claim] = value

            token = jwt.encode(
                payload,
                algorithm="RS256",
                key=RSA256_PRIVATE_KEY,
                headers={"kid": RSA256_KEY["kid"]},
            )

            with pytest.raises(expected_exceptions[claim]):
                atc.check_token(token=token)

    def test_missing_role_claim_raises(self, openid_like_test_idp):
        """
        The access checker should raise an exception if an `expected_role_claim`
        is not contained in the token.
        """
        issuer = openid_like_test_idp[1]
        payload = self._generate_payload(issuer)

        token = jwt.encode(
            payload,
            algorithm="RS256",
            key=RSA256_PRIVATE_KEY,
            headers={"kid": RSA256_KEY["kid"]},
        )

        atc_kwargs = ATC_DEFAULT_KWARGS | {
            "expected_issuer": issuer,
            "expected_role_claim": [
                "resource_access",
                "keycloak-client",
                "roles",
            ],
            "expected_roles": [
                "demo-service:permission_1",
                "demo-service:permission_2",
                "demo-service:permission_3",
            ],
        }
        atc = AccessTokenChecker(**atc_kwargs)
        with pytest.raises(jwt.exceptions.MissingRequiredClaimError):
            atc.check_token(token=token)

    def test_granted_roles_returned(self, openid_like_test_idp):
        """
        Verify that the roles that are present in the token as well as in
        `expected_roles` are returned.
        """
        issuer = openid_like_test_idp[1]
        payload = self._generate_payload(issuer)
        payload["resource_access"] = {
            "keycloak-client": {
                "roles": [
                    "demo-service:permission_1",
                    "demo-service:permission_2",
                    "demo-service:other_permission",
                ],
            }
        }

        token = jwt.encode(
            payload,
            algorithm="RS256",
            key=RSA256_PRIVATE_KEY,
            headers={"kid": RSA256_KEY["kid"]},
        )

        atc_kwargs = ATC_DEFAULT_KWARGS | {
            "expected_issuer": issuer,
            "expected_role_claim": [
                "resource_access",
                "keycloak-client",
                "roles",
            ],
            "expected_roles": [
                "demo-service:permission_1",
                "demo-service:permission_2",
                "demo-service:permission_3",
            ],
        }

        expected_granted_roles = [
            "demo-service:permission_1",
            "demo-service:permission_2",
        ]

        atc = AccessTokenChecker(**atc_kwargs)
        _, actual_granted_roles = atc.check_token(token=token)

        assert actual_granted_roles == expected_granted_roles

    def test_granted_roles_empty_raises(self, openid_like_test_idp):
        """
        If no roles are granted that is equivalent to no access at all.
        Hence we expect an exception.
        """
        issuer = openid_like_test_idp[1]
        payload = self._generate_payload(issuer)
        payload["resource_access"] = {
            "keycloak-client": {
                "roles": [
                    "demo-service:other_permission",
                ],
            }
        }

        token = jwt.encode(
            payload,
            algorithm="RS256",
            key=RSA256_PRIVATE_KEY,
            headers={"kid": RSA256_KEY["kid"]},
        )

        atc_kwargs = ATC_DEFAULT_KWARGS | {
            "expected_issuer": issuer,
            "expected_role_claim": [
                "resource_access",
                "keycloak-client",
                "roles",
            ],
            "expected_roles": [
                "demo-service:permission_1",
                "demo-service:permission_2",
                "demo-service:permission_3",
            ],
        }

        atc = AccessTokenChecker(**atc_kwargs)
        with pytest.raises(jwt.exceptions.InvalidTokenError):
            atc.check_token(token=token)
