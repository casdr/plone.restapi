# -*- coding: utf-8 -*-
from datetime import datetime
from plone.app.testing import setRoles
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.app.textfield.value import RichTextValue
from plone.namedfile.file import NamedBlobFile
from plone.namedfile.file import NamedBlobImage
from plone.restapi.testing import PLONE_RESTAPI_FUNCTIONAL_TESTING
from plone.restapi.testing import RelativeSession
from plone.testing.z2 import Browser
from z3c.relationfield import RelationValue
from zope.component import getUtility
from zope.intid.interfaces import IIntIds

import json
import os
import unittest2 as unittest

REQUEST_HEADER_KEYS = [
    'accept'
]

RESPONSE_HEADER_KEYS = [
    'content-type',
    'allow',
]

ELLIPSIS_FIELDS = [
    'CreationDate',
    'Date',
    'ModificationDate',
    'UID',
    'created',
    'modified',
]

base_path = os.path.join(
    os.path.dirname(__file__),
    '..',
    '..',
    '..',
    '..',
    'docs/source/_json'
)


def ellipsify(obj, ellipsis_for):
    """Recursively substitute the values for any keys listed in `ellipsis_for`
    with an ellipsis (...).

    This is so we can keep a stable output for response types that include
    fields that change with every run, like modification dates.
    """
    if isinstance(obj, dict):
        new_dict = {}
        for key, value in sorted(obj.items()):
            if key in ellipsis_for:
                new_dict[key] = '<...>'
                continue
            if isinstance(value, (list, dict)):
                new_dict[key] = ellipsify(value, ellipsis_for)
            else:
                new_dict[key] = value
        return new_dict

    elif isinstance(obj, list):
        return [ellipsify(elem, ellipsis_for) for elem in obj]
    else:
        return obj


def save_response_for_documentation(filename, response, ellipsis_for=None):
    if ellipsis_for is None:
        ellipsis_for = ELLIPSIS_FIELDS

    f = open('{}/{}'.format(base_path, filename), 'w')
    f.write('{} {}\n'.format(
        response.request.method,
        response.request.path_url
    ))
    for key, value in response.request.headers.items():
        if key.lower() in REQUEST_HEADER_KEYS:
            f.write('{}: {}\n'.format(key, value))
    f.write('\n')
    f.write('HTTP {} {}\n'.format(response.status_code, response.reason))
    for key, value in response.headers.items():
        if key.lower() in RESPONSE_HEADER_KEYS:
            f.write('{}: {}\n'.format(key.lower(), value))
    f.write('\n')

    content = json.loads(response.content)
    content = ellipsify(content, ellipsis_for)

    f.write(json.dumps(content, indent=2, sort_keys=True))
    f.close()


class TestTraversal(unittest.TestCase):

    layer = PLONE_RESTAPI_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer['app']
        self.request = self.layer['request']
        self.portal = self.layer['portal']
        self.portal_url = self.portal.absolute_url()

        self.api_session = RelativeSession(self.portal_url)
        self.api_session.headers.update({'Accept': 'application/json'})
        self.api_session.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.portal.invokeFactory('Document', id='front-page')
        self.document = self.portal['front-page']
        self.document.title = u"Welcome to Plone"
        self.document.description = \
            u"Congratulations! You have successfully installed Plone."
        self.document.text = RichTextValue(
            u"If you're seeing this instead of the web site you were " +
            u"expecting, the owner of this web site has just installed " +
            u"Plone. Do not contact the Plone Team or the Plone mailing " +
            u"lists about this.",
            'text/plain',
            'text/html'
        )
        import transaction
        transaction.commit()
        self.browser = Browser(self.app)
        self.browser.handleErrors = False
        self.browser.addHeader(
            'Authorization',
            'Basic %s:%s' % (SITE_OWNER_NAME, SITE_OWNER_PASSWORD,)
        )

    def test_documentation_document(self):
        response = self.api_session.get(self.document.absolute_url())
        save_response_for_documentation('document.json', response)

    def test_documentation_news_item(self):
        self.portal.invokeFactory('News Item', id='newsitem')
        self.portal.newsitem.title = 'My News Item'
        self.portal.newsitem.description = u'This is a news item'
        self.portal.newsitem.text = RichTextValue(
            u"Lorem ipsum",
            'text/plain',
            'text/html'
        )
        image_file = os.path.join(os.path.dirname(__file__), u'image.png')
        self.portal.newsitem.image = NamedBlobImage(
            data=open(image_file, 'r').read(),
            contentType='image/png',
            filename=u'image.png'
        )
        self.portal.newsitem.image_caption = u'This is an image caption.'
        import transaction
        transaction.commit()
        response = self.api_session.get(self.portal.newsitem.absolute_url())
        save_response_for_documentation('newsitem.json', response)

    def test_documentation_event(self):
        self.portal.invokeFactory('Event', id='event')
        self.portal.event.title = 'Event'
        self.portal.event.description = u'This is an event'
        self.portal.event.start = datetime(2013, 1, 1, 10, 0)
        self.portal.event.end = datetime(2013, 1, 1, 12, 0)
        import transaction
        transaction.commit()
        response = self.api_session.get(self.portal.event.absolute_url())
        save_response_for_documentation('event.json', response)

    def test_documentation_link(self):
        self.portal.invokeFactory('Link', id='link')
        self.portal.link.title = 'My Link'
        self.portal.link.description = u'This is a link'
        self.portal.remoteUrl = 'http://plone.org'
        import transaction
        transaction.commit()
        response = self.api_session.get(self.portal.link.absolute_url())
        save_response_for_documentation('link.json', response)

    def test_documentation_file(self):
        self.portal.invokeFactory('File', id='file')
        self.portal.file.title = 'My File'
        self.portal.file.description = u'This is a file'
        pdf_file = os.path.join(
            os.path.dirname(__file__), u'file.pdf'
        )
        self.portal.file.file = NamedBlobFile(
            data=open(pdf_file, 'r').read(),
            contentType='application/pdf',
            filename=u'file.pdf'
        )
        intids = getUtility(IIntIds)
        file_id = intids.getId(self.portal.file)
        self.portal.file.file = RelationValue(file_id)
        import transaction
        transaction.commit()
        response = self.api_session.get(self.portal.file.absolute_url())
        save_response_for_documentation('file.json', response)

    def test_documentation_image(self):
        self.portal.invokeFactory('Image', id='image')
        self.portal.image.title = 'My Image'
        self.portal.image.description = u'This is an image'
        image_file = os.path.join(os.path.dirname(__file__), u'image.png')
        self.portal.image.image = NamedBlobImage(
            data=open(image_file, 'r').read(),
            contentType='image/png',
            filename=u'image.png'
        )
        import transaction
        transaction.commit()
        response = self.api_session.get(self.portal.image.absolute_url())
        save_response_for_documentation('image.json', response)

    def test_documentation_folder(self):
        self.portal.invokeFactory('Folder', id='folder')
        self.portal.folder.title = 'My Folder'
        self.portal.folder.description = u'This is a folder with two documents'
        self.portal.folder.invokeFactory(
            'Document',
            id='doc1',
            title='A document within a folder'
        )
        self.portal.folder.invokeFactory(
            'Document',
            id='doc2',
            title='A document within a folder'
        )
        import transaction
        transaction.commit()
        response = self.api_session.get(self.portal.folder.absolute_url())
        save_response_for_documentation('folder.json', response)

    def test_documentation_collection(self):
        self.portal.invokeFactory('Collection', id='collection')
        self.portal.collection.title = 'My Collection'
        self.portal.collection.description = \
            u'This is a collection with two documents'
        self.portal.collection.query = [{
            'i': 'portal_type',
            'o': 'plone.app.querystring.operation.string.is',
            'v': 'Document',
        }]
        self.portal.invokeFactory(
            'Document',
            id='doc1',
            title='Document 1'
        )
        self.portal.invokeFactory(
            'Document',
            id='doc2',
            title='Document 2'
        )
        import transaction
        transaction.commit()
        response = self.api_session.get(self.portal.collection.absolute_url())
        save_response_for_documentation('collection.json', response)

    def test_documentation_siteroot(self):
        response = self.api_session.get(self.portal.absolute_url())
        save_response_for_documentation('siteroot.json', response)

    def test_documentation_search(self):
        query = json.dumps({'sort_on': 'path'})
        response = self.api_session.get('/search', params={'q': query})
        save_response_for_documentation('search.json', response)

    def test_documentation_404_not_found(self):
        response = self.api_session.get('non-existing-resource')
        save_response_for_documentation('404_not_found.json', response)
