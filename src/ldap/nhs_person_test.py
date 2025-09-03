from datetime import date
import pytest
from unittest.mock import patch

from ldap.nhs_person import NhsOrgPersonRole, from_list_or_string


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
            "uniqueIdentifier": "role123"
            # Missing most fields
        }
        
        role = NhsOrgPersonRole(role_attrs)
        
        assert role.profile_id == "role123"
        assert role.role_granted is None
        assert role.role_stopped is None
        assert role.job_role == ""
        assert role.business_function_codes == []


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