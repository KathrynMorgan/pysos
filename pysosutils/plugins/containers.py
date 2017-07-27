import json
import re
import os
import sys
from pysosutils.utilities.plugin import Plugin
from pysosutils.utilities.sostests import SosTests


class containers(Plugin):
    ''' Docker, Rkt, Kubernetes, and Atomic '''

    def parse(self):
        if self.is_atomic:
            self.report_atomic()
        if self.is_docker:
            self.report_docker()
        if self.is_rkt:
            self.report_rkt()
        if self.is_kubernetes:
            self.report_kubernetes()

    def _fmt_node_name(self, node):
        return node.split('=')[2].strip('http://')[0:-2]

    def _parse_json(self, f):
        return json.loads("".join(open(f).readlines()))

    @property
    def is_atomic(self):
        if not os.path.exists(self.target + "etc/redhat-release"):
            return False
        cpe = open(self.target + "etc/redhat-release", "r").readlines()
        return 'Atomic' in cpe[0]

    @property
    def is_docker(self):
        pkgs = [
            'docker',
            'docker-latest',
            'docker-engine',
            'docker-io'
        ]
        return self.is_installed(pkgs)

    @property
    def is_rkt(self):
        return self.is_installed('rkt')

    @property
    def is_kubernetes(self):
        pkgs = [
            'kubernetes',
            'kubernetes-node',
            'kubernetes-master',
            'atomic-openshift'
        ]
        return self.is_installed(pkgs)

    def get_atomic_info(self):
        info = {}
        try:
            af = 'sos_commands/atomichost/atomic_host_status'
            b = self.get_section_content(af, 'Deployments:')
            info['branch'] = b['Version'].split('(')[0]
            info['commit'] = b['Commit']
            return info
        except:
            return False

    def report_atomic(self):
        info = self.get_atomic_info()
        if info:
            self.pprint.section('Atomic Host')
            self.pprint.bheader('Branch', info['branch'])
            self.pprint.bheader('Commit', info['commit'])

    def get_image_list(self):
        try:
            images = []
            with open(self.target +
                      'sos_commands/docker/docker_images') as d:
                for line in d:
                    if line.startswith('Cannot'):
                        break
                    l = line.split()
                    i = {}
                    i['repo'] = l[0]
                    i['tag'] = l[1]
                    i['image'] = l[2]
                    images.append(i)
            return images
        except IOError:
            return False

    def get_docker_info(self):
            try:
                df = self.target + 'sos_commands/docker/docker_info'
                with open(df) as dfile:
                    info = {}
                    for line in dfile:
                        line = line.split(':')
                        try:
                            info[line[0]] = line[1].strip()
                        except:
                            pass
                info['installed'] = self.get_rpm('docker')
                l = [
                    m.string for m in (re.search('docker-latest', l)
                                       for l in info['installed']) if m
                ]
                info['daemon'] = '/usr/bin/docker'
                if l:
                    with open(self.target + 'etc/sysconfig/docker', 'r') as f:
                        for line in f:
                            if 'DOCKERBINARY' in line:
                                info['daemon'] = line.split('=')[1]
                info['images'] = self.get_image_list()
                info['image count'] = len(info['images'])
                pf = self.target + 'sos_commands/docker/docker_ps'
                with open(pf) as pfile:
                    containers = []
                    for line in pfile:
                        if line.startswith('Cannot connect'):
                            break
                        if not line.startswith('CONTAINER'):
                            line = line.split()
                            container = {}
                            container['id'] = line[0]
                            container['image'] = line[1]
                            container['cmd'] = line[2]
                            container['status'] = line[4]
                            container['name'] = line[6]
                            containers.append(container)
                    info['containers'] = containers
                info['running'] = len(info['containers'])
                return info
            except Exception as e:
                return False

    def report_docker(self):
        self.pprint.bsection('Containers')
        info = self.get_docker_info()
        if info:
            self.pprint.section('  Docker')
            # do this twice to maintain order
            header = ['installed', 'daemon']
            self.print_header_values(info, headers=header)
            header = ['image count', 'running']
            self.print_header_values(info, headers=header)
            print '\n'
            if info['containers']:
                self.display_running_containers(info['containers'])
        else:
            self.pprint.bred('\t\t No container information found.')
            raise Exception

    def display_running_containers(self, info):
        keys = ['id', 'image', 'cmd']
        header = ['Name', 'Image', 'Command']
        tbl = self.format_as_table(info, keys, header, 'id', False)
        self.display_table(tbl, color='WHITE', indent='\t\t')

    def get_kubernetes_info(self):
        info = {}
        info['version'] = self.get_rpm('kubernetes')
        if 'Not Installed' in info['version']:
            return False

        kroot = self.target + 'sos_commands/kubernetes/kubectl_get-o_json_'

        # get pods
        for svc in ['pods', 'services', 'replicationController']:
            try:
                info[svc] = self._parse_json(kroot + svc)
            except ValueError:
                info[svc] = False
            except IOError:
                info[svc] = False

        return info

    def report_kubernetes(self):
        info = self.get_kubernetes_info()
        if info:
            self.pprint.section('  Kubernetes')
            self.pprint.bheader('\t Installed', '\n\t\t %s' % info['version'])
