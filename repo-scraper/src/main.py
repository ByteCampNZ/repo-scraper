import json
from typing import Dict, List, Tuple, Union

from flask import Flask, request
from flask_restful import Api, Resource
from flasgger import Swagger


from utils import create_response, get_analyzers, get_sources, run_search, SearchNames

__version__: str = '0.1.1'

# Initializes and configures the application.
app: Flask = Flask(__name__)
with open("repo-scraper/swagger_config.json") as f:
    app.config['SWAGGER'] = json.load(f)

# Matches the API documented version to the package version.
app.config['SWAGGER']['info']['version'] = __version__

# Initializes the application programming interface and documentation.
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
        search_names = SearchNames()

        # Constructs all the sources and analyzers for the search.
        try:
            sources = get_sources(body['sources'], search_names)
            analyzers = get_analyzers(body['analyzers'], search_names)
        except ValueError as e:
            return {'error-message': str(e)}, 422

        # Runs the search and returns the output.
        return run_search(sources=sources, analyzers=analyzers, search_names=search_names), 422


# Binds the search resource to the /search path.
api.add_resource(Search, '/search')

# Causes the restful API to run.
app.run()
