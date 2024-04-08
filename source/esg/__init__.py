"""
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

from dotenv import load_dotenv, find_dotenv

# This import is all we need to make `esg.__version__` possible.
from esg._version import __version__  # NOQA


# dotenv allows us to load env variables from .env files which is
# convenient for developing. If you set `override`` to True tests
# may fail as the tests assume that the existing environ variables
# have higher priority over ones defined in the .env file.
load_dotenv(find_dotenv(), verbose=True, override=False)
