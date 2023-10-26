from dataclasses import asdict, is_dataclass
import datetime
import json
from pathlib import Path
from typing import Any, Callable, Dict, List

from codesurvey import CodeSurvey
from codesurvey.sources import GithubSampleSource, GitSource
from codesurvey.analyzers import Analyzer
from codesurvey.analyzers.python import PythonAstAnalyzer
from codesurvey.analyzers.python.features import (
    py_module_feature_finder, has_for_else, has_try_finally, has_type_hint, has_set_function,
    has_set_value, has_set, has_fstring, has_ternary, has_pattern_matching, has_walrus
)
from flask import make_response, Response
import shortuuid


param_to_feature: Dict[str, Callable[[], str]] = {
    'for-else': has_for_else,
    'try-finally': has_try_finally,
    'has-type-hint': has_type_hint,
    'set-function': has_set_function,
    'set-value': has_set_value,
    'set': has_set,
    'fstring': has_fstring,
    'ternary': has_ternary,
    'pattern-matching': has_pattern_matching,
    'walrus': has_walrus
}


class SearchNames:
    """Keeps a record of the names used for sources, features, and
    analyzers during a search.
    """
    def __init__(self) -> None:
        self.source_names: List[str] = []
        self.analyzer_names: List[str] = []
        self.feature_names: List[str] = []

    def generate_source_name(self) -> str:
        """Generates a short UUID for a new source name and stores it.

        Returns:
            The generated and stored UUID.
        """
        uuid = shortuuid.uuid()
        self.source_names.append(uuid)
        return uuid

    def generate_analyzer_name(self) -> str:
        """Generates a short UUID for a new analyzer name and stores it.

        Returns:
            The generated and stored UUID.
        """
        uuid = shortuuid.uuid()
        self.analyzer_names.append(uuid)
        return uuid

    def add_feature_name(self, name: str) -> None:
        """Stores a name for a new feature/module.

        Args:
            name: The name of the feature/module.
        """
        self.feature_names.append(name)


class ExtendedEncoder(json.JSONEncoder):
    """Extended JSON serializer, allowing for dates, datetimes, and
    dataclasses.
    """
    def default(self, obj: Any) -> str | int | List | Dict:
        """Returns the serialized form of the object.

        Args:
            obj: The object to be serialized.

        Returns:
            The object in its serialized form.
        """
        if isinstance(obj, datetime.datetime):
            return str(obj)

        elif isinstance(obj, datetime.date):
            return str(obj)

        elif is_dataclass(obj):
            return asdict(obj)

        return json.JSONEncoder.default(self, obj)


def create_response(data: Any, code: int, headers=None) -> Response:
    """Creates a response from the provided return data and return code.

    Args:
        data: The data to be returned to the client.
        code: The return code for the API response.
        headers: The HTTP headers for the response.

    Returns:
        The response from the provided constituent parts.
    """
    dumped = json.dumps(data, cls=ExtendedEncoder)
    resp = make_response(dumped, code)
    resp.headers.extend(headers or {})

    return resp


def get_sources(
        sources_blueprint: List[Dict[str, str | List[str]]],
        search_names: SearchNames
) -> List[GitSource | GithubSampleSource]:
    """Creates a list of CodeSurvey Source objects from the provided
    arguments, updating the list of source names in the process.

    Args:
        sources_blueprint: A dictionary with instructions to obtaining
            sources.
        search_names: A SearchNames instance to be populated with source
            names.

    Returns:
        A list of Source objects.
    """
    # Prepares a list of Source objects.
    sources = []

    # Iterates over each provided source in the blueprint.
    for source in sources_blueprint:
        # Creates the source if possible, but otherwise raises an error.
        if sorted(source) == ['language']:
            sources.append(GithubSampleSource(
                language=source['language'], name=search_names.generate_source_name()
            ))
        elif sorted(source) == ['repositories']:
            sources.append(GitSource(
                source['repositories'], name=search_names.generate_source_name()
            ))
        else:
            raise ValueError(f'Unrecognized source: {source}.')

    return sources


def get_analyzers(
        analyzers_blueprint: List[Dict[str, List[str]]],
        search_names: SearchNames
) -> List[Analyzer]:
    """Creates a list of CodeSurvey Analyzer objects from the provided
    arguments, updating the list of source names in the process.

    Args:
        analyzers_blueprint: A dictionary with instructions to obtaining
            analyzers.
        search_names: A SearchNames instance to be populated with
            analyzer names and features names.

    Returns:
        A list of Analyzer objects.
    """
    # Prepares a list of Analyzer objects.
    analyzers = []

    # Iterates over each provided analyzer in the blueprint.
    for analyzer in analyzers_blueprint:
        # Prepares to find the names of every feature in the
        # analyzer.
        feature_finders = []

        # Adds each of the features to the analyzer.
        for feature in analyzer['features']:
            if feature in param_to_feature:
                feature_finders.append(param_to_feature[feature])
                search_names.add_feature_name(feature)
            else:
                raise ValueError(f"Unrecognized feature: {feature}")

        # Adds each of the modules to the analyzer.
        if analyzer['modules']:
            search_names.add_feature_name(','.join(analyzer['modules']))
            feature_finders.append(py_module_feature_finder(
                name=search_names.feature_names[-1], modules=analyzer['modules']
            ))

        # Creates an analyzer from the provided features and modules
        analyzers.append(PythonAstAnalyzer(
            feature_finders=feature_finders, name=search_names.generate_analyzer_name()
        ))

    return analyzers


def run_search(
        *, sources: List[GitSource | GithubSampleSource],
        analyzers: List[Analyzer],
        search_names: SearchNames,
        db_path: Path
) -> Dict[str, str | Dict | List[Dict]]:
    """Uses generated sources and analyzers to perform a search
    operation.

    Args:
        sources: The sources for the search.
        analyzers: The analyzers applied on the sources.
        search_names: A SearchNames instance to be populated with
            source, analyzer, and feature names.
        db_path: Path to the database where the results from the search
            are stored.

    Returns:
        A dictionary containing the following:
            * The repository features;
            * The code features;
            * The survey tree.
    """
    # Creates a CodeSurvey object and runs the search.
    survey = CodeSurvey(
        db_filepath=db_path,
        sources=sources,
        analyzers=analyzers,
        max_workers=3,
        use_saved_features=False
    )
    survey.run(max_repos=4, disable_progress=True)

    # Defines the filtering to be performed on the database.
    db_filter = {
        'source_names': search_names.source_names,
        'analyzer_names': search_names.analyzer_names,
        'feature_names': search_names.feature_names
    }

    # Returns the output from the search.
    return {
        'repo-features': survey.get_repo_features(**db_filter),
        'code-features': survey.get_code_features(**db_filter),
        'survey-tree': survey.get_survey_tree(**db_filter)
    }
