from markdown.inlinepatterns import InlineProcessor
from markdown.extensions import Extension
import xml.etree.ElementTree as etree


"""
Extended pattern. It matches inline references.
The reference at the start, the optional label.
And, though ignored, extra data chunks in between.

[[type:target]]
[[type:target | label]]
[[type:target | extra: data | label]]

\[\[\s*
    (?P<type>\w+) \s* : \s* (?P<target>[^\]\|]+?) \s*
    (?:(\| \s* \w+ \s* : \s* [^\|]+ \s*)* (?:\| \s* (?P<label>[^\]\|]+) \s*)?)?
\]\]
"""

class InlineReferenceProcessor(InlineProcessor):
    def handleMatch(self, m, data):
        reference_type = m.group('type')
        reference_target = m.group('target')
        reference_label = m.group('label')

        if not reference_label:
          reference_label = reference_target

        el = etree.Element('span')
        el.set('class', 'markdown--inline-reference')
        el.set('data-reference-type', reference_type)
        el.set('data-reference-target', reference_target)
        el.text = reference_label
        return el, m.start(0), m.end(0)

class InlineReferenceExtension(Extension):
    def extendMarkdown(self, md):
        INLINE_REFERENCE_PATTERN = r"\[\[\s*(?P<type>\w+)\s*:\s*(?P<target>[^\]\|]+?)\s*(?:(\|\s*\w+\s*:\s*[^\|]+\s*)*(?:\|\s*(?P<label>[^\]\|]+)\s*)?)?\]\]"
        md.inlinePatterns.register(InlineReferenceProcessor(INLINE_REFERENCE_PATTERN, md), 'inline_reference', 175)
