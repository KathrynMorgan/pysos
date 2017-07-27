import os

from pysosutils.utilities.plugin import Plugin


class network(Plugin):
    """Network device information"""

    def parse(self):
        self.dev_list = self.get_all_int_info()
        self.display_info()

    def display_info(self):
        self.pprint.bsection('Network Information')

        if self.options['netdev']:
            keys = ['name', 'rxgbytes', 'rxmpkts', 'rxerrs', 'rxdrop',
                    'txgbytes', 'txmpkts', 'txerrs', 'txdrop'
                    ]
            header = ['Device', 'RxGbytes', 'RxPkts', 'RxErrs', 'RxDrops',
                      'TxGbytes', 'TxPkts', 'TxErrs', 'TxDrops'
                      ]
            self.display_section_info('NetDev', self.devs, keys, header)

        if self.options['ethtool']:
            keys = ['name', 'linkdetected', 'autonegotiation', 'currentrx',
                    'currenttx', 'driver', 'driverversion'
                    ]
            header = ['Device', 'Link', 'Auto-Neg', 'Ring-Rx', 'Ring-Tx',
                      'Driver', 'Version'
                      ]
            self.display_section_info('Ethtool', self.devs, keys, header)

        if self.options['bonding']:
            keys = ['name', 'mode', 'slaves', 'bondingopts']
            header = ['Device', 'Mode', 'Slave Interfaces', 'Bonding Options']
            data = []
            for dev in self.devs:
                if 'bond' in dev['name']:
                    data.append(dev)
            self.display_section_info('Bonding', data, keys, header)

        if self.options['ip']:
            keys = ['name', 'ipaddr', 'hwaddr', 'master', 'mtu']
            header = ['Device', 'IP Address', 'MAC Address', 'Slave Of', 'MTU']
            self.display_section_info("IP", self.devs, keys, header)

    def display_section_info(self, section, data, keys, header):
        self.pprint.bheader('\n\t%s Information' % section)
        tbl = self.format_as_table(data, keys, header, False)
        self.display_table(tbl, color='WHITE', indent='\t\t')

    def get_int_list(self, dev_filter=False):
        """ Get list of interfaces """
        dev_list = []
        with open(self.target + 'proc/net/dev', 'r') as dfile:
            lines = dfile.readlines()
            # the 'Iter-' and '-face' lines from head of proc/net/dev
            # will get captured by this. Delete them from the list
            # There has to be a better way to do this
            lines.pop(0)
            lines.pop(0)
            for line in lines:
                index = line.find(':')
                dev = str(line[0:index]).strip()
                if dev_filter:
                    if dev_filter in dev:
                        dev_list.append(dev)
                else:
                    excludes = ['vnet', 'vlan', 'veth']
                    if all(ex not in dev for ex in excludes):
                        dev_list.append(dev)
                    else:
                        pass
                        # if self.vnetDisplay:
                        #    dev_list.append(dev)
        # we don't care about these devices
        try:
            dev_list.remove('lo')
            dev_list.remove(';vdsmdummy;')
        except:
            pass
        return dev_list

    def get_all_int_info(self):
        self.devs = []
        if not hasattr(self, 'dev_list'):
            self.dev_list = self.get_int_list()
        for device in self.dev_list:
            dev = {'name': device}
            dev = self.get_int_info(dev)
            if 'bond' in device:
                dev.update(self.get_bond_int_info(dev))
            self.devs.append(dev)

    def get_int_info(self, device):
        """ Given a device, compile ethtool, driver and ring info """
        try:
            device.update(self.get_netdev_info(device))
            device.update(self.get_ethtool_info(device))
            device.update(self.get_int_driver_info(device))
            device.update(self.get_ring_info(device))
            device.update(self.get_ip_addr(device))
        except:
            pass
        return device

    def get_ethtool_info(self, device):
        """ Get information as reported by ethtool for an interface """
        ef = self.target + 'sos_commands/networking/ethtool_' + device['name']
        if os.path.isfile(ef):
            dev_sets = self.parse_output_section(ef, 'Settings')
        else:
            return device
        try:
            if 'yes' in dev_sets['Link detected']:
                dev_sets['Link detected'] = 'UP'
            else:
                dev_sets['Link detected'] = 'DOWN'
        except:
            dev_sets['Link detected'] = '?'

        for key, value in list(dev_sets.items()):
            device[key.replace(' ', '').replace('-', '').lower()] = value
        try:
            device['speed']
        except:
            device['speed'] = ''
            device['autonegotiation'] = ''

        return device

    def get_netdev_info(self, device):
        """ Get interface stats from /proc/net/dev """
        if os.path.isfile(self.target + 'proc/net/dev'):
            stats = ['rxbytes', 'rxpkts', 'rxerrs', 'rxdrop', 'rxfifo',
                     'rxframe', 'rxcomprsd', 'rxmulti', 'txbytes', 'txpkts',
                     'txerrs', 'txdrop', 'txfifo', 'txcolls', 'txcarrier',
                     'txcomprsd']
            with open(self.target + 'proc/net/dev', 'r') as nfile:
                for line in nfile.readlines():
                    if line.split(':')[0].strip() == device['name']:
                        line = line.split()
                        # Depending on the OS there may or may not be a
                        # space between the device name and the number
                        # of bytes received.
                        if line[0].strip(':') == device['name']:
                            line.pop(0)
                        else:
                            line[0] = line[0].split(':')[1].strip()
                            if line[0] == '':
                                line.pop(0)
                        line = list(map(int, line))
                        x = 0
                        for stat in stats:
                            device[stat] = line[x]
                            x += 1
                        if device['rxbytes'] == '':
                            device['rxbytes'] = 0
            try:
                device['rxgbytes'] = device['rxbytes'] / 1073741824
                device['rxmpkts'] = str(device['rxpkts'] / 1000000) + 'm'
                device['txgbytes'] = device['txbytes'] / 1073741824
                device['txmpkts'] = str(device['txpkts'] / 1000000) + 'm'
                return device
            except Exception as e:
                device['rxgbytes'] = '---'
                device['rxmpkts'] = '---'
                device['txgbytes'] = '---'
                device['txmpkts'] = '---'
                return device
        else:
            return device

    def get_int_driver_info(self, device):
        """ Get driver information for an interface """
        ef = self.target + 'sos_commands/networking/ethtool_-i_'
        ef += device['name']
        if os.path.isfile(ef):
            with open(ef, 'r') as efile:
                for line in efile:
                    if line.startswith('driver'):
                        device['driver'] = line.split(':')[1].strip('\n')
                    elif line.startswith('version'):
                        device['driverversion'] = line.split(
                            ':')[1].strip('\n')
                    elif line.startswith('firmware-version'):
                        device['firmware'] = line.split(
                            ':')[1].strip('\n')
                    else:
                        break
        else:
            device['driver'] = ''
            device['driverversion'] = ''
            device['firmware'] = ''
        return device

    def get_ring_info(self, device):
        """ Get ring information for an interface """
        ef = self.target + 'sos_commands/networking/ethtool_-g_'
        ef += device['name']
        if os.path.isfile(ef):
            if 'bond' in device['name'] or 'vnet' in device['name']:
                for item in ['maxrx', 'maxtx', 'currentrx',
                             'currenttx']:
                    device[item] = '?'
                return device
            with open(ef, 'r') as rfile:
                if 'Operation not supported' in rfile.readline():
                    for item in ['maxrx', 'maxtx', 'currentrx',
                                 'currenttx']:
                        device[item] = '?'
                    return device
                # easiest way to parse this is by line number
                # since it's a fixed output
                for i, line in enumerate(rfile.readlines()):
                    if i == 1:
                        device['maxrx'] = line.split()[1].strip()
                    elif i == 4:
                        device['maxtx'] = line.split()[1].strip()
                    elif i == 6:
                        device['currentrx'] = line.split()[1].strip()
                    elif i == 9:
                        device['currenttx'] = line.split()[1].strip()
            return device
        else:
            for item in ['maxrx', 'maxtx', 'currentrx', 'currenttx']:
                device[item] = '?'
            return device

    def get_ip_addr(self, device):
        """ Get the IP address for an interface """
        # first try the ifcfg-* file
        device['ipaddr'] = ''
        device['hwaddr'] = ''
        device['master'] = ''
        device['mtu'] = ''
        ef = self.target + 'etc/sysconfig/network-scripts/ifcfg-'
        ef += device['name']
        if os.path.isfile(ef):
            with open(ef, 'r') as ifile:
                for line in ifile.readlines():
                    for i in ['IPADDR', 'HWADDR', 'MTU', 'MASTER']:
                        if line.startswith(i):
                            stat = line[line.find('=') + 1:len(line)].replace(
                                '"', '').replace("'", '').strip('\n')
                            device[i.lower()] = stat
            return device
        # if that fails, go to ifconfig -a
        ef = self.target + 'sos_commands/networking/ifconfig_-a'
        ef += device['name']
        if os.path.isfile(ef):
            dev_info = self.parse_output_section(ef, device['name'])
            try:
                if dev_info['inet addr']:
                    device['ipaddr'] = dev_info['inet addr']
                    return device
            except:
                return device
        # if that fails try ip_address which may or may not be present
        ef = self.target + 'sos_commands/networking/ip_address'
        if os.path.isfile(ef):
            with open(ef, 'r') as ifile:
                for n, line in enumerate(ifile):
                    if device['name'] in line:
                        for i in range(3):
                            line = next(ifile)
                            if 'inet ' in line:
                                ip = line[line.find('inet') + 4:
                                          line.find('/')].strip()
                                device['ipaddr'] = ip
                            if 'link/ether' in line:
                                mac = line.split()[1]
                                device['hwaddr'] = mac
            return device
        # if we reach this point, we can't reliably determine the IP
        return device

    def get_bond_int_info(self, bond):
        """ Get bond information from /proc/net/bonding/ """
        bond['slaves'] = []
        bond['failures'] = []
        bond['macaddrs'] = []
        bond['mode'] = ''
        bond['bondingopts'] = ''
        pbf = self.target + 'proc/net/bonding/' + bond['name']
        if os.path.isfile(pbf):
            with open(pbf, 'r') as bfile:
                for line in bfile.readlines():
                    if line.startswith('Bonding Mode:'):
                        mode = line[line.find(':') + 2:
                                    line.find('(') - 1].strip('\n')
                        if 'IEEE 802.3ad' in mode:
                            mode = '802.3ad (LACP)'
                        bond['mode'] = mode
                    elif line.startswith('Primary Slave'):
                        bond['primary'] = line[line.find(':') + 2:
                                               len(line)].strip('\n')
                    elif line.startswith('Currently Active Slave:'):
                        bond['active'] = line[line.find(':') + 2:
                                              len(line)].strip('\n')
                    elif line.startswith('Slave Interface:'):
                        slave = line[line.find(':') + 2:
                                     len(line)].strip('\n')
                        try:
                            if slave == bond['active']:
                                slave = slave + '*'
                        except:
                            pass
                        bond['slaves'].append(slave)
                    elif line.startswith('Link Failure Count:'):
                        bond['failures'].append(line[line.find(':') + 2:
                                                     len(line)].strip('\n'))
                    elif line.startswith('Permanent HW addr:'):
                        bond['macaddrs'].append(line[
                            line.find(':') + 2:len(line)].strip('\n'))

        ibf = '%setc/sysconfig/network-scripts/ifcfg-%s' % (self.target,
                                                            bond['name']
                                                            )
        if os.path.isfile(ibf):
            with open(ibf, 'r') as bfile:
                for line in bfile.readlines():
                    if line.startswith('BONDING_OPTS'):
                        l = line[line.find('=') + 1:len(line)].replace(
                                '"', '').replace("'", '').strip('\n')
                        bond['bondingopts'] = l
                        break

        for attr in ['linkdetected', 'autonegotiation']:
            if not hasattr(bond, attr):
                bond[attr] = '---'

        if bond['slaves']:
            bond['slaves'] = ' '.join(s for s in bond['slaves'])
        else:
            bond['slaves'] = ''

        return bond
