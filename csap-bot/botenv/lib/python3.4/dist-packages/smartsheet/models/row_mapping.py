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

class RowMapping(object):

    """Smartsheet RowMapping data model."""

    def __init__(self, props=None, base_obj=None):
        """Initialize the RowMapping model."""
        self._base = None
        if base_obj is not None:
            self._base = base_obj
        self._pre_request_filter = None

        self.__from = None
        self._to = None

        if props:
            # account for alternate variable names from raw API response
            if 'from' in props:
                self._from = props['from']
            if '_from' in props:
                self._from = props['_from']
            if 'to' in props:
                self.to = props['to']
        self.__initialized = True

    def __getattr__(self, key):
        if key == 'from':
            return self._from
        else:
            raise AttributeError(key)

    @property
    def _from(self):
        return self.__from

    @_from.setter
    def _from(self, value):
        if isinstance(value, six.integer_types):
            self.__from = value

    @property
    def to(self):
        return self._to

    @to.setter
    def to(self, value):
        if isinstance(value, six.integer_types):
            self._to = value

    def to_dict(self, op_id=None, method=None):
        obj = {
            'from': prep(self.__from),
            'to': prep(self._to)}
        return obj

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)

    def __str__(self):
        return json.dumps(self.to_dict())
