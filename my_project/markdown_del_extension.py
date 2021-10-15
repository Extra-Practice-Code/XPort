from markdown.inlinepatterns import SimpleTagInlineProcessor
from markdown.extensions import Extension

class DelExtension(Extension):
    def extendMarkdown(self, md):
        md.inlinePatterns.register(SimpleTagInlineProcessor(r'()--(.*?)--', 'del'), 'del', 175)
