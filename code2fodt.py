#!/usr/bin/env python3

# To the extent possible under law, Georgy Ustinov has waived
# all copyright and related or neighboring rights to code2fodt.
#
# This work is published from: Russian Federation.
#
# http://creativecommons.org/publicdomain/zero/1.0/

import argparse
import hashlib
import os
import re
import subprocess
import sys
from xml.sax.saxutils import escape

VERSION = "1.0.0.SNAPSHOT"

SHORT_DESCRIPTION = """
code2fodt v{}.

It prepares Git repository for printing
with OpenOffice / LibreOffice.

I designed it for multi-column printing
with very small font size. However, you may
modify these templates or create your own.
"""

USAGE = """
Example:
  ./code2fodt.py --title="MyProject" print_me.fodt
"""


def execute(cmd):
    return subprocess.check_output(cmd, shell=True, universal_newlines=True)


def repository_is_not_clean():
    A_SIGNIFICANT_CHANGE = re.compile('^\s*[MARCDU]')
    git_status = execute('git status --porcelain=v1')
    git_status = git_status.split('\n')
    git_status = list(filter(lambda x: re.match(A_SIGNIFICANT_CHANGE, x), git_status))
    return len(git_status) > 0


SUBTITLE = '<text:p text:style-name="Subtitle">{0}</text:p>\n'
FILE_NAME_HEADER = '<text:h text:style-name="Heading_20_1" text:outline-level="1">{0}</text:h>\n'
EMPTY_CODE_LINE = '<text:p text:style-name="Standard"/>\n'
CODE_LINE = '<text:p text:style-name="Standard">{0}</text:p>\n'
SPACES = '<text:s text:c="{0}"/>'
HR = '<text:p text:style-name="Horizontal_20_Line"/>\n'


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=SHORT_DESCRIPTION.format(VERSION),
        epilog=USAGE,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--title', required=True,
                        help='Document (project) title.')

    parser.add_argument('--short-description',
                        help='I do not recommend writing more than 255 characters here.')

    parser.add_argument('--template', default='template_A4_3c.fodt',
                        type=argparse.FileType('r', encoding='UTF-8'),
                        help='A template in OpenDocument Flat XML Document Format.')

    # TODO: tab size argument

    parser.add_argument('out', type=argparse.FileType('w', encoding='UTF-8'))

    namespace = parser.parse_args(sys.argv[1:])

    template = namespace.template.read()
    namespace.template.close()

    return template, namespace


def is_binary(file_path):
    r = execute('file --mime-encoding "{0}"'.format(file_path))
    r = r.split(':')
    return 'binary' in r[-1].lower()


def replace_tabs(s):
    # TODO переделать
    return s.replace("\t", ' ')


def transform_spaces(s):
    r = replace_tabs(s)
    for i in range(64, 1, -1):
        r = r.replace(' ' * i, SPACES.format(i))
    if r.startswith(' '):
        r = SPACES.format(1) + r[1:]
    return r


def format_line_number(line_number):
    max_length = 4
    s = str(line_number)
    if len(s) > max_length:
        s = '#' + s[-(max_length - 1):]
    return s.rjust(max_length) + '   '


def print_file(output, source_file_path):
    if is_binary(source_file_path):
        output.write(CODE_LINE.format('Binary file.'))
        size_bytes = os.path.getsize(source_file_path)

        hash = hashlib.md5()
        max_chunk_size = 8192
        with open(source_file_path, "rb") as f:
            chunk = f.read(max_chunk_size)
            while chunk:
                hash.update(chunk)
                chunk = f.read(max_chunk_size)

        md5 = hash.hexdigest()
        output.write(CODE_LINE.format('Size: {0} bytes.'.format(size_bytes)))
        output.write(CODE_LINE.format('MD5:<text:s text:c="2"/>{0}.'.format(md5)))
    else:
        with open(source_file_path, "r") as f:
            line = f.readline()
            line_number = 1
            while line:
                for l2 in line.split('\f'):
                    numbered = format_line_number(line_number) + escape(l2)
                    output.write(CODE_LINE.format(transform_spaces(numbered)))
                    line_number += 1
                line = f.readline()


if __name__ == "__main__":

    if repository_is_not_clean():
        print('ERROR: Unclean repositories are not supported.', file=sys.stderr)
        exit(1)

    # For page headers.
    git_commit_hash = execute('git show -s --format=%H')

    # For the first page.
    git_head_xml = execute('git show -s --format="commit %H%n'
                           'Author: %aN &lt;%aE&gt;%n'
                           'Date:<text:s text:c=\\"3\\"/>%aI"')
    git_head_xml = git_head_xml.split('\n')[:3]

    template, args = parse_arguments()

    TEMPLATE_SPLITTER = '</office:text>'

    template_start, template_end = template.split(TEMPLATE_SPLITTER)

    template_start = template_start.rstrip() + '\n\n'
    template_end = '\n  ' + TEMPLATE_SPLITTER + template_end

    try:
        template_start = template_start.replace('Project header', escape(args.title))
        template_start = template_start.replace('CommitHashCode', git_commit_hash)

        args.out.write(template_start)

        if args.short_description:
            args.out.write(SUBTITLE.format(escape(args.short_description)))

        for line in git_head_xml:
            args.out.write(CODE_LINE.format(line))

        files = execute('git ls-files').rstrip().split('\n')
        # TODO change order

        for file_path in files:
            args.out.write(FILE_NAME_HEADER.format(escape(file_path)))
            print_file(args.out, file_path)

        args.out.write(template_end)
    finally:
        if not args.out.closed:
            args.out.close()
