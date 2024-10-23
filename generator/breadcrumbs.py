from django.urls import reverse
from django.shortcuts import get_object_or_404
from going_hybrid.models import EtherportOrganisation
from ethertoff.utils import pathToSlug
from generator.utils import getPublicationData

def generate (request, path):
    organisation = get_object_or_404(EtherportOrganisation, slug=path[0], members__id=request.user.id)
    publication = getPublicationData(organisation.slug, path[1])
    
    crumbs = [
        (organisation.name, reverse('generator-list-publications') + f'#{organisation.slug}'),
        (publication['title'], reverse('manage', args=[ pathToSlug(path[:2]) ]))
    ]
    
    crumbs.extend([(path[i], reverse('manage', args=[ pathToSlug(path[:i+1]) ])) for i in range(2, len(path))])

    return crumbs
