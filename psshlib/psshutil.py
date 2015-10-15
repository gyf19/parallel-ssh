# Copyright (c) 2009, Andrew McNabb
# Copyright (c) 2003-2008, Brent N. Chun

import fcntl
import string
import sys
import time
import datetime
try:
    import hashlib 
    hash_function = hashlib.sha1
except ImportError:
    import sha
    hash_function = sha.sha

import random

from psshlib.exceptions import FatalError

HOST_FORMAT = 'Host format is [user@]host[:port] [user]'


def read_host_files(paths, default_user=None, default_port=None):
    """Reads the given host files.

    Returns a list of (host, port, user) triples.
    """
    hosts = []
    if paths:
        for path in paths:
            hosts.extend(read_host_file(path, default_user=default_user))
    return hosts


def read_host_file(path, default_user=None, default_port=None):
    """Reads the given host file.

    Lines are of the form: host[:port] [login].
    Returns a list of (host, port, user) triples.
    """
    lines = []
    f = open(path)
    for line in f:
        lines.append(line.strip())
    f.close()

    hosts = []
    for line in lines:
        # Pull out the non-commented portion of the line
        # This allows entries with comments anywhere in the line
        line = line.split('#')[0].strip()
        host, port, user, name = parse_host_entry(line, default_user, default_port)
        if host:
            hosts.append((host, port, user, name))
    return list(set(hosts)) # uniquify host list


# TODO: deprecate the second host field and standardize on the
# [user@]host[:port] format.
def parse_host_entry(line, default_user, default_port):
    """Parses a single host entry.

    This may take either the of the form [user@]host[:port] or
    host[:port][ user].

    Returns a (host, port, user) triple.
    """
    fields = line.split()
    if len(fields) == 0:
        return None, None, None, None
    if len(fields) > 3:
        sys.stderr.write('Bad line: "%s". Format should be'
                ' [user@]host[:port] [user]\n' % line)
        return None, None, None, None
    host_field = fields[0]
    host, port, user = parse_host(host_field, default_port=default_port)
    if len(fields) == 2:
        if user is None:
            user = fields[1]
        else:
            sys.stderr.write('User specified twice in line: "%s"\n' % line)
            return None, None, None, None
    
    name = None
    if len(fields) == 3:
        if name is None:
            name = fields[2]
        else:
            sys.stderr.write('servar Name specified twice in line: "%s"\n' % line)
            return server

    if name is None:
        name = host
    
    if user is None:
        user = default_user
    return host, port, user, name


def parse_host_string(host_string, default_user=None, default_port=None):
    """Parses a whitespace-delimited string of "[user@]host[:port]" entries.

    Returns a list of (host, port, user) triples.
    """
    hosts = []
    entries = host_string.split()
    for entry in entries:
        hosts.append(parse_host(entry, default_user, default_port))
    return hosts


def parse_host(host, default_user=None, default_port=None):
    """Parses host entries of the form "[user@]host[:port]".

    Returns a (host, port, user) triple.
    """
    # TODO: when we stop supporting Python 2.4, switch to using str.partition.
    user = default_user
    port = default_port
    if '@' in host:
        user, host = host.split('@', 1)
    if ':' in host:
        host, port = host.rsplit(':', 1)
    return (host, port, user)


def set_cloexec(filelike):
    """Sets the underlying filedescriptor to automatically close on exec.

    If set_cloexec is called for all open files, then subprocess.Popen does
    not require the close_fds option.
    """
    fcntl.fcntl(filelike.fileno(), fcntl.FD_CLOEXEC, 1)

def get_timestamp():
    return time.asctime().split()[3]

def run_manager(manager):
    try:
       statuses = manager.run()
    except FatalError:
       sys.exit(1)
    return statuses

def convert_task_time(timestamp):
    return datetime.datetime.utcfromtimestamp(timestamp)

def simple_uuid():
    seed = ''.join([ random.choice(string.hexdigits) for i in xrange(24) ])
    return hash_function(seed).hexdigest()
    
