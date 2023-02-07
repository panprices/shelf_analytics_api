from datetime import datetime
from typing import List, Optional, Literal, Union

from pydantic import BaseModel, Field, validator

from app.config.constants import DATE_FORMAT


class GlobalFilter(BaseModel):

    """
    Represents the model for filtering on the data showed through the UI.

    It corresponds to the filter widget showed at the top of every page in the FE.

    The date should be passed in the format: DD/MM/YYYY

    Countries are passed by the country code:
    - Sweden - SE
    - Norway - NO
    - Germany - DE
    ...

    Retailers and categories are passed by their literal values (as returned by this API).
    """

    start_date: datetime = Field(description="Test description", example="15/10/2022")
    countries: List[str] = Field(
        description="The list of desired countries. If no country is specified all countries are considered.",
        example=[],
    )
    retailers: List[str] = Field(
        description="""
            The list of desired retailers (identified by database id). 
            If no retailer is specified all retailers are considered.
        """,
        example=[],
    )
    categories: List[str] = Field(
        description="""
            The list of desired categories (identified by database id). 
            If no category is specified all categories are considered.
        """,
        example=[],
    )
    groups: List[str] = Field(
        description="The list of desired groups (identified by database id)",
        example=[],
    )

    @validator("start_date", pre=True)
    def parse_start_date(cls, value):
        if not isinstance(value, str):
            return value

        return datetime.strptime(value, DATE_FORMAT)


class DataGridFilterItem(BaseModel):
    column: str
    operator: str
    value: Optional[Union[str, int, float, List[str]]]

    def to_postgres_condition(self, index: int):
        if self.operator == "contains":
            return f"{self.column} LIKE ('%' || :fv_{index} || '%')"
        elif self.operator == "startsWith":
            return f"{self.column} LIKE (:fv_{index} || '%')"
        elif self.operator == "endsWith":
            return f"{self.column} LIKE ('%' || :fv_{index})"
        elif self.operator == "equals":
            return f"{self.column} = :fv_{index}"
        elif self.operator == "isEmpty":
            return f"{self.column} IS NULL"
        elif self.operator == "isNotEmpty":
            return f"{self.column} IS NOT NULL"
        elif self.operator == "isAnyOf":
            return f"{self.column} IN :fv_{index}"
        elif self.operator == "!=":
            return f"{self.column} <> :fv_{index}"
        elif self.operator in [">", "<", "<=", ">=", "="]:
            return f"{self.column} {self.operator} :fv_{index}"
        elif self.operator == "is":
            return f"{self.column} = :fv_{index}"
        elif self.operator == "after":
            return f"{self.column} > :fv_{index}"
        elif self.operator == "before":
            return f"{self.column} < :fv_{index}"
        elif self.operator == "onOrAfter":
            return f"{self.column} >= :fv_{index}"
        elif self.operator == "onOrBefore":
            return f"{self.column} <= :fv_{index}"
        elif self.operator == "not":
            return f"{self.column} <> :fv_{index}"
        return ""

    def get_safe_postgres_value(self):
        if self.operator == "isAnyOf":
            return tuple(self.value) if self.value else ()

        return self.value if self.value else ""

    @staticmethod
    def get_no_value_operators() -> List[str]:
        return ["isEmpty", "isNotEmpty"]

    def is_well_defined(self):
        return not not self.value or self.operator in self.get_no_value_operators()


class DataGridFilters(BaseModel):
    items: List[DataGridFilterItem]
    operator: Literal["or", "and"]


class DataGridSorting(BaseModel):
    column: str
    direction: Literal["asc", "desc"]


class DataPageFilter(GlobalFilter):
    data_grid_filter: DataGridFilters = Field(
        description="The filters defined in the data grid component"
    )
    search_text: Optional[str] = Field(
        description="The text used to search the data", example="7350133230816"
    )


class PagedGlobalFilter(DataPageFilter):
    page_number: int = Field(
        description="The number of the currently requested page in the pagination system. Index is 1 based.",
        example=1,
    )
    page_size: int = Field(
        default=10, description="The number of results displayed per page.", example=10
    )
    sorting: Optional[DataGridSorting]

    def get_products_offset(self):
        return (self.page_number - 1) * self.page_size
