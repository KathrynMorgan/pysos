import os
from pysosutils.utilities.plugin import Plugin


class lvm(Plugin):

    def parse(self):
        self.keys = ['name', 'size', 'path', 'status', 'uuid']
        self.header = ['Name', 'Size', 'Path', 'Status', 'UUID']
        df = self.target + 'sos_commands/devicemapper/vgdisplay_-vv'
        lf = self.target + ('sos_commands/lvm2/'
                            'vgdisplay_-vv_--config_global_locking_type_0'
                            )
        if os.path.isfile(df):
            self.lvfile = df
        elif os.path.isfile(lf):
            self.lvfile = lf
        self.display_lvm_data()

    def get_lvm_data(self):
        try:
            data = [l.strip() for l in open(self.lvfile).readlines()
                    if l.strip() and (l.strip().startswith('---') or
                                      l.strip().startswith('VG') or
                                      l.strip().startswith('LV') or
                                      l.strip().startswith('PV'))]
            vgs = []
            for x in [i for i in '+++'.join(data).split(
                    '--- Volume group ---') if i]:
                vg = VolumeGroup(x.split('+++'))
                vgs.append(vg)
        except IOError:
            vgs = False
            self.pprint.bred(
                '\tCould not find %s. Unable to parse' % self.lvfile
            )
        return vgs

    def display_lvm_data(self):
        data = self.get_lvm_data()
        self.pprint.bsection('Disk and LVM Information\n')
        if data:
            for vg in data:
                self.pprint.bheader('\t VG Name: ', vg.name)
                data = [lv.__dict__ for lv in vg.lvs]
                tbl = self.format_as_table(data, self.keys,
                                           self.header, 'name'
                                           )
                self.display_table(tbl, color='WHITE', indent='\t\t')
                print '\n'

        else:
            self.pprint.bred('\t Could not parse LVM information')


class VolumeGroup:

    def __init__(self, rawdata):
        self.rawdata = rawdata
        self.name = ''
        self.access = ''
        self.status = ''
        self.size = ''
        self.status = ''
        vglvdata, pvdata = [x.split(
            '+++') for x in '+++'.join(self.rawdata).split(
                                            '--- Physical volumes ---')]
        self.getvgdata(vglvdata)
        self.lvs = self.getlvs(vglvdata)
        self.pvs = self.getpvs(pvdata)

    def getvgdata(self, vglvdata):
        self.vgdata = [
            x for x in '+++'.join(vglvdata).split(
                            '--- Logical volume ---')[0].split('+++') if x]
        for l in self.vgdata:
            if 'VG Name' in l:
                self.name = l.split()[-1]
            elif 'VG Access' in l:
                self.access = l.split()[-1]
            elif 'VG Status' in l:
                self.status = l.split()[-1]
            elif 'VG Size' in l:
                self.size = ' '.join(l.split()[-2:])
            elif 'VG UUID' in l:
                self.uuid = l.split()[-1]

    def getlvs(self, vglvdata):
        self.lvdata = [x.split(
            '+++') for x in '+++'.join(vglvdata).split(
                                        '--- Logical volume ---')[1:] if x]
        lvs = []
        for i in self.lvdata:
            lv = {}
            for l in i:
                if 'LV' in l:
                    if 'Size' in l:
                        lv['size'] = " ".join(l.split()[-2:])
                    elif 'Creation' not in l:
                        attr = l.split()[-2].lower()
                        lv[attr] = l.split()[-1]
            lvs.append(LogicalVolume(lv))
        return lvs

    def getpvs(self, pvdata):
        self.pvdata = [x for x in pvdata if x]
        pvsdict = {}
        for l in self.pvdata:
            if 'PV Name' in l:
                name = l.split()[-1]
                if name not in list(pvsdict.keys()):
                    pvsdict[name] = {}
                    pvsdict[name]['name'] = name
            elif name:
                attr = l.split()[-2].lower()
                pvsdict[name][attr] = l.split()[-1]
        pvs = []
        for pv in list(pvsdict.values()):
            pvs.append(PhysicalVolume(pv))
        return pvs


class LogicalVolume:

    def __init__(self, lvdict):
        self.path = ''
        self.status = ''
        for k, v in lvdict.items():
            self.__dict__[k] = v


class PhysicalVolume:

    def __init__(self, pvdict):
        for k, v in pvdict.items():
            self.__dict__[k] = v
