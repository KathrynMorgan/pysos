import datetime
import os
import re
from pysosutils.utilities.color import Colors as c
from operator import itemgetter
from collections import OrderedDict

class Plugin():

    def __init__(self, target, args):
        self.options = {}
        self.target = target
        for opt, value in args.iteritems():
            self.options[opt] = value
        colors = c()
        self.pprint = colors
        self.color = colors.colors
        self.parse_failed = False

    def runtests(self, verbose):
        '''Runs all tests in a plugin. Methods must start with run_

        If a test should be run even if a plugin's parse() fails, then
        pass run_if_failed=True to the test method'''
        try:
            t = self.tests(self.target)
            t.verbose = verbose
            for i in dir(t):
                result = getattr(t, i)
                if self.parse_failed == False:
                    if i.startswith('run_') and hasattr(result, '__call__'):
                        result()
                else:
                    if i.startswith('run_') and hasattr(result, '__call__'):
                        if 'run_if_failed' in result.func_code.co_varnames:
                            result()
            t.report_tests()
        except:
            pass

    def file_to_string(self, filepath):
        '''For single line files, read the file in and return
        contents as a string.
        '''
        try:
            with open(filepath, 'r') as f:
                return f.readline().strip('\n')
        except IOError:
            return 'Not Found'

    def file_to_dict(self, filepath):
        '''For multi-line files, each line becomes a dict entry with the
        first word as the key'''
        try:
            fdict = {}
            with open(self.target + filepath, 'r') as f:
                for line in f:
                    fdict[line.split()[0].strip(':').lower()] = line.split()[1]
            return fdict
        except IOError:
            return False

    def get_cmdline(self):
        ''' Get the booted kernel cmdline options '''
        return self.file_to_string(self.target + 'proc/cmdline')

    def get_runlevel(self):
        ''' Get the _current_ runlevel '''
        return self.file_to_string(self.target +
                                       'sos_commands/startup/runlevel')

    def get_release(self):
        ''' Get the OS release '''
        return self.file_to_string(self.target + 'etc/redhat-release')

    def get_kernel(self):
        ''' Get the booted kernel version '''
        uname = self.file_to_string(self.target + 'sos_commands/kernel/uname_-a')
        return uname.split()[2]

    def get_hostname(self):
        ''' Get the hostname of the system '''
        return self.file_to_string(self.target +
                                'sos_commands/general/hostname')

    def get_sos_date(self):
        ''' Get time of when sosreport was run '''
        return self.file_to_string(self.target + 'date')

    def get_uptime(self):
        ''' Get and format system uptime into a readable string '''
        uptime = ''
        u = self.file_to_string(self.target + 'sos_commands/general/uptime')
        if 'not found' in u:
            return u
        up_string = u[u.find('up') + 2:u.find('user') - 3].strip().strip(',')
        if 'min' in up_string:
            return up_string
        elif ':' in u:
            days = up_string[0:up_string.find('day')].strip().strip(',')
            uptime += days + ' days'
            hours = up_string[up_string.find('day') + 4:
                             up_string.find(':')].strip().strip(',')
            uptime += hours + ' hours'
            minutes = up_string[up_string.find(':') + 1:
                               len(up_string)].strip()
            uptime += ' ' + minutes + ' minutes'
        return uptime

    def get_uname(self):
        ''' Get contents of uname_-a '''
        return self.file_to_string(self.target + 'sos_commands/kernel/uname_-a')

    def get_load_avg(self):
        ''' Get reported loadavg at time of sosreport '''
        uptime = self.file_to_string(self.target + 'sos_commands/general/uptime')
        index = uptime.find('e:')
        loads = uptime[index + 2:len(uptime)].split(',')
        return loads

    def get_sysctl(self, sysctl):
        ''' Get the value of a specific sysctl'''
        if os.path.isfile(self.target + 'sos_commands/kernel/sysctl_-a'):
            with open(self.target + 'sos_commands/kernel/sysctl_-a', 'r') as sfile:
                for line in sfile:
                    if line.startswith(sysctl):
                        return line.split()[2]
        else:
            return False

    def get_sysctls(self, sysctl):
        ''' Get all sysctls matching a given string'''
        sysctls = {}
        if os.path.isfile(self.target + 'sos_commands/kernel/sysctl_-a'):
            with open(self.target + 'sos_commands/kernel/sysctl_-a',
                      'r') as sysfile:
                for line in sysfile:
                    if sysctl in line:
                        name = line.split()[0]
                        value = line.split()[2]
                        sysctls[name] = value
        else:
            sysctls = False
        return sysctls

    def get_all_sysctls(self):
        pass

    def get_selinux(self):
        ''' Get the current and configured SELinux setting '''
        se_status = {}
        if os.path.isfile(self.target + 'sos_commands/selinux/sestatus_-b'):
            with open(self.target + 'sos_commands/selinux/sestatus_-b',
                      'r') as sfile:
                for i, line in enumerate(sfile):
                    index = line.find(':')
                    if line.startswith('SELinux status'):
                        se_status['status'] = line[index + 1:
                                                   len(line)].strip()
                        if se_status['status'] == 'disabled':
                            se_status['current'] = 'disabled'
                            se_status['config'] = 'disabled'
                            break
                    elif line.startswith('Current'):
                        se_status['current'] = line[index + 1:
                                                    len(line)].strip()
                    elif line.startswith('Mode'):
                        se_status['config'] = line[index + 1:
                                                   len(line)].strip()
                    elif i > 6:
                        break
        else:
            se_status['current'] = 'Not Found'
            se_status['config'] = 'Not Found'
        return se_status

    def get_proc_stat(self):
        ''' Get boottime, number of processes and running procs '''
        ps = self.file_to_dict('proc/stat')
        ps['boot time'] = datetime.datetime.fromtimestamp(
                                            int(ps['btime'])).strftime(
                                            '%a %b %d %H:%M:%S UTC %Y'
                                            )
        return ps

    def get_rpm(self, rpm, match_all=False):
        '''
        Get details on a given rpm.
    
        Boolean option can be used to see if rpm is installed or not.
        '''
        rpms = []
        if os.path.isfile(self.target + 'installed-rpms'):
            with open(self.target + 'installed-rpms', 'r') as rfile:
                for line in rfile:
                    if not match_all:
                        if line.split('.', 1)[0][:-2] == rpm:
                            index = line.find('.')
                            this_rpm = line[0:index - 2]
                            rpms.append(line.split()[0])
                            break
                    else:
                        if rpm in line.split('.', 1)[0][:-2]:
                            index = line.find('.')
                            this_rpm = line[0:index - 2]
                            rpms.append(line.split()[0])
        if len(rpms) == 0:
                rpms.append("Not Installed")
        return rpms

    def get_all_packages(self):
        pkgs = []
        if os.path.isfile(self.target + 'installed-rpms'):
            with open(self.target + 'installed-rpms', 'r') as rfile:
                for line in rfile:
                    pkgs.append(line.split()[0])
        return pkgs

    def is_installed(self, pkgnames):
        '''Simple check if a given package is installed.
        Returns only True or False'''
        if isinstance(pkgnames, str):
            pkgnames = [pkgnames]
        if os.path.isfile(self.target + 'installed-rpms'):
            with open(self.target + 'installed-rpms', 'r') as rfile:
                for line in rfile:
                    for pkg in pkgnames:
                        if line.startswith(pkg):
                            return True
        return False

    def get_rpm_version(self, rpm):
        ''' Get _just_ the version of a given RPM '''
        ver = self.get_rpm(rpm)[0]
        if 'Not Installed' in ver:
            return False
        else:
            formatVer = ver.strip(rpm).strip('x86_64').strip(
                'noarch').strip('-').strip('.')
            return formatVer

    def get_sysctl(self, sysctl):
        ''' Get the setting for a given sysctl '''
        sysctls = {}
        if os.path.isfile(self.target + 'sos_commands/kernel/sysctl_-a'):
            with open(self.target + 'sos_commands/kernel/sysctl_-a',
                      'r') as sysfile:
                for line in sysfile:
                    if sysctl in line:
                        name = line.split()[0]
                        value = line.split()[2]
                        sysctls[name] = value
        else:
            sysctls = "No sysctl_-a file to parse"
        return sysctls

    def get_nic_info(self, interface):
        '''Returns a single dict for given interface'''
        if hasattr(self, 'nics'):
            try:
                return self.nics[interface]
            except KeyError:
                return False
        else:
            self.get_nics()
        if self.nics:
            return self.nics[interface]
        return False

    def get_nics(self):
        '''Returns dict of nics, whereby the key is the nic name and
        the value is a dict of info about that nic
        '''
        # TODO: make this OS independent. Will likely need to set some
        # class vars based on OS though.
        self.nics = {}
        netfile = self.target + 'sos_commands/networking/ip_address'
        with open(netfile, 'r') as nfile:
            raw = nfile.read()
            niclist = re.split('\n\d: ', re.split('^\d: ', raw)[1])
            for nic in niclist:
                n = {}
                for i in [
                    'inet',
                    'inet6',
                    'link/ether']:
                    try:
                        n[i] = re.split(i, nic)[1].split()[0]
                    except:
                        pass
                name = nic.split()[0].strip(':')
                self.nics[name] = n
        return self.nics

    def get_enablement(self, service):
        '''
        Check the current service configuration from chkconfig.
    
        TO DO: expand to systemd.
        '''
        if os.path.isfile(self.target + 'chkconfig'):
            with open(self.target + 'chkconfig', 'r') as cfile:
                for line in cfile:
                    if service in line:
                        service_status = line.lstrip(service).rstrip(
                            '\n').lstrip()
                        return service_status
            return "Service not found in chkconfig"
        else:
            return "No chkconfig file found"
    
    def get_selinux(self):
        ''' Get the current and configured SELinux setting '''
        sel_status = {}
        if os.path.isfile(self.target + 'sos_commands/selinux/sestatus_-b'):
            with open(self.target + 'sos_commands/selinux/sestatus_-b',
                      'r') as sfile:
                for i, line in enumerate(sfile):
                    index = line.find(':')
                    if line.startswith('SELinux status'):
                        sel_status['status'] = line[index + 1:
                                                   len(line)].strip()
                        if sel_status['status'] == 'disabled':
                            sel_status['current'] = 'disabled'
                            sel_status['config'] = 'disabled'
                            break
                    elif line.startswith('Current'):
                        sel_status['current'] = line[index + 1:
                                                    len(line)].strip()
                    elif line.startswith('Mode'):
                        sel_status['config'] = line[index + 1:
                                                   len(line)].strip()
                    elif i > 6:
                        break
        else:
            sel_status['current'] = 'Not Found'
            sel_status['config'] = 'Not Found'
        return sel_status

    def get_section_content(self, fname, start, end='$'):
        '''
        Given a filename (fname) and a section header, parse the file
        and then return all content between the section header and
        a new line, signifying the end of the section.
        '''
        if os.path.isfile(self.target + fname):
            with open(self.target + fname, 'r') as pfile:
                handle_regex = re.compile('^%s\s' % start)
                newline = re.compile('^%s'% end)
                lines = pfile.readlines()
                for x in range(0, len(lines)):
                    line = lines[x]
                    if handle_regex.findall(line):
                        # Found header for section
                        sectionInfo = {}
                        sectionInfo['info'] = []
                        while True:
                            try:
                                line = lines[x + 1]
                        # repeat until we hit newline
                                if not newline.findall(line):
                                    sectionInfo['info'].append(line.strip(
                                    ).strip('\t'))
                                    x += 1
                                else:
                                    break
                            except:
                                break
                        info = {}
                        for item in sectionInfo['info']:
                            try:
                                key = item.split(':')[0]
                                value = item.split(':')[1]
                                info[key] = value.strip()
                            except:
                                pass
            try:
                return info
            except UnboundLocalError:
                return False
        else:
            return False


    def format_as_table(self, data, keys, header=None, sort_by_key=None,
                        sort_order_reverse=False):
        '''Takes a list of dictionaries, formats the data, and returns
        the formatted data as a text table.
    
        Required Parameters:
            data - Data to process (list of dictionaries). (Type: List)
            keys - List of keys in the dictionary. (Type: List)
    
        Optional Parameters:
            header - The table header. (Type: List)
            sort_by_key - The key to sort by. (Type: String)
            sort_order_reverse - Default sort order is ascending, if
                True sort order will change to descending. (Type: Boolean)
        '''
        # Sort the data if a sort key is specified (default sort order
        # is ascending)

        if sort_by_key:
            data = sorted(data,
                          key=itemgetter(sort_by_key),
                          reverse=sort_order_reverse)
        # If header is not empty, add header to data
        if header:
            # Get the length of each header and create a divider based
            # on that length
            header_divider = []
            for name in header:
                header_divider.append('-' * len(name))

            # Create a list of dictionary from the keys and the header and
            # insert it at the beginning of the list. Do the same for the
            # divider and insert below the header.
            header_divider = dict(zip(keys, header_divider))
            data.insert(0, header_divider)
            header = dict(zip(keys, header))
            data.insert(0, header)

        column_widths = []
        for key in keys:
            column_widths.append(max(len(str(column[key])) for column in data))
        # Create a tuple pair of key and the associated column width for it
        key_width_pair = zip(keys, column_widths)

        format = ('%-*s ' * len(keys)).strip() + '\n'
        formatted_data = ''
        for element in data:
            data_to_format = []
            # Create a tuple that will be used for the formatting in
            # width, value format
            for pair in key_width_pair:
                data_to_format.append(pair[1])
                data_to_format.append(element[pair[0]])
            formatted_data += format % tuple(data_to_format)
        try:
            data.pop(0)
            data.pop(0)
        except:
            pass
        return formatted_data

    def display_table(self, tbl, count=0, color=None, indent='', no_header=False):
        if count > 0:
            count +=2
        header = tbl.splitlines()[:2]
        if not no_header:
            for x in header:
                if color:
                    if color in self.color:
                        print indent + self.color[color] + x.strip() + self.color['ENDC']
                    else:
                        print indent + x.strip()
                else:
                    print indent + x.strip()
        if not count:
            for line in tbl.splitlines()[2:]:
                print indent + line.strip()
        else:
            for line in tbl.splitlines()[2:count]:
                print indent + line.strip()
        return True

    def _get_taints(self):
        with open(self.target + 'proc/sys/kernel/tainted', 'r') as tfile:
            check = tfile.read().splitlines()
            return int(check[0])

    def get_taints(self):
        '''
        Get the current taint state of the kernel and return a
        description of the code along with the numerical code.
        '''
        t = OrderedDict()
        t['536870912'] = "Technology Preview code is loaded"
        t['268435456'] = "Hardware is unsupported"
        t['134217728'] = "Taint by Zombie"
        t['32768'] = "The kernel has been live patched"
        t['16384'] = "A soft lockup has previously occurred on the system."
        t['8192'] = ("An unsigned module has been loaded in a kernel"
                    " supporting module signature")
        t['4096'] = "Out-of-tree module has been loaded"
        t['2048'] = "Working around severe firmware bug"
        t['1024'] = "Modules from drivers/staging are loaded"
        t['512'] = "Kernel warning occurred"
        t['256'] = "ACPI table overridden"
        t['128'] = "Kernel has oopsed before"
        t['64'] = "Unsigned kernel modules"
        t['32'] = "System has hit bad_page"
        t['16'] = "System experienced a machine check exception"
        t['8'] = "User forced a module unload"
        t['4'] = "SMP with CPUs not designed for SMP"
        t['2'] = "Module has been forcibly loaded"
        t['1'] = "Proprietary module has been loaded"
        t['0'] = "Not tainted. Hooray!"

        check = self._get_taints()
        taint_codes = []
        for key in t:
            cval = check - int(key)
            if cval > -1:
                taint_codes.append(('%4s - ' % (key) + t[key]).strip('\n'))
                check = check - int(key)
                if check == 0:
                    return taint_codes
            else:
                pass
        # we should only hit this if we have an undefined taint code
        taint_codes.append("Undefined taint code: %s" % self._get_taints() )
        return taint_codes

    def print_header_values(self, info, headers=None, key=None):
        ''' Takes info as a dict, and then prints each item in a standard
        fashion of 'key : value'. 
        
        Optionally, supply headers as a list to only print those keys
        '''
        if headers is None:
            for i in info:
                if not isinstance(info[i], dict):
                    self.pprint.bheader('\t{:20s} : '.format(i.title()), info[i])
                else:
                    self.pprint.bheader('\t{:20s} : '.format(i.title()), info[i][key])
        else:
            for i in info:
                if i in headers:
                    if isinstance(info[i], list):
                        if len(info[i]) == 1:
                            self.pprint.bheader('\t{:20s} : '.format(i.title()), info[i][0])
                        else:
                            self.pprint.bheader('\t{:20s} : '.format(i.title()), info[i][0])
                            info[i].pop(0)
                            for l in  info[i]:
                                self.pprint.bheader('\t{:20s} : '.format(' '), l)
                    elif isinstance(info[i], dict):
                        self.pprint.bheader('\t{:20s} : '.format(i.title()), info[i][key])
                    else:
                        self.pprint.bheader('\t{:20s} : '.format(i.title()), str(info[i]))


    def parse_output_section(self, fname, section):
        """
        Given a filename (fname) and a section header, parse the file
        and then return all content between the section header and
        a new line, signifying the end of the section.
        """
        if os.path.isfile(fname):
            with open(fname, 'r') as pfile:
                handle_regex = re.compile('^%s\s' % section)
                newline = re.compile('^$')
                lines = pfile.readlines()
                for x in range(0, len(lines)):
                    line = lines[x]
                    if handle_regex.findall(line):
                        # Found header for section
                        section_info = {}
                        section_info['info'] = []
                        while True:
                            try:
                                line = lines[x + 1]
                        # repeat until we hit newline
                                if not newline.findall(line):
                                    section_info['info'].append(line.strip(
                                    ).strip('\t'))
                                    x += 1
                                else:
                                    break
                            except:
                                break
                        info = {}
                        for item in section_info['info']:
                            try:
                                key = item.split(':')[0]
                                value = item.split(':')[1]
                                info[key] = value.strip()
                            except:
                                pass
            try:
                return info
            except UnboundLocalError:
                return False
        else:
            return False
