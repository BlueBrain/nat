__author__ = "Pierre-Alexandre Fonta"
__maintainer__ = "Pierre-Alexandre Fonta"

import traceback
from typing import List, Dict, Iterator, Optional, Any

from kg_utils import remove_empty_values
from nexus_utils import prettify


JSON = Dict[str, Any]


def transform_parameters(raw_annotations: List[JSON], data_context_iri: str,
                         variable_type_labels: Dict[str, str]) -> Iterator[JSON]:
    for i, x in enumerate(raw_annotations):
        for y in x["parameters"]:
            json_ld = transform_parameter(y, data_context_iri, variable_type_labels)
            if json_ld is None:
                # TODO Handle better recovery from transformation errors.
                print("<index>", i)
                break
            else:
                yield json_ld


# TODO Model the field 'relationship' from the source data.
def transform_parameter(x: JSON, data_context_iri: str,
                        variable_type_labels: Dict[str, str]) -> Optional[JSON]:
    try:
        _type = hp_type(x["description"]["type"])

        base_top = {
            "@context": data_context_iri,

            "@type": pp_type(_type, x["isExperimentProperty"]),

            # EntityShape properties.

            "schema:name": pp_name(x["id"], x["description"]["depVar"]["typeId"], variable_type_labels),

            "nsg:providerId": x["id"],

            # ParameterShape common derived properties.

            "nsg:dependentVariable": hp_variable(_type, x["description"]["depVar"]),
        }

        if _type == "nsg:NumericalTraceParameter":
            specific = {
                # NumericalTraceParameterShape properties.

                "nsg:independentVariable": pp_independentvariable(_type, x["description"]["indepVars"]),
            }
        elif _type == "nsg:FunctionParameter":
            specific = {
                # FunctionParameterShape properties.

                "nsg:independentVariable": pp_independentvariable(_type, x["description"]["indepVars"]),

                "nsg:equation": x["description"]["equation"],

                # Specific properties.

                "nsg:equationParameter": pp_equationparameter(x["description"]["parameterRefs"]),
            }
        else:
            specific = {}

        merged = {**base_top, **specific}

        base_bottom = {
            # Specific properties.

            "nsg:requiredTag": pp_requiredtag(x["requiredTags"]),
        }

        result = {**merged, **base_bottom}

        remove_empty_values(result)

        return result

    except Exception:
        print("<error>")
        print(traceback.format_exc())
        print("<data>")
        prettify(x)
        return None


def hp_type(_type: str) -> str:
    mapping = {
        "pointValue": "nsg:PointValueParameter",
        "numericalTrace": "nsg:NumericalTraceParameter",
        "function": "nsg:FunctionParameter",
    }
    return mapping[_type]


def pp_type(_type: str, is_experiment_property: bool) -> List[str]:
    if is_experiment_property:
        return [
            _type,
            "nsg:ExperimentalPropertyParameter",
        ]
    else:
        return [_type]


def pp_name(_id: str, type_id: str, variable_type_labels: Dict[str, str]) -> str:
    return f"p-{variable_type_labels[type_id]}-{_id[:8]}"


def hp_variable_type(parameter_type: str, variable: JSON) -> str:
    mapping = {
        "simple": "nsg:SimpleNumericalVariable",
        "compound": "nsg:CompoundNumericalVariable",
        "compounded": "nsg:CompoundNumericalVariable",
        "function": "nsg:AlgebraicVariable",
    }

    # Note: variable["values"]["type"] does not exist for 'nsg:FunctionParameter'.
    if parameter_type == "nsg:FunctionParameter":
        _type = "function"
    else:
        _type = variable["values"]["type"]

    return mapping[_type]


def hp_variable(parameter_type: str, variable: JSON) -> JSON:
    def t(x: JSON) -> JSON:
        values = [float(y) for y in x["values"]]
        value = values[0] if len(values) == 1 else values
        base = {
            # ValueShape properties.
            "schema:unitCode": x["unit"],
            "schema:value": value,
        }
        statistic = x["statistic"]
        if statistic != "raw":
            specific = {
                "nsg:statistic": statistic,
            }
        else:
            specific = {}
        return {**specific, **base}

    _type = hp_variable_type(parameter_type, variable)

    base = {
        "@type": [
            _type,
        ],

        # VariableShape common derived properties.
        "nsg:quantityType": variable["typeId"],
    }

    if _type == "nsg:SimpleNumericalVariable":
        specific = {
            # SimpleNumericalVariableShape properties.
            "nsg:series": t(variable["values"]),
        }

    elif _type == "nsg:CompoundNumericalVariable":
        specific = {
            # CompoundNumericalVariableShape properties.
            "nsg:series": [t(x) for x in variable["values"]["valueLst"]],
        }

    elif _type == "nsg:AlgebraicVariable":
        base_algebraic_value = {
            # AlgebraicValueShape properties.
            "schema:unitCode": variable["unit"],
        }
        statistic = variable["statistic"]
        if statistic != "raw":
            specific = {
                "nsg:statistic": statistic,
                **base_algebraic_value,
            }
        else:
            specific = base_algebraic_value
    else:
        raise Exception("Unknown variable type!", _type)

    return {**base, **specific}


def pp_independentvariable(parameter_type: str, indep_vars: List[JSON]) -> List[JSON]:
    return [hp_variable(parameter_type, x) for x in indep_vars]


def pp_equationparameter(parameter_refs: List[JSON]) -> List[JSON]:
    def t(x: JSON) -> JSON:
        return {
            "@id": x["instanceId"],  # TODO Use the user-provided ID feature of Nexus v1.
            "@type": [
                "nsg:Parameter",
            ],
        }
    return [t(x) for x in parameter_refs]


def pp_requiredtag(required_tags: List[JSON]) -> List[JSON]:
    def t(x: JSON) -> JSON:
        return {
            "nsg:rootId": x["rootId"],
            "@id": x["id"],
            "rdfs:label": x["name"],
        }
    return [t(x) for x in required_tags]
