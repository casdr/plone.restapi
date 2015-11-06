# -*- coding: utf-8 -*-
from plone.rest import Service
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.search.handler import SearchHandler


class DexterityGet(Service):

    def render(self):
        return ISerializeToJson(self.context)


# class DexterityPost(Service):
#
#     def render(self):
#         return {'service': 'post'}


# class DexterityPut(Service):
#
#     def render(self):
#         return {'service': 'put'}


# class DexterityDelete(Service):
#
#     def render(self):
#         return {'service': 'delete'}


class PloneSiteRootGet(Service):

    def render(self):
        return ISerializeToJson(self.context)


# class PloneSiteRootPost(Service):
#
#     def render(self):
#         return {'service': 'options'}


class SearchGet(Service):

    def render(self):
        json_query = self.request.form.get('q')
        return SearchHandler(self.context, self.request).search(json_query)


class SearchPost(Service):

    def render(self):
        json_query = self.request.get('BODY')
        return SearchHandler(self.context, self.request).search(json_query)
