from codeanvil.CLI.cli import argparser, choose_option
from codeanvil.config.logger import get_logger


def main():
    log = get_logger(__name__)
    args = argparser()
    choose_option(args)


if __name__ == "__main__":
    main()
