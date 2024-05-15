"""
Collection of tools that aid the interaction with JWTs for authorization
and authentication.

Some relevant external docs:
https://pyjwt.readthedocs.io/en/latest/usage.html
https://openid.net/specs/openid-connect-core-1_0.html#CodeFlowTokenValidation
https://auth0.com/docs/secure/tokens/access-tokens/validate-access-tokens
https://auth0.com/blog/why-should-use-accesstokens-to-secure-an-api/

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

import jwt
from pydantic import HttpUrl

import requests


class AccessTokenChecker:
    """
    A tool that can be used to verify access tokens in JWT format.

    This class is intended to operate with JWT based access tokens as they
    are issued by IDPs implementing OpenID Connect. It is in particular
    implemented to operate on JWTs issued by Keycloak. Other IDPs may work
    too or not at all.

    Beyond the usually checking of JWT attributes this class furthermore
    allows to verify if certain `roles` have been assigned to the user.
    This role checking enables fine grained authorization like e.g.
    dedicated permissions for each endpoint of an API.
    """

    def __init__(
        self,
        expected_issuer,
        expected_audience,
        expected_role_claim=None,
        expected_roles=None,
    ):
        """
        Arguments:
        ----------
        expected_issuer : str
            The value expected in the `iss` field of the access token.
            Is additionally used to retrieve the public certificates
            for cryptographic checking from the .well-known endpoint.
        expected_audience : str
            The value expected in the `aud` field of the access token.
        expected_role_claim: list of str
            Definition where the roles should be found in the JWT.
            E.g. `["client", "roles"]` will look for a structure like
            `"client": {"roles": ["role_1", "role_2"]}` in the JWT.
        expected_roles : list of str
            Which roles are expected in the part of the JWT defined
            by `expected_role_claim`. At least one of these roles
            must be present in the token.
        """
        # Check that `expected_issuer´ is  URL, it used later as such.
        _ = HttpUrl(expected_issuer)

        # Verify that `expected_roles` cannot be None or empty if
        # `expected_role_claim` is set, as this would cause nasty
        # downstream errors in `self.check_token`.
        if expected_role_claim is not None:
            if expected_roles is None:
                raise ValueError(
                    "`expected_roles` cannot be `None` if `expected_role_claim`"
                    " is used."
                )
            elif len(expected_roles) < 1:
                raise ValueError(
                    "`expected_roles` cannot be empty if `expected_role_claim` "
                    "is used."
                )

        self.expected_issuer = expected_issuer
        self.expected_audience = expected_audience
        self.expected_role_claim = expected_role_claim
        self.expected_roles = expected_roles

        # Fetch the relevant information used later for validating JWTs.
        # First fetch the allowed signing algorithms and the endpoint for the
        # public keys from the OpenID Connect Discovery endpoint. See also:
        # https://openid.net/specs/openid-connect-discovery-1_0.html
        response = requests.get(self.get_well_known_url())
        response.raise_for_status()
        oidc_config = response.json()
        self.allowed_signing_algorithms = oidc_config[
            "id_token_signing_alg_values_supported"
        ]
        self.jwks_client = jwt.PyJWKClient(oidc_config["jwks_uri"])

    def get_well_known_url(self):
        """
        Return the URL of OIDC configuration.

        NOTE: This well known path is standardized, see:
        https://openid.net/specs/openid-connect-discovery-1_0.html#ProviderConfig

        Returns:
        --------
        well_known_url : str
            The URL under which the OIDC configuration is expected.
        """
        well_known_url = (
            f"{self.expected_issuer}/.well-known/openid-configuration"
        )
        return well_known_url

    def check_token(self, token):
        """
        Checks the token is valid.

        This checks:
        * That `iss` claim exists and is equal to `self.expected_issuer`.
        * That `aud` claim exists and contains `self.expected_audience`.
        * That `exp` claim exists and value is not expired.
        * That `iat` claim exists and value is not in the future.
        * That `sub` claim exists.

        Arguments:
        ----------
        token : str
            The encoded JWT token that should be checked.

        Returns:
        --------
        sub : str
            The value of the `sub` claim of the token. For Keycloak that is
            the ID of the user which looks like this:
            `"18e72351-7d97-4c56-b593-038be8e00d2b"`
        granted_roles : list of str
            The subset of `expected_roles` that is present in the
            token.

        Raises:
        -------
        jwt.exceptions.InvalidTokenError:
            Or children of this exception if the token is not valid
            nor not all expected claims are contained.
        """
        signing_key = self.jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            key=signing_key.key,
            algorithms=self.allowed_signing_algorithms,
            options={"require": ["iss", "iat", "exp", "aud", "sub"]},
            issuer=self.expected_issuer,
            audience=self.expected_audience,
        )

        if self.expected_role_claim is None:
            # Quick exit if roles should not be checked.
            return payload["sub"], []

        try:
            part_of_payload = payload
            for role_claim_part in self.expected_role_claim:
                part_of_payload = part_of_payload[role_claim_part]
            roles_in_token = part_of_payload
        # TypeError for cases if a token contains a string that should be
        # a dict.
        except (KeyError, TypeError):
            raise jwt.exceptions.MissingRequiredClaimError(
                "Could not find `expected_role_claim` "
                f"({self.expected_role_claim}) in token."
            )

        granted_roles = []
        for role in roles_in_token:
            if role in self.expected_roles:
                granted_roles.append(role)

        if len(granted_roles) < 1:
            raise jwt.exceptions.InvalidTokenError(
                "Token did not contain any roles of `expected_roles`."
            )

        return payload["sub"], granted_roles
