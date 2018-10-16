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
    def __init__(self, name, top=False):
        self.name = name
        boxes[self.name] = self
        self._shape = 'square'
        self._label = ''
        self.inputs = []
        self.outputs = []
        self.children = []
        self.top = top
        self.has_direct_connections = False

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

    @property
    def shape(self):
        if self._shape == 'point':
            return 'node [shape=point color=black height=0.4 width=0.4]'
        elif self._shape == 'ellipse':
            return 'node [shape=ellipse style=filled fillcolor=gray95]'
        else:
            return 'node [shape=square style=filled fillcolor=gray95]'

    # TODO faire un node property qui pour centraliser l'info

    @shape.setter
    def shape(self, shape_name):
        self._shape = shape_name

    @property
    def is_container(self):
        return bool(self.inputs or self.outputs or self.children)

    def to_boxaro(self):
        if self.is_container:
            graph = dedent("""\

                subgraph cluster_BOXNAME {
                    color=black
                    LABEL_COLOR

                    DUMMY_NODE

                    // inputs
                    node [shape=box style=filled color="#DDFFDD" fontsize=20]
                    BOXINPUTS

                    // outputs
                    node [shape=box style=filled color="#FFEEDD" fontsize=20]
                    BOXOUTPUTS

                    // processes and instances
                    node [shape=plaintext style=solid color=black fontsize=14]

                    BOXSUBBOXES
                }
            """)
        else:
            graph = dedent("""\
                BOXSHAPE
                BOXNAME [label = "BOXLABEL"]
            """)

        graph = graph.replace('BOXNAME', self.name)
        graph = graph.replace('BOXLABEL', self.label)
        graph = graph.replace('BOXSHAPE', self.shape)
        graph = graph.replace('    BOXINPUTS', self.boxaro_inputs())
        graph = graph.replace('    BOXOUTPUTS', self.boxaro_outputs())

        if self.has_direct_connections:
            graph = graph.replace(
                '    DUMMY_NODE',
                '    // dummy node for box direct connection\n'
                '    node [shape=point color=invis height=0 width=0]\n'
                '    dummy__' + self.name + '\n')
        else:
            graph = graph.replace('    DUMMY_NODE', '')

        if self.top:
            graph = graph.replace('    LABEL_COLOR', '    color = white')
        else:
            graph = graph.replace(
                '    LABEL_COLOR',
                '    label = "{}"'.format(
                    self.label))

        subboxes = ''
        for box in self.children:
            subboxes += box.to_boxaro()
        graph = graph.replace('    BOXSUBBOXES', subboxes)

        return indent(graph, '    ')

    def _boxaro_io_list(self, ios):
        text = ''
        for io in ios:
            text += '    {}\n'.format(io)
        text += '    {{rank = same; {}}}\n'.format(' '.join(ios))
        return text

    def boxaro_inputs(self):
        return self._boxaro_io_list(self.inputs)

    def boxaro_outputs(self):
        return self._boxaro_io_list(self.outputs)

    @property
    def connection_name(self):
        if self.is_container:
            return 'dummy__{}'.format(self.name)
        else:
            return self.name


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

        key = self.start + '#' + self.label
        if key not in connections:
            connections[key] = []
        connections[key].append(self)

        if self.simple_start in boxes:
            boxes[self.simple_start].has_direct_connections = True
        if self.simple_end in boxes:
            boxes[self.simple_end].has_direct_connections = True

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

    def to_boxaro(self, split_mode=False):
        if self.label:
            configuration = 'label="{}" '.format(self.label)
        else:
            configuration = ''

        start = connection.simple_start
        if start in boxes and boxes[start].is_container:
            configuration += 'ltail=cluster_{} '.format(start)
            start = boxes[start].connection_name

        end = connection.simple_end
        if end in boxes and boxes[end].is_container:
            configuration += 'lhead=cluster_{} '.format(end)
            end = boxes[end].connection_name

        graph = '    {} -> {}'.format(start, end)

        if configuration:
            graph += ' [{}]\n'.format(configuration.strip())
        else:
            graph += '\n'

        return graph


connections = {}


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
                read_state.append(('box', line_level, name))
                if top_box:
                    box = Box(name)
                else:
                    top_box = name
                    box = Box(name, top=True)
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
            elif line.lstrip().startswith('shape'):
                box_name = read_state[-1][2]
                boxes[box_name].shape = line.lstrip()[6:].strip()
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
    graph += '    graph [pad="0.5", nodesep="1", ranksep="2" compound=true];\n'
    if len(box.children) < 4000000:
        graph += '    rankdir="LR" // horizontal graph\n'
    graph += indent(dedent("""\
        splines = "spline" // nice arrows
        newrank = true // better ranking

    """), '    ')
    graph += box.to_boxaro()
    graph += '\n    // connections\n'

    for cons in connections.values():
        if len(cons) == 1:
            split_mode = False
        else:
            split_mode = True
        # def valid_id(text):
        #     return text.replace(' ', '').replace('.', '_')
        # splitter_name = 'splitter__{}__{}'.format(
        #     valid_id(cons[0].start),
        #     valid_id(cons[0].label),
        # )

        # graph += '    {} [shape = point]\n'.format(splitter_name)
        # graph += '    {} -> {} [label = "{}"]\n'.format(
        #     cons[0].simple_start,
        #     splitter_name,
        #     cons[0].label,
        # )
        # for connection in cons:
        #     graph += '    {} -> {}\n'.format(
        #         splitter_name,
        #         connection.simple_end,
        #     )
        for connection in cons:
            graph += connection.to_boxaro(split_mode=split_mode)

    graph += '\n    // dummy alignment hack\n'
    graph += '    edge[style=invis]\n'
    for box in boxes.values():
        if box.is_container and box.has_direct_connections:
            for io in box.inputs:
                graph += '    {} -> {} [weight=5]\n'.format(
                    io,
                    box.connection_name,
                )
            for io in box.outputs:
                graph += '    {} -> {} [weight=5]\n'.format(
                    box.connection_name,
                    io,
                )

    graph += '}\n'
    with open(args.output_file, 'w') as f:
        f.write(graph)
