import importlib.metadata
import json
from pathlib import Path
from typing import Dict, List, Tuple

from flasgger import Swagger
from flask import Flask, request
from flask_restful import Api, Resource

import reposcraper.lib.utils as utils


# Obtains the version from the package metadata.
__version__: str = importlib.metadata.version('repo-scraper')

# Initializes and configures the application.
_app: Flask = Flask(__name__)
_root: Path = Path(__file__).parent.parent
with open(_root / 'swagger' / 'swagger_config.json') as f:
    _app.config['SWAGGER'] = json.load(f)

# Matches the API documented version to the package version.
_app.config['SWAGGER']['info']['version'] = __version__

# Initializes the application programming interface and documentation.
_api: Api = Api(_app)
_swagger: Swagger = Swagger(_app)

# Modifies the API to create a response which allows for timestamps and
# dataclasses.
_api.representations.update({
    'application/json': utils.create_response
})


class Search(Resource):
    """Performs a basic search for certain features/modules within the
    requested resources.
    """
    def __init__(self, db_path: Path | str) -> None:
        """Stores the database path.

        Args:
            db_path: Path to the database where the results from the
                search are stored.
        """
        self.db_path: Path = Path(db_path)

    def post(self) -> Tuple[Dict[str, str | Dict | List[Dict]], int]:
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
        search_names = utils.SearchNames()

        # Constructs all the sources and analyzers for the search.
        try:
            sources = utils.get_sources(body['sources'], search_names)
            analyzers = utils.get_analyzers(body['analyzers'], search_names)
        except ValueError as e:
            return {'error-message': str(e)}, 422

        # Runs the search and returns the output.
        return utils.run_search(
            sources=sources, analyzers=analyzers, search_names=search_names, db_path=self.db_path
        ), 422


def run(db_path: Path | str) -> None:
    """Runs the RESTful API."""
    # Binds the search resource to the /search path.
    _api.add_resource(Search, '/search', resource_class_kwargs={'db_path': db_path})

    # Runs the application.
    _app.run()
