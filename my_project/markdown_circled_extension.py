from markdown.inlinepatterns import InlineProcessor
from markdown.extensions import Extension
import xml.etree.ElementTree as etree

class CircledInlineProcessor(InlineProcessor):
    def handleMatch(self, m, data):
        el = etree.Element('span')
        el.set('class', 'markdown--circled')
        el.text = m.group(1)
        return el, m.start(0), m.end(0)

class CircledExtension(Extension):
    def extendMarkdown(self, md):
        CIRCLED_PATTERN = r'\(\((.*?)\)\)'  # like ((del))
        md.inlinePatterns.register(CircledInlineProcessor(CIRCLED_PATTERN, md), 'circled', 175)
