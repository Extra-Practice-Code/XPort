from generator.utils import loadPublications

def publications (_):
    return { 'publications': loadPublications() }
