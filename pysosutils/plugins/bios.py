import sys
import os
import re
from pysosutils.utilities.plugin import Plugin
from cpu import cpu


class bios(Plugin):

    def parse(self):
        if self.dmifile:
            self.report_bios()
        else:
            self.pprint.bred("No dmidecode file present")

    @property
    def dmifile(self):
        if os.path.isfile(self.target + 'sos_commands/hardware/dmidecode'):
            return self.target + 'sos_commands/hardware/dmidecode'
        else:
            return False

    def _parse_dmi(self, section):
        """
        Parse the given dmidecode file and then parse out
        the section specified by the 'section' arg.

        The results are then returned as a dictionary
        """
        return self.get_section_content(
                                    self.dmifile,
                                    section
                                )

    def report_bios(self):
        self.pprint.bsection('BIOS')
        r = ['BIOS', 'Processor', 'System', 'DIMM']
        i = {}
        i['BIOS'] = ['Vendor', 'Version', 'Release Date']
        i['System'] = ['Manufacturer', 'Product Name', 'UUID', 'Serial Number']
        i['Processor'] = ['vendor', 'model', 'processors', 'cores', 'sockets']
        i['DIMM'] = ['ALL']
        for s in r:
            self.print_info_for_section(s, i[s])

    def print_info_for_section(self, section, props):
        info = getattr(self, 'get_%s_info' % section.lower())()
        if info:
            self.pprint.bheader('\t%s' % section)
            if 'ALL' in props:
                props = [k for k in info.keys()]
                props.remove('extra')
            for prop in props:
                propn = prop[0].upper() + prop[1:]
                if info[prop]:
                    self.pprint.bblue('\t\t{:15} : '.format(propn),
                                      str(info[prop])
                                      )
            if 'extra' in info:
                    self.pprint.white('\t\t%s' % info['extra'])

    def get_processor_info(self):
        cinfo = cpu(self.target, self.options).get_cpu_info()
        cinfo['extra'] = '{} sockets - {} cores - {} threads per core'.format(
            cinfo['sockets'], cinfo['cores'], cinfo['threadspercore'])
        return cinfo

    def get_system_info(self):
        return self._parse_dmi('System Information')

    def get_bios_info(self):
        return self._parse_dmi('BIOS Information')

    def get_dimm_info(self):
        """ Get information about populated and empty dimms.
        We can then also extract memory support data from this
        """
        props = ['Max Memory', 'Total Memory']
        mem_arrays = 0
        dimm_count = 0
        empty_dimms = 0

        dimm = {}
        for prop in props:
            dimm[prop] = 0

        with open(self.dmifile, 'r') as dfile:
            # main iterables that have distinct leading names
            for line in dfile:
                if 'Maximum Capacity:' in line:
                    index = line.find(':')
                    maxmem = line[index + 1:len(line)].strip()
                    if 'GB' in maxmem:
                        dimm['Max Memory'] = int(maxmem.strip('GB'))
                    elif 'TB' in maxmem:
                        dimm['Max Memory'] = int(maxmem.strip('TB')) * 1024
                if 'Number Of Devices:' in line:
                    dimm_count += int(line.split()[3])
                if re.match('\tSize:', line):
                    if 'No Module Installed' in line:
                        empty_dimms += 1
                    else:
                        size = int(line.split()[1])
                        dimm['Total Memory'] += size
                if 'Physical Memory Array' in line:
                    mem_arrays += 1

        dimm['Max Memory'] = dimm['Max Memory'] * mem_arrays
        used = dimm_count - empty_dimms
        dimm['Slots'] = '{} of {} DIMMs populated'.format(used, dimm_count)
        dimm['Total Memory'] = str(dimm['Total Memory'] / 1024) + '  GB'
        dimm['extra'] = '{} controllers - {} GB max per controller'.format(
            mem_arrays, dimm['Max Memory'] / mem_arrays)
        dimm['Max Memory'] = str(dimm['Max Memory']) + ' GB'
        return dimm
