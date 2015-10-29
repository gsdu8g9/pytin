from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _


class CloudServiceImpl(object):
    def request(self, request_options):
        raise Exception(_("Not implemented."))


class Hypervisor(CloudServiceImpl):
    def create(self, type, vcpu, ram, hdd):
        pass


class Hosting(CloudServiceImpl):
    pass
