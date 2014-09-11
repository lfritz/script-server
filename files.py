"""Functions to access the user's files and directories.

To avoid confusion about relative and absolute paths, variables containing
paths relative to the user's directory are prefixed with 'r_'.
"""

from datetime import datetime
import os
import shutil

from flask import g


def absolute(r_path):
    """Return absolute path for a path in the user's directory."""
    return os.path.join(g.directory, r_path.lstrip('/'))


def exists(r_path):
    return os.path.exists(absolute(r_path))


def is_directory(r_path):
    return os.path.isdir(absolute(r_path))


def file_info(r_path):
    """Get information on a file and return it in a dictionary.

    The dictionary contains:
    path: filename with path (relative to user's directory)
    name: filename (without path)
    mtime: time of last modification, as a datetime object
    type: either 'dir' or file'
    size: file size in bytes (not present for directories)
    """
    path = absolute(r_path)
    info = {}
    s = os.stat(path)
    info['name'] = os.path.basename(path)
    mtime = datetime.fromtimestamp(s.st_mtime)
    mtime = mtime.replace(microsecond=0)
    info['mtime'] = mtime
    if os.path.isdir(path):
        info['type'] = 'dir'
    else:
        info['type'] = 'file'
        info['size'] = s.st_size
    return info


def directory_listing(r_path):
    """Get a directory listing.

    Return a list of dictionary objects, as returned by 'file_info'.
    """
    path = absolute(r_path)
    files = os.listdir(path)
    return [file_info(os.path.join(r_path, f))
            for f in files
            if not f.startswith('.')]


def copy_file(r_src, r_dst):
    """Copy r_src to r_dst.

    If r_src is a directory, its contents are copied recursively. r_dst must be
    a directory.
    """
    src = absolute(r_src)
    dst = absolute(r_dst)
    if os.path.isdir(src):
        shutil.copytree(src, dst)
    else:
        shutil.copy(src, dst)


def move_file(r_old, r_new):
    shutil.move(absolute(r_old), absolute(r_new))


def mkdir(r_path, name):
    """Create a new directory named 'name' in 'r_path'."""
    os.mkdir(os.path.join(absolute(r_path), name))


def delete_file(r_path):
    os.remove(absolute(r_path))


def delete_directory(r_path):
    shutil.rmtree(absolute(r_path))


def delete(r_path):
    if is_directory(r_path):
        delete_directory(r_path)
    else:
        delete_file(r_path)
