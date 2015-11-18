# coding=utf-8
from __future__ import unicode_literals

import os
import tempfile


class ProvisionScheduler(object):
    """
    Class used to select the best node for the VPS provisioning.
    """

    def __init__(self, node_list=None):
        assert node_list

        self.node_list = node_list

    def get_node(self):
        raise Exception("Not implemented!")


class RoundRobinScheduler(ProvisionScheduler):
    """
    This scheduler selects ProxMox nodes one by one.
    """

    def __init__(self, node_list):
        assert node_list

        self.last_used_file = os.path.join(tempfile.gettempdir(), 'rr-scheduler.tmp')

        super(RoundRobinScheduler, self).__init__(node_list)

    def reset(self):
        if os.path.exists(self.last_used_file):
            os.remove(self.last_used_file)

    def get_node(self):
        if len(self.node_list) <= 0:
            raise Exception("There is no hypervisors in the cloud.")

        last_node_id = self._get_last_node_id()
        found_node = None
        while not found_node:
            for hvisor in self.node_list:
                if hvisor.id > last_node_id:
                    found_node = hvisor
                    break

            if not found_node:
                last_node_id = 0  # start over

        self._set_last_node_id(found_node.id)

        return found_node

    def _get_last_node_id(self):
        open(self.last_used_file, 'a').close()

        with open(self.last_used_file, mode='r+b') as tmp_file:
            line = tmp_file.readline()
            return int(line) if line else 0

    def _set_last_node_id(self, node_id):
        assert node_id > 0

        with open(self.last_used_file, mode='w+b') as tmp_file:
            tmp_file.write(unicode(node_id))
