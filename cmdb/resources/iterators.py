class ParentsIterator(object):
    def __init__(self, resource):
        self.resource = resource

    def __iter__(self):
        for res in self._iter_inner(self.resource):
            yield res

    def _iter_inner(self, resource):
        if resource.parent:
            for res in self._iter_inner(resource.parent):
                yield res

        yield resource
