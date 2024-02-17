from tasks.prefect_tasks import create_message, read_bigquery_table

from prefect import flow
from prefect.blocks.notifications import SlackWebhook


@flow(log_prints=True)
def notify() -> None:
    df = read_bigquery_table()
    message = create_message(df)
    slack_webhook_block = SlackWebhook.load('travelagent')
    if message != 'Nothing New':
        slack_webhook_block.notify(message)


if __name__ == '__main__':
    notify()
