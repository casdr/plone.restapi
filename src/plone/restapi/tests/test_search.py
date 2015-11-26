# -*- coding: utf-8 -*-
from datetime import date
from DateTime import DateTime
from datetime import datetime
from plone.app.contenttypes.behaviors.richtext import IRichText
from plone.app.testing import setRoles
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.dexterity.utils import createContentInContainer
from plone.restapi.search.query import DateIndexQueryOptionsParser
from plone.restapi.search.handler import SearchHandler
from plone.restapi.testing import PLONE_RESTAPI_FUNCTIONAL_TESTING
from plone.restapi.testing import PLONE_RESTAPI_INTEGRATION_TESTING
from plone.restapi.testing import RelativeSession
from Products.CMFCore.utils import getToolByName
from pytz import timezone

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
            created=DateTime(2015, 12, 31, 23, 45),
            title=u'My Document')

        # /plone/my-folder/really-old-document
        createContentInContainer(
            self.folder, u'Document',
            created=DateTime(1950, 1, 1, 14, 45),
            title=u'Really old Document',
            text=IRichText['text'].fromUnicode(u'<p>Lorem Ipsum</p>'))

        createContentInContainer(
            self.portal, u'Document',
            created=DateTime(1950, 1, 1, 14, 45),
            title=u'Old Document outside search context',
            text=IRichText['text'].fromUnicode(u'<p>Lorem Ipsum</p>'))

        transaction.commit()

    def test_complex_query_get(self):
        query = {
            'SearchableText': 'lorem',
            'created': {
                'query': [date(1949, 1, 1).isoformat(),
                          date(1951, 1, 1).isoformat()],
                'range': 'min:max'},
            'path': {
                'query': '/'.join(self.folder.getPhysicalPath()),
            }
        }
        response = self.api_session.get(
            '/search', params={'q': json.dumps(query)})

        self.assertEqual(1, response.json()['items_count'])
        self.assertEqual(1, len(response.json()['member']))

        self.assertEqual(
            u'Really old Document',
            response.json()['member'][0]['Title']
        )

    def test_complex_query_post(self):
        query = {
            'SearchableText': 'lorem',
            'created': {
                'query': [date(1949, 1, 1).isoformat(),
                          date(1951, 1, 1).isoformat()],
                'range': 'min:max'},
            'path': {
                'query': '/'.join(self.folder.getPhysicalPath()),
            }
        }
        response = self.api_session.post('/search', json=query)

        self.assertEqual(1, response.json()['items_count'])
        self.assertEqual(1, len(response.json()['member']))

        self.assertEqual(
            u'Really old Document',
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

    def test_date_range_query(self):
        createContentInContainer(
            self.folder, u'Document',
            created=DateTime(1950, 1, 1, 14, 45),
            title=u'Really old Document')

        createContentInContainer(
            self.folder, u'Document',
            created=DateTime(2015, 1, 1, 14, 45),
            title=u'Doc outside date range',
            text=IRichText['text'].fromUnicode(u'<p>Lorem Ipsum</p>'))

        createContentInContainer(
            self.portal, u'Document',
            created=DateTime(1950, 1, 1, 14, 45),
            title=u'Old Document outside search context')

        json_query = json.dumps({
            'created': {
                'query': [date(1949, 1, 1).isoformat(),
                          date(1951, 1, 1).isoformat()],
                'range': 'min:max'},
            'path': {
                'query': '/'.join(self.folder.getPhysicalPath()),
            }
        })

        results = SearchHandler(self.portal, self.request).search(json_query)

        self.assertEqual(1, results['items_count'])
        self.assertEqual(1, len(results['member']))

        self.assertEqual(
            u'Really old Document',
            results['member'][0]['Title']
        )


class TestDateIndexQueryOptionsParser(unittest.TestCase):

    def test_nested_options(self):
        query = {
            'query': [date(1949, 12, 27).isoformat(),
                      date(1951, 12, 27).isoformat()],
            'range': 'min:max'
        }
        self.assertEqual(
            {u'query': [DateTime('1949/12/27 00:00:00 GMT+0'),
                        DateTime('1951/12/27 00:00:00 GMT+0')],
             u'range': u'min:max'},
            DateIndexQueryOptionsParser()(query)
        )

    def test_py_date(self):
        query = date(2015, 12, 27).isoformat()
        self.assertEqual(
            DateTime('2015/12/27 00:00:00 GMT+0'),
            DateIndexQueryOptionsParser()(query)
        )

    def test_py_datetime_naive(self):
        query = datetime(2015, 12, 27, 16, 45).isoformat()
        self.assertEqual(
            DateTime('2015/12/27 16:45:00 GMT+0'),
            DateIndexQueryOptionsParser()(query)
        )

    def test_zope_datetime_naive(self):
        query = DateTime(2015, 12, 27).ISO8601()
        self.assertEqual(
            DateTime('2015/12/27 00:00:00 GMT+0'),
            DateIndexQueryOptionsParser()(query)
        )

    def test_py_datetime_tz(self):
        tz = timezone('Europe/Zurich')

        # Winter
        query = tz.localize(datetime(2015, 12, 27, 16, 45)).isoformat()
        self.assertEqual(
            DateTime('2015/12/27 16:45:00 GMT+1'),
            DateIndexQueryOptionsParser()(query)
        )

        # Summer (DST)
        query = tz.localize(datetime(2015, 06, 27, 16, 45)).isoformat()
        self.assertEqual(
            DateTime('2015/06/27 16:45:00 GMT+2'),
            DateIndexQueryOptionsParser()(query)
        )

    def test_zope_datetime_tz(self):
        # Winter
        query = DateTime('2015/12/27 16:45:00 Europe/Zurich').ISO8601()
        self.assertEqual(
            DateTime('2015/12/27 16:45:00 GMT+1'),
            DateIndexQueryOptionsParser()(query)
        )

        # Summer (DST)
        query = DateTime('2015/06/27 16:45:00 Europe/Zurich').ISO8601()
        self.assertEqual(
            DateTime('2015/06/27 16:45:00 GMT+2'),
            DateIndexQueryOptionsParser()(query)
        )
