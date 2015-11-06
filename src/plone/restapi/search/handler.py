# -*- coding: utf-8 -*-
from plone.restapi.interfaces import ISerializeToJson
from Products.CMFCore.utils import getToolByName

import json


class SearchHandler(object):
    """Executes a catalog search based on a JSON query, and returns
    JSON compatible results.
    """
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.catalog = getToolByName(self.context, 'portal_catalog')

    def search(self, json_query=None):
        if json_query is None:
            json_query = '{}'

        query = json.loads(json_query)

        lazy_resultset = self.catalog.searchResults(query)
        result = ISerializeToJson(lazy_resultset)
        return result
