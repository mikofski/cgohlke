#! /usr/bin/env python

from bs4 import BeautifulSoup
import requests
import re
import argparse
import os
import sys
import platform
import pprint
import csv
import logging

# basic logging configuration
LOG_FMT = '[%(levelname)s] (%(asctime)-10s) %(message)s'
logging.basicConfig(level=logging.DEBUG, format=LOG_FMT)

PATTERN = 'javascript:dl\(\[(?P<ml>\d+(?:,\d+)+)\], "(?P<mi>.+)"'
CGOHLKE_URL = 'http://www.lfd.uci.edu/~gohlke/pythonlibs/'
VERSION = '0.1'
BUILD_DIR = os.path.expanduser(os.path.join('~', '.cgohlke'))
BUILD_LOG = os.path.join(BUILD_DIR, 'cgohlke.log')
PYVERSION = 'py%d.%d' % (sys.version_info.major, sys.version_info.minor)
WIN_AMD64 = 'win-amd64'
WIN32 = 'win32'
MACHINE = WIN_AMD64 if platform.machine() == 'AMD64' else WIN32

if not os.path.exists(BUILD_DIR):
    os.mkdir(BUILD_DIR)

def decode_link(encoded_link):
    ml = [int(i) for i in encoded_link['ml'].split(',')]
    mi = encoded_link['mi']
    mi = mi.replace('&lt;','<')
    mi = mi.replace('&gt;','>')
    mi = mi.replace('&amp;','&')
    ot = ''
    for j in mi:
        ot += chr(ml[ord(j) - 48])
    return ot

    
def get_cgohlke_pkgs(cgohlke_url=CGOHLKE_URL):
    r = requests.get(cgohlke_url)
    soup = BeautifulSoup(r.content)
    index = [item.contents[0].string for item in soup.ol.contents[3::2]]
    index.append(u'uncategorized')
    pkgs = dict.fromkeys(index)
    for item in soup.find_all('a'):
        grp = item.get('id')
        if grp and grp in index:
            pkgs[grp] = []
            #print 'group: %s' % grp
            for subitem in item.parent.find_all('a'):
                onclick_event = subitem.get('onclick')
                if onclick_event:
                    pkg = {}
                    group = subitem.parent.parent.parent.contents[0]['id']
                    #assert group == grp
                    fullname = subitem.string[:-4].replace(u'\u2011', '-')
                    pkg['fullname'] = fullname
                    name, pyversion = fullname.rsplit('-', 1)
                    name, machine = name.rsplit('.', 1)
                    name, version = name.rsplit('-', 1)
                    #print 'package: %s' % pkg['fullname']
                    pkg['name'] = name
                    pkg['version'] = version
                    pkg['machine'] = machine
                    pkg['pyversion'] = pyversion
                    encoded_link = re.match(PATTERN, onclick_event).groupdict()
                    pkg['link'] = decode_link(encoded_link)
                    pkgs[group].append(pkg)
    return pkgs

PKGS = get_cgohlke_pkgs()

def search(pkgs):
    print 'search results:'
    for pkg, _ in pkgs:
        if pkg not in PKGS:
            continue
        pprint.pprint(PKGS[pkg])


def install(pkgs):
    for pkg in pkgs:
        if len(pkg) == 2:
            pkg, ver = pkg
        else:
            pkg = pkg[0]
            ver = None
        if pkg not in PKGS:
            continue
        if ver:
            pyvers = [(p['machine'], p['pyversion'], p['version']) for p in PKGS[pkg]]
            idx = pyvers.index((MACHINE, PYVERSION, ver))
        else:
            pyvers = [(p['machine'], p['pyversion']) for p in PKGS[pkg]]
            idx = pyvers.index((MACHINE, PYVERSION))
        logging.debug('packages:\n%s', pyvers)
        link = CGOHLKE_URL + PKGS[pkg][idx]['link']
        filename = PKGS[pkg][idx]['fullname'] + '.exe'
        if os.path.exists(os.path.join(BUILD_DIR, filename)):
            logging.debug('file already exists: %s', filename)
            return
        logging.debug('downloading package: %s', link)
        r = requests.get(link, headers={'User-Agent': 'Mozilla/5.0'}, stream=True)
        if r.ok:
            with open(os.path.join(BUILD_DIR, filename), 'wb') as f:
                f.write(r.content)
        r.close()


def init_log(*args):
    files = os.listdir(os.path.expanduser(BUILD_DIR))
    pkgs = [os.path.join(BUILD_DIR, f).replace('C:/','/c/').replace('C:\\','/c/').replace('c:/','/c/').replace('c:\\','/c/').replace('\\','/') for f in files if f.endswith('.exe')]
    with open(BUILD_LOG, 'w') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter='\n')
        spamwriter.writerow(pkgs)
    logging.debug('(re)initialized log: %s', BUILD_LOG)


if __name__ == '__main__':
    # parse the input arguments from the command line, defaults are None
    parser = argparse.ArgumentParser(prog='cgohlke',
                                     description='install cgohlke python libs',
                                     epilog='Mark Mikofski, copyright (c) 2014')
    # show version info
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s-%(version)s' %
                        {"prog": parser.prog, "version": VERSION})
    parser.set_defaults(pkgs='')
    subparsers = parser.add_subparsers(help='sub-command help')
    # create the parser for the "search" command
    parser_search = subparsers.add_parser('search', help='search for package')
    parser_search.add_argument('pkgs', nargs='+', help='name of package to find')
    parser_search.set_defaults(func=search)
    # create the parser for the "install" command
    parser_install = subparsers.add_parser('install', help='install package')
    parser_install.add_argument('pkgs', nargs='+', help='name of package to install')
    parser_install.set_defaults(func=install)
    # create the parser for the "init" command
    parser_init = subparsers.add_parser('init', help='(re)initialize log')
    parser_init.set_defaults(func=init_log)
    args = parser.parse_args()  # parse arguments
    pkgs = [re.split('==|>=', pkg) for pkg in args.pkgs]
    logging.debug('args: %s', args)
    logging.debug('packages: %s', pkgs)
    args.func(pkgs)
