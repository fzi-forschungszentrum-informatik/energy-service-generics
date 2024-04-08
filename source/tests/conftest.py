"""
Fixtures that are relevant for the execution of (almost) all tests.

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

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

try:
    from prometheus_client import REGISTRY
except ModuleNotFoundError:
    REGISTRY = None

if REGISTRY is not None:

    @pytest.fixture(autouse=True)
    def clean_prom_registry_after_test():
        """
        This seems necessary as the prometheus client will else complain
        about duplicate metrics in the registry.
        """
        yield  # this is where the testing happens

        collectors = list(REGISTRY._collector_to_names.keys())
        for collector in collectors:
            REGISTRY.unregister(collector)


@pytest.fixture(scope="session")
def celery_config():
    """
    Speed up tests by reducing polling interval for workers.
    Still, every tests that invokes a tasks extends runtime by 0.5s.
    Furthermore, make celery use the the filesystem transport for testing.
    Use a temporary directory for this. This allows communication between
    processes, which is is a preliminary for testing the `service` parts.
    """
    tmp_dir = TemporaryDirectory()
    tmp_dir_path = Path(tmp_dir.name)
    broker_path = tmp_dir_path / "broker"
    results_path = tmp_dir_path / "results"
    broker_path.mkdir()
    results_path.mkdir()

    celery_config = {
        "broker_url": "filesystem://",
        "broker_transport_options": {
            "polling_interval": 0.01,
            "data_folder_in": f"{broker_path}/",
            "data_folder_out": f"{broker_path}/",
        },
        "result_backend": f"file://{results_path}/",
    }
    yield celery_config

    tmp_dir.cleanup()


# See the this page for details:
# https://docs.celeryq.dev/en/stable/userguide/testing.html#:~:text=Celery%20app%20instance.-,use_celery_app_trap,-%2D%20Raise%20exception%20on
@pytest.fixture(scope="session")
def use_celery_app_trap():
    return True
