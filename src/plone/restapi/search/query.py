# -*- coding: utf-8 -*-
from DateTime import DateTime
from plone.restapi.interfaces import IQueryOptionsParser
from Products.CMFCore.utils import getToolByName
from zope.component import queryMultiAdapter
import json


class DateIndexQueryOptionsParser(object):
    """Parses query options for queries against date related indexes
    (DateIndex, DateRangeIndex, DateRecurringIndex).
    """

    def __init__(self, index=None, context=None, request=None):
        self.index = index
        self.context = context
        self.request = request

    def __call__(self, query_opts):
        """query_opts can be either a dict (with just the options), a list or
        a string. Any dates or datetimes occurring as ISO formatted strings in
        those query options will be deserialized back to Zope DateTimes.
        """
        if isinstance(query_opts, dict):
            return self._parse_dict(query_opts)
        elif isinstance(query_opts, list):
            return self._parse_list(query_opts)
        elif isinstance(query_opts, basestring):
            return self._parse_str(query_opts)
        else:
            raise TypeError(
                "Unexpected type for query options: %r" % query_opts)

    def _parse_dict(self, query_opts):
        parsed_query_opts = {}
        for key, value in query_opts.items():
            if key == 'query':
                if isinstance(value, list):
                    value = self._parse_list(value)
                else:
                    value = self._parse_str(value)
            parsed_query_opts[key] = value
        return parsed_query_opts

    def _parse_list(self, query_opts):
        return [self._parse_str(value) for value in query_opts]

    def _parse_str(self, query_opts):
        return DateTime(query_opts)


class JSONQueryParser(object):
    """Converts a catalog query that has been serialized to JSON back to a
    Python dictionary suitable for passing to catalog.searchResults().
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.catalog = getToolByName(self.context, 'portal_catalog')

    def get_index(self, name):
        return self.catalog._catalog.indexes.get(name)

    def __call__(self, json_query):
        query = {}

        # First deserialize the JSON to Python
        query = json.loads(json_query)

        for idx_name, query_opts in query.items():
            # Then check for each index present in the query if there is a
            # IQueryOptionsParser that knows how to deserialize any values
            # that could not be serialized in JSON directly
            index = self.get_index(idx_name)
            query_opts_parser = queryMultiAdapter(
                (index, self.context, self.request), IQueryOptionsParser)

            if query_opts_parser is not None:
                query_opts = query_opts_parser(query_opts)

            query[idx_name] = query_opts
        return query
