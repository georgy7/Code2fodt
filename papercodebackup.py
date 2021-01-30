#!/usr/bin/env python3

import argparse
import sys
import subprocess
from xml.sax.saxutils import escape

VERSION="1.0.0.SNAPSHOT"

SHORT_DESCRIPTION = """
PaperCodeBackup v{}.

It prepares Git repository for printing
with OpenOffice / LibreOffice.

I designed it for multi-column printing
with very small font size. However,
you can change the styles of the template
to whatever you like.
"""

USAGE = """
Example:
  ./papercodebackup --title="MyProject" print_me.fodt
"""

def execute(cmd):
    return subprocess.check_output(cmd, shell=True)


SUBTITLE = '<text:p text:style-name="Subtitle">{0}</text:p>\n'
FILE_NAME_HEADER = '<text:h text:style-name="Heading_20_1" text:outline-level="1">{0}</text:h>\n'
EMPTY_CODE_LINE = '<text:p text:style-name="Standard"/>\n'
CODE_LINE = '<text:p text:style-name="Standard">{0}</text:p>\n'
SPACES = '<text:s text:c="{0}"/>'
HR = '<text:p text:style-name="Horizontal_20_Line"/>\n'


if __name__ == "__main__":
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

    parser.add_argument('out', type=argparse.FileType('w', encoding='UTF-8'))

    namespace = parser.parse_args(sys.argv[1:])

    template = namespace.template.read()
    namespace.template.close()

    TEMPLATE_SPLITTER = '</office:text>'

    template_start, template_end = template.split(TEMPLATE_SPLITTER)

    template_start = template_start.rstrip() + '\n\n'
    template_end = '\n  ' + TEMPLATE_SPLITTER + template_end

    try:
        template_start = template_start.replace('Project header', escape(namespace.title))

        namespace.out.write(template_start)

        if namespace.short_description:
            namespace.out.write(SUBTITLE.format(escape(namespace.short_description)))

        status = execute('git log -n 1')
        status = status.split('\n')[:3]

        for line in status:
            namespace.out.write(CODE_LINE.format(escape(line)))

        namespace.out.write(HR)

        namespace.out.write(template_end)
    finally:
        if not namespace.out.closed:
            namespace.out.close()
