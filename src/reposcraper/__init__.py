import sys

from reposcraper.lib.main import run


# Causes the RESTful API to run.
if __name__ == '__main__':
    run(db_path=sys.argv[1])
