from subprocess import Popen, PIPE


class GenericBlocker:
    def block(self, ip):
        pass

    def unblock(self, ip):
        pass


class ApfBlocker(GenericBlocker):
    def __init__(self):
        self.block_command = ['/etc/apf/apf', '-d']  # ip comment
        self.unblock_command = ['/etc/apf/apf', '-u']  # ip comment

    def block(self, ip):
        assert ip

        block_cmd = list(self.block_command)
        block_cmd.append(ip)
        block_cmd.append('nginx_protector')

        Popen(block_cmd, stdout=PIPE).wait()

    def unblock(self, ip):
        assert ip

        unblock_cmd = list(self.unblock_command)
        unblock_cmd.append(ip)
        unblock_cmd.append('nginx_protector')

        Popen(unblock_cmd, stdout=PIPE).wait()
