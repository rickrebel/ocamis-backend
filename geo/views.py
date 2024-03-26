from django.shortcuts import render
from scripts.common import text_normalizer


def build_catalog_delegation_by_id(institution, key_field='name'):
    from geo.models import Delegation
    delegation_value_list = [
        'name', 'other_names', 'id']
    curr_delegations = Delegation.objects.filter(institution=institution)
    delegations_query = list(curr_delegations.values(*delegation_value_list))
    catalog_delegation = {}
    for delegation in delegations_query:
        delegation_name = text_normalizer(delegation[key_field])
        if delegation_name not in catalog_delegation:
            catalog_delegation[delegation_name] = delegation["id"]
        alt_names = delegation["other_names"] or []
        for alt_name in alt_names:
            alt_name = text_normalizer(alt_name)
            if alt_name not in catalog_delegation:
                catalog_delegation[alt_name] = delegation["id"]
    # final_path = f"{self.agency.provider.acronym}/catalogs/delegation_by_{key_field}.json"
    # file_name, errors = create_file(
    #     catalog_delegation, self.s3_client, final_path=final_path)
    return catalog_delegation
