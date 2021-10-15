from markdown.inlinepatterns import SimpleTagInlineProcessor
from markdown.extensions import Extension

class MarkExtension(Extension):
    def extendMarkdown(self, md):
        md.inlinePatterns.register(SimpleTagInlineProcessor(r'()==(.*?)==', 'mark'), 'mark', 175)
