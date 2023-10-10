from generator.utils import load_publications

def publications (_):
    return { 'publications': load_publications() }
