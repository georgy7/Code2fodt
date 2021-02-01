#!/usr/bin/env python3

import argparse
import sys
import subprocess
from xml.sax.saxutils import escape
import re

VERSION="1.0.0.SNAPSHOT"

SHORT_DESCRIPTION = """
code2fodt v{}.

It prepares Git repository for printing
with OpenOffice / LibreOffice.

I designed it for multi-column printing
with very small font size. However,
you can change the styles of the template
to whatever you like.
"""

USAGE = """
Example:
  ./code2fodt.py --title="MyProject" print_me.fodt
"""

def execute(cmd):
    return subprocess.check_output(cmd, shell=True, universal_newlines=True)


def repository_is_not_clean():
    A_SIGNIFICANT_CHANGE_REGEX = re.compile('^\s*[MARCDU]')
    git_status = execute('git status --porcelain=v1')
    git_status = git_status.split('\n')
    git_status = list(filter(lambda x: re.match(A_SIGNIFICANT_CHANGE_REGEX, x), git_status))
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

    parser.add_argument('--template', default='template.fodt',
                        type=argparse.FileType('r', encoding='UTF-8'),
                        help='A template in OpenDocument Flat XML Document Format.')

    # TODO: tab size argument

    parser.add_argument('out', type=argparse.FileType('w', encoding='UTF-8'))

    namespace = parser.parse_args(sys.argv[1:])

    template = namespace.template.read()
    namespace.template.close()

    return template, namespace


if __name__ == "__main__":

    if repository_is_not_clean():
        print('ERROR: Unclean repositories are not supported.', file=sys.stderr)
        exit(1)

    git_abbreviated_commit_hash = execute('git show -s --format=%h')

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

        args.out.write(template_start)

        if args.short_description:
            args.out.write(SUBTITLE.format(escape(args.short_description)))

        for line in git_head_xml:
            args.out.write(CODE_LINE.format(line))

        args.out.write(HR)

        args.out.write(template_end)
    finally:
        if not args.out.closed:
            args.out.close()
