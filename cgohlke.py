#! /usr/bin/env python

from bs4 import BeautifulSoup
import requests
import re
import argparse
import os
import sys
import platform
from urllib import urlretrieve
import pprint

PATTERN = 'javascript:dl\(\[(?P<ml>\d+(?:,\d+)+)\], "(?P<mi>.+)"'
CGOHLKE_URL = 'http://www.lfd.uci.edu/~gohlke/pythonlibs/'
VERSION = '0.1'
BUILD_DIR = os.path.expanduser(os.path.join('~','.cgohlke'))
PYVERSION = 'py%d.%d' % (sys.version_info.major, sys.version_info.minor)
WIN_AMD64 = 'win-amd64'
WIN32 = 'win32'
MACHINE = WIN_AMD64 if platform.machine() == 'AMD64' else WIN32


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
            pkg = {}
            for subitem in item.parent.find_all('a'):
                onclick_event = subitem.get('onclick')
                if onclick_event:
                    group = subitem.parent.parent.parent.contents[0]['id']
                    #assert group == grp
                    fullname = subitem.string[:-4].replace(u'\u2011', '-')
                    pkg['fullname'] = fullname
                    name, pyversion = fullname.rsplit('-', 1)
                    name, machine = name.rsplit('.', 1)
                    name, version = name.rsplit('-', 1)
                    #print 'package: %s' % pkg['fullname']
                    pkg['name'] = name
                    if version.endswith(WIN_AMD64):
                        pkg['machine'] = WIN_AMD64
                        pkg['version'] = version[:len(WIN_AMD64)]
                    else:
                        pkg['machine'] = WIN32
                        pkg['version'] = version[:len(WIN32)]
                    pkg['pyversion'] = pyversion
                    encoded_link = re.match(PATTERN, onclick_event).groupdict()
                    pkg['link'] = decode_link(encoded_link)
                    pkgs[group].append(pkg)
    return pkgs

PKGS = get_cgohlke_pkgs()

def search(pkgs):
    print 'search results:'
    for pkg in pkgs:
        if pkg in PKGS:
            pprint.pprint(PKGS[pkg])


def install(pkgs):
    for pkg in pgks:
        if pkg in PKGS:
            pyvers = [(p['machine'], p['pyversion']) for p in pkg]
            idx = pyvers.index((MACHINE, PYVERSION))
            link = pkg[idx]['link']
            filename, headers = urlretrieve(link, os.join(BUILD_DIR, link))
    return filename, headers

if __name__ == '__main__':
    # parse the input arguments from the command line, defaults are None
    parser = argparse.ArgumentParser(prog='cgohlke',
                                     description='install cgohlke python libs',
                                     epilog='Mark Mikofski, copyright (c) 2014')
    # show version info
    parser.add_argument('--version', '-v', action='version',
                        version='%(prog)s-%(version)s' %
                        {"prog": parser.prog, "version": VERSION})
    subparsers = parser.add_subparsers(help='sub-command help')
    # create the parser for the "search" command
    parser_search = subparsers.add_parser('search', help='search for package')
    parser_search.add_argument('pkgs', nargs='+', help='name of package to find')
    parser_search.set_defaults(func=search)
    # create the parser for the "install" command
    parser_install = subparsers.add_parser('install', help='install package')
    parser_install.add_argument('pkgs', nargs='+', help='name of package to install')
    parser_install.set_defaults(func=install)
    args = parser.parse_args()  # parse arguments
    args.func(args.pkgs)
