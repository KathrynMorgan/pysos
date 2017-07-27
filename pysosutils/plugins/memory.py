# -*- coding: utf-8 -*-

import os
from pysosutils.utilities.plugin import Plugin


class memory(Plugin):

    def parse(self):
        self.gprops = [
                       ('used', 'blue'),
                       ('cached', 'cyan'),
                       ('in use', 'dblue'),
                       ('buffers', 'purple'),
                       ('swap used', 'white'),
                       ('dirty', 'red'),
                       ('slab', 'gray')
                       ]
        self.props = [
                       'used',
                       'cached',
                       'buffers',
                       'dirty',
                       'active',
                       'inactive',
                       'unevictable',
                    ]
        self.display_mem_info()

    def _graph(self, perc):
        """
        General graphing function to spit out a line graph.
        """
        tick = u'◆'
        empty = u'◇'
        if perc == 0:
            filled = 0
        else:
            filled = round(40 * (perc / 100))
        nofill = 40 - filled
        percf = '%.2f' % perc + ' %'
        graph = tick * int(filled) + empty * int(
            nofill) + '  %7s' % percf
        return graph

    def _display_graph(self, prop, mem=None):
        pprint = getattr(self.pprint, prop[1])
        if mem is None:
            mem = self.mem
        ram = self._fmt_mem(self.mem[prop[0]])

        pprint('\t\t {:10} :   {:>8} {:20}'.format(prop[0].title(),
                                                   ram,
                                                   self.graphs[prop[0]]
                                                   )
               )

    def _fmt_mem(self, mem):
        if mem > 1023:
            return str(round((float(mem) / 1024), 2)) + ' GB'
        else:
            return str(mem) + ' MB'

    def display_mem_info(self):
        self.pprint.bsection('Memory Information')
        self.mem = self.get_mem_info()
        if self.mem:
            self.mem = self.convert_mem_info(self.mem)
            self.graphs = self.get_mem_graphed(self.mem)
            self.pprint.bheader('\t Memory Statistics Graphed')
            for p in self.gprops:
                self._display_graph(p)
            self.pprint.bheader('\n\t Memory Statistics')
            memt = round(self.mem['memtotal'] / 1024, 2)
            meml = '\t\t\t   {:>4.2f} GB total memory on system'.format(memt)
            self.pprint.reg(meml)
            for m in self.props:
                self.display_mem_prop_stat(m)
            if self.mem['swaptotal'] > 0:
                self.display_swap_info()
        else:
            self.pprint.bred('\t\t Could not parse proc/meminfo')
            raise Exception

    def display_swap_info(self):
        self.pprint.bheader('\t Swap Info')
        swapt = self._fmt_mem(self.mem['swaptotal'])
        self.pprint.white('\t\t\t %s total swap on system' % swapt)
        for s in ['swap free', 'swap used']:
            sval = self._fmt_mem(self.mem[s])
            perc = round((self.mem[s] / self.mem['swaptotal']) * 100, 2)
            sline = '{} ({}%) {}'.format(sval, perc, s.title())
            self.pprint.grey('\t\t\t %s' % sline)

    def display_mem_prop_stat(self, memprop):
        mused = float(self.mem[memprop])
        mperc = round((mused / self.mem['memtotal']) * 100, 2)
        if mused > 1023:
            mused = str(round(mused / 1024, 2)) + ' GB'
        else:
            mused = str(round(mused, 2)) + ' MB'
        mline = "{:>9} ({:>6.2f} %) {}".format(mused, mperc, memprop)
        self.pprint.reg('\t\t\t %s' % mline)

    def get_mem_info(self):
        """ Returns the contents of meminfo as a dict and adds values for
        used, swapused and inuse which is used minus cached
        """
        if not os.path.isfile(self.target + 'proc/meminfo'):
            return False
        mem = self.file_to_dict('proc/meminfo')
        for m in mem:
            mem[m] = int(mem[m])
        mem['used'] = mem['memtotal'] - mem['memfree']
        mem['in use'] = mem['used'] - mem['cached']
        mem['swap free'] = mem.pop('swapfree')
        mem['swap used'] = mem['swaptotal'] - mem['swap free']
        return mem

    def convert_mem_info(self, meminfo):
        """ Converts the kB size of meminfo from get_mem_info()
        to MB
        """
        for m in meminfo:
            if 'HugePage' not in m:
                meminfo[m] = round(int(meminfo[m]) / 1024, 2)
        return meminfo

    def get_mem_graphed(self, meminfo=None):
        graphs = {}
        if meminfo is None:
            meminfo = self.get_mem_info()
        for g in self.gprops:
            perc = round((meminfo[g[0]] / meminfo['memtotal']) * 100, 2)
            graphs[g[0]] = self._graph(perc).encode('utf-8')
        return graphs
