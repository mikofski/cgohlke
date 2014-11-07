#! /usr/bin/env python

from bs4 import BeautifulSoup
import requests
import re
import argparse
import sys

PATTERN = 'javascript:dl\(\[(?P<ml>\d+(?:,\d+)+)\], "(?P<mi>.+)"'
CGOHLKE_URL = 'http://www.lfd.uci.edu/~gohlke/pythonlibs/'
VERSION = '0.1'


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
            print 'group: %s' % grp
            pkg = {}
            for subitem in item.parent.find_all('a'):
                onclick_event = subitem.get('onclick')
                if onclick_event:
                    group = subitem.parent.parent.parent.contents[0]['id']
                    assert group == grp
                    fullname = subitem.string[:-4]
                    name, version, pyversion = fullname.rsplit(u'\u2011', 2)
                    pkg['fullname'] = fullname.replace(u'\u2011', '-')
                    print 'package: %s' % pkg['fullname']
                    pkg['name'] = name
                    pkg['version'] = version
                    pkg['pyversion'] = pyversion
                    encoded_link = re.match(PATTERN, onclick_event).groupdict()
                    pkg['link'] = decode_link(encoded_link)
                    pkgs[group].append(pkg)
    return pkgs


if __name__ == '__main__':
    # parse the input arguments from the command line, defaults are None
    parser = argparse.ArgumentParser(description='install cgohlke python libs',
                                     epilog='Mark Mikofski, copyright (c) 2014')
    # show version info
    parser.add_argument('--version', '-v', action='version',
                        version='%(prog)s version: %(version)s' %
                        {"prog": parser.prog, "version": VERSION})
    # input pvsim data filename
    parser.add_argument('--pvsim-data', '-d', type=str, default=PVSIMDATA,
                        help="PVSim data file [%(default)s]")
    parser.add_argument('--year', '-y', type=int, default=YEAR,
                        help="simulation year [%(default)s]")
    # select output file
    parser.add_argument('--output-filename', '-f', type=str,
                        default=OUTPUTFILENAME,
                        help="output data file [%(default)s]")
    # select optimization flag
    parser.add_argument('--optimize', '-o', type=int, choices=[0, 1],
                        help='optimization flags')
    # select losses flag
    parser.add_argument('--loss-contributors', '-l', type=int,
                        choices=range(5), help='loss contributor flags')
    # select a JSON file with all system inputs
    parser.add_argument('--system-inputs', '-s', type=str,
                        help="JSON file with additional inputs")
    # turn on multiprocessing
    parser.add_argument('--parallel', '-p',  action="store_true",
                        help="activate multiprocessing")
    # max tasks per child
    parser.add_argument('--max-tasks', '-t', type=int,
                        help="max tasks per worker before being freed")
    # TODO: add some more of Ben's favorite input arguments here
    args = parser.parse_args()  # parse arguments
