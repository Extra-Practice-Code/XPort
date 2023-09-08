import re
from collections import OrderedDict

# Global Vars
META_RE = re.compile(r'^[ ]{0,3}(?P<key>[A-Za-z0-9_-]+):\s*(?P<value>.*)')
META_MORE_RE = re.compile(r'^[ ]{4,}(?P<value>.*)')
BEGIN_RE = re.compile(r'^-{3}(\s.*)?')
END_RE = re.compile(r'^(-{3}|\.{3})(\s.*)?')

EMPTY_LINE_RE = re.compile(r'^\s*$')
ESCAPED_UNDERSCORES = re.compile(r'(?<!\\)\\_')

def filter_empty_lines_markdown_export (lines):
  print(lines)
  while EMPTY_LINE_RE.match(lines[0]):
    lines.pop(0)

  i = 0
  lines_to_delete = []

  while i < len(lines):
    lines[i] = ESCAPED_UNDERSCORES.subn('_', lines[i])[0]
    line = lines[i]
    next_line = lines[i+1]

    if '\\' in line:
       print('*****\n', line, ESCAPED_UNDERSCORES.subn('_', lines[i])[0])


    if META_RE.match(line) or (i > 0 and META_RE.match(line)):
      if EMPTY_LINE_RE.match(next_line):
        lines_to_delete.append(i+1)
        i += 2
      else:
        i += 1
    else:
      break


  for line_to_delete in lines_to_delete[::-1]:
    lines.pop(line_to_delete)

  return lines


"""
    Taken from the python markdown extension
"""

def extract_meta (content):
    """ Extract and parse metadata from the file. """
    meta = OrderedDict()
    key = None
    lines = filter_empty_lines_markdown_export(content.split('\n'))
    print(lines)
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
