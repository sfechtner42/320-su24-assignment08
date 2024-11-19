"""Unittests for main.py"""
import unittest
from unittest.mock import patch, MagicMock
from peewee import IntegrityError
import main
from main import USER_TABLE, STATUS_TABLE

USER_TABLE = "UserModel"
STATUS_TABLE = "StatusModel"


# pylint: disable= C0301, E1101, C0302
class TestInitDatabase(unittest.TestCase):
    '''testing initializing database'''

    def setUp(self):
        # Create mock objects for database and tables
        self.mock_db = MagicMock()
        self.mock_user_table = MagicMock()
        self.mock_status_table = MagicMock()

        # Simulate initial columns state
        self.mock_user_table.columns = ["id"]
        self.mock_status_table.columns = ["id"]

        # Set up the mock database to return the mock tables
        self.mock_db.__getitem__.side_effect = lambda key: {
            USER_TABLE: self.mock_user_table,
            STATUS_TABLE: self.mock_status_table
        }.get(key, None)

        # Mock get_ds to return our mock database
        patch('main.get_ds', return_value=self.mock_db).start()

    def test_init_database(self):
        """
        Test for init_database function in the main module.
        """
        # Call the function
        db = main.init_database()

        # Assertions
        self.assertIsNotNone(db.get(USER_TABLE), "USER_TABLE is not correctly mocked")
        self.assertIsNotNone(db.get(STATUS_TABLE), "STATUS_TABLE is not correctly mocked")

        # Verify that create_index was called correctly
        self.mock_user_table.create_index.assert_called_once_with(["user_id"], unique=True)
        self.mock_status_table.create_index.assert_called_once_with(["status_id"], unique=True)


class TestMainUserFunctions(unittest.TestCase):
    """
    Unit tests for user-related functions in main.py
    """

    def setUp(self):
        """
        Set up test environment.
        """
        self.mock_db = MagicMock()
        self.mock_user_table = MagicMock()
        self.mock_db.__getitem__.side_effect = {
            USER_TABLE: self.mock_user_table,
            STATUS_TABLE: MagicMock()
        }.get

    @patch('main.db')
    def test_load_users_success(self, mock_db):
        """
        Test successful loading of users from a CSV file.
        """
        mock_dictreader = MagicMock()
        mock_dictreader.__iter__.return_value = [
            {
                "USER_ID": "Test",
                "EMAIL": "test@uw.edu",
                "NAME": "Test",
                "LASTNAME": "Test",
            },
            {
                "USER_ID": "SF",
                "EMAIL": "safe@uw.edu",
                "NAME": "Sabrina",
                "LASTNAME": "Fechtner",
            },
        ]

        mock_user_table = MagicMock()
        mock_db.__getitem__.return_value = mock_user_table
        mock_user_table.insert = MagicMock()

        with patch("builtins.open", create=True), patch("csv.DictReader", return_value=mock_dictreader):
            result = main.load_users("test.csv")
            self.assertTrue(result)

            called_args = [call.kwargs for call in mock_user_table.insert.call_args_list]

            self.assertEqual(
                called_args,
                [
                    {
                        "user_id": "Test",
                        "user_email": "test@uw.edu",
                        "user_name": "Test",
                        "user_last_name": "Test",
                    },
                    {
                        "user_id": "SF",
                        "user_email": "safe@uw.edu",
                        "user_name": "Sabrina",
                        "user_last_name": "Fechtner",
                    },
                ]
            )

    def test_load_users_failure(self):
        """
        Test failure when loading users from a non-existent CSV file.
        """
        with patch("builtins.open", side_effect=FileNotFoundError):
            result = main.load_users("nonexistent.csv")
            self.assertFalse(result)

    @patch('main.db')
    @patch('builtins.print')
    def test_load_users_integrity_error(self, mock_print, mock_db):
        """ Test handling of IntegrityError when inserting user data into the database. """
        # Mock the insert method to raise IntegrityError
        mock_insert = MagicMock(side_effect=IntegrityError("Integrity Error"))
        mock_db[USER_TABLE].insert = mock_insert

        # Simulate CSV data
        csv_data = 'USER_ID,EMAIL,NAME,LASTNAME\nuser1,email1,name1,last1\n'
        with patch('builtins.open', new_callable=unittest.mock.mock_open, read_data=csv_data):
            result = main.load_users('fakefile.csv')

        # Assert that the result is True (function should handle the error and continue)
        self.assertTrue(result)

        # Assert that print was called to report the IntegrityError
        mock_print.assert_called_with('Failed to add user due to IntegrityError: '
                                      "{'user_id': 'user1', 'user_email': 'email1', 'user_name': 'name1', 'user_last_name': 'last1'}")

        # Assert that insert was called once
        mock_insert.assert_called_once_with(
            user_id='user1',
            user_email='email1',
            user_name='name1',
            user_last_name='last1'
        )

    def test_add_user_success(self):
        """Test successful addition of a new user."""
        user_data = {
            "user_id": "SC",
            "user_email": "sesame@uw.edu",
            "user_name": "Sesame",
            "user_last_name": "Chan"
        }

        with patch('main.db') as mock_db:
            mock_user_table = MagicMock()
            mock_db.__getitem__.return_value = mock_user_table
            mock_user_table.find_one.return_value = None
            mock_user_table.insert.return_value = True

            result = main.add_user(user_data)
            self.assertTrue(result)
            mock_user_table.insert.assert_called_once_with(**user_data)

    def test_add_user_failure(self):
        """
        Test failure when adding a user that already exists.
        """
        user_data = {
            "user_id": "SC",
            "user_email": "sesame@uw.edu",
            "user_name": "Sesame",
            "user_last_name": "Chan"
        }

        with patch('main.db') as mock_db:
            mock_user_table = MagicMock()
            mock_db.__getitem__.return_value = mock_user_table
            mock_user_table.find_one.return_value = user_data

            result = main.add_user(user_data)
            self.assertFalse(result)
            mock_user_table.insert.assert_not_called()

    @patch('main.db')
    def test_add_user_integrity_error(self, mock_db):
        """
        Test that add_user handles IntegrityError correctly.
        """
        # Create sample user data
        user_data = {
            "user_id": "user123",
            "user_email": "user123@example.com",
            "user_name": "John",
            "user_last_name": "Doe"
        }
        # Mock find_one to return None (user does not exist)
        mock_user_table = MagicMock()
        mock_user_table.find_one.return_value = None

        # Set up the mock to raise IntegrityError on insert
        mock_user_table.insert.side_effect = IntegrityError

        # Patch the db to return the mocked user table
        mock_db.__getitem__.return_value = mock_user_table

        # Call the function
        result = main.add_user(user_data)

        # Check that the function returned False due to the IntegrityError
        self.assertFalse(result)

        # Verify that the insert was attempted
        mock_user_table.insert.assert_called_once_with(**user_data)

    def test_update_user_success(self):
        """
        Test successful update of a user's details.
        """
        user_id = "SC"
        new_email = "newemail@uw.edu"
        new_user_name = "Sesame"
        new_user_last_name = "Chan"

        mock_user_table = MagicMock()
        mock_db = MagicMock()
        mock_db[USER_TABLE] = mock_user_table
        mock_db.transaction.return_value.__enter__.return_value = mock_db

        with patch('main.search_user') as mock_search_user:
            mock_search_user.return_value = MagicMock()
            result = main.update_user(mock_db, user_id, new_email, new_user_name, new_user_last_name)
            self.assertTrue(result)
            mock_db.transaction.assert_called_once()

    @patch('main.search_user')
    @patch('builtins.print')  # Mock the built-in print function
    def test_update_user_not_found(self, mock_print, mock_search_user):
        """
        Test that update_user prints a message and returns False if user_to_modify is not found.
        """
        # Set up
        mock_search_function = MagicMock(return_value=None)
        mock_search_user.return_value = mock_search_function

        # Call the function
        result = main.update_user(
            db=MagicMock(),  # Mock the db parameter
            user_id='user1',
            email='user1@example.com',
            user_name='User',
            user_last_name='One'
        )

        # Assertions
        self.assertFalse(result)
        mock_print.assert_called_once_with("Nothing to update.")


class TestDeleteUser(unittest.TestCase):
    """
    Unit tests for the delete_user function in main.py.
    """

    def setUp(self):
        """
        Set up test environment.
        """
        self.mock_db = MagicMock()
        self.mock_user_table = MagicMock()
        self.mock_status_table = MagicMock()
        self.mock_db.__getitem__.side_effect = {
            USER_TABLE: self.mock_user_table,
            STATUS_TABLE: self.mock_status_table,
        }.get
        main.db = self.mock_db  # Patch the db used in scrap_main with the mock

    def test_delete_user_success(self):
        """
        Test successful deletion of user and associated statuses.
        """
        user_id = "SC"
        user_mock = {"id": "user_db_id"}
        status_mock = [{"status_id": "status1"}, {"status_id": "status2"}]

        # Mock the database calls
        self.mock_status_table.find.return_value = status_mock
        self.mock_status_table.find_one.side_effect = [
            {"id": "status1_db_id"},
            {"id": "status2_db_id"},
        ]
        self.mock_user_table.find_one.return_value = user_mock

        # Run the function
        result = main.delete_user(user_id)

        # Assertions
        self.assertTrue(result)
        self.mock_status_table.find.assert_called_once_with(user_id=user_id)
        self.mock_status_table.delete.assert_any_call(id="status1_db_id")
        self.mock_status_table.delete.assert_any_call(id="status2_db_id")
        self.mock_user_table.delete.assert_called_once_with(id="user_db_id")

    def test_delete_user_not_found(self):
        """
        Test deletion when the user is not found.
        """
        user_id = "NC"

        # Mock the database calls
        self.mock_user_table.find_one.return_value = None

        with patch('builtins.print') as mock_print:
            result = main.delete_user(user_id)

            # Assertions
            self.assertFalse(result)
            self.mock_user_table.find_one.assert_called_once_with(user_id=user_id)
            mock_print.assert_called_once_with(f"User record not found for user_id: {user_id}")

    def test_delete_user_status_not_found(self):
        """
        Test deletion when one or more statuses are not found.
        """
        user_id = "SC"
        user_mock = {"id": "user_db_id"}
        status_mock = [{"status_id": "status1"}, {"status_id": "status2"}]

        # Mock the database calls
        self.mock_status_table.find.return_value = status_mock
        self.mock_status_table.find_one.side_effect = [
            {"id": "status1_db_id"},
            None,  # Simulate status2 not being found
        ]
        self.mock_user_table.find_one.return_value = user_mock

        with patch('builtins.print') as mock_print:
            result = main.delete_user(user_id)

            # Assertions
            self.assertFalse(result)
            self.mock_status_table.find.assert_called_once_with(user_id=user_id)
            self.mock_status_table.delete.assert_called_once_with(id="status1_db_id")
            mock_print.assert_any_call("Status record not found for status_id: status2")
            self.mock_user_table.delete.assert_called_once_with(id="user_db_id")

    def test_delete_user_status_deletion_exception(self):
        """
        Test deletion when an exception occurs during status deletion.
        """
        user_id = "SC"
        user_mock = {"id": "user_db_id"}
        status_mock = [{"status_id": "status1"}, {"status_id": "status2"}]

        # Mock the database calls
        self.mock_status_table.find.return_value = status_mock
        self.mock_status_table.find_one.side_effect = [
            {"id": "status1_db_id"},
            Exception("Database error")  # Simulate an exception during status2 deletion
        ]
        self.mock_user_table.find_one.return_value = user_mock

        with patch('builtins.print') as mock_print:
            result = main.delete_user(user_id)

            # Assertions
            self.assertFalse(result)
            self.mock_status_table.find.assert_called_once_with(user_id=user_id)
            self.mock_status_table.delete.assert_called_once_with(id="status1_db_id")
            mock_print.assert_any_call(
                "Failed to delete status with status_id: status2. Error: Database error"
            )
            self.mock_user_table.delete.assert_called_once_with(id="user_db_id")

    def test_delete_user_overall_exception(self):
        """
        Test overall exception handling during the deletion process.
        """
        user_id = "SC"

        # Mock the database calls to raise an exception
        self.mock_status_table.find.side_effect = Exception("Unexpected database error")

        with patch('builtins.print') as mock_print:
            result = main.delete_user(user_id)

            # Assertions
            self.assertFalse(result)
            self.mock_status_table.find.assert_called_once_with(user_id=user_id)
            mock_print.assert_called_once_with(
                "An error occurred while deleting user: Unexpected database error"
            )


class TestSearchUser(unittest.TestCase):
    """
    Unit tests for the search_user function in main.py.
    """

    def setUp(self):
        """
        Set up test environment.
        """
        self.mock_db = MagicMock()
        self.mock_user_table = MagicMock()
        self.mock_db.__getitem__.side_effect = {
            USER_TABLE: self.mock_user_table
        }.get
        main.db = self.mock_db  # Patch the db used in main with the mock

    def test_search_user_found(self):
        """
        Test successful search for an existing user.
        """
        user_id = "SC"
        user_mock = {"user_id": user_id}

        self.mock_user_table.find_one.return_value = user_mock

        search_function = main.search_user()
        result = search_function(user_id)
        self.assertEqual(result, user_mock)
        self.mock_user_table.find_one.assert_called_once_with(user_id=user_id)

    def test_search_user_not_found(self):
        """
        Test search when user is not found.
        """
        user_id = "NC"
        self.mock_user_table.find_one.return_value = None

        search_function = main.search_user()
        result = search_function(user_id)
        self.assertIsNone(result)
        self.mock_user_table.find_one.assert_called_once_with(user_id=user_id)

    def test_search_user_exception(self):
        """
        Test search when an exception occurs during the search.
        """
        user_id = "EX"
        self.mock_user_table.find_one.side_effect = Exception("Database error")

        with patch('builtins.print') as mock_print:
            search_function = main.search_user()
            result = search_function(user_id)
            self.assertIsNone(result)
            self.mock_user_table.find_one.assert_called_once_with(user_id=user_id)
            mock_print.assert_called_once_with(
                f"An error occurred while searching for user_id {user_id}: Database error"
            )

    @patch('main.validate_length')
    @patch('main.db')
    def test_add_user_invalid_data(self, mock_db, mock_validate_length):
        """
        Test that add_user returns False when validate_length fails.
        """
        # Set up the mock to return False for validation
        mock_validate_length.side_effect = [False, True, True]  # Adjust this to match the order of checks

        user_data = {
            "user_id": "SC",
            "user_email": "sesame@uw.edu",
            "user_name": "Sesame",
            "user_last_name": "Chan"
        }

        # Call the add_user function
        result = main.add_user(user_data)

        # Check that the function returned False due to validation failure
        self.assertFalse(result)

        # Verify that validate_length was called with the correct arguments
        mock_validate_length.assert_any_call(user_data['user_id'], 30)
        mock_validate_length.assert_any_call(user_data['user_name'], 30)
        mock_validate_length.assert_any_call(user_data['user_last_name'], 100)

        # Ensure that the database insert was not called since validation failed
        mock_db[USER_TABLE].insert.assert_not_called()

class TestLoadStatusUpdates(unittest.TestCase):
    """
    Unit tests for the load_status_updates function in main.py.
    """

    @patch('main.db')
    def test_load_status_updates_success(self, mock_db):
        """
        Test successful loading of statuses from a CSV file.
        """
        # Mock DictReader to simulate CSV file data
        mock_dictreader = MagicMock()
        mock_dictreader.__iter__.return_value = [
            {
                "STATUS_ID": "status1",
                "USER_ID": "user1",
                "STATUS_TEXT": "This is status 1",
            },
            {
                "STATUS_ID": "status2",
                "USER_ID": "user2",
                "STATUS_TEXT": "This is status 2",
            },
        ]

        mock_status_table = MagicMock()
        mock_db.__getitem__.return_value = mock_status_table
        mock_status_table.insert = MagicMock()

        with patch("builtins.open", create=True), patch("csv.DictReader", return_value=mock_dictreader):
            result = main.load_status_updates("status_updates.csv")
            self.assertTrue(result)

            # Verify that insert was called with the correct arguments
            called_args = [call.kwargs for call in mock_status_table.insert.call_args_list]
            self.assertEqual(
                called_args,
                [
                    {
                        "status_id": "status1",
                        "user_id": "user1",
                        "status_text": "This is status 1",
                    },
                    {
                        "status_id": "status2",
                        "user_id": "user2",
                        "status_text": "This is status 2",
                    },
                ]
            )

    @patch('main.db')
    @patch('builtins.print')
    def test_load_status_updates_file_not_found(self, mock_print, mock_db):
        """
        Test handling of FileNotFoundError when loading statuses from a non-existent CSV file.
        """
        mock_db.__getitem__.return_value = MagicMock()
        with patch("builtins.open", side_effect=FileNotFoundError):
            result = main.load_status_updates("nonexistent.csv")
            self.assertFalse(result)
            mock_print.assert_called_once_with('An error occurred while loading statuses: ')

    @patch('main.db')
    @patch('builtins.print')
    def test_load_status_updates_key_error(self, mock_print, mock_db):
        """
        Test handling when a CSV file has missing columns.
        """
        # Simulate CSV file with missing STATUS_TEXT column
        mock_dictreader = MagicMock()
        mock_dictreader.__iter__.return_value = [
            {
                "STATUS_ID": "status1",
                "USER_ID": "user1",
                # Missing STATUS_TEXT
            }
        ]

        mock_status_table = MagicMock()
        mock_db.__getitem__.return_value = mock_status_table
        mock_status_table.insert = MagicMock()

        with patch("builtins.open", create=True), patch("csv.DictReader", return_value=mock_dictreader):
            result = main.load_status_updates("status_updates.csv")

        # The function should return True because it will skip the row with missing columns
        self.assertTrue(result)

        # Ensure the insert was never called because the row was incomplete
        mock_status_table.insert.assert_not_called()

        # Ensure the print function was not called since no exception occurred
        mock_print.assert_not_called()

    @patch('main.db')
    @patch('builtins.print')
    def test_load_status_updates_integrity_error(self, mock_print, mock_db):
        """
        Test handling of IntegrityError when inserting status data into the database.
        """
        mock_dictreader = MagicMock()
        mock_dictreader.__iter__.return_value = [
            {
                "STATUS_ID": "status1",
                "USER_ID": "user1",
                "STATUS_TEXT": "This is status 1",
            }
        ]

        mock_status_table = MagicMock()
        mock_db.__getitem__.return_value = mock_status_table
        mock_status_table.insert.side_effect = IntegrityError("Integrity Error")

        with patch("builtins.open", create=True), patch("csv.DictReader", return_value=mock_dictreader):
            result = main.load_status_updates("status_updates.csv")
            self.assertFalse(result)
            mock_print.assert_called_once_with(
                'Failed to add status due to IntegrityError: {\'status_id\': \'status1\', \'user_id\': \'user1\', \'status_text\': \'This is status 1\'}')

    @patch('main.db')
    def test_load_status_updates_incomplete_data(self, mock_db):
        """
        Test handling of rows with incomplete data (missing fields).
        """
        # Simulate CSV file with some incomplete rows
        mock_dictreader = MagicMock()
        mock_dictreader.__iter__.return_value = [
            {
                "STATUS_ID": "status1",
                "USER_ID": "user1",
                # Missing STATUS_TEXT
            },
            {
                "STATUS_ID": "status2",
                "USER_ID": "user2",
                "STATUS_TEXT": "This is status 2",
            },
        ]

        mock_status_table = MagicMock()
        mock_db.__getitem__.return_value = mock_status_table
        mock_status_table.insert = MagicMock()

        with patch("builtins.open", create=True), patch("csv.DictReader", return_value=mock_dictreader):
            result = main.load_status_updates("status_updates.csv")
            self.assertTrue(result)

            # Verify that only complete rows are inserted
            called_args = [call.kwargs for call in mock_status_table.insert.call_args_list]
            self.assertEqual(
                called_args,
                [
                    {
                        "status_id": "status2",
                        "user_id": "user2",
                        "status_text": "This is status 2",
                    },
                ]
            )


class TestStatusFunctions(unittest.TestCase):
    """
    Unit tests for status-related functions in main.py.
    """

    def setUp(self):
        """
        Set up test environment.
        """
        self.mock_db = MagicMock()
        self.mock_user_table = MagicMock()
        self.mock_status_table = MagicMock()
        self.mock_db.__getitem__.side_effect = {
            USER_TABLE: self.mock_user_table,
            STATUS_TABLE: self.mock_status_table
        }.get
        # Patch the db used in main with the mock
        main.db = self.mock_db

    def test_create_add_status_function_success(self):
        """
        Test successful addition of a status when the user is verified.
        """
        # Setup
        add_status = main.create_add_status_function()
        user_id = "user1"
        status_id = "status1"
        status_text = "Hello World"

        self.mock_user_table.find_one.return_value = {"user_id": user_id}
        self.mock_status_table.find_one.return_value = None  # Status ID does not exist
        self.mock_status_table.insert.return_value = None  # Simulate successful insertion

        # Call the function
        result = add_status(status_id, user_id, status_text)

        # Assertions
        self.assertTrue(result)
        self.mock_status_table.insert.assert_called_once_with(
            status_id=status_id,
            user_id=user_id,
            status_text=status_text
        )

    def test_create_add_status_function_user_not_verified(self):
        """
        Test addition of a status for a user not yet verified.
        """
        # Setup
        add_status = main.create_add_status_function()
        user_id = "user1"
        status_id = "status1"
        status_text = "Hello World"

        self.mock_user_table.find_one.return_value = None  # User not found

        # Call the function
        result = add_status(status_id, user_id, status_text)

        # Assertions
        self.assertFalse(result)
        self.mock_status_table.insert.assert_not_called()

    def test_create_add_status_function_duplicate_status_id(self):
        """
        Test failure to add a status due to duplicate status_id.
        """
        # Setup
        add_status = main.create_add_status_function()
        user_id = "user1"
        status_id = "status1"
        status_text = "Hello World"

        self.mock_user_table.find_one.return_value = {"user_id": user_id}
        self.mock_status_table.find_one.return_value = {"status_id": status_id}  # Status ID exists

        with patch('builtins.print') as mock_print:
            # Call the function
            result = add_status(status_id, user_id, status_text)

            # Assertions
            self.assertFalse(result)
            self.mock_status_table.insert.assert_not_called()
            mock_print.assert_called_once_with(f'Failed to add status due to duplicate status_id: {status_id}')

    def test_create_add_status_function_failure(self):
        """
        Test failure to add a status due to IntegrityError.
        """
        # Setup
        add_status = main.create_add_status_function()
        user_id = "user1"
        status_id = "status1"
        status_text = "Hello World"

        self.mock_user_table.find_one.return_value = {"user_id": user_id}
        self.mock_status_table.find_one.return_value = None  # Status ID does not exist
        self.mock_status_table.insert.side_effect = IntegrityError("Integrity Error")

        with patch('builtins.print') as mock_print:
            # Call the function
            result = add_status(status_id, user_id, status_text)

            # Assertions
            self.assertFalse(result)
            self.mock_status_table.insert.assert_called_once_with(
                status_id=status_id,
                user_id=user_id,
                status_text=status_text
            )
            mock_print.assert_called_once_with(
                f'Failed to add status due to IntegrityError: {status_id}, {user_id}')

    def test_create_add_status_function_user_id_not_found(self):
        """
        Test failure to add a status because the user_id does not exist.
        """
        # Setup
        add_status = main.create_add_status_function()
        user_id = "user1"
        status_id = "status1"
        status_text = "Hello World"

        self.mock_user_table.find_one.return_value = None  # User ID does not exist
        self.mock_status_table.find_one.return_value = None  # Status ID does not exist

        with patch('builtins.print') as mock_print:
            # Call the function
            result = add_status(status_id, user_id, status_text)

            # Assertions
            self.assertFalse(result)
            self.mock_status_table.insert.assert_not_called()
            mock_print.assert_called_once_with(f'Failed to add status because user_id does not exist: {user_id}')


class TestUpdateStatusFunctions(unittest.TestCase):
    '''testing update status functions'''

    def setUp(self):
        """
        Set up test environment.
        """
        self.mock_db = MagicMock()
        self.mock_user_table = MagicMock()
        self.mock_status_table = MagicMock()
        self.mock_db.__getitem__.side_effect = {
            USER_TABLE: self.mock_user_table,
            STATUS_TABLE: self.mock_status_table
        }.get
        # Patch the db used in main with the mock
        main.db = self.mock_db

    def test_update_status_success(self):
        """
        Test successful update of a status.
        """
        # Setup
        status_id = "status1"
        user_id = "user1"
        status_text = "Updated Status"

        # Configure the mock return value
        self.mock_user_table.find_one.return_value = {"user_id": user_id}
        self.mock_status_table.find_one.return_value = {"status_id": status_id}
        self.mock_status_table.update = MagicMock()

        # Call the function
        result = main.update_status(status_id, user_id, status_text)

        # Assertions
        self.assertTrue(result)
        self.mock_status_table.update.assert_called_once_with(
            status_id=status_id,
            user_id=user_id,
            status_text=status_text,
            columns=["status_id"]
        )

    @patch('main.search_user')
    def test_update_status_user_not_found(self, mock_search_user):
        """
        Test failure to update a status if the user is not found.
        """
        # Setup
        mock_search_function = MagicMock(return_value=None)
        mock_search_user.return_value = mock_search_function

        status_id = "status1"
        user_id = "user1"
        status_text = "Updated Status"

        # Call the function
        result = main.update_status(status_id, user_id, status_text)

        # Assertions
        self.assertFalse(result)
        self.mock_status_table.update.assert_not_called()

    def test_update_status_status_not_found(self):
        """
        Test failure to update a status if the status_id is not found.
        """
        # Setup
        status_id = "status1"
        user_id = "user1"
        status_text = "Updated Status"

        self.mock_user_table.find_one.return_value = {"user_id": user_id}
        self.mock_status_table.find_one.return_value = None  # Status not found

        # Call the function
        result = main.update_status(status_id, user_id, status_text)

        # Assertions
        self.assertFalse(result)
        self.mock_status_table.update.assert_not_called()

    def test_update_status_transaction_error(self):
        """
        Test failure to update a status due to an exception during the transaction.
        """
        # Setup
        status_id = "status1"
        user_id = "user1"
        status_text = "Updated Status"

        self.mock_user_table.find_one.return_value = {"user_id": user_id}
        self.mock_status_table.find_one.return_value = {"status_id": status_id}
        self.mock_db.transaction.side_effect = Exception("Transaction Error")

        # Call the function
        result = main.update_status(status_id, user_id, status_text)

        # Assertions
        self.assertFalse(result)
        self.mock_status_table.update.assert_not_called()

    def test_update_status_exception_handling(self):
        """Test that an exception during the transaction is caught and handled."""
        # Setup
        status_id = "status1"
        user_id = "user1"
        status_text = "Updated Status"

        # Mock the user and status exist
        self.mock_user_table.find_one.return_value = {"user_id": user_id}
        self.mock_status_table.find_one.return_value = {"status_id": status_id}
        # Mock the update operation to raise an exception
        self.mock_status_table.update.side_effect = Exception("Update Failed")

        # Call the function
        result = main.update_status(status_id, user_id, status_text)

        # Assertions
        self.assertFalse(result)
        self.mock_status_table.update.assert_called_once_with(
            status_id=status_id,
            user_id=user_id,
            status_text=status_text,
            columns=["status_id"]
        )

    @patch('main.search_user')
    def test_update_status_not_found(self, mock_search_user):
        """
        Test failure to update a status if the user is not found.
        """
        # Setup
        mock_search_function = MagicMock(return_value=None)
        mock_search_user.return_value = mock_search_function

        status_id = "status1"
        user_id = "user1"
        status_text = "Updated Status"

        # Call the function
        result = main.update_status(status_id, user_id, status_text)

        # Assertions
        self.assertFalse(result)
        self.mock_status_table.update.assert_not_called()


class TestDeleteStatusFunctions(unittest.TestCase):
    """testing delete status functions"""

    def setUp(self):
        """Set up test environment."""
        self.mock_db = MagicMock()
        self.mock_user_table = MagicMock()
        self.mock_status_table = MagicMock()
        self.mock_db.__getitem__.side_effect = {
            USER_TABLE: self.mock_user_table,
            STATUS_TABLE: self.mock_status_table
        }.get
        # Patch the db used in main with the mock
        main.db = self.mock_db

    def test_delete_status_success(self):
        """Test successful deletion of a status."""
        status_id = "status1"
        self.mock_status_table.find_one.return_value = {"id": 1}

        # Call the function
        result = main.delete_status(status_id)

        # Assertions
        self.assertTrue(result)
        self.mock_status_table.delete.assert_called_once_with(id=1)

    def test_delete_status_not_found(self):
        """Test failure to delete a status if it is not found."""
        status_id = "status1"
        self.mock_status_table.find_one.return_value = None

        # Call the function
        result = main.delete_status(status_id)

        # Assertions
        self.assertFalse(result)
        self.mock_status_table.delete.assert_not_called()

    def test_delete_status_error(self):
        """Test failure to delete a status due to an exception."""
        status_id = "status1"
        self.mock_status_table.find_one.return_value = {"id": 1}
        self.mock_status_table.delete.side_effect = Exception("Deletion Error")

        # Call the function
        result = main.delete_status(status_id)

        # Assertions
        self.assertFalse(result)
        self.mock_status_table.delete.assert_called_once_with(id=1)


class TestSearchStatusFunctions(unittest.TestCase):
    """Unit tests for status-related functions in main.py."""

    def setUp(self):
        """Set up test environment."""
        self.mock_db = MagicMock()
        self.mock_user_table = MagicMock()
        self.mock_status_table = MagicMock()
        self.mock_db.__getitem__.side_effect = {
            USER_TABLE: self.mock_user_table,
            STATUS_TABLE: self.mock_status_table
        }.get
        # Patch the db used in main with the mock
        main.db = self.mock_db

    def test_search_status_success(self):
        """Test successful search for a status."""
        status_id = "status1"
        expected_status = {"status_id": status_id, "status_text": "Test Status"}
        self.mock_status_table.find_one.return_value = expected_status

        # Call the function
        result = main.search_status(status_id)

        # Assertions
        self.assertEqual(result, expected_status)
        self.mock_status_table.find_one.assert_called_once_with(status_id=status_id)

    def test_search_status_error(self):
        """Test failure to search for a status due to an exception."""
        status_id = "status1"
        self.mock_status_table.find_one.side_effect = Exception("Search Error")

        # Call the function
        result = main.search_status(status_id)

        # Assertions
        self.assertIsNone(result)
        self.mock_status_table.find_one.assert_called_once_with(status_id=status_id)


class TestValidateLength(unittest.TestCase):
    ''' Test to validate character limits '''

    @patch('builtins.print')
    def test_validate_length_exceeds_max(self, mock_print):
        """
        Test that validate_length prints a message and returns False when the length of value exceeds max_length.
        """
        value = "This is a very long string"
        max_length = 10

        result = main.validate_length(value, max_length)

        # Check the result
        self.assertFalse(result)

        # Check the printed message
        mock_print.assert_called_once_with(f"Value '{value}' exceeds maximum length of {max_length} characters.")

    def test_validate_length_within_limit(self):
        """
        Test that validate_length returns True when the length is within the limit.
        """
        value = "Short"
        max_length = 10

        result = main.validate_length(value, max_length)
        self.assertTrue(result)

if __name__ == "__main__":
    unittest.main()
