# -*- coding: utf-8 -*-
from plone.restapi.interfaces import IJSONQueryParser
from plone.restapi.interfaces import ISerializeToJson
from Products.CMFCore.utils import getToolByName
from zope.component import getMultiAdapter


class SearchHandler(object):
    """Executes a catalog search based on a JSON query, and returns
    JSON compatible results.
    """
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.catalog = getToolByName(self.context, 'portal_catalog')

    def _parse_json_query(self, json_query):
        query_parser = getMultiAdapter(
            (self.context, self.request), IJSONQueryParser)
        query = query_parser(json_query)
        return query

    def _constrain_query_by_path(self, query):
        # If no 'path' parameter was supplied, restrict search to current
        # context and its children by adding a path constraint
        if 'path' not in query:
            path = '/'.join(self.context.getPhysicalPath())
            query['path'] = path

    def search(self, json_query=None):
        if json_query is None:
            json_query = '{}'

        query = self._parse_json_query(json_query)
        self._constrain_query_by_path(query)

        lazy_resultset = self.catalog.searchResults(query)
        result = ISerializeToJson(lazy_resultset)
        return result
