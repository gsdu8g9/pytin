import re

from importer.providers.l3_switch import L3Switch, L3SwitchPort


class DSG3200SwitchPort(L3SwitchPort):
    local_port__regexp = re.compile(r'^\d+/\d+$', re.IGNORECASE)

    @property
    def is_local(self):
        if self.local_port__regexp.match(self._port_name):
            return True

        return False


class DSG3200Switch(L3Switch):
    port_implementor = DSG3200SwitchPort
