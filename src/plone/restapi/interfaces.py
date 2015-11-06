# -*- coding: utf-8 -*-

# pylint: disable=E0211, W0221
# E0211: Method has no argument
# W0221: Arguments number differs from overridden '__call__' method

from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class IPloneRestapiLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IAPIRequest(Interface):
    """Marker for API requests.
    """


class ISerializeToJson(Interface):
    """Adapter to serialize a Dexterity object into a JSON object.
    """


class IJsonCompatible(Interface):
    """Convert a value to a JSON compatible data structure.
    """


class IFieldSerializer(Interface):
    """The field serializer multi adapter serializes the field value into
    JSON compatible python data.
    """

    def __init__(field, context, request):
        """Adapts field, context and request.
        """

    def __call__():
        """Returns JSON compatible python data.
        """


class IJSONQueryParser(Interface):
    """A multi adapter responsible for converting a catalog query that has
    been serialized to a JSON string back to a Python dictionary that can be
    passed directly to catalog.searchResults().

    Values for query options that can't be serialized in JSON directly
    (like datetimes) must be converted back by this adapter (usually by
    delegatig that job to a IQueryOptionsParser).
    """

    def __init__(context, request):
        """Adapts context and request.
        """

    def __call__(json_query):
        """Returns a ZCatalog compatible query (Python dictionary).
        """


class IQueryOptionsParser(Interface):
    """A multi adapter responsible for deserializing values in catalog query
    options for a particular index type.

    When serializing a catalog query to JSON, some of the values in query
    options (like date range queries) can't be serialized directly in JSON, so
    they are represented as strings. This adapter needs to know what data type
    the adapted index expects, and deserialize those values back to the proper
    data type.
    """

    def __init__(index, context, request):
        """Adapts a catalog index, context and request.
        """

    def __call__(query_opts):
        """Takes catalog query options (the value part of a query against a
        particular index). Those can be
          - a single string value
          - a list of string values
          - a dictionary with multiple query options, among them the actual
            "query"

        Returns query options (of the same type) with all values deserialized
        to the data types that the respective index expects.
        """
