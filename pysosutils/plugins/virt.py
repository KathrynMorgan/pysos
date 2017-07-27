from processes import processes
from pysosutils.utilities.plugin import Plugin


class virt(Plugin):

    def parse(self):
        self.platform = self.determine_platform()
        self.packages = self.get_virt_packages()
        self.info = self.get_platform_info()
        self.display_platform_info()

    def determine_platform(self):
        """Used to see what virt platform the sosreport is from"""
        if self.is_installed('rhevm'):
            return 'rhevm'

        if self.is_installed('vdsm'):
            return 'rhev'

        if self.is_installed('qemu-kvm'):
            return 'kvm'

    def get_virt_packages(self):
        """Based on the virt platform, return what packages in use"""
        if not hasattr(self, 'platform'):
            self.platform = self.determine_platform()

        packages = []
        vpackages = []

        if self.platform == 'rhev':
            packages = ['vdsm', 'qemu-kvm-rhev-tools', 'qemu-kvm-rhev',
                        'qemu-img-rhev', 'libvirt-daemon', 'spice-server'
                        ]

        if self.platform == 'rhevm':
            packages = ['rhevm']
            if self.is_hosted_engine():
                packages.append('ovirt-hosted-engine-ha')

        if self.platform == 'kvm':
            packages = ['qemu-kvm', 'qemu-img', 'libvirt']

        for package in packages:
            pkg = {'name': package}
            pkg['version'] = self.get_rpm_version(package)
            if not pkg['version']:
                pkg['version'] = ''
            vpackages.append(pkg)

        return vpackages

    @property
    def is_hosted_engine(self):
        return self.is_installed('ovirt-hosted-engine-ha')

    @property
    def is_spm(self):
        f = 'sos_commands/vdsm/vdsClient_-s_0_getAllTasksStatuses'
        spm = self.file_to_string(self.target + f)
        return spm or False

    def get_platform_info(self):
        if not hasattr(self, 'platform'):
            self.packages = self.get_virt_packages()
        info = {}

        info['kernel'] = self.get_kernel()
        info['release'] = self.get_release()

        if self.platform == 'rhev' or self.platform == 'kvm':
            info['vms'] = self.get_running_vms()

        if self.platform == 'rhevm':
            self.get_rhevm_info()

        return info

    def get_running_vms(self):
        vms = []
        procs = processes(self.target, self.options).parse_proc_file()
        for proc in procs:
            vm = {}
            if '/usr/libexec/qemu-kvm' in proc['command']:
                s = proc['command']
                vm['name'] = s[s.find('-name'):-1].split()[1].split(
                                ',')[0].replace('guest=', '')
                vm.update(proc)
                vms.append(vm)
        return vms

    def get_rhevm_info(self):
        pass

    def display_rhev_hyper_info(self):
        self.pprint.white('\n\t{:20s} : '.format('Is SPM'), '%s' % self.is_spm)
        self.pprint.white('\t{:20s} : '.format('Hosted Engine'), '%s' % (
                            self.is_hosted_engine)
                          )

    def display_platform_info(self):
        if not hasattr(self, 'info'):
            self.info = self.get_platform_info()

        self.pprint.bsection('Virtualization Information\n')
        self.print_header_values(self.info, headers=['kernel', 'release'])

        keys = ['name', 'version']
        header = ['Name', 'Version']
        tbl = self.format_as_table(self.packages, keys, header, 'name')
        self.pprint.bheader('\n\t{:20s} : '.format('Packages'))
        self.display_table(tbl, color='BHEADER', indent='\t\t\t\t',
                           no_header=True
                           )

        self.display_rhev_hyper_info()

        if 'vms' in self.info:
            self.pprint.bheader('\n\tRunning VMs : \n')
            keys = ['name', 'rssmb', 'cpu']
            header = ['Name', 'Memory (MB)', 'CPU (%)']
            tbl = self.format_as_table(self.info['vms'], keys, header, 'name')
            self.display_table(tbl, color='WHITE', indent='\t\t\t\t')
