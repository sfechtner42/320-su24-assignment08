"""
Main driver for a simple social network project using a functional approach
"""

import csv
from peewee import IntegrityError
from socialnetwork_model import get_ds

db = get_ds()
USER_TABLE = "UserModel"
STATUS_TABLE = "StatusModel"
BATCH_SIZE = 10000

def init_database():
    '''
    Creates and returns a new instance of a database
    '''
    db = get_ds()
    # make sure user_id column is unique
    if db[USER_TABLE].columns == ["id"]:
        db[USER_TABLE].insert(id=-1,
                              user_id="dummy",
                              user_email="dummy",
                              user_name="dummy",
                              user_last_name="dummy")
        db[USER_TABLE].delete(id=-1)
    db[USER_TABLE].create_index(["user_id"], unique=True)
    # make sure status_id column is unique
    if db[STATUS_TABLE].columns == ["id"]:
        db[STATUS_TABLE].insert(id=-1,
                                status_id="dummy",
                                user_id="dummy",
                                status_text="dummy")
        db[STATUS_TABLE].delete(id=-1)
    db[STATUS_TABLE].create_index(["status_id"], unique=True)
    return db

# User-related functions

def add_user(user_data):
    """
    Adds a new user to the database. Returns True if the user was added successfully, False otherwise.
    """
    existing_user = db[USER_TABLE].find_one(user_id=user_data['user_id'])
    if existing_user:
        print(f"User with ID {user_data['user_id']} already exists.")
        return False

    try:
        db[USER_TABLE].insert(**user_data)
        return True
    except IntegrityError:
        print(f"Failed to add user due to IntegrityError: {user_data}")
        return False

def update_user(user_id, email, user_name, user_last_name):
    """
    Updates a user in the database.
    """
    user_to_modify = search_user(user_id)
    if not user_to_modify:
        return False
    try:
        db[USER_TABLE].update(
            user_email=email,
            user_name=user_name,
            user_last_name=user_last_name
        ).where(db[USER_TABLE].user_id == user_id).execute()
        return True
    except Exception as e:
        print(f"An error occurred while updating user: {e}")
        return False

def delete_user(user_id):
    """
    Deletes a user from the database and all associated statuses. Returns True if the deletion was successful, False otherwise.
    """
    try:
        # First, delete all statuses associated with the user
        statuses = db[STATUS_TABLE].find(user_id=user_id)
        for status in statuses:
            delete_status(status["status_id"])

        # Then, delete the user
        db[USER_TABLE].delete().where(db[USER_TABLE].user_id == user_id).execute()
        return True

    except Exception as e:
        print(f"An error occurred while deleting user: {e}")
        return False

def search_user(user_id):
    """
    Searches for a user in the database and returns their data if found.
    """
    try:
        return db[USER_TABLE].find_one(user_id=user_id)
    except Exception as e:
        print(f"An error occurred while searching for user: {e}")
        return None

def load_users(filename):
    """
    Opens a CSV file with user data and adds it to the database.
    """
    try:
        with open(filename, encoding="utf-8", newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if all(
                        key in row and row[key]
                        for key in ["USER_ID", "EMAIL", "NAME", "LASTNAME"]
                ):
                    user_data = {
                        "user_id": row["USER_ID"],
                        "user_email": row["EMAIL"],
                        "user_name": row["NAME"],
                        "user_last_name": row["LASTNAME"],
                    }
                    add_user(user_data)
            return True
    except (FileNotFoundError, KeyError) as e:
        print(f"An error occurred while loading users: {e}")
        return False

# Status-related functions

def add_status(status_id, user_id, status_text):
    """
    Adds a new status for a user in the database. Returns True if the status was added successfully, False otherwise.
    """
    if db[USER_TABLE].find_one(user_id=user_id):
        try:
            db[STATUS_TABLE].insert(
                status_id=status_id,
                user_id=user_id,
                status_text=status_text
            )
            return True
        except IntegrityError:
            print(f"Failed to add status due to IntegrityError: {status_id}, {user_id}")
            return False
    return False

def update_status(status_id, user_id, status_text):
    """
    Updates information for an existing status. Returns True if the update was successful, False otherwise.
    """
    if db[STATUS_TABLE].find_one(status_id=status_id):
        try:
            updated_count = db[STATUS_TABLE].update(
                status_text=status_text
            ).where(db[STATUS_TABLE].status_id == status_id).execute()
            return updated_count > 0
        except Exception as e:
            print(f"An error occurred while updating status: {e}")
            return False
    return False

def delete_status(status_id):
    """
    Deletes a status from the database. Returns True if the deletion was successful, False otherwise.
    """
    try:
        if db[STATUS_TABLE].find_one(status_id=status_id):
            db[STATUS_TABLE].delete().where(db[STATUS_TABLE].status_id == status_id).execute()
            return True
        return False
    except Exception as e:
        print(f"An error occurred while deleting status: {e}")
        return False

def search_status(status_id):
    """
    Searches for a status in the database and returns its data if found.
    """
    try:
        return db[STATUS_TABLE].find_one(status_id=status_id)
    except Exception as e:
        print(f"An error occurred while searching for status: {e}")
        return None

def load_status_updates(filename):
    """
    Opens a CSV file with status update data and adds it to the database.
    """
    try:
        with open(filename, encoding="utf-8", newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if all(
                        key in row and row[key]
                        for key in ["STATUS_ID", "USER_ID", "STATUS_TEXT"]
                ):
                    status_data = {
                        "status_id": row["STATUS_ID"],
                        "user_id": row["USER_ID"],
                        "status_text": row["STATUS_TEXT"],
                    }
                    add_status(**status_data)
            return True
    except (FileNotFoundError, KeyError) as e:
        print(f"An error occurred while loading statuses: {e}")
        return False

def delete_status_without_user():
    """
    Delete statuses without a user in the database.
    """
    user_table = db[USER_TABLE]
    status_table = db[STATUS_TABLE]
    user_query = user_table.find()
    status_query = status_table.find()

    status_user_id_set = set()
    for status in status_query:
        status_user_id_set.add(status["user_id"])
    user_id_set = set()
    for user in user_query:
        user_id_set.add(user["user_id"])

    difference = list(status_user_id_set.difference(user_id_set))
    with db.transaction():
        for diff in difference:
            status_table.delete(user_id=diff)
