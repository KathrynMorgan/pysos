
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
        self.dat_files = {}
        for entity in self._mapping:
            self.dat_files[entity] = self.find_dat(self._mapping[entity])

    def find_dat(self, table):
        '''This is what actually finds the dat file for a specific table'''
        with open(self.db_dir + 'restore.sql') as rfile:
            for line in rfile:
                if line.startswith('copy'):
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
            hyp = hypervisor(host)
            self.hypervisors.append(hyp)
        for host in self._hypervisor_dynamic:
            hyp = hyperdynamic(host, self.version)
            self.hypervisor_dynamic.append(hyp)
        for stor in self._storage_domains:
            sd = storagedomain(stor, self.version)
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
                      "vdsm_version": 39,
                      "host_os": 27,
                      "kvm_ver": 28,
                      "spice_ver": 29,
                      "kernel_version": 30
                      },
              '3.2': {
                      'uuid': 0,
                      "host_os": 25,
                      "kvm_ver": 26,
                      "spice_ver": 27,
                      "kernel_version": 28,
                      'vdsm_version': 37
                      },
              '3.3': {
                      'uuid': 0,
                      "vdsm_version": 38,
                      "host_os": 26,
                      "kvm_ver": 27,
                      "spice_ver": 28,
                      "kernel_version": 29
                      },
              '3.4': {
                      'uuid': 0,
                      "vdsm_version": 36,
                      "host_os": 25,
                      "kvm_ver": 26,
                      "spice_ver": 27,
                      "kernel_version": 28
                      }
              }

    def __init__(self, hyp_string, ver):
        for key in self.schema[ver]:
            try:
                val = hyp_string[self.schema[ver][key]]
                if val == "\N":
                    val = ''
                self[key] = hyp_string[self.schema[ver][key]].strip(' ')
            except:
                pass


class hypervisor(dict):

    schema = {
              "uuid": 0,
              "name": 1,
              "ip_addr": 2,
              "host_name": 4,
              "host_cluster_uuid": 6,
              "host_type": 8,
              }

    def __init__(self, hyp_string):
        '''Based on the ver provided, break hyp_string into a dict'''
        self['ip_addr'] = ''
        self['datacenter'] = ''
        for key in self.schema:
            try:
                val = hyp_string[self.schema[key]]
                if val == "\\N":
                    val = ''
                self[key] = hyp_string[self.schema[key]]
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

    schema = {'3.2': {
                     'uuid': 0,
                     'name': 2,
                     'storage_type': 4,
                     }
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

    def __init__(self, sd_string, ver):
        self['status'] = ''
        self['dc_uuid'] = ''
        for key in self.schema[ver]:
            try:
                self[key] = sd_string[self.schema[ver][key]]
            except:
                pass

        for stat in self.stype:
            if self['storage_type'] == stat:
                self['storage_type'] = self.stype[stat]


class cluster(dict):

    schema = {'3.2': {
                      'uuid': 0,
                      'name': 1,
                      'dc_uuid': 10,
                      'compat': 12
                      }
              }

    def __init__(self, clus_string, ver):
        for key in self.schema[ver]:
            try:
                self[key] = clus_string[self.schema[ver][key]]
            except:
                pass
