class PathIterator(object):
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


class TreeIterator(object):
    def __init__(self, resource):
        self.resource = resource
        self.level = 0

    def __iter__(self):
        self.level = 0

        for res in self._iter_inner(self.resource):
            yield res, self.level

    def _iter_inner(self, resource):
        self.level += 1

        yield resource

        for res in resource:
            for res_inner in self._iter_inner(res):
                yield res_inner

        self.level -= 1
