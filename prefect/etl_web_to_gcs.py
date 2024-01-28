from tasks.prefect_tasks import (PARQUET_PATH, clean_data,  # type: ignore
                                 fetch, save_parquet_file, upload_to_gcs)
from prefect import flow


@flow(log_prints=True)
def etl_web_to_gcs() -> None:
    """ The main ETL Code """
    # print('hi')
    raw_data = fetch()
    data = clean_data(raw_data)
    # print(data)
    save_parquet_file(data, PARQUET_PATH)
    upload_to_gcs(PARQUET_PATH)
    print(data.head(2))


if __name__ == '__main__':
    etl_web_to_gcs()
