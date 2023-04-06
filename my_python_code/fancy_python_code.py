import argparse
import logging

logging.basicConfig(level=logging.INFO)


def print_hello(name: str) -> None:
    logging.info(f'Your name is {name}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Capture Name')
    parser.add_argument('--name', required=True, help='Your Name')
    args = parser.parse_args()
    print_hello(args.name)
