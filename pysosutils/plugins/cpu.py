import textwrap
import re
from pysosutils.utilities.plugin import Plugin
from pysosutils.utilities.sostests import SosTests


class cpu(Plugin):

    def _fmt_flags(self, flags):
        important_flags = ['vmx', ' svm ', 'nx', ' lm ']
        for flag in important_flags:
            pattern = re.compile(flag)
            flags = pattern.sub(self.color['WHITE'] + flag +
                                self.color['ENDC'], flags
                                )
        return flags

    def parse(self):
        self.info = self.get_cpu_info(highlight_flags=True)
        self.report_cpu_info()

    def report_cpu_info(self):
        if not hasattr(self, 'info'):
            self.info = self.get_cpu_info(highlight_flags=True)
        self.pprint.bsection('Processor')
        if not self.info:
            self.pprint.bred('No proc/cpuinfo found.')
            raise Exception
        self.pprint.white('\t\t %s processors' % self.info['processors'])
        self.pprint.reg('\t\t %s %s packages' % (self.info['sockets'],
                                                 self.info['model']
                                                 )
                        )
        self.pprint.reg(
            '\t\t %s cores / %s threads per core / %s threads per package' % (
                self.info['cores'],
                self.info['threadspercore'],
                self.info['threadspercpu']
            )
        )
        self.info['flags'] = self._fmt_flags(self.info['flags'])
        self.pprint.bheader('\t\t Flags :', textwrap.fill(self.info['flags'],
                            90, subsequent_indent='\t\t\t ')
                            )

    def get_cpu_info(self, highlight_flags=False):
        cinfo = {}
        with open(self.target + 'proc/cpuinfo') as cfile:
            # we read in reverse since the cpu info output is the same
            # no need to iterate over dozens of the same template
            # we can extrapolate the data points that may change once we
            # assume that the lines being read are for the last CPU
            for line in reversed(cfile.readlines()):
                line = line.rstrip('\n')
                index = line.find(':')
                if line.startswith('flags'):
                    cinfo['flags'] = line[index + 2:len(line)]
                # number of physical cores
                elif line.startswith('cpu cores'):
                    cinfo['cores'] = int(line[index + 2:len(line)])
                # number of threads per physical core
                elif line.startswith('siblings'):
                    cinfo['threadspercpu'] = int(
                        line[index + 2:len(line)])
                # number of physical sockets
                elif line.startswith('core id'):
                    cinfo['sockets'] = int(line[index + 2:len(line)]) + 1
                # proc model
                elif line.startswith('model name'):
                    cinfo['model'] = line[index + 2:len(line)]
                # proc family
                elif line.startswith('cpu family'):
                    cinfo['family'] = line[index + 2:len(line)]
                # proc vendor
                elif line.startswith('vendor_id'):
                    cinfo['vendor'] = line[index + 2:len(line)]
                # finally, total number of CPUs
                elif line.startswith('processor'):
                    try:
                        cinfo['processors'] = int(line[index + 2:
                                                  len(line)]) + 1
                    except ValueError:
                        # implies we're not on x86
                        cinfo['processors'] = int(
                            line.split()[1].strip(':')
                        ) + 1
                        cinfo['flags'] = 'Undeterminable'
                        cinfo['model'] = 'Undefined'
                        cinfo['sockets'] = 'Undefined'
                        cinfo['cores'] = 'Undefined'
                        cinfo['threadspercore'] = 'Undefined'
                    break
        cinfo['threadspercore'] = cinfo['processors'] / cinfo['cores']
        return cinfo

    class tests(SosTests, Plugin):

        def setup(self):
            self.cinfo = cpu(self.target, self.options).get_cpu_info()

        def run_socket_check(self):
            if self.cinfo['sockets'] > self.cinfo['processors']:
                self.warn(
                    'More sockets than processors reported. '
                    'If on VMware, this may be safely ignored.'
                )
            else:
                self.succeed()

        def run_virt_capable(self):
            virt_flags = ['vmx', ' svm ', 'nx', ' lm ']
            if any(flag in self.cinfo['flags'] for flag in virt_flags):
                self.succeed()
            else:
                self.fail('No virtualization extensions reported.')
