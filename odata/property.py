# -*- coding: utf-8 -*-

from decimal import Decimal
try:
    # noinspection PyUnresolvedReferences
    from urllib.parse import urljoin
except ImportError:
    # noinspection PyUnresolvedReferences
    from urlparse import urljoin

import dateutil.parser


class PropertyBase(object):

    def __init__(self, name, primary_key=False):
        """
        :type name: str
        :type primary_key: bool
        """
        self.name = name
        self.primary_key = primary_key

    def __repr__(self):
        return '<Property({0})>'.format(self.name)

    def __get__(self, instance, owner):
        """
        :type instance: odata.entity.EntityBase
        :type owner: odata.entity.EntityBase
        """
        if instance is None:
            return self

        if self.name in instance.__odata__:
            raw_data = instance.__odata__[self.name]
            return self._return_data(raw_data)
        else:
            raise AttributeError()

    def __set__(self, instance, value):
        """
        :type instance: odata.entity.EntityBase
        """
        if self.name in instance.__odata__:
            new_value = self._set_data(value)
            old_value = instance.__odata__[self.name]
            if new_value != old_value:
                instance.__odata__[self.name] = new_value
                if self not in instance.__odata_dirty__:
                    instance.__odata_dirty__.append(self)

    def _set_data(self, value):
        """ Called when serializing the value to JSON """
        return value

    def _return_data(self, value):
        """ Called when deserializing the value from JSON to Python """
        return value

    def escape_value(self, value):
        return value

    def asc(self):
        return '{0} asc'.format(self.name)

    def desc(self):
        return '{0} desc'.format(self.name)

    def __eq__(self, other):
        value = self.escape_value(other)
        return u'{0} eq {1}'.format(self.name, value)

    def __ne__(self, other):
        value = self.escape_value(other)
        return u'{0} ne {1}'.format(self.name, value)

    def __ge__(self, other):
        value = self.escape_value(other)
        return u'{0} ge {1}'.format(self.name, value)

    def __gt__(self, other):
        value = self.escape_value(other)
        return u'{0} gt {1}'.format(self.name, value)

    def __le__(self, other):
        value = self.escape_value(other)
        return u'{0} le {1}'.format(self.name, value)

    def __lt__(self, other):
        value = self.escape_value(other)
        return u'{0} lt {1}'.format(self.name, value)

    def startswith(self, value):
        value = self.escape_value(value)
        return u'startswith({0}, {1})'.format(self.name, value)

    def endswith(self, value):
        value = self.escape_value(value)
        return u'endswith({0}, {1})'.format(self.name, value)


class IntegerProperty(PropertyBase):
    pass


class StringProperty(PropertyBase):

    def escape_value(self, value):
        return u"'{0}'".format(value)


class BooleanProperty(PropertyBase):

    def escape_value(self, value):
        if value:
            return 'true'
        return 'false'

    def _set_data(self, value):
        return bool(value)

    def _return_data(self, value):
        return bool(value)


class FloatProperty(PropertyBase):
    pass


class DecimalProperty(PropertyBase):

    def _set_data(self, value):
        return float(value)

    def _return_data(self, value):
        return Decimal(str(value))


class DatetimeProperty(PropertyBase):

    def _set_data(self, value):
        r = value.isoformat()
        if value.tzinfo is None:
            r += 'Z'
        return r

    def _return_data(self, value):
        return dateutil.parser.parse(value)


class Relationship(object):

    def __init__(self, name, entitycls, collection=False):
        self.name = name
        self.entitycls = entitycls
        self.is_collection = collection

    def __repr__(self):
        return '<Relationship to {0}>'.format(self.entitycls)

    def instances_from_data(self, raw_data):
        if self.is_collection:
            return [self.entitycls(from_data=d) for d in raw_data]
        else:
            return self.entitycls(from_data=raw_data)

    def __get__(self, instance, owner):
        if instance is None:
            return self

        parent_url = instance.__odata_instance_url__()
        parent_url += '/'
        url = urljoin(parent_url, self.name)

        if self.name in instance.__odata__:
            raw_data = instance.__odata__[self.name]
            if raw_data:
                return self.instances_from_data(raw_data)

        else:
            # Read from service
            cnx = self.entitycls.__odata_connection__
            raw_data = cnx.execute_get(url)
            if raw_data and 'value' in raw_data:
                raw_data = raw_data['value']
                instance.__odata__[self.name] = raw_data
                return self.instances_from_data(raw_data)

            raise AttributeError()
