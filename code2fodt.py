#!/usr/bin/env python3

# To the extent possible under law, Georgy Ustinov has waived
# all copyright and related or neighboring rights to code2fodt.
#
# This work is published from: Russian Federation.
#
# http://creativecommons.org/publicdomain/zero/1.0/

# ----------
# Affirmer offers the Work as-is and makes no representations or warranties
# of any kind concerning the Work, express, implied, statutory or otherwise,
# including without limitation warranties of title, merchantability, fitness
# for a particular purpose, non infringement, or the absence of latent
# or other defects, accuracy, or the present or absence of errors, whether
# or not discoverable, all to the greatest extent permissible under applicable law.

import argparse
import encodings
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


ERROR_LIMIT_PER_FILE = 5

DEFAULT_EXTENSION = '.fodt'

TITLE_INNER = 'Project header'
TITLE = '<text:p text:style-name="Title"><text:title>{0}</text:title></text:p>'
SUBTITLE = '<text:p text:style-name="Subtitle">{0}</text:p>\n'
FILE_NAME_HEADER = '<text:h text:style-name="Heading_20_1" text:outline-level="1">{0}</text:h>\n'

EMPTY_CODE_LINE = '<text:p text:style-name="Standard"/>\n'
CODE_LINE = '<text:p text:style-name="Standard">{0}</text:p>\n'

SPACES = '<text:s text:c="{0}"/>'


def natural_argument(arg):
    try:
        i = int(arg)
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e))

    if i < 1:
        raise argparse.ArgumentTypeError("Must be greater than or equal 1.")

    return i


def tab_size_argument(arg):
    try:
        i = int(arg)
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e))

    if i < 0:
        raise argparse.ArgumentTypeError("Tab must be greater than or equal 0.")
    elif i > 8:
        raise argparse.ArgumentTypeError("Tab must be less than or equal 8.")

    return i


def output_argument(arg):
    if not arg.endswith(DEFAULT_EXTENSION):
        raise argparse.ArgumentTypeError("Output filename must have extension fodt.")
    return arg


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=SHORT_DESCRIPTION.format(VERSION),
        epilog=USAGE,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument('--title', required=True,
                        help='Document (project) title.')

    parser.add_argument('-d', '--short-description',
                        help='I do not recommend more than 500 characters here.')

    parser.add_argument('--template', default='template_A4_3c.fodt',
                        type=argparse.FileType('r', encoding='UTF-8'),
                        help='A template in OpenDocument Flat XML Document Format.')

    parser.add_argument('-v', '--volume-loc-threshold', type=natural_argument,
                        default=500000,
                        help='After this number of lines, '
                             'the next source file will start a new FODT file. '
                             'Please, set it to 100000 or less to print directly '
                             'from OpenOffice.')

    parser.add_argument('--tab-size', type=tab_size_argument,
                        default=8, help='Tab size.')

    # TODO
    # parser.add_argument('--print-binary', action='store_true',
    #                     help='Print binary files as hex code.')

    parser.add_argument('out', type=output_argument)

    namespace = parser.parse_args(sys.argv[1:])

    template = namespace.template.read()
    namespace.template.close()

    return template, namespace


def get_raw_list_of_encoding_aliases():
    result = set()
    filtered = filter(
        lambda kv: not kv[1].endswith('_codec'),
        encodings.aliases.aliases.items()
    )

    flat_array = ['cp720', 'cp737', 'cp856', 'cp874', 'cp875', 'cp1006', 'koi8_u', 'utf_8_sig']
    for k, v in filtered:
        flat_array.append(k)
        flat_array.append(v)

    for x in flat_array:
        result.add(x.lower())
        result.add(x.lower().replace('_', '-'))

    result = list(filter(lambda x: not x.isnumeric(), result))
    return result


ENCODING_ALIASES = get_raw_list_of_encoding_aliases()
ENCODING_ALIASES_UNAMBIGUOUS = list(filter(lambda x: len(x) >= 5, ENCODING_ALIASES))
ENCODING_ALIASES_A_LITTLE_AMBIGUOUS = list(filter(lambda x: len(x) >= 3, ENCODING_ALIASES))


def get_fn_parts(file_path):
    # Filenames may contain encoding name.
    # For instance: freebsd-src/contrib/bc/locales/*
    fn = os.path.basename(file_path)
    without_extension = os.path.splitext(fn)[0]
    fn_parts = without_extension.split('.')
    return list(map(lambda x: x.lower(), fn_parts))


def get_encoding_lowercase(file_path):
    fn_parts = get_fn_parts(file_path)
    for i in range(1, len(fn_parts)):
        part = fn_parts[i]
        if part in ENCODING_ALIASES_UNAMBIGUOUS:
            return part
    r = execute('file --mime-encoding "{0}"'.format(file_path))
    r = r.split(':')
    r = r[-1].lower().strip()
    return r


def reinterpret_encoding(raw_encoding, file_path):
    if raw_encoding in ['unknown-8bit', 'us-ascii', 'iso-8859-1']:
        fn_parts = get_fn_parts(file_path)
        for i in range(1, len(fn_parts)):
            part = fn_parts[i]
            if part in ENCODING_ALIASES_A_LITTLE_AMBIGUOUS:
                return part
        # Most widely used single-byte character set.
        return 'windows-1252'
    elif raw_encoding == 'ebcdic':
        return 'cp500'
    return raw_encoding


def replace_tabs(s, tab_size):
    result = ''
    for i in range(len(s)):
        if '\t' == s[i]:
            modulo = len(result) % tab_size
            result += ' ' * (tab_size - modulo)
        else:
            result += s[i]
    return result


def transform_spaces(s):
    r = s
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


def print_file(output, source_file_path, tab_size):
    if os.path.islink(source_file_path):
        target = os.readlink(source_file_path)
        output.write(CODE_LINE.format('Link to ' + escape(target)))
        return 1

    encoding_detected = get_encoding_lowercase(source_file_path)
    encoding_interpreted = reinterpret_encoding(encoding_detected, source_file_path)

    if 'binary' in encoding_detected:
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
        return 3
    else:
        line_number = 1
        meta_lines = 0

        if encoding_detected == encoding_interpreted:
            output.write(CODE_LINE.format('Encoding: {0}.'.format(encoding_detected)))
            meta_lines += 1
        else:
            output.write(CODE_LINE.format('Encoding detected: {0}. Interpreted as: {1}.'
                                          .format(encoding_detected, encoding_interpreted)))
            meta_lines += 1
            if not ((encoding_detected in ['us-ascii', 'iso-8859-1'])
                    and ('windows-1252' == encoding_interpreted)):
                print(
                    'Interpreting {0} as {1}. File: {2}'.format(
                        encoding_detected,
                        encoding_interpreted,
                        source_file_path),
                    file=sys.stderr)

        output.write(EMPTY_CODE_LINE)
        meta_lines += 1

        try:
            ERROR_REPLACEMENT_CHARACTER = '\ufffd'
            with open(source_file_path, mode='r', encoding=encoding_interpreted, errors='replace') as f:
                errors_in_the_file = 0
                line = f.readline()
                while line:
                    for l2 in line.split('\f'):
                        raw = l2.rstrip()

                        error_count = raw.count(ERROR_REPLACEMENT_CHARACTER)
                        if error_count > 0:
                            print(
                                'Could not read {0} character(s): {1}:{2}.'.format(
                                    error_count,
                                    source_file_path,
                                    line_number),
                                file=sys.stderr
                            )

                        errors_in_the_file += error_count
                        if errors_in_the_file > ERROR_LIMIT_PER_FILE:
                            print('Replacements per file limit exceeded.', file=sys.stderr)
                            exit(1)

                        raw = replace_tabs(raw, tab_size)
                        filtered = ''.join(filter(lambda x: x.isprintable(), list(raw)))
                        numbered = format_line_number(line_number) + escape(filtered)
                        output.write(CODE_LINE.format(transform_spaces(numbered)))
                        line_number += 1
                    line = f.readline()
        except:
            print("Unexpected error:", sys.exc_info()[0], file=sys.stderr)
            print(
                'At reading {0}. Line number: {1}.'.format(source_file_path, line_number),
                file=sys.stderr
            )
            raise
        return meta_lines + line_number



def file_path_sort_key(x):
    parts = re.split('[/\\\\]', x.lstrip('/\\'))

    # Space is the smallest real Unicode character, I suppose.
    # So, files will be on the top with this manipulation.
    parts[-1] = ' ' + parts[-1]

    # Just in case, some folder name starts with space.
    for i in range(len(parts) - 1):
        parts[i] = 'z' + parts[i]

    return parts


def sort_files_before_folders(input):
    return sorted(input, key=file_path_sort_key)


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

    template_start_template, template_end = template.split(TEMPLATE_SPLITTER)

    template_start_template = template_start_template.rstrip() + '\n\n'
    template_end = '\n  ' + TEMPLATE_SPLITTER + template_end

    files = execute('git ls-files').rstrip().split('\n')
    files = sort_files_before_folders(files)

    file_index = 0
    volume_number = 1

    while file_index < len(files):

        print('Volume {0}.'.format(volume_number), file=sys.stderr)

        volume_loc_counter = 0

        if 1 == volume_number:
            output_file_path = args.out
        else:
            output_file_path = (args.out)[:-len(DEFAULT_EXTENSION)] + \
                               '.volume' + str(volume_number) + '.fodt'

        with open(output_file_path, mode='w', encoding='UTF-8') as out:

            template_start = template_start_template

            escaped_title = escape(args.title)
            template_start = template_start.replace(TITLE_INNER, escaped_title)

            template_start = template_start.replace('CommitHashCode', git_commit_hash)

            if 1 == volume_number:
                volume_label = ''
            else:
                volume_label = 'Volume {0}'.format(volume_number)

            template_start = template_start.replace('PartX', volume_label)

            out.write(template_start)

            if 1 == volume_number:
                out.write(TITLE.format(escaped_title))

                if args.short_description:
                    out.write(SUBTITLE.format(escape(args.short_description)))

                for line in git_head_xml:
                    out.write(CODE_LINE.format(line))

            while (file_index < len(files)) and (volume_loc_counter < args.volume_loc_threshold):
                file_path = files[file_index]
                file_index += 1

                out.write(FILE_NAME_HEADER.format(escape(file_path)))
                volume_loc_counter += print_file(out, file_path, args.tab_size)

            out.write(template_end)

        volume_number += 1
