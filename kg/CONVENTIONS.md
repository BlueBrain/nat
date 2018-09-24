# Styling rules for the transformation logic

For this use case, this applies to annotations.py and parameters.py.


## Function creation

**Functions called in a `dict`**

As soon as the mapping include a processing.

**When the field is a `list`**

Create a `t(x)` function (`t` for transform) for each nested object and use a
list comprehension calling this function. It makes the mapping testable and
git diffs more readable.


## Naming rules

#### Function name

**Entity transformation function**

`transform_` + `entity name`

**Field transformation function**

* `p` (for prepare) OR `h` (for helper)
* \+ `a` (for annotation) OR `p` (for parameter)
* \+ `_`
* \+ `target field name in lower case without underscores`.

If this target field name is nested, use underscore to put the parent path
hierarchy: `px_root_nested()`.

#### Function parameters

**What is passed:**

The lowest possible level field in the source data. Don't use Python variable
to store this field so that it remains clear which one is used in the
`transform_xyz()` function.

**What is in the function signature:**

`Source field name in lower case with underscores before each upper case letter
in the source field name`.

#### Function returned values

`px_yyy()` functions (prepare) return only one value.

`hx_zzz()` functions (helper) can return more than one value.


## Style rules

Indent the dicts like pretty JSONs. So, no { ... } or [ ... ] on one line.

For sibling fields in the dict(s) of the `transform_xyz()`function, introduce
an empty line between fields.

Last element of dicts has a `,` at the end for more readable git diffs.

The `mapping` dict is always at the beginning of the function body.

#### Function order

First the transform_xyz() one and after the px_yyy() ones in the order they are used.

The nested `t(x)` is at the beginning of the function which uses one. 

### Tackling complex conditional cases

Use dictionary merging.

Example/Template:

```
def hp_variable(parameter_type: str, variable: JSON) -> JSON:
    def t(x: JSON) -> JSON:
        ...

    _type = hp_variable_type(parameter_type, variable)

    base = {
        "@type": _type,
        "quantityType": "nsg:" + variable["typeId"],
    }

    if _type == "nsg:SimpleNumericalVariable":
        specific = {
            "series": t(variable["values"]),
        }

    elif _type == "nsg:CompoundNumericalVariable":
        specific = {
            "series": [t(x) for x in variable["values"]["valueLst"]],
        }

    else:
        raise Exception("Unknown variable type!")

    return {**base, **specific}
```
