from etl_gcp_to_bq import etl_gcs_to_bq
from etl_web_to_gcs import etl_web_to_gcs
from notify import notify
from prefect_gcp.cloud_run import CloudRunJob
from prefect_gcp.cloud_storage import GcsBucket

from prefect import get_client
from prefect.deployments import Deployment

client = get_client()
gcs_block = GcsBucket.load('bucket')
cloud_run_job_block = CloudRunJob.load('runner')


deployment_web_to_gcs = Deployment.build_from_flow(
    flow=etl_web_to_gcs,
    name='TRAVEL_web_to_gcs',
    storage=gcs_block,
    infrastructure=cloud_run_job_block,
    work_pool_name='my-push-pool'
)


deployment_gcs_to_gcp = Deployment.build_from_flow(
    flow=etl_gcs_to_bq,
    name='TRAVEL_gcs_to_bq',
    storage=gcs_block,
    infrastructure=cloud_run_job_block,
    work_pool_name='my-push-pool'
)


deployment_notify = Deployment.build_from_flow(
    flow=notify,
    name='notify',
    storage=gcs_block,
    infrastructure=cloud_run_job_block,
    work_pool_name='my-push-pool'
)


if __name__ == '__main__':
    deployment_web_to_gcs.apply()  # type: ignore
    deployment_gcs_to_gcp.apply()  # type: ignore
    deployment_notify.apply()