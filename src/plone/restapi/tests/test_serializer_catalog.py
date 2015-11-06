# -*- coding: utf-8 -*-
from DateTime import DateTime
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.utils import createContentInContainer
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.testing import PLONE_RESTAPI_INTEGRATION_TESTING
from Products.CMFCore.utils import getToolByName

import unittest


class TestCatalogSerializers(unittest.TestCase):

    layer = PLONE_RESTAPI_INTEGRATION_TESTING

    def setUp(self):
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.request = self.portal.REQUEST
        self.catalog = getToolByName(self.portal, 'portal_catalog')
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

        # /plone/my-folder
        self.folder = createContentInContainer(
            self.portal, u'Folder',
            title=u'My Folder')

        # /plone/my-folder/my-document
        self.doc = createContentInContainer(
            self.folder, u'Document',
            created=DateTime(2015, 12, 31, 23, 45),
            title=u'My Document')

    def test_lazy_cat_serialization_empty_resultset(self):
        # Force an empty resultset
        lazy_map = self.catalog(path='doesnt-exist')

        results = ISerializeToJson(lazy_map)
        self.assertDictEqual(
            {'member': [], 'items_count': 0},
            results)

    def test_lazy_map_serialization(self):
        lazy_map = self.catalog()
        results = ISerializeToJson(lazy_map)
        self.assertEqual(3, len(results['member']))
        self.assertDictContainsSubset(
            {'items_count': 3},
            results)

    def test_brain_serialization(self):
        path = '/'.join(self.doc.getPhysicalPath())
        brain = self.catalog(path=path)[0]
        self.assertDictContainsSubset(
            {'Creator': u'test_user_1_',
             'Description': u'',
             'EffectiveDate': u'None',
             'ExpirationDate': u'None',
             'Subject': [],
             'Title': u'My Document',
             'Type': u'Page',
             'UID': self.doc.UID(),
             'author_name': None,
             'cmf_uid': 1,
             'commentators': [],
             'created': u'2015-12-31T23:45:00+00:00',
             'effective': u'1969-12-31T00:00:00+00:00',
             'end': None,
             'exclude_from_nav': False,
             'expires': u'2499-12-31T00:00:00+00:00',
             'getIcon': u'',
             'getId': u'my-document',
             'getObjSize': u'0 KB',
             'getPath': u'/plone/my-folder/my-document',
             'getRemoteUrl': None,
             'getURL': u'http://nohost/plone/my-folder/my-document',
             'id': u'my-document',
             'in_response_to': None,
             'is_folderish': False,
             'last_comment_date': None,
             'listCreators': [u'test_user_1_'],
             'location': None,
             'meta_type': u'Dexterity Item',
             'portal_type': u'Document',
             'review_state': u'private',
             'start': None,
             'sync_uid': None,
             'total_comments': 0},
            ISerializeToJson(brain))
