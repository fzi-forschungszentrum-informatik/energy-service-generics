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

from setuptools import setup, find_packages
from distutils.util import convert_path

# Fetch version from file as suggested here:
# https://stackoverflow.com/a/24517154
main_ns = {}
ver_path = convert_path("esg/_version.py")
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)

setup(
    name="Energy Service Generics",
    version=main_ns["__version__"],
    author="David Wölfle",
    author_email="woelfle@fzi.de",
    url="https://github.com/fzi-forschungszentrum-informatik/energy-service-generics",  # NOQA
    packages=find_packages(),
    install_requires=[
        "pydantic==2.*",  # V2 of pydantic has major API differences to V1.
        "fastapi==0.*",  # We use the jsonable function from here.
        "python-dotenv",
        "pyjwt[crypto]",
        "requests",
        "pytest",
        "pytest-httpserver",
    ],
    extras_require={
        "service": [
            "uvicorn==0.*",
            "celery[pytest]",
            "prometheus-fastapi-instrumentator==6.*",
        ],
        "pandas": [
            "numpy",
            "pandas==2.*",
        ],
    },
)
