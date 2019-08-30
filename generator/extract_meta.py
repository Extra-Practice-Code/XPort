import re
from collections import OrderedDict

# Global Vars
META_RE = re.compile(r'^[ ]{0,3}(?P<key>[A-Za-z0-9_-]+):\s*(?P<value>.*)')
META_MORE_RE = re.compile(r'^[ ]{4,}(?P<value>.*)')
BEGIN_RE = re.compile(r'^-{3}(\s.*)?')
END_RE = re.compile(r'^(-{3}|\.{3})(\s.*)?')

"""
    Taken from the python markdown extension
"""

def extract_meta (content):
    """ Extract and parse metadata from the file. """
    meta = OrderedDict()
    key = None
    lines = content.split('\n')
    if lines and BEGIN_RE.match(lines[0]):
        lines.pop(0)
    while lines:
        line = lines.pop(0)
        m1 = META_RE.match(line)
        if line.strip() == '' or END_RE.match(line):
            break  # blank line or end of YAML header - done
        if m1:
            key = m1.group('key').lower().strip()
            value = m1.group('value').strip()
            try:
                meta[key].append(value)
            except KeyError:
                meta[key] = [value]
        else:
            m2 = META_MORE_RE.match(line)
            if m2 and key:
                # Add another line to existing key
                meta[key].append(m2.group('value').strip())
            else:
                lines.insert(0, line)
                break  # no meta data - done
    return (meta, '\n'.join(lines))
