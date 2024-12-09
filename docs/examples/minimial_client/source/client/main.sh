# Copyright 2024 FZI Research Center for Information Technology
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-FileCopyrightText: 2024 FZI Research Center for Information Technology
# SPDX-License-Identifier: Apache-2.0

SERVICE_BASE_URL=${SERVICE_BASE_URL:-http://localhost:8800}
SERVICE_VERSION="test_version"

# Request a PV power generation forecast from the basic example service.
response=$(
    curl -X 'POST' \
    "${SERVICE_BASE_URL}/${SERVICE_VERSION}/request/" \
    -d '{
        "arguments": {
            "geographic_position": {
                "latitude": 49.01365,
                "longitude": 8.40444
            }
        },
        "parameters": {
            "pv_system": {
                "azimuth_angle": 0,
                "inclination_angle": 30,
                "nominal_power": 15
            }
        }
    }'
)

# Extract the ID of the task from the JSON response.
task_ID=$(echo $response | jq -r .task_ID)

# Poll status endpoint until status is ready.
status="unknown"
while [ $status != "ready" ]
do
    sleep 1
    response=$(
        curl -X 'GET' \
        "${SERVICE_BASE_URL}/${SERVICE_VERSION}/request/${task_ID}/status/"
    )
    status=$(echo $response | jq -r .status_text)
done

# Fetch and print the result.
response=$(
    curl -X 'GET' \
    "${SERVICE_BASE_URL}/${SERVICE_VERSION}/request/${task_ID}/result/"
)
echo $response | jq