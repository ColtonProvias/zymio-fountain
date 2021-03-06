"""
zymio-fountain
Ported to Python 3 by Colton J. Provias - cj@coltonprovias.com
Based on Fountain by Nima Yousefi & John August
Original code for Objective-C at https://github.com/nyousefi/Fountain
"""


COMMON_TRANSITIONS = {'FADE OUT.', 'CUT TO BLACK.', 'FADE TO BLACK.'}


class FountainElement:
    def __init__(self, element_type, element_text, section_depth=0, scene_number='', is_centered=False, is_dual_dialogue=False):
        self.element_type = element_type
        self.element_text = element_text
        self.section_depth = section_depth
        self.scene_number = scene_number
        self.is_centered = is_centered
        self.is_dual_dialogue = is_dual_dialogue

    def __repr__(self):
        return self.element_type + ': ' + self.element_text


class Fountain:
    def __init__(self, string=None, path=None):
        if path:
            with open(path) as fp:
                self.contents = fp.read()
        else:
            self.contents = string
        self.parse()

    def parse(self):
        self.metadata = dict()
        contents = self.contents.strip().replace('\r', '')
        if ':' in contents[:20]:
            script_head, script_body = contents.split('\n\n', 1)
            self._parse_head(script_head.splitlines())
            self._parse_body(script_body.splitlines())
        else:
            self._parse_body(contents.splitlines())

    def _parse_head(self, script_head):
        open_key = None
        for line in script_head:
            line = line.rstrip()
            if line[0].isspace():
                self.metadata[open_key].append(line.strip())
            elif line[-1] == ':':
                open_key = line[0:-1].lower()
                self.metadata[open_key] = list()
            else:
                key, value = line.split(':', 1)
                self.metadata[key.strip().lower()] = [value.strip()]

    def _parse_body(self, script_body):
        is_comment_block = False
        is_inside_dialogue_block = False
        newlines_before = 0
        index = -1
        self.elements = list()
        comment_text = list()

        for line in script_body:
            assert type(line) is str
            index += 1
            line = line.lstrip()
            full_strip = line.strip()

            if (not line or line.isspace()) and not is_comment_block:
                is_inside_dialogue_block = False
                newlines_before += 1
                continue

            if line.startswith('/*'):
                line = line.rstrip()
                if line.endswith('*/'):
                    text = line.replace('/*', '').replace('*/', '')
                    self.elements.append(FountainElement('Boneyard', text))
                    is_comment_block = False
                    newlines_before = 0
                else:
                    is_comment_block = True
                    comment_text.append('')
                continue

            if line.rstrip().endswith('*/'):
                text = line.replace('*/', '')
                comment_text.append(text.strip())
                self.elements.append(FountainElement('Boneyard',
                                                     '\n'.join(comment_text)))
                is_comment_block = False
                comment_text = list()
                newlines_before = 0
                continue

            if is_comment_block:
                comment_text.append(line)
                continue

            if line.startswith('==='):
                self.elements.append(FountainElement('Page Break', line))
                newlines_before = 0
                continue

            if len(full_strip) > 0 and full_strip[0] == '=':
                self.elements.append(FountainElement('Synopsis',
                                                     full_strip[1:].strip()))
                continue

            if newlines_before > 0 and full_strip.startswith('[[') and full_strip.endswith(']]'):
                self.elements.append(FountainElement('Comment',
                                                     full_strip.strip('[] \t')))
                continue

            if len(full_strip) > 0 and full_strip[0] == '#':
                newlines_before = 0
                depth = full_strip.split()[0].count('#')
                self.elements.append(FountainElement('Section Heading',
                                                     full_strip[depth:],
                                                     section_depth=depth))
                continue

            if len(line) > 1 and line[0] == '.' and line[1] != '.':
                newlines_before = 0
                if full_strip[-1] == '#' and full_strip.count('#') > 1:
                    scene_number_start = len(full_strip) - full_strip[::-1].find('#', 1) - 1
                    self.elements.append(FountainElement('Scene Heading', full_strip[1:scene_number_start].strip(), scene_number=full_strip[scene_number_start:].strip('#').strip()))
                else:
                    self.elements.append(FountainElement('Scene Heading', full_strip[1:].strip()))
                continue

            if line[0:4] in ['INT ', 'INT.', 'EXT ', 'EXT.', 'EST ', 'EST.', 'I/E ', 'I/E.'] or\
               line[0:8] in ['INT/EXT ', 'INT/EXT.'] or\
               line[0:9] in ['INT./EXT ', 'INT./EXT.']:
                newlines_before = 0
                if full_strip[-1] == '#' and full_strip.count('#') > 1:
                    scene_number_start = len(full_strip) - full_strip[::-1].find('#', 1) - 1
                    self.elements.append(FountainElement('Scene Heading', full_strip[:scene_number_start].strip(), scene_number=full_strip[scene_number_start:].strip('#').strip()))
                else:
                    self.elements.append(FountainElement('Scene Heading', full_strip.strip()))
                continue

            if full_strip.endswith(' TO:'):
                newlines_before = 0
                self.elements.append(FountainElement('Transition', full_strip))
                continue

            if full_strip in COMMON_TRANSITIONS:
                newlines_before = 0
                self.elements.append(FountainElement('Transition', full_strip))
                continue

            if full_strip[0] == '>':
                newlines_before = 0
                if len(full_strip) > 1 and full_strip[-1]:
                    self.elements.append(FountainElement('Action', full_strip[1:-1].strip(), is_centered=True))
                else:
                    self.elements.append(FountainElement('Transition', full_strip[1:].strip()))
                continue

            if newlines_before > 0 and index + 1 < len(script_body) and script_body[index + 1]:
                newlines_before = 0
                if full_strip[-1] == '^':
                    for element in reversed(self.elements):
                        if element.element_type == 'Character':
                            element.is_dual_dialogue = True
                            break
                    self.elements.append(FountainElement('Character', full_strip.rstrip('^').strip(), is_dual_dialogue=True))
                else:
                    self.elements.append(FountainElement('Character', full_strip))
                    is_inside_dialogue_block = True
                continue

            if is_inside_dialogue_block:
                if newlines_before == 0 and full_strip[0] == '(':
                    self.elements.append(FountainElement('Parenthetical', full_strip))
                else:
                    if self.elements[-1].element_type == 'Dialogue':
                        self.elements[-1].element_text = '\n'.join([self.elements[-1].element_text, full_strip])
                    else:
                        self.elements.append(FountainElement('Dialogue', full_strip))
                continue

            if newlines_before == 0 and len(self.elements) > 0:
                self.elements[-1].element_text = '\n'.join([self.elements[-1].element_text, full_strip])
                newlines_before = 0
            else:
                self.elements.append(FountainElement('Action', full_strip))
                newlines_before = 0
