
from pysosutils.utilities.sostests import SosTests
from pysosutils.utilities.plugin import Plugin


class dockertests(SosTests, Plugin):

    enabled_for = ['docker']

    def setup(self):
        pass

    def run_storage_driver(self):
        try:
            with open(self.target +
                'sos_commands/docker/docker_info') as s:
                if 'loopback' in s.readlines():
                    self.warn('Loopback storage in use. Should use LVM')
                else:
                    self.succeed()
        except IOError:
            pass

    def run_package_version(self, run_if_failed=True):
        rpms = self.get_rpm('docker')
        upstream_list = ['docker-engine', 'centos', 'docker-io']
        if any(substr in r for substr in upstream_list for r in rpms):
            self.fail('Upstream packages are installed.')
        else:
            self.succeed()
