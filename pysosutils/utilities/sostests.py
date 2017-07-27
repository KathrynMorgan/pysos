import inspect
import os
import sys

from pysosutils.utilities.color import Colors as c
from pysosutils.utilities.plugin import Plugin
from distutils.sysconfig import get_python_lib

class SosTests():
    '''Used to define unit checks for modules'''

    def __init__(self, target):
        self.target = target
        self.passed = []
        self.warned = []
        self.failed = []
        self.pprint = c()
        enabled_for = ()

    def succeed(self, reason='OK'):
        check = {}
        check['name'] = inspect.stack()[1][3].lstrip('run_')
        check['reason'] = reason
        self.passed.append(check)

    def fail(self, reason):
        check = {}
        check['name'] = inspect.stack()[1][3].lstrip('run_')
        check['reason'] = reason
        self.failed.append(check)

    def warn(self, reason):
        check = {}
        check['name'] = inspect.stack()[1][3].lstrip('run_')
        check['reason'] = reason
        self.warned.append(check)

    def return_results(self):
        return {
            'passed': self.passed,
            'warned': self.warned,
            'failed': self.failed
            }

class SosChecker(Plugin):
    '''Loads all tests that are defined for plugins that have been run
    then runs them and reports cummulative results'''

    def __init__(self, target, plugs):
        self.target = target
        self.verbose = plugs['verbose']
        self.plugs = plugs
        self.plugins = [p for p in plugs if plugs[p]]
        self.pprint = c()
        self.packages = self.get_all_packages()

    def run_all_tests(self):
        self.init_enabled_tests()
        res = self.run_enabled_tests()
        self.report_results(res)

    def report_results(self, results):
        self.pprint.bsection('\nTest Results')
        self.pprint.reg('{:10s} {:^10s} {:^14s}  {}\n'.format(
                                                    'Result',
                                                    'Module',
                                                    'Test Name',
                                                    'Reason'
                                                ))
        report = [('warned', 'warn'), ('failed', 'bred')]
        if self.verbose:
            report.insert(0, ('passed', 'bgreen'))
        for i in report:
            l = []
            for k in results:
                if len(results[k][i[0]]) > 0:
                    for j in results[k][i[0]]:
                        l.append((k.replace('tests', ''), j['name'], j['reason']))
            if len(l) > 0:
                p = getattr(self.pprint, i[1])
                p(i[0].capitalize())
                for m in l:
                    p('\t {:>10s}  {:<16s} {}'.format(m[0], m[1], m[2]))

    def run_enabled_tests(self):
        test_results = {}
        for t in self.run_tests:
            t.setup()
            for i in dir(t):
                if i.startswith('run_'):
                    result = getattr(t, i)
                    result()
            test_results[str(t.__module__)] = t.return_results()
        return test_results

    def init_enabled_tests(self):
        self.test = {}
        self.run_tests = []

        if 'pysosutils' not in os.listdir(os.getcwd()):
            p = get_python_lib()
            path = p + '/pysosutils/sostests/'
        else:
            path = 'pysosutils/sostests/'

        sys.path.insert(0, path)
        for f in sorted(os.listdir(path)):
            fname, ext = os.path.splitext(f)
            if ext == '.py':
                mod = __import__(fname)
                class_ = getattr(mod, fname)
                self.test[fname] = class_(self.target)
        sys.path.pop(0)
        for t in self.test:
            try:
                pkgs = self.test[t].enabled_for
                for pkg in pkgs:
                     for p in self.packages:
                         if pkg in p:
                            self.run_tests.append(self.test[t])
                            break
            except:
                pass

