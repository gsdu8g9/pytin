from __future__ import unicode_literals

from importer.providers.l3_switch import L3Switch, L3SwitchPort


class Switch3Com2250Port(L3SwitchPort):
    @property
    def is_local(self):
        return self._port_name.startswith('ethernet') or \
               self._port_name.startswith('copper') or \
               self._port_name.startswith('fiber')


class Switch3Com2250(L3Switch):
    port_implementor = Switch3Com2250Port
