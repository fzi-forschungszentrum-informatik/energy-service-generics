"""
Forecasting or optimization code of the service.

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

import numpy as np


def handle_request(input_data):
    """
    Compute the linear function values at points `x`.
    """
    x = np.asarray(input_data.arguments.x)
    w = np.asarray(input_data.parameters.w)
    f = np.dot(x, w)
    return {"f": f.tolist()}


def fit_parameters(input_data):
    """
    Fit the weight parameter of the linear model.
    """
    x = np.expand_dims(input_data.arguments.x, -1)
    y = np.expand_dims(input_data.observations.y, -1)

    # Approach is inspired by this article: https://earnold.me/post/bayesianlr/
    w = np.dot(np.dot(np.linalg.inv(np.dot(x.T, x)), x.T), y)
    return {"w": w[0, 0]}
