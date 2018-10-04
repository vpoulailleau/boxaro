# BSD 3-Clause License
#
# Copyright (c) 2018, Vincent Poulailleau
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import argparse
import logging
import re
from pathlib import Path
from textwrap import dedent, indent

# Setup logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s :: %(levelname)10s :: %(filename)s(%(lineno)d):%(funcName)s :: %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class Box:
    def __init__(self, name):
        self.name = name
        boxes[self.name] = self
        self._label = ''
        self.inputs = []
        self.outputs = []
        self.children = []

    def __repr__(self):
        return '<Box({})>'.format(self.name)

    def __str__(self):
        text = '#' * 80
        text += '\nBox {}\n'.format(self.name)
        text += '    Inputs\n'
        for input in self.inputs:
            text += '        {}\n'.format(input)
        text += '    Outputs\n'
        for output in self.outputs:
            text += '        {}\n'.format(output)
        text += '    Children\n'
        for child in self.children:
            text += '        {}\n'.format(repr(child))
        return text

    @property
    def label(self):
        return self._label or self.name

    @label.setter
    def label(self, name):
        self._label = name

    def to_boxaro(self):
        if self.inputs or self.outputs or self.children:
            graph = dedent("""\

                subgraph cluster_BOXNAME {
                    label = "BOXLABEL"
                    node [shape = plaintext]

                    // inputs
                    subgraph cluster_BOXNAME_inputs {
                        label = ""
                        color = white
                        BOXINPUTS
                    }

                    // outputs
                    subgraph cluster_BOXNAME_outputs {
                        label = ""
                        color = white
                        BOXOUTPUTS
                    }

                    // processes and instances
                    BOXSUBBOXES
                }
            """)
        else:
            graph = dedent("""\
                node [shape = square style = filled fillcolor = gray95]
                BOXNAME [label = "BOXLABEL"]
            """)

        graph = graph.replace('BOXNAME', self.name)
        graph = graph.replace('BOXLABEL', self.label)
        graph = graph.replace('        BOXINPUTS', self.boxaro_inputs())
        graph = graph.replace('        BOXOUTPUTS', self.boxaro_outputs())

        subboxes = ''
        for box in self.children:
            subboxes += box.to_boxaro()
        graph = graph.replace('    BOXSUBBOXES', subboxes)

        return indent(graph, '    ')

    def _boxaro_io_list(self, ios):
        text = ''
        for io in ios:
            text += '        {}\n'.format(io)
        text += '        {{rank = same; {}}}\n'.format(' '.join(ios))
        return text

    def boxaro_inputs(self):
        return self._boxaro_io_list(self.inputs)

    def boxaro_outputs(self):
        return self._boxaro_io_list(self.outputs)


boxes = {}


class Connection:
    def __init__(self, text):
        self.start = ''
        self.end = ''
        self.label = ''

        label = r'(\w[\w.]+)'
        m = re.search(
            label + r'\s+(.*)\s+' + label,
            text
        )
        if m:
            self.start = m.group(1)
            separator = m.group(2)
            separator = separator.strip()[:-2].strip()
            if separator:
                separator = separator[1:-1]
            self.label = separator
            self.end = m.group(3)
        else:
            logger.error('unrecognized connection: %s', text)

        if self.label:
            key = self.start + '#' + self.label
            if key not in connections_labelled:
                connections_labelled[key] = []
            connections_labelled[key].append(self)
        else:
            connections_not_labelled.append(self)

    def __repr__(self):
        return '<Connection({}, {}, {})>'.format(
            self.start,
            self.end,
            self.label,
        )

    @property
    def simple_start(self):
        return self.start.split('.')[-1]

    @property
    def simple_end(self):
        return self.end.split('.')[-1]


connections_labelled = {}
connections_not_labelled = []


def parse(filepath):
    try:
        with open(filepath, encoding='utf-8') as infile:
            lines = infile.readlines()
    except UnicodeDecodeError:
        with open(filepath, encoding='latin-1') as infile:
            lines = infile.readlines()

    return parse_lines(lines)


def parse_lines(lines):
    read_state = []  # list of tuples (type, level of indentation)
    top_box = ''

    for line in lines:
        if line.strip():
            logger.debug('Treating %s', line)
            line = line.replace('\t', '    ')
            line_level = len(line) - len(line.lstrip())

            while read_state and line_level <= read_state[-1][1]:
                read_state.pop()

            if line.lstrip().startswith('box '):
                name = line.split()[-1]
                top_box = top_box or name
                read_state.append(('box', line_level, name))
                box = Box(name)
                for state in reversed(read_state[:-1]):
                    if state[0] == 'box':
                        boxes[state[2]].children.append(box)
                        break
            elif line.lstrip().startswith('inputs'):
                read_state.append(('inputs', line_level))
            elif line.lstrip().startswith('outputs'):
                read_state.append(('outputs', line_level))
            elif line.lstrip().startswith('connections'):
                read_state.append(('connections', line_level))
            elif line.lstrip().startswith('label'):
                box_name = read_state[-1][2]
                boxes[box_name].label = line.lstrip()[6:].strip()
            else:
                # find current state
                state = read_state[-1][0]
                if state == 'inputs':
                    box_name = read_state[-2][2]
                    boxes[box_name].inputs.append(line.strip())
                elif state == 'outputs':
                    box_name = read_state[-2][2]
                    boxes[box_name].outputs.append(line.strip())
                elif state == 'connections':
                    Connection(line)

            logger.debug('    state is now %s', str(read_state))
    return top_box


if __name__ == '__main__':
    # Setup argument parser
    parser = argparse.ArgumentParser(
        description='Tool to convert boxaro file to graphviz compatible file')
    parser.add_argument(
        '-v',
        '--verbose',
        help='increase the verbosity level',
        action='count',
        default=0)
    parser.add_argument(
        '--version',
        help='display version number',
        action='version',
        version='%(prog)s 1.0.0')
    parser.add_argument(
        '-i',
        '--input-file',
        required=True,
        help='Input file (default value: %(default)s)',
        metavar='./nice_box.bao')
    parser.add_argument(
        '-o',
        '--output-file',
        required=True,
        help='Output file (default value: %(default)s)',
        metavar='./nice_box.gv')

    args = parser.parse_args()

    # Set verbose level
    if args.verbose <= 0:
        console_handler.setLevel(logging.WARNING)
    elif args.verbose == 1:
        console_handler.setLevel(logging.INFO)
    else:
        console_handler.setLevel(logging.DEBUG)

    box_name = parse(args.input_file)
    box = boxes[box_name]
    graph = 'digraph HDD {\n'
    graph += '    graph [pad="0.5", nodesep="1", ranksep="2"];\n'
    if len(box.children) < 4000000:
        graph += '    rankdir="LR" // horizontal graph\n'
    graph += indent(dedent("""\
        splines = "spline" // nice arrows
        newrank = true // better ranking

    """), '    ')
    graph += box.to_boxaro()
    graph += '\n    // connections\n'
    for connection in connections_not_labelled:
        graph += '    {} -> {}\n'.format(
            connection.simple_start,
            connection.simple_end,
            connection.label,
        )
    for key in connections_labelled:
        cons = connections_labelled[key]
        if len(cons) == 1:
            connection = cons[0]
            graph += '    {} -> {} [label = "{}"]\n'.format(
                connection.simple_start,
                connection.simple_end,
                connection.label,
            )
        else:
            def valid_id(text):
                return text.replace(' ', '').replace('.', '_')
            splitter_name = 'splitter__{}__{}'.format(
                valid_id(cons[0].start),
                valid_id(cons[0].label),
            )

            graph += '    {} [shape = point]\n'.format(splitter_name)
            graph += '    {} -> {} [label = "{}"]\n'.format(
                cons[0].simple_start,
                splitter_name,
                cons[0].label,
            )
            for connection in cons:
                graph += '    {} -> {}\n'.format(
                    splitter_name,
                    connection.simple_end,
                )

    graph += '}\n'
    with open(args.output_file, 'w') as f:
        f.write(graph)
