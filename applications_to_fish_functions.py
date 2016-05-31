#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""Build the list of fish aliases/commands from all mac os x Applications."""

__author__ = 'matthias.wiesmann@gmail.com (Matthias Wiesmann)'

import itertools
import os
import re
import subprocess
import sys

ENCODING = os.getenv('LANG', 'en_US.UTF-8').split('.')[1].lower()

MDFIND = ('/usr/bin/mdfind', 'kMDItemKind == Application')

MDLS = (
    '/usr/bin/mdls',
    '--name=kMDItemAppStoreCategory',
    '--name=kMDItemDisplayName',
    '--name=kMDItemKind',
    '--raw')

FUNCTION_TEMPLATE = """function %(command_name)s --description "%(description)s" --wraps /usr/bin/open
  /usr/bin/open -a %(application_path)s $argv
end

"""

def GetAllApps():
  """Yield all applications in the system."""
  find_process = subprocess.Popen(MDFIND, stdout=subprocess.PIPE, bufsize=1)
  while True:
    line = find_process.stdout.readline()
    if not line:
      return
    yield line.decode(ENCODING).rstrip('\n')


def GetDescription(paths):
  """For each path in paths, yield the pair path, description."""
  for path in paths:
    command = itertools.chain(MDLS, [path])
    result = subprocess.check_output(command).decode(ENCODING)
    app_type, name, item_kind = result.split('\0')
    if app_type != '(null)':
      description = u'%s – %s %s' % (name, app_type, item_kind)
    else:
      description = name
    yield path, description


def FilterPath(path):
  """Should an application path be kept?"""
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
  """Make a CLI command name out of a binary name."""
  name = os.path.basename(path).lower().replace("'","").replace('"', '')
  return '_'.join(re.split(r'[().;!?,\s]', name))


def EscapePath(path):
  """Escape a path for the fish shell."""
  return re.escape(path).replace('\/', '/')


def EscapeDescription(description):
  """Escape a description for the fish shell."""
  return description.replace("'", "\\'").replace('"', '\\"')


if __name__ == '__main__':
  good_paths = itertools.ifilter(FilterPath, GetAllApps())
  commands = set()
  for path, description in GetDescription(good_paths):
    command = MakeCommandName(path)
    if command in commands:
      sys.stderr.write("Ignoring duplicate command %s\n" % command)
    else:
      commands.add(command)
      args = {
        'description': EscapeDescription(description),
        'command_name': command,
        'application_path': EscapePath(path),
      }
      func_text = FUNCTION_TEMPLATE % args
      sys.stdout.write(func_text.encode(ENCODING))

