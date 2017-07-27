import os
from pysosutils.utilities.plugin import Plugin


class filesystem(Plugin):

    def parse(self):
        self.excludes = ['cgroup', 'tmpfs', 'none', 'sunrpc', 'debugfs',
                         'configfs', 'fusectl', 'hugetlbfs', 'devpts',
                         'sysfs', 'mqueue', 'systemd', 'binfmt_misc',
                         'devtmpfs', 'securityfs', 'pstore', 'proc', 'shm'
                         ]
        self.keys = ['device', 'mountpoint', 'fstype', 'size', 'used',
                     'available', 'mountopts'
                     ]
        self.display_fs_info()

    def display_fs_info(self):
        ''' Gathers FS data from sosreport and prints a table '''
        self.pprint.bsection('Filesystem')
        try:
            fs = self.get_all_filesystems()
            fsl = [fs[f] for f in fs]
            header = ['Device', 'Mount Point', 'Type', 'Size (GB)',
                      'Used (GB)', 'Free (GB)', 'Mount Opts'
                      ]
            tbl = self.format_as_table(fsl, self.keys, header, 'device', False)
            self.display_table(tbl, color='WHITE', indent='\t\t')
        except Exception as e:
            print e
            self.pprint.bred('Could not parse FS data')
            raise Exception

    def get_all_filesystems(self):
        ''' Finds all mount points and returns those a dict keys '''
        fs = {}
        fsfile = self.target + 'sos_commands/filesys/mount_-l'
        if not os.path.isfile(fsfile):
            raise Exception
        with open(fsfile, 'r') as fsfile:
            for line in fsfile:
                if line.startswith(tuple(self.excludes)):
                    continue
                fsl = line.strip('\n').split()
                if 'docker' in fsl[0]:
                    continue
                try:
                    name = fsl[0]
                    dev = fsl[0].replace('/dev/mapper/', '').replace(
                                 "/dev/", '')[:50]
                    mntpt = fsl[2].strip()[:50]
                    fstype = fsl[4]
                    mountopts = line[line.find(
                                '(')+1:line.find(')')].strip()[:75]
                except Exception as e:
                    pass
                fs[name] = {
                            'name': name,
                            'device': dev,
                            'mountpoint': mntpt,
                            'fstype': fstype,
                            'mountopts': mountopts
                            }
                fs[name].update(self.get_fs_size(fs[name]['mountpoint']))
        return fs

    def get_fs_size(self, mount):
        ''' Returns a dict of size, used, available space for mount'''
        s = {}
        gb = 1048576
        s['size'] = '-'
        s['used'] = '-'
        s['available'] = '-'
        sfile = self.target + 'sos_commands/filesys/df_-al'
        if not os.path.isfile(sfile):
            return s
        with open(sfile, 'r') as sf:
            for line in sf:
                if line.split()[5] == mount:
                    line = line.split()
                    s['perc_used'] = line[4].strip('%')
                    try:
                        s['perc_avail'] = 100 - float(s['perc_used'])
                    except:
                        s['perc_avail'] = '-'
                    try:
                        s['size'] = round(float(int(line[1])) / gb, 2)
                        s['used'] = round(float(int(line[2])) / gb, 2)
                        s['available'] = round(float(int(line[3])) / gb, 2)
                    except:
                        pass
                    return s
        return s
