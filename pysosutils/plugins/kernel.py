import os
from collections import OrderedDict
from pysosutils.utilities.plugin import Plugin


class kernel(Plugin):

    def parse(self):
        self.report_kernel()

    def report_kernel(self):
        self.pprint.bsection('Kernel')
        info = self.get_kernel_info()
        if not info:
            self.pprint.bred('Could not parse kernel info')
            raise Exception
        h = ['running kernel', 'taint state', 'kexec-tools version']
        self.print_header_values(info, h)

        self.pprint.bheader('\n\t{:20s} :\n'.format("kdump.conf"))
        for k in info['kdump']:
            self.pprint.blue('\t\t\t{:15s}  : '.format(k), info['kdump'][k])

        self.pprint.bheader('\n\t{:20s} :\n'.format('Kernel Panic Sysctls'))
        for p in info['panics']:
            q = info['panics'][p]
            if q == '0':
                q += ' [disabled]'
            if q == '1':
                q += self.color['BGREEN'] + ' [enabled]' + self.color['ENDC']
            self.pprint.reg('\t\t\t\t{:32s}  = {}'.format(p, q))

    def get_kernel_info(self):
        info = OrderedDict()
        info['running kernel'] = self.get_kernel()
        info['taint state'] = self.get_taints()
        info['kexec-tools version'] = self.get_rpm('kexec-tools')[0]
        info['kdump'] = self.get_kdump_info()
        info['panics'] = self.get_sysctls('panic')
        return info

    def get_kdump_config(self):
        """ Get all config settings for kdump """
        kdump = {}
        if os.path.isfile(self.target + 'etc/kdump.conf'):
            with open(self.target + 'etc/kdump.conf', 'r') as kfile:
                for line in kfile:
                    if (not line.startswith("#") and not
                            line.startswith('\n')):
                        kdump[line.split()[0]] = (line.split(
                            line.split()[0])[1].strip('\n'))
        else:
            kdump = False
        return kdump

    def get_kdump_info(self):
        kinfo = {}
        try:
            kinfo['memreserve'] = self.get_cmdline().split(
                                            'crashkernel=')[1].split()[0]
        except IndexError:
            kinfo['memreserve'] = 'Not Defined'
        kconfig = self.get_kdump_config()
        if kconfig:
            kinfo.update(kconfig)
        return kinfo
