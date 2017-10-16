import re

from pysosutils.utilities.sostests import SosTests
from pysosutils.utilities.plugin import Plugin


class sharedtests(SosTests, Plugin):
    '''
    These are tests that span across plugins and packages.
    They are intended to run every time pysos -t is run
    '''

    def run_rhel_kernel(self):
        kernel = self.get_kernel()
        if re.search('\.el(.+?).', kernel):
            self.succeed()
        else:
            self.fail('Not a RHEL kernel: %s' % kernel)

    def run_rhel_release(self):
        rel = self.get_release()
        if 'Red Hat' in rel:
            self.succeed()
        else:
            self.fail('A non-RHEL OS is installed')

    def run_selinux_state(self):
        state = self.get_selinux()
        if state['config'] is not 'disabled':
            self.succeed()
        else:
            self.warn('SELinux is disabled')
