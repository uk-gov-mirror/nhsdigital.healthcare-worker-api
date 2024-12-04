import unittest

from fhir.fhir_reference import FhirReference, FhirReferable, FhirIdentifier
from request_handlers.include_populator import add_includes_to_response, add_revincludes_to_response


class FhirTestObject(FhirReferable):
    value: str
    reference_field: FhirReference['FhirTestObject']
    other_reference: FhirReference['FhirTestObject']

    def __init__(self, value: str):
        super().__init__("TestObject")
        self.value = value

    def get_reference(self) -> str:
        return f"Test/{self.value}"

    def get_identifier(self) -> FhirIdentifier:
        return FhirIdentifier("system", self.value)

    def get_display(self) -> str:
        return self.value


class TestIncludeQueryParam(unittest.TestCase):
    """
    Tests for the _include query param to ensure it's matching on included references.
    """
    def test_successful_include(self):
        original = FhirTestObject("base")
        original.reference_field = FhirReference(FhirTestObject("referenced"))

        with_includes = add_includes_to_response([original], {"_include": ["TestObject:reference_field"]})

        assert len(with_includes) == 2
        assert with_includes[0] == original
        assert with_includes[1] == FhirTestObject("referenced")

    def test_include_unknown_resource_ignored(self):
        original = FhirTestObject("base")
        original.reference_field = FhirReference(FhirTestObject("referenced"))

        with_includes = add_includes_to_response([original], {"_include": ["Unknown:reference_field"]})

        assert len(with_includes) == 1
        assert with_includes[0] == original

    def test_include_unknown_field_ignored(self):
        original = FhirTestObject("base")
        original.reference_field = FhirReference(FhirTestObject("referenced"))

        with_includes = add_includes_to_response([original], {"_include": ["TestObject:unknown"]})

        assert len(with_includes) == 1
        assert with_includes[0] == original

    def test_same_reference_not_duplicated(self):
        original = [FhirTestObject("base")] * 2
        for x in original:
            x.reference_field = FhirReference(FhirTestObject("referenced"))

        with_includes = add_includes_to_response(original, {"_include": ["TestObject:reference_field"]})

        assert len(with_includes) == 3
        assert with_includes[0] == original[0]
        assert with_includes[1] == original[1]
        assert with_includes[2] == FhirTestObject("referenced")

    def test_same_reference_from_different_include_not_duplicated(self):
        original = [FhirTestObject("base"), FhirTestObject("base2")]
        for x in original:
            x.reference_field = FhirReference(FhirTestObject("referenced"))
            x.other_reference = FhirReference(FhirTestObject("referenced"))

        includes = ["TestObject:reference_field", "TestObject:other_reference"]
        with_includes = add_includes_to_response(original, {"_include": includes})

        assert len(with_includes) == 3
        assert with_includes[0] == original[0]
        assert with_includes[1] == original[1]
        assert with_includes[2] == FhirTestObject("referenced")

    def test_multiple_references(self):
        original = [FhirTestObject("base"), FhirTestObject("base2")]
        original[0].reference_field = FhirReference(FhirTestObject("referenced1"))
        original[0].other_reference = FhirReference(FhirTestObject("referenced2"))
        original[1].reference_field = FhirReference(FhirTestObject("referenced3"))
        original[1].other_reference = FhirReference(FhirTestObject("referenced1"))

        includes = ["TestObject:reference_field", "TestObject:other_reference"]
        with_includes = add_includes_to_response(original, {"_include": includes})

        self.assertCountEqual(with_includes, [original[0], original[1], FhirTestObject("referenced1"),
                                                FhirTestObject("referenced2"), FhirTestObject("referenced3")])

    def test_no_includes(self):
        original = FhirTestObject("base")
        original.reference_field = FhirReference(FhirTestObject("referenced"))

        with_includes = add_includes_to_response([original], {"not_include": "test"})

        assert with_includes == [original]


class TestRevIncludeQueryParam(unittest.TestCase):
    """
    Tests for the _revinclude query param to ensure it's finding included objects which reference the one we're
    returning.
    """
    def test_successful_revinclude(self):
        main_response = FhirTestObject("base")
        related_entries = [FhirTestObject("related")]
        related_entries[0].reference_field = FhirReference(main_response)

        with_includes = add_revincludes_to_response([main_response],
                                                    {"_revinclude": ["TestObject:reference_field"]},
                                                    related_entries)

        assert len(with_includes) == 2
        assert with_includes[0] == main_response
        assert with_includes[1] == FhirTestObject("related")

    def test_revinclude_unknown_resource_ignored(self):
        main_response = FhirTestObject("base")
        related_entries = [FhirTestObject("related")]
        related_entries[0].reference_field = FhirReference(main_response)

        with_includes = add_revincludes_to_response([main_response],
                                                    {"_revinclude": ["Unknown:reference_field"]},
                                                    related_entries)

        assert len(with_includes) == 1
        assert with_includes[0] == main_response

    def test_revinclude_unknown_field_ignored(self):
        main_response = FhirTestObject("base")
        related_entries = [FhirTestObject("related")]
        related_entries[0].reference_field = FhirReference(main_response)

        with_includes = add_revincludes_to_response([main_response],
                                                    {"_revinclude": ["TestObject:unknown"]},
                                                    related_entries)

        assert len(with_includes) == 1
        assert with_includes[0] == main_response

    def test_same_reference_not_duplicated(self):
        main_response = FhirTestObject("base")
        related_entries = [FhirTestObject("related")]
        related_entries[0].reference_field = FhirReference(main_response)
        related_entries[0].other_reference = FhirReference(main_response)

        includes = ["TestObject:reference_field", "TestObject:other_reference"]
        with_includes = add_revincludes_to_response([main_response], {"_revinclude": includes},
                                                    related_entries)

        assert len(with_includes) == 2
        assert with_includes[0] == main_response
        assert with_includes[1] == FhirTestObject("related")

    def test_multiple_references(self):
        main_response = FhirTestObject("base")
        related_entries = [FhirTestObject("related"), FhirTestObject("related2")]
        related_entries[0].reference_field = FhirReference(main_response)
        related_entries[1].reference_field = FhirReference(main_response)

        with_includes = add_revincludes_to_response([main_response],
                                                    {"_revinclude": ["TestObject:reference_field"]},
                                                    related_entries)

        assert len(with_includes) == 3
        self.assertCountEqual(with_includes, [main_response, FhirTestObject("related"), FhirTestObject("related2")])

    def test_ignore_unrelated_entries(self):
        main_response = FhirTestObject("base")
        related_entries = [FhirTestObject("related"), FhirTestObject("related2")]
        related_entries[0].reference_field = FhirReference(FhirTestObject("something_else"))
        related_entries[1].reference_field = FhirReference(main_response)

        with_includes = add_revincludes_to_response([main_response],
                                                    {"_revinclude": ["TestObject:reference_field"]},
                                                    related_entries)

        assert len(with_includes) == 2
        assert with_includes[0] == main_response
        assert with_includes[1] == FhirTestObject("related2")

    def test_no_includes(self):
        main_response = FhirTestObject("base")
        related_entries = [FhirTestObject("related")]
        related_entries[0].reference_field = FhirReference(main_response)

        with_includes = add_revincludes_to_response([main_response],
                                                    {"not_include": "test"},
                                                    related_entries)

        assert with_includes == [main_response]

# Include extra items we're not matching
