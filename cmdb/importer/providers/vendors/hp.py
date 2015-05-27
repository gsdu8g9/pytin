from importer.providers.l3_switch import L3Switch, L3SwitchPort


class HP1910SwitchPort(L3SwitchPort):
    @property
    def is_local(self):
        return self._port_name.startswith('gigabitethernet')


class HP1910Switch(L3Switch):
    port_implementor = HP1910SwitchPort
