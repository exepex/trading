"""Commands for the paper accounts: `python -m fno account init` and `python -m fno account show` (never orders)."""

from __future__ import annotations

import json

from ..constants import BOOKS

EXIT_BUSY = 3  # another writer holds the account: this run wrote nothing


def add_account_parser(subparsers) -> None:
    account = subparsers.add_parser("account", help="the three books' paper accounts (never orders)")
    actions = account.add_subparsers(dest="account_cmd", required=True)
    init = actions.add_parser("init", help="open each book's account once with risk.paper_account_rs and no positions")
    init.add_argument("--book", choices=BOOKS, action="append", help="only this book (repeatable); default all three")
    show = actions.add_parser("show", help="cash, closed equity and open legs of one book (no marks needed)")
    show.add_argument("book", choices=BOOKS)
    account.set_defaults(func=cmd_account)


def cmd_account(args) -> int:
    from ..books.lock import AccountBusy
    from ..composition import build_paper_account, open_account_writer
    from ..models import now_ist

    if args.account_cmd == "show":
        print(json.dumps(build_paper_account(args.book).summary(), indent=1))
        return 0
    status = 0
    for book in args.book or BOOKS:
        try:
            with open_account_writer(book) as writer:
                print(f"{book}: {'started' if writer.start(now_ist().date()) else 'already started; unchanged'}")
        except AccountBusy as busy:
            print(f"{book}: not written: {busy}")
            status = EXIT_BUSY
    return status
