"""
Main driver for a simple social network project using a functional approach
"""

import csv
from peewee import IntegrityError
from socialnetwork_model import get_ds

db = get_ds()
USER_TABLE = "UserModel"
STATUS_TABLE = "StatusModel"

# pylint: disable= C0301, W0621, W0718

def init_database():
    """
    Creates and returns a new instance of a database
    """
    db = get_ds()

    # Ensure the user_id column is unique
    if db[USER_TABLE].columns == ["id"]:
        # Create the index directly if columns match
        db[USER_TABLE].create_index(["user_id"], unique=True)

    # Ensure the status_id column is unique
    if db[STATUS_TABLE].columns == ["id"]:
        # Create the index directly if columns match
        db[STATUS_TABLE].create_index(["status_id"], unique=True)

    return db

# Load databases
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
                    try:
                        db[USER_TABLE].insert(**user_data)
                    except IntegrityError:
                        print(f"Failed to add user due to IntegrityError: {user_data}")
            return True
    except (FileNotFoundError, KeyError) as e:
        print(f"An error occurred while loading users: {e}")
        return False

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

                    try:
                        db[STATUS_TABLE].insert(**status_data)
                    except IntegrityError:
                        print(f"Failed to add status due to IntegrityError: {status_data}")
                        return False
            return True
    except (FileNotFoundError, KeyError) as e:
        print(f"An error occurred while loading statuses: {e}")
        return False


def validate_length(value, max_length):
    """Utility function to validate the length of a given value."""
    if len(value) > max_length:
        print(f"Value '{value}' exceeds maximum length of {max_length} characters.")
        return False
    return True

# User-related functions

def add_user(user_data):
    """
    Adds a new user to the database. Returns True if the user was added successfully, False otherwise.
    """
    # Validate user data
    user_id_valid = validate_length(user_data['user_id'], 30)
    user_name_valid = validate_length(user_data['user_name'], 30)
    user_last_name_valid = validate_length(user_data['user_last_name'], 100)

    if not (user_id_valid and user_name_valid and user_last_name_valid):
        return False

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


def update_user(db, user_id, email, user_name, user_last_name):
    """
    Updates a user in the database.
    """
    # Search for the user first
    user_to_modify = search_user()(user_id=user_id)
    if not user_to_modify:
        print("Nothing to update.")
        return False

    # Perform the update within a transaction
    with db.transaction():
        db[USER_TABLE].update(
            user_id=user_id,
            user_email=email,
            user_name=user_name,
            user_last_name=user_last_name,
            columns=["user_id"]
        )
        return True


def delete_user(user_id):
    """
    Deletes a user from the database and all associated statuses. Returns True if the deletion was successful, False otherwise.
    """
    try:
        # Flag to track if all deletions are successful
        all_statuses_deleted = True

        # Retrieve and delete all statuses associated with the user
        statuses = db[STATUS_TABLE].find(user_id=user_id)
        for status in statuses:
            status_id = status["status_id"]
            try:
                status_to_delete = db[STATUS_TABLE].find_one(status_id=status_id)
                if status_to_delete:
                    db[STATUS_TABLE].delete(id=status_to_delete["id"])
                else:
                    print(f"Status record not found for status_id: {status_id}")
                    all_statuses_deleted = False
            except Exception as e:
                print(f"Failed to delete status with status_id: {status_id}. Error: {e}")
                all_statuses_deleted = False

        # Delete the user
        user_to_delete = db[USER_TABLE].find_one(user_id=user_id)
        if user_to_delete:
            db[USER_TABLE].delete(id=user_to_delete["id"])
            user_deleted = True
        else:
            print(f"User record not found for user_id: {user_id}")
            user_deleted = False

        # Return True only if both statuses and user were successfully deleted
        return all_statuses_deleted and user_deleted

    except Exception as e:
        print(f"An error occurred while deleting user: {e}")
        return False


def search_user():
    """
    Returns a function to search for a user by user_id in the database.
    """

    def search(user_id):
        try:
            user = db[USER_TABLE].find_one(user_id=user_id)
            if user is None:
                print(f"User with user_id {user_id} not found.")
                return None
            return user
        except Exception as e:
            print(f"An error occurred while searching for user_id {user_id}: {e}")
            return None

    return search


# Status-related functions

def create_add_status_function():  # Closure example
    """
    Returns a function to add a new status for a user in the database with a closure to remember which users are already verified.
    """
    # Initialize a set to keep track of verified user IDs
    verified_users = set()

    def add_status(status_id, user_id, status_text):
        """
        Adds a new status for a user in the database. Returns True if the status was added successfully, False otherwise.
        """
        # Check if user exists in the database
        user_exists = db[USER_TABLE].find_one(user_id=user_id)

        # Check if the status_id already exists in the database
        status_exists = db[STATUS_TABLE].find_one(status_id=status_id)

        # Use closure variable to track if user has already been verified
        if user_exists:
            if user_id not in verified_users:
                verified_users.add(user_id)  # Add user to the set of verified users

            if not status_exists:
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
            else:
                print(f"Failed to add status due to duplicate status_id: {status_id}")
                return False
        else:
            print(f"Failed to add status because user_id does not exist: {user_id}")
            return False

    return add_status


def update_status(status_id, user_id, status_text):
    """
    Updates information for an existing status. Returns True if the update was successful, False otherwise.
    """
    # Search for the user first
    status_to_modify = search_user()(user_id=user_id)
    if not status_to_modify:
        return False

    # Check if the status ID exists in the status table
    existing_status = db[STATUS_TABLE].find_one(status_id=status_id)
    if not existing_status:
        return False

    try:
        # Perform the update within a transaction
        with db.transaction():
            db[STATUS_TABLE].update(
                status_id=status_id,
                user_id=user_id,
                status_text=status_text,
                columns=["status_id"]
            )
        return True
    except Exception as e:
        print(f"An error occurred during the transaction: {e}")
        return False


def delete_status(status_id):
    """
    Deletes a status from the database. Returns True if the deletion was successful, False otherwise.
    """
    try:
        status_to_delete = db[STATUS_TABLE].find_one(status_id=status_id)
        if status_to_delete:
            db[STATUS_TABLE].delete(id=status_to_delete["id"])
            return True
        print(f"Status record not found for status_id: {status_id} ")
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

# # not sure if needed?
# def delete_status_without_user():
#     """
#     Delete statuses without a user in the database.
#     """
#     user_table = db[USER_TABLE]
#     status_table = db[STATUS_TABLE]
#     user_query = user_table.find()
#     status_query = status_table.find()
#
#     status_user_id_set = set()
#     for status in status_query:
#         status_user_id_set.add(status["user_id"])
#     user_id_set = set()
#     for user in user_query:
#         user_id_set.add(user["user_id"])
#
#     difference = list(status_user_id_set.difference(user_id_set))
#     with db.transaction():
#         for diff in difference:
#             status_table.delete(user_id=diff)
