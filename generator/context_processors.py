from generator.utils import loadPublications
from ethertoff.models import EtherportOrganisation

def publications (request):
    if request.user.is_authenticated:
        user_organisations = EtherportOrganisation.objects.filter(members__id=request.user.id)
        publications = loadPublications()

        return { 'etherport_organisation_publication': {
            organisation.name: publications[organisation.slug] if organisation.slug in publications else [] for organisation in user_organisations
        } }
    else:
        return { 'etherport_organisation_publication': []}
