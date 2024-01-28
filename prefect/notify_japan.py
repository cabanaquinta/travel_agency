from prefect import flow
from prefect.blocks.notifications import SlackWebhook


@flow(log_prints=True)
def notify() -> None:
    slack_webhook_block = SlackWebhook.load('travelagent')
    slack_webhook_block.notify('Hello from Prefect!')


if __name__ == '__main__':
    notify()
