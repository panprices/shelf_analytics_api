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

    start_date: datetime = Field(description="Test description", example="2022-09-01")
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

    def to_postgres_condition(self, index: int, table_name: Optional[str] = None):
        full_column_name = f"{table_name}.{self.column}" if table_name else self.column

        if self.operator == "contains":
            return f"LOWER({full_column_name}) LIKE ('%' || :fv_{index} || '%')"
        elif self.operator == "startsWith":
            return f"LOWER({full_column_name}) LIKE (:fv_{index} || '%')"
        elif self.operator == "endsWith":
            return f"LOWER({full_column_name}) LIKE ('%' || :fv_{index})"
        elif self.operator == "equals":
            return f"{full_column_name} = :fv_{index}"
        elif self.operator == "isEmpty":
            return f"{full_column_name} IS NULL"
        elif self.operator == "isNotEmpty":
            return f"{full_column_name} IS NOT NULL"
        elif self.operator == "isAnyOf":
            return f"{full_column_name} IN :fv_{index}"
        elif self.operator == "!=":
            return f"{full_column_name} <> :fv_{index}"
        elif self.operator in [">", "<", "<=", ">=", "="]:
            return f"{full_column_name} {self.operator} :fv_{index}"
        elif self.operator == "is":
            return f"{full_column_name} = :fv_{index}"
        elif self.operator == "after":
            return f"{full_column_name} > :fv_{index}"
        elif self.operator == "before":
            return f"{full_column_name} < :fv_{index}"
        elif self.operator == "onOrAfter":
            return f"{full_column_name} >= :fv_{index}"
        elif self.operator == "onOrBefore":
            return f"{full_column_name} <= :fv_{index}"
        elif self.operator == "not":
            return f"{full_column_name} <> :fv_{index}"
        return ""

    def get_safe_postgres_value(self):
        if self.operator == "isAnyOf":
            return tuple(self.value) if self.value else ()
        elif self.operator in ["contains", "startsWith", "endsWith"]:
            return self.value.lower() if self.value else ""

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


class PaginationMixin(BaseModel):
    page_number: int = Field(
        description="The number of the currently requested page in the pagination system. Index is 1 based.",
        example=1,
    )
    page_size: int = Field(
        default=10, description="The number of results displayed per page.", example=10
    )

    def get_products_offset(self):
        return (self.page_number - 1) * self.page_size


class PagedGlobalFilter(DataPageFilter, PaginationMixin):
    sorting: Optional[DataGridSorting]


class PricingChangesFilter(GlobalFilter, PaginationMixin):
    pass


class PriceValuesFilter(GlobalFilter):
    currency: str


class PagedPriceValuesFilter(PriceValuesFilter, PagedGlobalFilter):
    pass
