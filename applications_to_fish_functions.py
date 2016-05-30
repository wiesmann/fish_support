#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""Build the list of fish aliases/commands from all mac os x Applications."""

__author__ = 'matthias.wiesmann@a3.epfl.ch (Matthias Wiesmann)'

import itertools
import operator
import os
import re
import subprocess
import sys

ENCODING = os.getenv('LANG', 'en_US.UTF-8').split('.')[1].lower()

MDFIND = ('/usr/bin/mdfind', '-0', 'kMDItemKind == Application')

MDLS = (
    '/usr/bin/mdls',
    '--name=kMDItemAppStoreCategory',
    '--name=kMDItemDisplayName',
    '--raw')

FUNCTION_TEMPLATE = """function %(command_name)s --description "%(description)s" --wraps /usr/bin/open
  /usr/bin/open -a %(application_path)s $argv
end
"""

def GetAllApps():
  result = subprocess.check_output(MDFIND).decode(ENCODING)
  return result.split('\0')


def GetDescription(paths):
  for path in paths:
    command = itertools.chain(MDLS, [path])
    result = subprocess.check_output(command).decode(ENCODING)
    app_type, name,  = result.split('\0')
    if app_type != '(null)':
      description = u'%s – %s Application' % (name, app_type)
    else:
      description = name
    yield path, description


def FilterPath(path):
  if path.startswith('/System'):
    return False
  if path.startswith('/Library'):
    return False
  if path.startswith(os.path.expanduser("~/Library")):
    return False
  if not path.endswith('.app'):
    return False
  return True


def MakeCommandName(path):
  name = os.path.basename(path).lower().replace("'","").replace('"', '')
  return '_'.join(re.split(r'[().;!?,\s]', name))


def EscapePath(path):
  return re.escape(path).replace('\/', '/')


def EscapeDescription(description):
  return description.replace("'", "\\'").replace('"', '\\"')


if __name__ == '__main__':
  good_paths = itertools.ifilter(FilterPath, GetAllApps())
  for path, description in GetDescription(good_paths):
    args = {
      'description': EscapeDescription(description),
      'command_name': MakeCommandName(path),
      'application_path': EscapePath(path),
    }
    func_text = FUNCTION_TEMPLATE % args
    print func_text.encode(ENCODING)

