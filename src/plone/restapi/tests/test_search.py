# -*- coding: utf-8 -*-
from DateTime import DateTime
from plone.app.contenttypes.behaviors.richtext import IRichText
from plone.app.testing import setRoles
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.dexterity.utils import createContentInContainer
from plone.restapi.search.handler import SearchHandler
from plone.restapi.testing import PLONE_RESTAPI_FUNCTIONAL_TESTING
from plone.restapi.testing import PLONE_RESTAPI_INTEGRATION_TESTING
from plone.restapi.testing import RelativeSession
from Products.CMFCore.utils import getToolByName

import json
import transaction
import unittest


class TestSearchFunctional(unittest.TestCase):

    layer = PLONE_RESTAPI_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.portal_url = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

        self.api_session = RelativeSession(self.portal_url)
        self.api_session.headers.update({'Accept': 'application/json'})
        self.api_session.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

        # /plone/my-folder
        self.folder = createContentInContainer(
            self.portal, u'Folder',
            title=u'My Folder')

        # /plone/my-folder/my-document
        self.doc = createContentInContainer(
            self.folder, u'Document',
            title=u'My Document')

        # /plone/my-folder/some-document
        createContentInContainer(
            self.folder, u'Document',
            title=u'Some document',
            text=IRichText['text'].fromUnicode(u'<p>Lorem Ipsum</p>'))

        transaction.commit()

    def test_complex_query_get(self):
        query = {
            'SearchableText': 'lorem',
            'path': {
                'query': '/'.join(self.folder.getPhysicalPath()),
            }
        }
        response = self.api_session.get(
            '/search', params={'q': json.dumps(query)})

        self.assertEqual(1, response.json()['items_count'])
        self.assertEqual(1, len(response.json()['member']))

        self.assertEqual(
            u'Some document',
            response.json()['member'][0]['Title']
        )

    def test_complex_query_post(self):
        query = {
            'SearchableText': 'lorem',
            'path': {
                'query': '/'.join(self.folder.getPhysicalPath()),
            }
        }
        response = self.api_session.post('/search', json=query)

        self.assertEqual(1, response.json()['items_count'])
        self.assertEqual(1, len(response.json()['member']))

        self.assertEqual(
            u'Some document',
            response.json()['member'][0]['Title']
        )

    def test_overall_response_format(self):
        # GET
        response = self.api_session.get('/search')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get('Content-Type'),
            'application/json',
        )

        results = response.json()
        self.assertEqual(
            results[u'items_count'],
            len(results[u'member']),
            'items_count property should match actual item count.'
        )

        # POST
        response = self.api_session.post('/search')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get('Content-Type'),
            'application/json',
        )

        results = response.json()
        self.assertEqual(
            results[u'items_count'],
            len(results[u'member']),
            'items_count property should match actual item count.'
        )


class TestSearchIntegration(unittest.TestCase):

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

    def test_fulltext_search(self):
        self.doc.text = IRichText['text'].fromUnicode(u'<p>Lorem Ipsum</p>')
        self.doc.reindexObject()

        json_query = json.dumps({'SearchableText': 'lorem'})
        results = SearchHandler(self.portal, self.request).search(json_query)

        self.assertEqual(1, results['items_count'])
        self.assertEqual(1, len(results['member']))

        self.assertEqual(
            u'My Document',
            results['member'][0]['Title']
        )
