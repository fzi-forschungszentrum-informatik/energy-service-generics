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

import jwt
from pydantic import ValidationError
import pytest

from esg.utils.jwt import AccessTokenChecker
from esg.test.jwt_utils import RSA256_KEY
from esg.test.jwt_utils import RSA256_PRIVATE_KEY
from esg.test.jwt_utils import INVALID_RSA_PRIVATE_KEY

# Sane default kwargs for testing `AccessTokenChecker`.
ATC_DEFAULT_KWARGS = {
    "expected_issuer": "http://localhost/realms/test",
    "expected_audience": "some_client_id",
}


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


class TestAccessTokenCheckerGetWellKnownURL:
    """
    Tests for `esg.utils.jwt.AccessTokenChecker.get_well_known_url`
    """

    def test_expected_url_returned(self, openid_like_test_idp):
        """
        Simplest case, check that the expected URL is returned.
        """
        issuer = openid_like_test_idp[1]
        atc_kwargs = ATC_DEFAULT_KWARGS | {"expected_issuer": issuer}
        atc = AccessTokenChecker(**atc_kwargs)

        expected_url = f"{issuer}/.well-known/openid-configuration"
        actual_url = atc.get_well_known_url()

        assert actual_url == expected_url


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
