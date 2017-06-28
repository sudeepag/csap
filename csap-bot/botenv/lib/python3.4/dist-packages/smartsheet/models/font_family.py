# pylint: disable=C0111,R0902,R0904,R0912,R0913,R0915,E1101
# Smartsheet Python SDK.
#
# Copyright 2016 Smartsheet.com, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"): you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from __future__ import absolute_import

from ..types import TypedList
from ..util import prep
from datetime import datetime
import json
import logging
import six

class FontFamily(object):

    """Smartsheet FontFamily data model."""

    def __init__(self, props=None, base_obj=None):
        """Initialize the FontFamily model."""
        self._base = None
        if base_obj is not None:
            self._base = base_obj
        self._pre_request_filter = None

        self._name = None
        self._traits = TypedList(str)

        if props:
            if 'name' in props:
                self.name = props['name']
            if 'traits' in props:
                self.traits = props['traits']

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if isinstance(value, six.string_types):
            self._name = value

    @property
    def traits(self):
        return self._traits

    @traits.setter
    def traits(self, value):
        if isinstance(value, list):
            self._traits.purge()
            self._traits.extend([
                (str(x)
                 if not isinstance(x, str) else x) for x in value
            ])
        elif isinstance(value, TypedList):
            self._traits.purge()
            self._traits = value.to_list()
        elif isinstance(value, str):
            self._traits.purge()
            self._traits.append(value)

    def to_dict(self, op_id=None, method=None):
        obj = {
            'name': prep(self._name),
            'traits': prep(self._traits)}
        return obj

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)

    def __str__(self):
        return json.dumps(self.to_dict())
