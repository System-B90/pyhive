"""
Name: assignment_response_content.py
Purpose: AssignmentResponseContent type definition.
Created: 2026-04-05
Author: Michael K. Steinberg
"""

from typing import TYPE_CHECKING, Any, Self, TypeVar

from pydantic import Field, PrivateAttr

from .core_item import HiveCoreItem

if TYPE_CHECKING:
    from ...client import HiveClient
    from .assignment import Assignment, AssignmentLike
    from .assignment_response import AssignmentResponse
    from .form_field import FormField


class AssignmentResponseContent(HiveCoreItem):
    """
    Attributes:
        raw_content: The raw content string from the response payload.
        field_id: ID of the associated form field.
    """

    hive_client: "HiveClient" = Field(exclude=True, repr=False)
    assignment_id: int = Field(exclude=True)
    assignment_response_id: int = Field(exclude=True)
    raw_content: str = Field(alias="content")
    field_id: int = Field(alias="field")

    _content: "str | int | list[str | int] | None" = PrivateAttr(default=None)
    _field: "FormField | None" = PrivateAttr(default=None)
    _assignment: "Assignment | None" = PrivateAttr(default=None)
    _assignment_response: "AssignmentResponse | None" = PrivateAttr(default=None)

    @classmethod
    def from_dict(
        cls,
        src_dict: dict[str, Any],
        assignment: "AssignmentLike",
        assignment_response_id: int,
        hive_client: "HiveClient",
    ) -> Self:
        """
        Deserializes an AssignmentResponseContent instance from a dictionary payload.

        Args:
            src_dict (dict[str, Any]): The raw dictionary from the API response.
            assignment (AssignmentLike): The parent assignment object or its ID.
            assignment_response_id (int): The ID of the parent assignment response.
            hive_client (HiveClient): The client instance for deferred network operations.

        Returns:
            Self: An instantiated and validated AssignmentResponseContent model.
        """
        data = dict(src_dict)
        data["hive_client"] = hive_client
        data["assignment_response_id"] = assignment_response_id

        # Extracts the ID cleanly whether passed an int or an Assignment object
        data["assignment_id"] = getattr(assignment, "id", assignment)

        return cls.model_validate(data)

    @property
    def field(self) -> "FormField":
        """
        Lazily load and return the field this assignment belongs to.

        Returns:
            FormField: The associated form field.
        """
        if self._field is None:
            self._field = self.hive_client.get_exercise_field(
                exercise=self.assignment.exercise_id, field_id=self.field_id
            )
        return self._field

    @property
    def assignment(self) -> "Assignment":
        """
        Lazily load and return the assignment this content belongs to.

        Returns:
            Assignment: The associated assignment entity.
        """
        if self._assignment is None:
            self._assignment = self.hive_client.get_assignment(
                assignment_id=self.assignment_id
            )
        return self._assignment

    @property
    def assignment_response(self) -> "AssignmentResponse":
        """
        Lazily load and return the assignment response this content belongs to.

        Returns:
            AssignmentResponse: The associated assignment response entity.
        """
        if self._assignment_response is None:
            self._assignment_response = self.hive_client.get_assignment_response(
                assignment=self.assignment_id,
                response_id=self.assignment_response_id,
            )
        return self._assignment_response

    @property
    def content(self) -> "str | int | list[str | int]":
        """
        Lazily parse and return the content based on the field type.

        Returns:
            str | int | list[str | int]: The dynamically typed content value.

        Raises:
            ValueError: If the choice lists are missing or the field type is unsupported.
        """
        from .enums.form_field_type_enum import FormFieldTypeEnum

        if self._content is None:
            if self.field.type_ is FormFieldTypeEnum.NUMBER:
                self._content = int(self.raw_content)
            elif self.field.type_ is FormFieldTypeEnum.TEXT:
                self._content = str(self.raw_content)
            elif self.field.type_ is FormFieldTypeEnum.MULTIPLE:
                choices = self.field.choices
                if not isinstance(choices, list):
                    raise ValueError(
                        "Expected a list of choices for MULTIPLE field type"
                    )
                self._content = choices[int(self.raw_content)]
            elif self.field.type_ is FormFieldTypeEnum.MULTIRESPONSE:
                choices = self.field.choices
                if not isinstance(choices, list):
                    raise ValueError(
                        "Expected a list of choices for MULTIRESPONSE field type"
                    )
                self._content = [choices[int(i)] for i in self.raw_content.split(",")]
            else:
                raise ValueError(f"Unsupported form field type: {self.field.type_}")
        return self._content

    def __str__(self) -> str:
        return str(self.content)


AssignmentResponseContentLike = TypeVar(
    "AssignmentResponseContentLike", AssignmentResponseContent, int
)
