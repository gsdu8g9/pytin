# coding=utf-8
from __future__ import unicode_literals

import os
import tempfile


class ProvisionScheduler(object):
    """
    Class used to select the best node for the VPS provisioning.
    """

    def get_best_node(self, node_list):
        raise Exception("Not implemented!")


class RatingBasedScheduler(ProvisionScheduler):
    """
    This scheduler uses node rating option to select best node.
    Node must have the 'rating' option. This option can be populated from
    any source, such as UnixBench score or more complex metrics.
    The rule is: higher rating is better.
    """

    RATING_ATTR = 'rating'

    def get_best_node(self, node_list):
        assert node_list

        best_node = None
        max_rating = -1
        for node in node_list:
            node_rating = node.get_option_value(self.RATING_ATTR, default=0)

            if node_rating > max_rating:
                best_node = node

        if not best_node:
            raise Exception("Can't find best node.")

        return best_node


class RoundRobinScheduler(ProvisionScheduler):
    """
    This scheduler selects ProxMox nodes one by one.
    """

    def __init__(self):
        self.last_used_file = os.path.join(tempfile.gettempdir(), 'rr-scheduler.tmp')

    def reset(self):
        if os.path.exists(self.last_used_file):
            os.remove(self.last_used_file)

    def get_best_node(self, node_list):
        assert node_list

        if len(node_list) <= 0:
            raise Exception("There is no hypervisors in the cloud.")

        last_node_id = self._get_last_node_id()
        found_node = None
        while not found_node:
            for hvisor in node_list:
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
