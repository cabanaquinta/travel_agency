from tasks.prefect_tasks import PARQUET_PATH, upload_to_bq  # type: ignore

from prefect import flow


@flow(log_prints=True)
def etl_gcs_to_bq() -> None:
    """ Move files from GCS to BQ """
    upload_to_bq(PARQUET_PATH)


if __name__ == '__main__':
    etl_gcs_to_bq()
