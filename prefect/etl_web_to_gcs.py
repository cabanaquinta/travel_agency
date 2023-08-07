from prefect import flow
from tasks.prefect_tasks import (clean_data, fetch, save_parquet_file,
                                 upload_to_gcs, PARQUET_PATH)


@flow(log_prints=True)
def etl_web_to_gcs() -> None:
    """ The main ETL Code """
    raw_data = fetch()
    data = clean_data(raw_data)
    save_parquet_file(data, PARQUET_PATH)
    upload_to_gcs(PARQUET_PATH)
    print(data.head(2))


if __name__ == '__main__':
    etl_web_to_gcs()
