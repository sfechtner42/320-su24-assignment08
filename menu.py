"""
Provides a basic frontend for the social network project
"""

import sys
import main


def load_users():
    """
    Loads user accounts from a file
    """
    filename = input("Enter filename of user file: ")
    if not main.load_users(filename):
        print("An error occurred while loading users.")
    else:
        print("Accounts loaded successfully.")


def load_status_updates():
    """
    Loads status updates from a file
    """
    filename = input("Enter filename for status file: ")
    if not main.load_status_updates(filename):
        print("An error occurred while loading status updates.")
    else:
        print("Status updates loaded successfully.")


def add_user():
    '''
    adds a new user
    '''

    user_id = input("User ID: ")
    email = input("User email: ")
    user_name = input("User name: ")
    user_last_name = input("User last name: ")

    user_data = {
        "user_id": user_id,
        "user_email": email,
        "user_name": user_name,
        "user_last_name": user_last_name
    }

    if not main.add_user(user_data):
        print(f"Failed to add user: {user_data}")
    else:
        print("User added successfully.")


def update_user():
    """
    Updates information for an existing user.
    """
    user_id = input('User ID: ')
    email = input('User email: ')
    user_name = input('User name: ')
    user_last_name = input('User last name: ')

    if main.update_user(main.db, user_id, email, user_name, user_last_name):
        print("User was successfully updated")
    else:
        print("An error occurred while trying to update user; check user id")


def search_user():
    """
    Searches for a user in the database.
    """
    user_id = input('Enter user ID to search: ')
    # Get the search function from scrap_main
    search_function = main.search_user()
    result = search_function(user_id)
    if result:
        print(f"User ID: {result['user_id']}")
        print(f"Email: {result['user_email']}")
        print(f"Name: {result['user_name']}")
        print(f"Last name: {result['user_last_name']}")
    else:
        print("User not found")


def delete_user():
    """
    Deletes a user from the database.
    """
    user_id = input("Enter user ID to delete: ")
    if main.delete_user(user_id):
        print("User was successfully deleted.")
    else:
        print("An error occurred while trying to delete user; check user id")


def add_status():
    '''
    Adds a new status to the database.
    '''
    status_id = input("Status ID: ")
    user_id = input("User ID: ")
    status_text = input("Status text: ")

    # Initialize the function with the database instance
    add_status_function = main.create_add_status_function()

    if add_status_function(status_id, user_id, status_text):
        print("New status was successfully added.")
    else:
        print("An error occurred while trying to add new status.")


def update_status():
    '''
    Updates information for an existing status. Only with corrct status and user id's.
    '''
    status_id = input("Enter status ID to update: ")
    user_id = input("Enter user ID for the status: ")
    status_text = input("Enter new status text: ")

    if main.update_status(status_id, user_id, status_text):
        print("Status was successfully updated.")
    else:
        print("An error occurred while trying to update status; check user and status id's")


def search_status():
    """
    Searches for a status in the database.
    """
    status_id = input('Enter status ID to search: ')
    result = main.search_status(status_id)
    if result:
        print(f"User ID: {result['user_id']}")
        print(f"Status ID: {result['status_id']}")
        print(f"Status text: {result['status_text']}")
    else:
        print("Status not found")


def delete_status():
    """
    Deletes a status from the database.
    """
    status_id = input("Enter status ID to delete: ")
    if main.delete_status(status_id):
        print("Status was successfully deleted.")
    else:
        print("An error occurred while trying to delete status; check status id")

# not needed
# def delete_status_without_user():
#     """
#     Deletes statuses without a user from the database.
#     """
#     main.delete_status_without_user()


def quit_program():
    '''
    Quits the program.
    '''
    sys.exit()


if __name__ == "__main__":
    menu_options = {
        "A": load_users,
        "B": load_status_updates,
        "C": add_user,
        "D": update_user,
        "E": search_user,
        "F": delete_user,
        "G": add_status,
        "H": update_status,
        "I": search_status,
        "J": delete_status,
        "Q": quit_program,
    }

    while True:
        user_selection = input(
            """
                            A: Load user database
                            B: Load status database
                            C: Add user
                            D: Update user
                            E: Search user
                            F: Delete user
                            G: Add status
                            H: Update status
                            I: Search status
                            J: Delete status
                            Q: Quit

                            Please enter your choice: """
        ).upper()

        if user_selection in menu_options:
            menu_options[user_selection]()
        else:
            print("Invalid option")
