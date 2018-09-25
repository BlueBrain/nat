__author__ = "Pierre-Alexandre Fonta"
__maintainer__ = "Pierre-Alexandre Fonta"

import json
import logging
import re
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path
from typing import Dict, Optional, List, Tuple, Any, Set, Union, Iterator, Iterable
from urllib.parse import urlparse

from openid_http_client.auth_client.access_token_client import AccessTokenClient
from pyxus.client import NexusClient
from pyxus.resources.entity import (Instance, Schema, Organization, Domain,
                                    SearchResultList, SearchResult)
from requests import HTTPError

from kg_utils import prepare


JSON = Dict[str, Any]


def prettify(data: JSON) -> None:
    print(json.dumps(data, indent=2))


def init_client(token: str, deployment: str) -> NexusClient:
    auth_client = AccessTokenClient(token)
    parsed = urlparse(deployment)
    alt_namespace = f"{parsed.scheme}://{parsed.netloc}"
    return NexusClient(parsed.scheme, parsed.netloc, parsed.path, alt_namespace, auth_client)


# Nexus v0 specific method.
def uuid_iri_mapping(instances: Iterable[Instance]) -> Iterator[Tuple[str, str]]:
    for x in instances:
        provider_uuid = x.data["providerId"]
        nexus_id = x.get_self_link()
        yield provider_uuid, nexus_id


@dataclass
class PipelineConfiguration:

    token: str = field(repr=False)
    deployment: str
    client: NexusClient = field(repr=False)
    organization: str
    domain: str
    organization_desc: str = ""
    domain_desc: str = ""
    data_context_version: str = field(default="v1.0.4")
    data_context: str = field(init=False)
    _key_separator: str = field(repr=False, init=False, default="/")

    def __post_init__(self):
        self.data_context = (f"{self.deployment}/contexts/neurosciencegraph/"
                             f"core/data/{self.data_context_version}")

    # is_xyz_pushed() methods.

    def is_organization_pushed(self) -> bool:
        organization = self.client.organizations.read(self.organization)
        return False if organization is None else True

    def is_domain_pushed(self) -> bool:
        domain = self.client.domains.read(self.organization, self.domain)
        return False if domain is None else True

    # TODO Add def is_context_pushed(self, name: str, version: str) -> bool.

    def is_schema_pushed(self, name: str, version: str) -> bool:
        schema = self.client.schemas.read(self.organization, self.domain, name, version)
        return False if schema is None else True

    def are_schemas_pushed(self, names_versions: List[Tuple[str, str]]) -> Dict[str, bool]:
        checks = dict()
        for name, version in names_versions:
            check = self.is_schema_pushed(name, version)
            checks[self._entity_name(name, version)] = check
        return checks

    # create_xyz() methods.

    def create_organization(self) -> Optional[Organization]:
        if self.is_organization_pushed():
            self._print_already_pushed(self.organization)
            return None
        else:
            local = Organization.create_new(self.organization, self.organization_desc)
            distant = self.client.organizations.create(local)
            self._print_pushed(self.organization)
            return distant

    def create_domain(self) -> Optional[Domain]:
        if self.is_domain_pushed():
            self._print_already_pushed(self.domain)
            return None
        else:
            local = Domain.create_new(self.organization, self.domain, self.domain_desc)
            distant = self.client.domains.create(local)
            self._print_pushed(self.domain)
            return distant

    # TODO Add def create_publish_context(self, name: str, version: str, data: JSON) -> Optional[Context].

    def create_publish_schema(self, name: str, version: str, data: JSON) -> Optional[Schema]:
        key = self._entity_name(name, version)
        if self.is_schema_pushed(name, version):
            self._print_already_pushed(key)
            return None
        else:
            local = Schema.create_new(self.organization, self.domain, name, version, data)
            schema = self.client.schemas.create(local)
            self.client.schemas.publish(schema, publish=True)
            self._print_pushed(key)
            return schema

    def create_publish_schemas(self, data: Dict[str, JSON]) -> Dict[str, Optional[Schema]]:
        schemas = dict()
        for key, data in data.items():
            name, version = self._entity_name_split(key)
            schema = self.create_publish_schema(name, version, data)
            schemas[key] = schema
        return schemas

    def create_instance(self, schema_name: str, schema_version: str, data: JSON) -> Optional[Instance]:
        if not self.is_schema_pushed(schema_name, schema_version):
            print("<error> Schema does not exist!")
            return None

        # TODO Check if the instance has already been pushed thanks to Nexus v1.
        local = Instance.create_new(self.organization, self.domain, schema_name,
                                    schema_version, data)

        # Note: Even if NexusClient.logger.hasHandlers() is False and
        # NexusClient.logger.propagate is set to False, the logging message is
        # displayed in the IPython notebook. A new logger is then needed.
        # Using  NexusClient.instances.create() outside the current method will
        # display the logging message as without the following modification.
        stream = StringIO()
        stream_handler = logging.StreamHandler(stream=stream)
        logger = logging.getLogger()
        logger.addHandler(stream_handler)

        try:
            return self.client.instances.create(local)
        except HTTPError:
            # Note: repr(HTTPError) is not informative on what really happened.
            # Note: The 'violations' key is two times in the string.
            message = stream.getvalue()
            match = re.search("""{"violations":[^}]+}$""", message)
            print("<error>")
            if match:
                errors = match.group(0)
                prettify(json.loads(errors))
            else:
                print("--- was not able to parse the error message ---")
            print("<data>")
            prettify(data)
            return None
        finally:
            # Note: StringIO.close() flushes and closes the stream.
            stream.close()
            logger.removeHandler(stream_handler)

    def create_instances(self, schema_name: str, schema_version: str, data: List[JSON],
                         start: int = 0, exclude_idxs: Set[int] = None) -> None:
        created_count = 0
        for i, x in enumerate(data[start:]):
            i0 = start + i
            if not exclude_idxs or (exclude_idxs and i0 not in exclude_idxs):
                instance = self.create_instance(schema_name, schema_version, x)
                if instance is None:
                    # TODO Handle better recovery from Nexus errors.
                    print("<index>", i0)
                    break
                else:
                    created_count += 1
        print("<count>", created_count)

    # load_prepare_xyz() methods

    def load_prepare_schema(self, neuroshapes_dir: str, name: str, version: str,
                            specific: bool = False) -> JSON:
        part_1 = Path(neuroshapes_dir, "modules")
        part_2 = Path("src/main/resources/schemas")
        part_3 = Path(name, f"{version}.json")

        if specific:
            path = (part_1 / self.organization / part_2 / "neurosciencegraph" /
                    self.organization / part_3)
        else:
            path = (part_1 / self.domain / part_2 / self.organization /
                    self.domain / part_3)

        with path.open() as f:
            data = json.load(f)
            prepared_data = prepare(data, [("{{base}}", self.deployment)])
            schema = json.loads(prepared_data)
            print("<prepared>", self._entity_name(name, version))
            return schema

    def load_prepare_schemas(self, neuroshapes_dir: str, names_versions: List[Tuple[str, str]],
                             specific: bool = False) -> Dict[str, JSON]:
        schemas = dict()
        for name, version in names_versions:
            key = self._entity_name(name, version)
            schema = self.load_prepare_schema(neuroshapes_dir, name, version, specific)
            schemas[key] = schema
        return schemas

    # instances_by_xyz() methods.

    def instances_by_schema(self, name: str, version: str, resolved: bool = False,
                            deprecated: bool = False) -> SearchResultList:
        # TODO Put size: int = None as parameter when Nexus removes the limit of 50.
        size = 50
        r = self.client.instances.list_by_schema(self.organization, self.domain,
                                                 name, version, resolved=resolved,
                                                 size=size, deprecated=deprecated)
        self._search_result_list_stats(r)
        return r

    def instances_of_domain(self, resolved: bool = False, deprecated: bool = False) -> SearchResultList:
        # TODO Put size: int = None as parameter when Nexus removes the limit of 50.
        size = 50
        r = self.client.instances.list(subpath=f"/{self.organization}/{self.domain}",
                                       resolved=resolved, size=size, deprecated=deprecated)
        self._search_result_list_stats(r)
        return r

    def retrieve_all_results(self, x: SearchResultList) -> Optional[List[Union[SearchResult, Instance]]]:
        results = x.results
        next_page = x.get_next_link()

        while next_page:
            y = self.client.instances.list_by_full_path(next_page)
            next_page = y.get_next_link()
            results.extend(y.results)

        try:
            assert(len(results) == x.total)
        except AssertionError:
            print("<error>", (f"Retrieved item count ({len(results)}) and "
                              f"result count ({x.total}) are different!"))
            return None

        return results

    # Cleaning helpers.

    def clean(self, organization: bool, domain: bool) -> None:
        with redirect_stdout(None):
            instances_search = self.instances_of_domain(resolved=True)
            instances = self.retrieve_all_results(instances_search)

        for x in instances:
            # The actual performed operation is a deprecation and not a deletion.
            # See issue https://github.com/HumanBrainProject/pyxus/issues/28.
            self.client.instances.delete(x)
        print("<deprecated>", len(instances), "instances")

        if domain:
            d = self.client.domains.read(self.organization, self.domain)
            self.client.domains.delete(d)
            print("<deprecated>", self.domain)

        if organization:
            o = self.client.organizations.read(self.organization)
            self.client.organizations.delete(o)
            print("<deprecated>", self.organization)

    # Internal helpers.

    @staticmethod
    def _print_already_pushed(name: str) -> None:
        print("<already pushed>", name)

    @staticmethod
    def _print_pushed(name: str) -> None:
        print("<pushed>", name)

    @staticmethod
    def _search_result_list_stats(x: SearchResultList) -> None:
        count = x.total
        print("<count>", count)
        if len(x.results) < count:
            print("<warning>", "More than one result page. Iteration required.")

    def _entity_name(self, name: str, version: str) -> str:
        return f"{name}{self._key_separator}{version}"

    def _entity_name_split(self, entity_name: str) -> Tuple[str, str]:
        name, version = entity_name.split(self._key_separator)
        return name, version
