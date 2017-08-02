import tarfile
import os


class Database():

    def __init__(self, db_file, version):
        self.version = version
        self.data_centers = []
        self.storage_domains = []
        self.hypervisors = []
        self.clusters = []
        self.hypervisor_dynamic = []
        self.db_dir = os.path.dirname(db_file) + '/'
        self.db_tar = tarfile.open(db_file)
        self.find_dat_files()
        self.load_tables()
        self.parse()
        self.link_values()

    def find_dat_files(self):
        '''Finds which dat files contain the tables we're interested in'''
        db = self.db_tar.extractall(self.db_dir)
        self._mapping = {'data_centers': 'storage_pool',
                         'storage_domains': 'storage_domain_static',
                         'hypervisors': 'vds_static',
                         'clusters': 'vds_groups',
                         'hypervisor_dynamic': 'vds_dynamic'
                         }
        if float(self.version) >= 4:
            self._mapping['clusters'] = 'cluster'
        self.dat_files = {}
        for entity in self._mapping:
            self.dat_files[entity] = self.find_dat(self._mapping[entity])

    def find_dat(self, table):
        '''This is what actually finds the dat file for a specific table'''
        with open(self.db_dir + 'restore.sql') as rfile:
            for line in rfile:
                if line.lower().startswith('copy'):
                    try:
                        if line.split()[1] == table:
                            dat_idx = line.find("PATH")
                            dat_file = line[dat_idx+7:dat_idx+15]
                            if dat_file.endswith(".dat"):
                                return dat_file
                    except:
                        pass

    def load_tables(self):
        '''Reads table content into a list, each row is a new list item'''
        for entity in self._mapping:
            ent_list = []
            if entity in self.dat_files:
                with open(self.db_dir + self.dat_files[entity], 'r') as dat:
                    for line in dat:
                        if len(line.strip('\n')) > 2:
                            ent_list.append(line.split('\t'))
                setattr(self, '_' + entity, ent_list)

    def parse(self):
        '''For each entity, parse the raw data and massage it into a usable
        dict'''
        for datacen in self._data_centers:
            dc = datacenter(datacen)
            self.data_centers.append(dc)
        for clus in self._clusters:
            c = cluster(clus, self.version)
            self.clusters.append(c)
        for host in self._hypervisors:
            hyp = hypervisor(host, self.version)
            self.hypervisors.append(hyp)
        for host in self._hypervisor_dynamic:
            hyp = hyperdynamic(host, self.version)
            self.hypervisor_dynamic.append(hyp)
        for stor in self._storage_domains:
            sd = storagedomain(stor)
            self.storage_domains.append(sd)

    def link_values(self):
        for dc in self.data_centers:
            for host in self.hypervisors:
                if host['uuid'] == dc['spm_uuid']:
                    dc['spm'] = host['name']

        for cluster in self.clusters:
            for dc in self.data_centers:
                if cluster['dc_uuid'] == dc['uuid']:
                    cluster['datacenter'] = dc['name']

        for host in self.hypervisors:
            for cluster in self.clusters:
                if cluster['uuid'] == host['host_cluster_uuid']:
                    host['cluster'] = cluster['name']
            for hyp in self.hypervisor_dynamic:
                if host['uuid'] == hyp['uuid']:
                    host.update(hyp)


class hyperdynamic(dict):

    schema = {'3.1': {
                      'uuid': 0,
                      'status': 1,
                      "vdsm_version": 39,
                      "host_os": 27,
                      "kvm_ver": 28,
                      "spice_ver": 29,
                      "kernel_version": 30
                      },
              '3.2': {
                      'uuid': 0,
                      'status': 1,
                      "host_os": 25,
                      "kvm_ver": 26,
                      "spice_ver": 27,
                      "kernel_version": 28,
                      'vdsm_version': 37
                      },
              '3.3': {
                      'uuid': 0,
                      'status': 1,
                      "vdsm_version": 38,
                      "host_os": 26,
                      "kvm_ver": 27,
                      "spice_ver": 28,
                      "kernel_version": 29
                      },
              '3.4': {
                      'uuid': 0,
                      'status': 1,
                      "vdsm_version": 36,
                      "host_os": 25,
                      "kvm_ver": 26,
                      "spice_ver": 27,
                      "kernel_version": 28
                      },
              '3.5': {
                      'uuid': 0,
                      'status': 1,
                      'vdsm_version': 34,
                      'host_os': 25,
                      'kvm_ver': 26,
                      'spice_ver': 27,
                      'kernel_version': 28
                      },
              '3.6': {
                      'uuid': 0,
                      'status': 1,
                      'vdsm_version': 34,
                      'host_os': 24,
                      'kvm_ver': 25,
                      'spice_ver': 26,
                      'kernel_version': 27,
                      },
              '4.0': {
                      'uuid': 0,
                      'status': 1,
                      'host_os': 24,
                      'kvm_ver': 25,
                      'spice_ver': 26,
                      'kernel_vesion': 27,
                      'vdsm_version': 34
                      }
              }

    def __init__(self, hyp_string, version):
        if float(version) > 4:
            version = '4.0'
        for key in self.schema[version]:
            try:
                val = hyp_string[self.schema[version][key]]
                if val == "\N":
                    val = ''
                self[key] = hyp_string[self.schema[version][key]].strip(' ')
            except:
                pass


class hypervisor(dict):

    schema = {'3.0': {
                      "uuid": 0,
                      "name": 1,
                      "host_name": 4,
                      "host_cluster_uuid": 6,
                      "host_type": 8,
                      },
              '3.6': {
                      'uuid': 0,
                      'name': 1,
                      'host_name': 3,
                      'host_cluster_uuid': 5,
                      'host_type': 7
                      },
              '4.0': {
                      'uuid': 0,
                      'name': 1,
                      'host_name': 3,
                      'host_cluster_uuid': 5,
                      'host_type': 7
                      }
              }

    def __init__(self, hyp_string, version):
        '''Based on the ver provided, break hyp_string into a dict'''
        self['datacenter'] = ''
        if float(version) > 2 and float(version) < 3.6:
            version = '3.0'
        if float(version) > 4:
            version = '4.0'
        for key in self.schema[version]:
            try:
                val = hyp_string[self.schema[version][key]].strip()
                if val == "\\N":
                    val = ''
                self[key] = val
            except:
                pass


class datacenter(dict):

    schema = {
              "uuid": 0,
              "name": 1,
              'status': 5,
              "compat": 8,
              "spm_uuid": 7
              }

    status = {
              '0': 'Uninitialized',
              '1': 'Up',
              '2': 'Maintenance',
              '3': 'Not Operational',
              '4': 'Non-Responsive',
              '5': 'Contending'
              }

    def __init__(self, dc_string):
        self['spm'] = ''
        for key in self.schema:
            try:
                self[key] = dc_string[self.schema[key]]
            except:
                pass
        for stat in self.status:
            if self['status'] == stat:
                self['status'] = self.status[stat]


class storagedomain(dict):

    schema = {
              'uuid': 0,
              'name': 2,
              'storage_type': 4,
              'domain_type': 3
              }

    stype = {
             '0': 'Unknown',
             '1': 'NFS',
             '2': 'Fibre',
             '3': 'iSCSI',
             '4': 'Local FS',
             '5': 'CIFS',
             '6': 'POSIXFS',
             '7': 'Gluster',
             '8': 'Glance'
             }

    dtype = {
             '0': 'Data(master)',
             '1': 'Data',
             '2': 'ISO',
             '3': 'Export',
             '4': 'Unknown'
             }

    def __init__(self, sd_string):
        self['status'] = ''
        self['dc_uuid'] = ''
        for key in self.schema:
            try:
                self[key] = sd_string[self.schema[key]]
            except:
                pass

        for stat in self.stype:
            if self['storage_type'] == stat:
                self['storage_type'] = self.stype[stat]

        for stat in self.dtype:
            if self['domain_type'] == stat:
                self['domain_type'] = self.dtype[stat]


class cluster(dict):

    schema = {'3.0': {
                      'uuid': 0,
                      'name': 1,
                      'dc_uuid': 10,
                      'compat': 12
                      },
              '3.6': {
                      'uuid': 0,
                      'name': 1,
                      'dc_uuid': 6,
                      'compat': 8
                      },
              '4.0': {
                      'uuid': 0,
                      'name': 1,
                      'dc_uuid': 6,
                      'compat': 8
                      }
              }

    def __init__(self, clus_string, version):
        if float(version) > 2 and float(version) < 3.6:
            version = '3.0'
        if float(version) > 4:
            version = '4.0'
        for key in self.schema[version]:
            try:
                self[key] = clus_string[self.schema[version][key]]
            except:
                pass
