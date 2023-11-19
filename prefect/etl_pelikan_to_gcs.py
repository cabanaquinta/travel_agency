# from tasks.prefect_tasks import enrich_data  # type: ignore
# from tasks.prefect_tasks import read_bigquery_table

# from prefect import flow


# @flow(log_prints=True)
# def etl_pelikan_to_gcs() -> None:
#     """ Pelikan to GCS Bucket"""
#     df = read_bigquery_table()
#     df_enriched = enrich_data(df.head(4))
#     df_enriched.to_csv('enriched.csv')
#     print(df_enriched)


# if __name__ == '__main__':
#     etl_pelikan_to_gcs()
