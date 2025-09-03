from datetime import date
import pytest
from unittest.mock import patch

from ldap.nhs_person import NhsOrgPersonRole, NhsOrgPerson, from_list_or_string


class TestNhsOrgPersonRole:
    """Test NhsOrgPersonRole class, especially handling of missing date fields"""

    def test_role_with_valid_dates(self):
        """Test role creation with valid open and close dates"""
        role_attrs = {
            "uniqueIdentifier": "role123",
            "nhsOrgOpenDate": "20200101",
            "nhsOrgCloseDate": "20301231",
            "nhsJobRole": "Doctor",
            "nhsJobRoleCode": "DOC"
        }

        role = NhsOrgPersonRole(role_attrs)

        assert role.role_granted == date(2020, 1, 1)
        assert role.role_stopped == date(2030, 12, 31)
        assert role.profile_id == "role123"
        assert role.job_role == "Doctor"

    def test_role_missing_open_date_only(self):
        """Test role creation with missing nhsOrgOpenDate but valid nhsOrgCloseDate"""
        role_attrs = {
            "uniqueIdentifier": "role123",
            "nhsOrgOpenDate": "",  # Missing
            "nhsOrgCloseDate": "20301231",  # Future
            "nhsJobRole": "Doctor",
            "nhsJobRoleCode": "DOC"
        }

        role = NhsOrgPersonRole(role_attrs)

        assert role.role_granted is None
        assert role.role_stopped == date(2030, 12, 31)

    def test_role_missing_both_dates(self):
        """Test role creation with both dates missing"""
        role_attrs = {
            "uniqueIdentifier": "role123",
            "nhsOrgOpenDate": "",  # Missing
            "nhsOrgCloseDate": "",  # Missing
            "nhsJobRole": "Doctor",
            "nhsJobRoleCode": "DOC"
        }

        role = NhsOrgPersonRole(role_attrs)

        assert role.role_granted is None
        assert role.role_stopped is None

    def test_role_whitespace_open_date(self):
        """Test role creation with whitespace-only nhsOrgOpenDate"""
        role_attrs = {
            "uniqueIdentifier": "role123",
            "nhsOrgOpenDate": "   ",  # Whitespace only
            "nhsOrgCloseDate": "20301231",
            "nhsJobRole": "Doctor",
            "nhsJobRoleCode": "DOC"
        }

        role = NhsOrgPersonRole(role_attrs)

        assert role.role_granted is None
        assert role.role_stopped == date(2030, 12, 31)

    def test_role_array_empty_open_date(self):
        """Test role creation with empty array for nhsOrgOpenDate"""
        role_attrs = {
            "uniqueIdentifier": "role123",
            "nhsOrgOpenDate": [],  # Empty array
            "nhsOrgCloseDate": "20301231",
            "nhsJobRole": "Doctor",
            "nhsJobRoleCode": "DOC"
        }

        role = NhsOrgPersonRole(role_attrs)

        assert role.role_granted is None
        assert role.role_stopped == date(2030, 12, 31)

    @patch('ldap.nhs_person.logger')
    def test_role_invalid_open_date_format(self, mock_logger):
        """Test role creation with invalid nhsOrgOpenDate format"""
        role_attrs = {
            "uniqueIdentifier": "role123",
            "nhsOrgOpenDate": "invalid-date",
            "nhsOrgCloseDate": "20301231",
            "nhsJobRole": "Doctor",
            "nhsJobRoleCode": "DOC"
        }

        role = NhsOrgPersonRole(role_attrs)

        assert role.role_granted is None
        assert role.role_stopped == date(2030, 12, 31)
        mock_logger.warning.assert_called_once()
        assert "INVALID_OPEN_DATE" in str(mock_logger.warning.call_args)

    @patch('ldap.nhs_person.logger')
    def test_role_invalid_close_date_format(self, mock_logger):
        """Test role creation with invalid nhsOrgCloseDate format"""
        role_attrs = {
            "uniqueIdentifier": "role123",
            "nhsOrgOpenDate": "20200101",
            "nhsOrgCloseDate": "invalid-date",
            "nhsJobRole": "Doctor",
            "nhsJobRoleCode": "DOC"
        }

        role = NhsOrgPersonRole(role_attrs)

        assert role.role_granted == date(2020, 1, 1)
        assert role.role_stopped is None
        mock_logger.warning.assert_called_once()
        assert "INVALID_CLOSE_DATE" in str(mock_logger.warning.call_args)

    def test_role_missing_fields_gracefully_handled(self):
        """Test role creation with minimal required fields"""
        role_attrs = {
            "uniqueIdentifier": "role123",
            # Missing most fields
        }

        role = NhsOrgPersonRole(role_attrs)

        assert role.profile_id == "role123"
        assert role.role_granted is None
        assert role.role_stopped is None
        assert role.job_role == ""
        assert role.business_function_codes == []


class TestNhsOrgPerson:
    """Test NhsOrgPerson class, especially handling of missing date fields"""

    def test_org_person_with_valid_date(self):
        """Test org person creation with valid date"""
        org_attrs = {
            "uniqueIdentifier": "org123",
            "nhsOrgOpenDate": "20200101",
            "nhsIDCode": "Y51",
            "o": "Test Hospital"
        }

        org_person = NhsOrgPerson(org_attrs)

        assert org_person.joined == date(2020, 1, 1)
        assert org_person.org_person_id == "org123"
        assert org_person.ods_code == "Y51"
        assert org_person.org_name == "Test Hospital"

    def test_org_person_missing_open_date(self):
        """Test org person creation with missing nhsOrgOpenDate"""
        org_attrs = {
            "uniqueIdentifier": "org123",
            "nhsOrgOpenDate": "",  # Missing
            "nhsIDCode": "Y51",
            "o": "Test Hospital"
        }

        org_person = NhsOrgPerson(org_attrs)

        assert org_person.joined is None
        assert org_person.org_person_id == "org123"
        assert org_person.ods_code == "Y51"
        assert org_person.org_name == "Test Hospital"

    def test_org_person_whitespace_open_date(self):
        """Test org person creation with whitespace-only nhsOrgOpenDate"""
        org_attrs = {
            "uniqueIdentifier": "org123",
            "nhsOrgOpenDate": "   ",  # Whitespace only
            "nhsIDCode": "Y51",
            "o": "Test Hospital"
        }

        org_person = NhsOrgPerson(org_attrs)

        assert org_person.joined is None
        assert org_person.org_person_id == "org123"
        assert org_person.ods_code == "Y51"
        assert org_person.org_name == "Test Hospital"

    def test_org_person_array_empty_open_date(self):
        """Test org person creation with empty array for nhsOrgOpenDate"""
        org_attrs = {
            "uniqueIdentifier": "org123",
            "nhsOrgOpenDate": [],  # Empty array
            "nhsIDCode": "Y51",
            "o": "Test Hospital"
        }

        org_person = NhsOrgPerson(org_attrs)

        assert org_person.joined is None
        assert org_person.org_person_id == "org123"
        assert org_person.ods_code == "Y51"
        assert org_person.org_name == "Test Hospital"

    @patch('ldap.nhs_person.logger')
    def test_org_person_invalid_date_format(self, mock_logger):
        """Test org person creation with invalid date format"""
        org_attrs = {
            "uniqueIdentifier": "org123",
            "nhsOrgOpenDate": "invalid-date",
            "nhsIDCode": "Y51",
            "o": "Test Hospital"
        }

        org_person = NhsOrgPerson(org_attrs)

        assert org_person.joined is None
        assert org_person.org_person_id == "org123"
        assert org_person.ods_code == "Y51"
        assert org_person.org_name == "Test Hospital"
        mock_logger.warning.assert_called_once()
        assert "INVALID_ORG_OPEN_DATE" in str(mock_logger.warning.call_args)

    def test_org_person_missing_optional_fields(self):
        """Test org person creation with minimal fields"""
        org_attrs = {
            "uniqueIdentifier": "org123",
            "nhsIDCode": "Y51",
            "o": "Test Hospital",
            # Missing nhsOrgOpenDate entirely
        }

        org_person = NhsOrgPerson(org_attrs)

        assert org_person.joined is None
        assert org_person.org_person_id == "org123"
        assert org_person.ods_code == "Y51"
        assert org_person.org_name == "Test Hospital"
        assert org_person.nhs_id_code == "Y51"


class TestFromListOrString:
    """Test the from_list_or_string utility function"""

    def test_string_input(self):
        """Test with string input"""
        result = from_list_or_string("test_string")
        assert result == "test_string"

    def test_list_input(self):
        """Test with list input"""
        result = from_list_or_string(["first", "second"])
        assert result == "first"

    def test_empty_list(self):
        """Test with empty list"""
        result = from_list_or_string([])
        assert result == ""

    def test_none_input(self):
        """Test with None input"""
        result = from_list_or_string(None)
        assert result == ""

