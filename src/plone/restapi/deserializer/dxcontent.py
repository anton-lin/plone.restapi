# -*- coding: utf-8 -*-
from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.utils import iterSchemata
from plone.restapi.deserializer import DeserializationError
from plone.restapi.interfaces import IDeserializeFromJson
from plone.restapi.interfaces import IFieldDeserializer
from zope.component import adapter
from zope.component import queryMultiAdapter
from zope.event import notify
from zope.interface import Interface
from zope.interface import implementer
from zope.lifecycleevent import ObjectModifiedEvent
from zope.schema import getFields
import json


@implementer(IDeserializeFromJson)
@adapter(IDexterityContent, Interface)
class DeserializeFromJson(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        try:
            data = json.loads(self.request.get('BODY', '{}'))
        except ValueError:
            raise DeserializationError('No JSON object could be decoded')
        if not isinstance(data, dict):
            raise DeserializationError('Malformed body')

        for schemata in iterSchemata(self.context):
            for name, field in getFields(schemata).items():
                if field.readonly:
                    continue

                if name in data:
                    deserializer = queryMultiAdapter(
                        (field, self.context, self.request),
                        IFieldDeserializer)
                    if deserializer is None:
                        continue
                    value = deserializer(data[name])
                    field.set(field.interface(self.context), value)

        notify(ObjectModifiedEvent(self.context))
        return self.context
