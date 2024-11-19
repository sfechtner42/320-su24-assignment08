"""
implements database as a social network model
"""

# pylint: disable=R0903, E0401
from playhouse.dataset import DataSet

DATABASE = "databaseA08.db"


def get_ds():
    """
    Gets and returns the database used in other files
    """
    db = DataSet(f"sqlite:///{DATABASE}")
    return db
