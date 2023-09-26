import json
from typing import Callable, Dict, List, Tuple, Union
import sys

from flask import Flask, request
from flask_restful import Api, Resource
from flasgger import Swagger
from codesurvey import CodeSurvey
from codesurvey.sources import GithubSampleSource, GitSource
from codesurvey.analyzers.python import PythonAstAnalyzer
from codesurvey.analyzers.python.features import (
    py_module_feature_finder, has_for_else, has_try_finally, has_type_hint, has_set_function,
    has_set_value, has_set, has_fstring, has_ternary, has_pattern_matching, has_walrus
)

from utils import create_response, SearchNames

__version__: str = '0.1.0'


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


# Initializes the application programming interface.
app: Flask = Flask(__name__)
with open("repo-scraper/swagger_config.json") as f:
    app.config['SWAGGER'] = json.load(f)

app.config['SWAGGER']['info']['version'] = __version__

api: Api = Api(app)
swagger: Swagger = Swagger(app)

# Modifies the API to create a response which allows for timestamps and
# dataclasses.
api.representations.update({
    'application/json': create_response
})


class Search(Resource):
    """Performs a basic search for certain features/modules within the
    requested resources.

    """
    @staticmethod
    def post() -> Tuple[Dict[str, Union[str, Dict, List[Dict]]], int]:
        """Searches for code features
        Returns the output from a search using the provided sources
        while looking for particular features.
        ---
        tags:
        - search
        requestBody:
          description: The sources used in the feature search.
          required: true
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/search'

        responses:
            200:
                description: Search succeeded.
                content:
                    application/json:
                        schema:
                            $ref: '#/components/schemas/search-results'
            422:
                description: Provided parameters cannot be processed.
                content:
                    application/json:
                        schema:
                            $ref: '#/components/schemas/error-message'
            default:
                description: An unexpected error occurred.
                content:
                    application/json:
                        schema:
                            type: object
                            description: The search failed.
                            properties:
                                message:
                                    type: string
                                    description: Error details.
                                    example: Internal Server Error

        """
        # Obtains the body parameters.
        body = request.get_json()

        # Returns errors if there are missing arguments.
        if 'sources' not in body or len(body['sources']) == 0:
            return {'error-message': 'No sources provided.'}, 422
        elif 'analyzers' not in body or len(body['analyzers']) == 0:
            return {'error-message': 'No analyzers provided.'}, 422

        # Prepares to collect all sources, analyzers, and names.
        sources = []
        analyzers = []
        search_names = SearchNames()

        # Prepares to collect all the names of every feature.
        feature_names = []

        # Adds each of the sources.
        for source in body['sources']:
            if sorted(source) == ['language']:
                sources.append(GithubSampleSource(
                    language=source['language'], name=search_names.generate_source_name()
                ))
            elif sorted(source) == ['repositories']:
                sources.append(GitSource(
                    source['repositories'], name=search_names.generate_source_name()
                ))
            else:
                return {'error-message': f'Unrecognized source: {source}.'}, 422

        # Adds every feature listed amongst the arguments to the search
        # features, and returns an error if a requested source is
        # unrecognized.
        for analyzer in body['analyzers']:
            # Prepares to find the names of every feature in the
            # analyzer.
            feature_finders = []

            # Adds each of the features to the analyzer.
            for feature in analyzer['features']:
                if feature in param_to_feature:
                    feature_finders.append(param_to_feature[feature])
                    feature_names.append(feature)
                else:
                    return {
                        'error-message': 'Unrecognized feature',
                        'feature-name': feature
                    }, 422

            # Adds each of the modules to the analyzer.
            if analyzer['modules']:
                feature_names.append(','.join(analyzer['modules']))
                feature_finders.append(py_module_feature_finder(
                    name=feature_names[-1], modules=analyzer['modules']
                ))

            # Creates an analyzer from the provided features and modules
            analyzers.append(PythonAstAnalyzer(
                feature_finders=feature_finders, name=search_names.generate_analyzer_name()
            ))

        # Creates a CodeSurvey object and runs the search.
        survey = CodeSurvey(
            db_filepath=sys.argv[1],
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
            'feature_names': feature_names
        }

        # Returns the output from the search.
        return {
            'repo-features': survey.get_repo_features(**db_filter),
            'code-features': survey.get_code_features(**db_filter),
            'survey-tree': survey.get_survey_tree(**db_filter)
        }, 200


# Binds the search resource to the /search path.
api.add_resource(Search, '/search')

# Causes the restful API to run.
app.run()
