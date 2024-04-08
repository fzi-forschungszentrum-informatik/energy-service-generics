#!/bin/bash
#
# A simple wrapper that automatically runs pytest on every file change.
# All input arguments are forwarded to pytest.
#
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
#

PYTEST_ARGS="$@"
pytest $PYTEST_ARGS
while true; do 
  # r : recursive
  # q : quiet
  # --include '.*\.py$' : watch only for Python files.
  # -e modify : Catches usual saves, e.g. from VSCode
  # -e close : Catches save events from editors that replace files with move.
  #            This is e.g. done by gedit. 
  # /source/ : Watch for all changes in the /source/ directory. In theory
  #            we could watch in the relevant subdirectory only, but parsing
  #            this information from pytest args seems not worth the effort.
  # NOTE: This does not use the -m flag, because this would trigger at every
  #       save event, even if the last test run hasn't finished yet. 
  inotifywait -rq --include '.*\.py$' -e modify -e move /source/ && \
  pytest $PYTEST_ARGS
done
