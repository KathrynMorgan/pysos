import os
from pysosutils.utilities.plugin import Plugin


class lspci(Plugin):

    def parse(self):
        self.lspci_info = self.get_lspci_info()
        self.display_all_devices()

    def get_lspci_info(self):
        ls_info = []
        if os.path.isfile(self.target + 'lspci'):
            with open(self.target + 'lspci', 'r') as lfile:
                for line in lfile:
                    if 'lspci -nvv:' in line:
                        break
                    try:
                        pciaddr = line[0:line.find('.') - 1].strip()
                        new_dev = True
                        if len(ls_info) > 0:
                            for dev in ls_info:
                                if dev['pciaddr'] == pciaddr:
                                    dev['count'] += 1
                                    new_dev = False
                                    break
                        if new_dev:
                            dev = {}
                            dev['pciaddr'] = pciaddr
                            dev['devtype'] = line[line.find(pciaddr):
                                                  line.find(': ') + 1].strip(
                                pciaddr).strip()
                            dev['name'] = line[line.find(': ') + 2:
                                               len(line)].strip('\n')
                            if 'Ethernet' in dev['devtype']:
                                dev['devtype'] = 'Ethernet'
                            elif 'VGA' in dev['devtype']:
                                dev['devtype'] = 'VGA'
                            elif 'SCSI' in dev['devtype']:
                                dev['devtype'] = 'SCSI'
                            elif 'Fibre Channel' in dev['devtype']:
                                dev['devtype'] = 'Fibre'
                            dev['count'] = 1
                            ls_info.append(dev)
                    except:
                        pass
        return ls_info

    def display_all_devices(self):
        """Not all devices found, just the major types we care about"""
        self.pprint.bsection('Device Information\n')
        for dev in ['Ethernet', 'VGA', 'SCSI', 'Fibre']:
            self.display_lspci_device_type(dev)

    def display_lspci_device_type(self, dev_type):
        """ Display hardware devices for the given type of device """
        for dev in self.lspci_info:
            if dev_type in dev['devtype']:
                if dev['count'] > 1:
                    self.pprint.bheader(
                        '\t\t {:10} : '.format(dev['devtype']),
                        '[{} ports] '.format(dev['count']),
                        dev['name']
                    )
                else:
                    self.pprint.bheader(
                        '\t\t {:10} : '.format(dev['devtype']),
                        '{}'.format(dev['name'])
                    )
