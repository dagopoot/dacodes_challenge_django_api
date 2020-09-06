from django.shortcuts import render


class MultiSerializerViewSet(object):

    def get_serializer_class(self):
        """ Return the class to use for serializer w.r.t to the request method."""
        try:
            return self.custom_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(MultiSerializerViewSet, self).get_serializer_class()
