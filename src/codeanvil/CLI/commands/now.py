"""`codeanvil now` — print the current timestamp."""


def cmd_now(tz: str | None = None, machine: bool = False) -> None:
    from codeanvil.config.time import format_timestamp, format_timestamp_machine
    if machine:
        print(format_timestamp_machine(tz_name=tz))
    else:
        print(format_timestamp(tz_name=tz))
