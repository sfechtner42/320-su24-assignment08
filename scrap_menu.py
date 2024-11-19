"""
Provides a basic frontend for the social network project
"""

import sys
import scrap_main

def load_users():
    """
    Loads user accounts from a file
    """
    filename = input("Enter filename of user file: ")
    if not scrap_main.load_users(filename):
        print("An error occurred while loading users.")
    else:
        print("Accounts loaded successfully.")

def load_status_updates():
    """
    Loads status updates from a file
    """
    filename = input("Enter filename for status file: ")
    if not scrap_main.load_status_updates(filename):
        print("An error occurred while loading status updates.")
    else:
        print("Status updates loaded successfully.")

def add_user():
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

    if not scrap_main.add_user(user_data):
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

    if scrap_main.update_user(user_id, email, user_name, user_last_name):
        print("User was successfully updated")
    else:
        print("An error occurred while trying to update user; check user id")

def search_user():
    """
    Searches for a user in the database.
    """
    user_id = input('Enter user ID to search: ')
    result = scrap_main.search_user(user_id)
    if result:
        print(f"User found: {result}")
    else:
        print("User not found")

def delete_user():
    """
    Deletes a user from the database.
    """
    user_id = input("Enter user ID to delete: ")
    if scrap_main.delete_user(user_id):
        print("User was successfully deleted.")
    else:
        print("An error occurred while trying to delete user; check user id")

def add_status():
    status_id = input("Status ID: ")
    user_id = input("User ID: ")
    status_text = input("Status text: ")

    if scrap_main.add_status(status_id, user_id, status_text):
        print("New status was successfully added.")
    else:
        print("An error occurred while trying to add new status")

def update_status():
    status_id = input("Enter status ID to update: ")
    user_id = input("Enter new user ID for the status: ")
    status_text = input("Enter new status text: ")

    if scrap_main.update_status(status_id, user_id, status_text):
        print("Status was successfully updated.")
    else:
        print("An error occurred while trying to update status")

def search_status():
    """
    Searches for a status in the database.
    """
    status_id = input('Enter status ID to search: ')
    result = scrap_main.search_status(status_id)
    if result:
        print(f"Status found: {result}")
    else:
        print("Status not found")

def delete_status():
    """
    Deletes a status from the database.
    """
    status_id = input("Enter status ID to delete: ")
    if scrap_main.delete_status(status_id):
        print("Status was successfully deleted.")
    else:
        print("An error occurred while trying to delete status; check status id")

def delete_status_without_user():
    """
    Deletes statuses without a user from the database.
    """
    scrap_main.delete_status_without_user()

def quit_program():
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
