"""
Tools that help documenting services.

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


def get_api_docs_from_description_file(description_path):
    """
    Extract API `title` and `description` from markdown file.

    This makes writing docs nicer, no more markdown in python docstrings!
    See also the fastapit docs about the fields:
    https://fastapi.tiangolo.com/tutorial/metadata/

    TODO: Add a test for this method.

    Arguments:
    ----------
    description_path: pathlib.Path
        The path of the markdown file to open.

    Returns:
    --------
    title: str
        The title of the API (for the API docs etc.). Method assumes
        that the title is in the first line of the description file.
    description: str
        The description of the API for the docs. It is assumed that
        these are all lines apart from the first.
    """
    with description_path.open("r") as description_file:
        lines = description_file.readlines()
    # Remove the header signs, the title is always formated as headline.
    title = lines[0].replace("#", "")
    if len(lines) > 1:
        description = "\n".join(lines[1:])
    else:
        description = ""

    return title, description
