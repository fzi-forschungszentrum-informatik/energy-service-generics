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

import os

# GOTCHA: This is super important here! The tests will not be able to import
# from `worker` (or `api` as the latter imports `worker`) as this issues a
# call to `celery_app_from_environ` which needs these settings to run.
os.environ["CELERY__NAME"] = "test_name"
os.environ["CELERY__BROKER_URL"] = "filesystem://"
os.environ["CELERY__FS_TRANSPORT_BASE_FOLDER"] = "/tmp/"

# Service needs a version for running the API tests too.
os.environ["VERSION"] = "latest-testing"
