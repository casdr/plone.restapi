# -*- coding: utf-8 -*-
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.serializer.converters import json_compatible
from Products.CMFCore.utils import getToolByName
from Products.ZCatalog.interfaces import ICatalogBrain
from Products.ZCatalog.Lazy import Lazy
from zope.component import adapter
from zope.component.hooks import getSite
from zope.interface import implementer


@implementer(ISerializeToJson)
@adapter(ICatalogBrain)
def BrainSerializer(brain):
    """Serializes a brain to a Python data structure that can in turn be
    serialized to JSON.
    """
    site = getSite()
    catalog = getToolByName(site, 'portal_catalog')
    metadata_attrs = catalog.schema()

    result = {}
    for attr in metadata_attrs:
        value = getattr(brain, attr, None)
        value = json_compatible(value)

        # TODO: Deal with metadata attributes that already contain
        # timestamps as isoformat strings, like 'Created'
        result[attr] = value

    # Handle values that are provided via methods on brains, like getPath
    # (See ICatalogBrain for details)
    for name in ['getPath', 'getURL']:
        meth = getattr(brain, name)
        result[name] = meth()

    return result


@implementer(ISerializeToJson)
@adapter(Lazy)
def LazyCatalogResultSerializer(lazy_resultset):
    """Serializes a ZCatalog resultset (one of the subclasses of `Lazy`) to
    a Python data structure that can in turn be serialized to JSON.
    """
    results = {}
    results['items_count'] = lazy_resultset.actual_result_count
    results['member'] = []

    for brain in lazy_resultset:
        data = ISerializeToJson(brain)
        results['member'].append(data)
    return results
