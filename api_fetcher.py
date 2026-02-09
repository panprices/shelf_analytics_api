import requests
import typer
import pandas as pd
from tqdm import tqdm
from structlog import get_logger

app = typer.Typer()
logger = get_logger()


@app.command()
def fetch(api_key: str, file_name: str):
    """
    Loops through the pages from the API and exports all the data to a CSV file
    Response format:
    {
        "rows": [...],
        "page": int,
        "pages_count": int,
        "count": int
    }

    Where:
    * rows: the actual data from the API
    * page: the current page number
    * pages_count: the total number of pages
    * count: the total number of items

    :param api_key:
    :param file_name:
    :return:
    """

    api_endpoint = "https://api.getloupe.co/v2/products/retailer_offers"

    # Fetch the first page and extract data and pagination info
    response = requests.get(api_endpoint, headers={"x-api-key": api_key})
    data = response.json()

    full_rows = data["rows"]
    page = data["page"]
    pages_count = data["pages_count"]
    count = data["count"]
    logger.info(
        f"Fetched page {page} of {pages_count}, received {len(data['rows'])} rows"
    )

    for page in tqdm(range(1, pages_count)):
        response = requests.get(
            api_endpoint, headers={"x-api-key": api_key}, params={"page": page}
        )
        data = response.json()
        full_rows.extend(data["rows"])
        logger.info(
            f"Fetched page {data['page']} of {pages_count}, received {len(data['rows'])} rows"
        )

    # Export the data to a CSV file
    df = pd.DataFrame(full_rows)
    df.to_csv(file_name, index=False)

    print("Total count according to the returned data", len(full_rows))


if __name__ == "__main__":
    app()
