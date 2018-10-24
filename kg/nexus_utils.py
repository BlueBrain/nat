__author__ = "Pierre-Alexandre Fonta"
__maintainer__ = "Pierre-Alexandre Fonta"

import json
import logging
import re
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path
from typing import (Dict, Optional, List, Tuple, Any, Set, Union, Iterator,
                    Iterable, Callable)
from urllib.parse import urlparse

from openid_http_client.auth_client.access_token_client import AccessTokenClient
from pyxus.client import NexusClient
from pyxus.resources.entity import (Instance, Schema, Organization, Domain,
                                    SearchResultList, SearchResult, Context)
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
        provider_uuid = x.data["nsg:providerId"]
        nexus_id = x.get_self_link()
        yield provider_uuid, nexus_id


@dataclass
class PipelineConfiguration:

    neuroshapes_dir: str
    client: NexusClient = field(repr=False)
    organization: str
    domain: str
    organization_desc: str = field(default="")
    domain_desc: str = field(default="")
    deployment: str = field(init=False)
    _key_separator: str = field(repr=False, init=False, default="/")

    def __post_init__(self):
        cfg = self.client.config
        self.deployment = cfg.NEXUS_ENDPOINT + cfg.NEXUS_PREFIX

    # Checking helpers.

    def is_organization_created(self) -> bool:
        organization = self.client.organizations.read(self.organization)
        return False if organization is None else True

    def is_domain_created(self) -> bool:
        domain = self.client.domains.read(self.organization, self.domain)
        return False if domain is None else True

    def is_context_created(self, name: str, version: str) -> bool:
        context = self.client.contexts.read(self.organization, self.domain, name, version)
        return False if context is None else True

    def is_schema_created(self, name: str, version: str) -> bool:
        schema = self.client.schemas.read(self.organization, self.domain, name, version)
        return False if schema is None else True

    def are_contexts_created(self, names_versions: List[Tuple[str, str]]) -> Dict[str, bool]:
        return self._fun_list_tuples(self.is_context_created, names_versions)

    def are_schemas_created(self, names_versions: List[Tuple[str, str]]) -> Dict[str, bool]:
        return self._fun_list_tuples(self.is_schema_created, names_versions)

    # Preparation helpers.

    def prepare_context(self, name: str, version: str) -> JSON:
        # TODO Make it generic when Neuroshapes will be (now tied to 'core' domain).
        mid_path = Path("commons/src/main/resources/contexts/neurosciencegraph/core/")
        return self._prepare_context_schema(name, version, mid_path)

    def prepare_schema(self, name: str, version: str, is_user_domain: bool = False) -> JSON:
        mid = "src/main/resources/schemas"
        if is_user_domain:
            mid_path = Path(self.organization, mid, "neurosciencegraph", self.organization)
        else:
            mid_path = Path(self.domain, mid, self.organization, self.domain)
        return self._prepare_context_schema(name, version, mid_path)

    def prepare_contexts(self, names_versions: List[Tuple[str, str]]) -> Dict[str, JSON]:
        return self._fun_list_tuples(self.prepare_context, names_versions)

    def prepare_schemas(self, names_versions: List[Tuple[str, str]], is_user_domain: bool = False) -> Dict[str, JSON]:
        return self._fun_list_tuples(self.prepare_schema, names_versions, is_user_domain)

    # Creation helpers.

    def create_organization(self) -> Organization:
        organization = self.client.organizations.read(self.organization)
        if organization is not None:
            self._print_already_created(self.organization)
            return organization
        else:
            local = Organization.create_new(self.organization, self.organization_desc)
            distant = self.client.organizations.create(local)
            self._print_created(self.organization)
            return distant

    def create_domain(self) -> Domain:
        domain = self.client.domains.read(self.organization, self.domain)
        if domain is not None:
            self._print_already_created(self.domain)
            return domain
        else:
            local = Domain.create_new(self.organization, self.domain, self.domain_desc)
            distant = self.client.domains.create(local)
            self._print_created(self.domain)
            return distant

    # TODO Handle when contexts or schemas are already created but not published.

    def create_context(self, name: str, version: str, data: JSON, publish: bool) -> Context:
        key = self._entity_name(name, version)
        context = self.client.contexts.read(self.organization, self.domain, name, version)
        if context is not None:
            self._print_already_created(key)
            return context
        else:
            local = Context.create_new(self.organization, self.domain, name, version, data)
            context = self.client.contexts.create(local)
            self.client.contexts.publish(context, publish=publish)
            self._print_created(key)
            return context

    def create_schema(self, name: str, version: str, data: JSON, publish: bool) -> Schema:
        key = self._entity_name(name, version)
        schema = self.client.schemas.read(self.organization, self.domain, name, version)
        if schema is not None:
            self._print_already_created(key)
            return schema
        else:
            local = Schema.create_new(self.organization, self.domain, name, version, data)
            schema = self.client.schemas.create(local)
            self.client.schemas.publish(schema, publish=publish)
            self._print_created(key)
            return schema

    def create_contexts(self, data: Dict[str, JSON], publish: bool) -> Dict[str, Context]:
        return self._create_contexts_schemas(self.create_context, data, publish)

    def create_schemas(self, data: Dict[str, JSON], publish: bool) -> Dict[str, Schema]:
        return self._create_contexts_schemas(self.create_schema, data, publish)

    def create_instance(self, schema_name: str, schema_version: str, data: JSON) -> Optional[Instance]:
        if not self.is_schema_created(schema_name, schema_version):
            print("<error> Schema does not exist!")
            return None

        # TODO Check if the instance has already been created when Nexus v1.
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
                print(message)
            print("<data>")
            prettify(data)
            return None
        finally:
            # Note: StringIO.close() flushes and closes the stream.
            stream.close()
            logger.removeHandler(stream_handler)

    def create_instances(self, schema_name: str, schema_version: str, data: List[JSON],
                         start_idx: int = 0, exclude_idxs: Set[int] = None) -> None:
        created_count = 0
        for i, x in enumerate(data[start_idx:]):
            i0 = start_idx + i
            if not exclude_idxs or (exclude_idxs and i0 not in exclude_idxs):
                instance = self.create_instance(schema_name, schema_version, x)
                if instance is None:
                    # TODO Handle better recovery from Nexus errors.
                    print("<index>", i0)
                    break
                else:
                    created_count += 1
        print("<count>", created_count)

    # Searching helpers.

    def instances_by_schema(self, name: str, version: str, resolve: bool = False) -> SearchResultList:
        # TODO Put size: int = None as parameter when Nexus removes the limit of 50.
        size = 50
        r = self.client.instances.list_by_schema(self.organization, self.domain,
                                                 name, version, resolved=resolve,
                                                 size=size)
        self._search_result_list_stats(r)
        return r

    def instances_of_domain(self, resolve: bool = False) -> SearchResultList:
        # TODO Put size: int = None as parameter when Nexus removes the limit of 50.
        size = 50
        r = self.client.instances.list(subpath=f"/{self.organization}/{self.domain}",
                                       resolved=resolve, size=size)
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
            instances_search = self.instances_of_domain(resolve=True)
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
    def _print_already_created(name: str) -> None:
        print("<already created>", name)

    @staticmethod
    def _print_created(name: str) -> None:
        print("<created>", name)

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

    def _prepare_context_schema(self, name: str, version: str, mid_path: Path) -> JSON:
        head_path = Path(self.neuroshapes_dir, "modules")
        tail_path = Path(name, f"{version}.json")
        path = head_path / mid_path / tail_path
        with path.open() as f:
            data = json.load(f)
            prepared_data = prepare(data, [("{{base}}", self.deployment)])
            prepared_json = json.loads(prepared_data)
            print("<prepared>", self._entity_name(name, version))
            return prepared_json

    def _create_contexts_schemas(self, fun: Callable, data: Dict[str, JSON], publish: bool) -> Dict[str, Any]:
        entities = dict()
        for key, data in data.items():
            name, version = self._entity_name_split(key)
            entity = fun(name, version, data, publish)
            entities[key] = entity
        return entities

    def _fun_list_tuples(self, fun: Callable, names_versions: List[Tuple[str, str]], *args) -> Dict[str, Any]:
        _dict = dict()
        for name, version in names_versions:
            key = self._entity_name(name, version)
            value = fun(name, version, *args)
            _dict[key] = value
        return _dict
