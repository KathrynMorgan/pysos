import os

from processes import processes
from pysosutils.utilities.plugin import Plugin
from pysosutils.utilities.rhevdatabase import Database


class virt(Plugin):

    def parse(self):
        self.platform = self.determine_platform()
        self.packages = self.get_virt_packages()
        self.info = self.get_platform_info()
        self.display_platform_info()
        if self.options['db']:
            self.display_db_info()

    def determine_platform(self):
        """Used to see what virt platform the sosreport is from"""
        if self.is_installed('rhevm'):
            return 'rhevm'

        if self.is_installed('vdsm'):
            return 'rhev'

        if self.is_installed('qemu-kvm'):
            return 'kvm'
        return ''

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
            if self.is_hosted_engine:
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
            pass

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
        if self.options['db']:
            db_file = self.find_db_file()
            if db_file:
                self.db = self.get_database(db_file)

    def get_database(self, db_file):
        ver = self.get_rpm_version('rhevm').split('-')[0].split('.', 2)[:2]
        simple_ver = '.'.join(ver)
        return Database(db_file, simple_ver)

    def find_db_file(self):
        for root, dirs, files in os.walk(self.target + '..'):
            for f in files:
                if f == 'sos_pgdump.tar':
                    return os.path.join(root, f)
        return False

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

        if self.platform == 'rhev':
            self.display_rhev_hyper_info()

        if 'vms' in self.info:
            self.pprint.bheader('\n\tRunning VMs : \n')
            keys = ['name', 'rssmb', 'cpu']
            header = ['Name', 'Memory (MB)', 'CPU (%)']
            tbl = self.format_as_table(self.info['vms'], keys, header, 'name')
            self.display_table(tbl, color='WHITE', indent='\t\t\t\t')

    def display_db_info(self):
        self.data_centers_keys = ['name', 'status', 'compat', 'spm']
        self.data_centers_header = ['Name', 'Status', 'Compat', 'SPM']

        self.clusters_keys = ['name', 'datacenter', 'compat']
        self.clusters_header = ['Name', 'Datacenter', 'Compat']

        self.hypervisors_keys = [
                                 'name', 'cluster', 'host_name', 'host_os',
                                 'vdsm_version'
                                 ]
        self.hypervisors_header = [
                                   'Name', 'Cluster', 'Hostname', 'Host OS',
                                   'VDSM Version'
                                   ]

        self.storage_domains_keys = ['name', 'storage_type', 'domain_type']
        self.storage_domains_header = ['Name', 'Storage Type', 'Domain Type']

        for ent in ['data_centers', 'clusters', 'hypervisors',
                    'storage_domains']:
            self.pprint.bheader('\t{} Report'.format(
                                ent.replace('_', ' ').title())
                                )
            keys = getattr(self, ent + '_keys')
            header = getattr(self, ent + '_header')
            t = getattr(self.db, ent)
            tbl = self.format_as_table(t, keys, header, 'name')
            self.display_table(tbl, color='BBLUE', indent='\t\t')
            print ''
