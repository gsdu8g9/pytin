from __future__ import unicode_literals
from importer.providers.l3_switch import L3Switch, L3SwitchPort


class HP1910SwitchPort(L3SwitchPort):
    @property
    def is_local(self):
        return self._port_name.startswith('gigabitethernet')


class HP1910Switch(L3Switch):
    """
    Also known as 3Com 2952
    """
    port_implementor = HP1910SwitchPort
