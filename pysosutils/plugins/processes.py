import os
import operator
from pysosutils.utilities.plugin import Plugin


class processes(Plugin):
    '''Process information'''

    def parse(self):
        self.ps_info = self.parse_proc_file()
        if self.ps_info:
            self.pprint.bsection('Processes')
            self.pprint.white('\tTotal Running Processes:',
                              ' %s' % self.num_procs
                              )
            self.get_user_totals()
            self.display_top_users()
            self.display_defunct_procs()
            self.display_top_procs()

    def parse_proc_file(self):
        '''Parse through a ps output file and return the contents as a list
        of dicts where each dict is a process.'''
        if os.path.isfile(
                self.target + 'sos_commands/process/ps_auxwww'):
            ps_info = []
            stats = ['user', 'pid', 'cpu', 'mem', 'vsz', 'rss',
                     'tty', 'stat', 'start', 'time']
            with open(self.target +
                      'sos_commands/process/ps_auxwww', 'r') as psfile:
                next(psfile)
                for line in psfile:
                    proc = {}
                    line = line.split()
                    try:
                        for x, stat in enumerate(stats):
                            proc[stat] = line[x]
                        proc['command'] = ' '.join(line[10:-1])[:100]
                        proc['shortcmd'] = proc['command'].split()[0]
                        proc['rssmb'] = int(proc['rss']) / 1024
                        ps_info.append(proc)
                    except Exception as e:
                        pass
            return ps_info
        else:
            return False

    @property
    def num_procs(self):
        '''Returns the total number of current processes'''
        return len(self.ps_info)

    def get_user_totals(self):
        '''Returns a sorted list of top consuming users'''
        top = []
        users = {}
        for proc in self.ps_info:
            if proc['user'] in users:
                for x in ['cpu', 'mem', 'rssmb', 'vsz']:
                    users[proc['user']][x] += float(proc[x])
            else:
                new_user = {}
                new_user['user'] = proc['user']
                for x in ['cpu', 'mem', 'rssmb', 'vsz']:
                    new_user[x] = float(proc[x])
                users[proc['user']] = new_user

        for user in users:
            top.append(users[user])

        self.user_report = top

    def get_defunct_procs(self):
        '''Get a list of all defunct or uninterruptible processess'''
        defunct = []
        for proc in self.ps_info:
            if ('<defunct>' in proc['command'] or
                    'D' in proc['stat'] or 'Ds' in proc['stat']):
                defunct.append(proc)
        return defunct

    def get_sorted_user_report(self, sort_by):
        '''Get a report on usage by user sorted by a metric'''

        return sorted(self.user_report, reverse=True, key=lambda x: x[sort_by])

    def get_top_by_metric(self, metric):
        '''Returns a sorted list of processes by a given metric'''
        return sorted(self.ps_info, reverse=True, key=lambda x: x[metric])

    def display_defunct_procs(self):
        '''If needed, display the defunct processess'''
        defunct = self.get_defunct_procs()
        if defunct:
            self.pprint.bred(
                '\tUninterruptable Sleep and Defunct Processes : ')
            keys = ['user', 'pid', 'cpu', 'mem', 'rssmb', 'tty', 'stat',
                    'time', 'command'
                    ]
            header = ['User', 'PID', '%CPU ', '%MEM ', 'RSS-MB', 'TTY',
                      'STAT', 'TIME', 'Command'
                      ]
            tbl = self.format_as_table(defunct,
                                       keys,
                                       header,
                                       x,
                                       True
                                       )
            self.display_table(tbl, 5, 'BBLUE', '\t\t ')

    def display_top_users(self):
        '''Displays the top consuming users ordered by CPU usage'''
        self.pprint.white('\n\tTop Users of CPU:')
        keys = ['user', 'cpu', 'mem', 'rssmb']
        header = ['User', 'CPU', 'Memory', 'RSS(MB)']
        tbl = self.format_as_table(self.get_sorted_user_report('cpu'),
                                   keys,
                                   header,
                                   'cpu',
                                   True
                                   )
        self.display_table(tbl, 5, 'BBLUE', '\t\t ')

    def display_top_procs(self):
        '''Displays the top processes for cpu and memory consumption'''
        for x in ['cpu', 'mem']:
            self.pprint.white('\n\tTop usage processes of %s: ' % x.upper())
            keys = ['user', 'pid', 'cpu', 'mem', 'rssmb', 'tty', 'stat',
                    'time', 'command'
                    ]
            header = ['User', 'PID', '%CPU ', '%MEM ', 'RSS-MB', 'TTY',
                      'STAT', 'TIME', 'Command'
                      ]
            tbl = self.format_as_table(self.get_top_by_metric(x),
                                       keys,
                                       header,
                                       x,
                                       True
                                       )
            self.display_table(tbl, 5, 'BBLUE', '\t\t ')
