# Copyright 2024 FZI Research Center for Information Technology
#
# Licensed under the Apache License, Version 2.0 (the "License")#
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

# Base image for tag x.y.z
FROM python:3.11 as esg-base

# Install the auto-pytest tool incl. dependencies.
RUN apt-get update && \
    apt-get install -y inotify-tools && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
COPY auto-pytest.sh /usr/bin/auto-pytest
RUN chmod a+rx /usr/bin/auto-pytest

# Create the /source/ dir with write permission for all the source code
# that should be run by derived containers
RUN mkdir -p /source/ && \
    chmod a+rwx /source/

WORKDIR /source/

# Install the package install it.
RUN mkdir -p /source/energy_service_generics/
COPY esg /source/energy_service_generics/esg
COPY tests /source/energy_service_generics/tests
COPY setup.py pytest.ini /source/energy_service_generics/
RUN pip install /source/energy_service_generics

# Place the dummy forecasting or optimization component. 
COPY esg/service/dummy_fooc.py /source/service/fooc.py


# Extended image for tag x.y.z-service
# Contains the additional dependencies to run a service.
FROM esg-base as esg-service

RUN pip install /source/energy_service_generics[service]



# Extended image for tag x.y.z-pandas
# Contains pandas -> allows the usage of esg.utils.pandas
FROM esg-base as esg-pandas

RUN pip install /source/energy_service_generics[pandas]


# Extended image for tag x.y.z-service-pandas
# Contains pandas, allows the usage of esg.utils.pandas
# This starts from the pandas stage as installing pandas will likely
# take longer then the dependencies of the service.
FROM esg-pandas as esg-service-pandas

RUN pip install /source/energy_service_generics[service,pandas]
