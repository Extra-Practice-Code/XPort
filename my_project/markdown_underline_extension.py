from markdown.inlinepatterns import SimpleTagInlineProcessor
from markdown.extensions import Extension

class UnderlineExtension(Extension):
    def extendMarkdown(self, md):
        md.inlinePatterns.register(SimpleTagInlineProcessor(r'()\[\](.*?)\[\]', 'u'), 'underline', 175)