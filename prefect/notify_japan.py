from prefect.blocks.notifications import SlackWebhook
from prefect import flow


@flow(log_prints=True)
def notify() -> None:
   slack_webhook_block = SlackWebhook.load("travelagent")
   slack_webhook_block.notify("Hello from Prefect!")   


if __name__ == '__main__':
    notify()

