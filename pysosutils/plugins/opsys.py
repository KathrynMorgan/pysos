import textwrap
from pysosutils.utilities.plugin import Plugin
from cpu import cpu


class opsys(Plugin):

    def parse(self):
        self.report_opsys()

    def _fmt_load_avg(self):
        '''Format get_load_avg() into string with percentages'''
        loads = self.get_load_avg()
        cpus = cpu(self.target, self.options).get_cpu_info()['processors']
        percs = []
        for item in loads:
            index = loads.index(item)
            loadperc = (float(item) / cpus) * 100
            if loadperc < 75:
                pc = self.color['DBLUE']
            elif loadperc > 74 and loadperc < 100:
                pc = self.color['WARN']
            else:
                pc = self.color['BRED']

            loads[index] = (loads[index] + pc + '(%.2f)' +
                            self.color['ENDC']) % loadperc
        ldavg = '[%s CPUs] %s' % (cpus, str(loads[0] + loads[1] + loads[2]))
        return ldavg

    def report_opsys(self):
        info = self.get_opsys_info()
        if not info:
            raise Exception
        self.pprint.bsection('OS')
        props = [
                 'Hostname',
                 'Release',
                 'Runlevel',
                 'SELinux',
                 'Kernel',
                 'CMDline',
                 'Taints',
                 'Boot Time',
                 'Sys Time',
                 'Uptime',
                 'Load Avg'
                ]
        for i in props:
            self.pprint.bheader('\t {:10s} : '.format(i), info[i.lower()])
        self.pprint.bheader('\t /proc/stat :')
        self.pprint.bblue('\t\tRunning    :', info['procs_running'])
        self.pprint.bblue('\t\tSince Boot :', info['processes'])

    def get_opsys_info(self):
        props = [
                 'hostname',
                 'release',
                 'runlevel',
                 'uptime',
                 'selinux',
                 'taints',
                 'kernel',
                 'cmdline'
                 ]
        info = {}
        for prop in props:
            meth = getattr(self, 'get_' + prop)
            info[prop] = meth()
        info['selinux'] = '{} ( config: {})'.format(info['selinux']['current'],
                                                    info['selinux']['config'])
        info['taints'] = info['taints'][0].strip()
        info['cmdline'] = textwrap.fill(info['cmdline'], 100,
                                        subsequent_indent=' ' * 23) + '\n'

        info.update(self.get_proc_stat())
        info['uptime'] = self.get_uptime()
        info['sys time'] = self.get_sos_date()
        info['load avg'] = self._fmt_load_avg()
        return info
