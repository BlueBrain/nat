__author__ = "Pierre-Alexandre Fonta"
__maintainer__ = "Pierre-Alexandre Fonta"

import traceback
from typing import List, Dict, Iterator, Optional, Any

from kg_utils import remove_empty_values
from nexus_utils import prettify


JSON = Dict[str, Any]


def transform_annotations(raw_annotations: List[JSON], data_context: str, agent_iri_base: str,
                          parameter_uuid_mapping: Dict[str, str]) -> Iterator[JSON]:
    for i, x in enumerate(raw_annotations):
        json_ld = transform_annotation(x, data_context, agent_iri_base, parameter_uuid_mapping)
        if json_ld is None:
            # TODO Handle better recovery from transformation errors.
            print("<index>", i)
            break
        else:
            yield json_ld


def transform_annotation(x: JSON, data_context: str, agent_iri_base: str,
                         parameter_uuid_mapping: Dict[str, str]) -> Optional[JSON]:
    try:
        base = {
            "@context": data_context,

            "@type": "nsg:ParameterAnnotation",

            # EntityShape properties.

            "name": pa_name(x["annotId"], x["localizer"]["type"]),

            "providerId": x["annotId"],

            # AnnotationShape properties.

            "contribution": {

                # ContributionShape properties.

                "agent": pa_contribution_agent(x["authors"], agent_iri_base),
            },

            "hasTarget": {

                "@type": pa_hastarget_type(x["localizer"]["type"]),

                # SelectorTargetShape properties.

                "hasSource": pa_hastarget_hassource(x["pubId"]),

                "hasSelector": pa_hastarget_hasselector(x["localizer"]),
            },

            "hasBody": pa_hasbody(x["parameters"], parameter_uuid_mapping),

            # Specific properties.

            "keywords": pa_keywords(x["tags"]),

            "comment": x["comment"],

            "experimentalProperties":
                pa_experimentalproperties(x["experimentProperties"], parameter_uuid_mapping),
        }

        remove_empty_values(base)

        return base

    except Exception:
        print("<error>")
        print(traceback.format_exc())
        print("<data>")
        prettify(x)
        return None


def pa_name(annot_id: str, _type: str) -> str:
    return f"a-{_type}-{annot_id[:8]}"


def pa_contribution_agent(authors: List[str], agent_iri_base: str) -> List[JSON]:
    def t(x: str) -> JSON:
        mapping = {
            "oreilly": f"{agent_iri_base}/124d1066-41cd-4d1b-b0ad-eed2672cf927",
            "iavarone": f"{agent_iri_base}/575c0c49-3203-4dc7-813b-2903680b6b8a",
            "sjimenez": f"{agent_iri_base}/a0cc78fc-f80f-4e1b-9625-a6a9843f6daa",
        }
        return {
            "@id": mapping[x],
            "@type": "prov:Agent",
        }
    return [t(x) for x in authors]


def pa_hastarget_type(_type: JSON) -> str:
    mapping = {
        "text": "nsg:TextPositionTarget",
        "figure": "nsg:FigureTarget",
        "equation": "nsg:EquationTarget",
        "table": "nsg:TableTarget",
        "position": "nsg:AreaTarget",
    }
    return mapping[_type]


# TODO Tackle the case UNPUBLISHED (not DOI nor PMID).
def pa_hastarget_hassource(pub_id: str) -> str:
    prefixes = {
        "doi": "https://doi.org/",
        "pmid": "https://www.ncbi.nlm.nih.gov/pubmed/",
    }

    if pub_id.startswith("UNPUBLISHED_"):
        raise Exception("UNPUBLISHED reference IDs are not supported yet!")
    elif pub_id.startswith("PMID_"):
        _type = "pmid"
        _id = pub_id.replace("PMID_", "")
    else:
        _type = "doi"
        _id = pub_id

    prefix = prefixes[_type]

    return f"{prefix}{_id}"


def pa_hastarget_hasselector(localizer: JSON) -> JSON:
    mapping = {
        "text": "nsg:TextPositionSelector",
        "figure": "nsg:FigureSelector",
        "equation": "nsg:EquationSelector",
        "table": "nsg:TableSelector",
        "position": "nsg:AreaSelector",
    }

    _type = mapping[localizer["type"]]

    base = {
        # SelectorShape properties.
        "@type": _type,
    }

    if _type == "nsg:TextPositionSelector":
        # TextPositionSelectorShape properties.
        start = localizer["location"]
        text = localizer["text"]
        specific = {
            "start": start,
            "end": start + len(text),
            "text": text,
        }
    elif _type in ["nsg:FigureSelector", "nsg:EquationSelector"]:
        # IndexSelectorShape properties.
        specific = {
            "index": localizer["no"],
        }
    elif _type == "nsg:TableSelector":
        # TableSelectorShape properties.
        specific = {
            "index": localizer["no"],
            "row": localizer["noRow"],
            "column": localizer["noCol"],
        }
    elif _type == "nsg:AreaSelector":
        # AreaSelectorShape properties.
        page_num = localizer["noPage"]
        left = localizer["x"]
        top = localizer["y"]
        wd = localizer["width"]
        ht = localizer["height"]
        specific = {
            # TODO Remove 'rdf' and 'dcterms' when mappings added to data context.
            "rdf:value": f"page={page_num}&viewrect={left},{top},{wd},{ht}",
            "dcterms:conformsTo": "http://tools.ietf.org/rfc/rfc3778",
        }
    else:
        raise Exception("Unknown localizer type!")

    return {**base, **specific}


# TODO Model the annotation of facts (i.e. no parameters).
def pa_hasbody(parameters: List[JSON], parameter_uuid_mapping: Dict[str, str]) -> List[JSON]:
    def t(x: JSON) -> JSON:
        return {
            "@id": parameter_uuid_mapping[x["id"]],
            "@type": "nsg:Parameter",
        }
    return [t(x) for x in parameters]


def pa_keywords(tags: List[JSON]) -> List[JSON]:
    def t(x: JSON) -> JSON:
        return {
            "@id": x["id"],
            "label": x["name"],
        }
    return [t(x) for x in tags]


def pa_experimentalproperties(experiment_properties: List[JSON],
                              parameter_uuid_mapping: Dict[str, str]) -> List[JSON]:
    def t(x):
        return {
            "@id": parameter_uuid_mapping[x["instanceId"]],
            "@type": "nsg:Parameter",
        }
    return [t(x) for x in experiment_properties]
