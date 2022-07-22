import argparse
import sqlite3
import datetime
import os
import itertools
from enum import Enum


DB_ENABLE_FOREIGN_KEYS = "PRAGMA foreign_keys = ON"

DB_INIT_BOOKS = "CREATE TABLE IF NOT EXISTS \
        books(\
        book_id integer PRIMARY KEY, \
        title text NOT NULL,\
        pages integer NOT NULL,\
        current_page integer NOT NULL,\
        category text NOT NULL, \
        state integer NOT NULL, \
        start_date text NOT NULL, \
        finish_date text NOT NULL \
        )"

DB_INIT_BOOK_TRACK = " CREATE TABLE IF NOT EXISTS \
        book_track(\
        track_id integer PRIMARY KEY AUTOINCREMENT , \
        date text NOT NULL, \
        pages integer NOT NULL, \
        book_id integer NOT NULL, \
        FOREIGN KEY(book_id) REFERENCES books(book_id)\
        );"

COLUMN_SPACE = 1


class BookState(Enum):
    OPEN = 0
    FINISHED = 1
    PENDING = 2
    NONE = 3


def parse_state(state):
    match str(state).lower():
        case "open" | "o" | "0":
            return BookState.OPEN
        case "finished" | "f" | "1":
            return BookState.FINISHED
        case "pending" | "p" | "2":
            return BookState.PENDING

    return BookState.NONE


def get_current_time():
    return datetime.date.today()


def print_table_row(title_max_len, cate_max_len, row):

    prefix = " " * COLUMN_SPACE

    id = str(
        prefix + str(row[0]) + " " * (COLUMN_SPACE + (4 - len(str(row[0]))))
    )

    title = str(prefix + row[1] + " " * (title_max_len - len(row[1])))

    pages = str(
        prefix + str(row[2]) + " " * (COLUMN_SPACE + (4 - len(str(row[2]))))
    )

    current_page = str(
        prefix + str(row[3]) + " " * (COLUMN_SPACE + (4 - len(str(row[3]))))
    )

    category = str(prefix + row[4] + " " * (cate_max_len - len(row[4])))

    state = parse_state(row[5]).name
    state = str(prefix + state + " " * (COLUMN_SPACE + (8 - len(state))))

    start_date = str(
        prefix + row[6] + " " * (COLUMN_SPACE + (10 - len(str(row[6]))))
    )

    finish_date = str(
        prefix + row[7] + " " * (COLUMN_SPACE + (10 - len(str(row[7]))))
    )

    print(
        id,
        title,
        pages,
        current_page,
        category,
        state,
        start_date,
        finish_date,
    )


def print_progress_bar(total, current):
    suffix = ""
    decimals = 1
    length = 80
    fill = "x"
    percent = ("{0:." + str(decimals) + "f}").format(
        100 * (current / float(total))
    )
    filledLength = int(length * current // total)
    bar = fill * filledLength + "-" * (length - filledLength)
    print(
        "\n |%s| %s%% %s %s/%s pages\r \n"
        % (bar, percent, suffix, current, total)
    )


def show_books(rows, progress_bar):

    if len(rows) == 0:
        return

    title_max_len = max([len(r[1]) for r in rows]) + (2 * COLUMN_SPACE)
    cate_max_len = max([len(r[4]) for r in rows]) + (2 * COLUMN_SPACE)

    print(
        "\n\033[1m",
        " " * COLUMN_SPACE,
        "id/ title/ pages/ current_page/ category/ state/ start_date/ finish_date",
        "\033[0m\n",
    )

    for row in rows:
        print_table_row(title_max_len, cate_max_len, row)

        if progress_bar:
            print_progress_bar(row[2], row[3])


def find_free_id(cursor):
    bk_ids = cursor.execute("SELECT book_id, title  FROM books").fetchall()
    bk_ids = [row[0] for row in bk_ids]
    for i in itertools.count():
        if i not in bk_ids:
            return i


def books(cursor, progress_bar, state=BookState.OPEN, category=None):
    if state == BookState.NONE and category:
        rows = cursor.execute(
            "SELECT * FROM books WHERE category=?", (category,)
        )
    elif category:
        rows = cursor.execute(
            "SELECT * FROM books WHERE category=? and state=?",
            (category, state.value),
        )
    elif state == BookState.NONE:
        rows = cursor.execute("SELECT * FROM books")
    else:
        rows = cursor.execute(
            "SELECT * FROM books WHERE state=?", (state.value,)
        )
    show_books(rows.fetchall(), progress_bar)


def add(cursor, title, pages, category):
    bk_id = find_free_id(cursor)
    book = (bk_id, title, pages, 0, category, 0, get_current_time(), "-")
    cursor.execute(
        "INSERT INTO \
                    books(\
                    book_id, \
                    title, \
                    pages, \
                    current_page, \
                    category, \
                    state, \
                    start_date, \
                    finish_date)\
                    VALUES(?,?,?,?,?,?,?,?)",
        book,
    )


def set_state(cursor, book_id, state):
    finish_date = get_current_time() if state == BookState.FINISHED else "-"
    cursor.execute(
        "UPDATE books SET state=? , finish_date =? WHERE book_id=?",
        (state.value, finish_date, book_id),
    )


def get_book_track(cursor, book_id):
    book_tracks = cursor.execute(
        "SELECT date, pages from book_track WHERE book_id=?", (book_id,)
    ).fetchall()

    for bt in book_tracks:
        print(bt)


def inc(cursor, book_id, pages):
    book = cursor.execute(
        "SELECT pages, current_page, state from books WHERE book_id=?",
        (book_id,),
    ).fetchone()

    pages = int(pages)

    if not book or pages <= 0:
        return

    book_pages = int(book[0])
    state = parse_state(int(book[2]))

    if state != BookState.OPEN:
        return

    current_page = pages + int(book[1])

    if current_page > book_pages:
        return

    cursor.execute(
        "UPDATE books SET current_page=? WHERE book_id=? AND state=?",
        (current_page, book_id, BookState.OPEN.value),
    )

    cursor.execute(
        "INSERT INTO book_track(date, pages, book_id) VALUES(?,?,?)",
        (get_current_time(), pages, book_id),
    )

    if current_page == book_pages:
        set_state(cursor, book_id, BookState.FINISHED)


def delete(cursor, book_id):
    cursor.execute("DELETE FROM book_track WHERE book_id=?", (book_id,))
    cursor.execute("DELETE FROM books WHERE book_id=?", (book_id,))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--add",
        nargs=3,
        metavar=("TITLE", "PAGES", "CATEGORY"),
        help="Add new book",
    )
    parser.add_argument(
        "--state",
        nargs=1,
        metavar=("STATE"),
        help="List books with specific state (ex: open, finish, pending)",
    )
    parser.add_argument("-v", action="store_true", help="Show progress bar")
    parser.add_argument("-a", action="store_true", help="List all books")
    parser.add_argument(
        "--set-state",
        nargs=2,
        metavar=("BOOK_ID", "STATE"),
        help="Set state for the book (ex: open, finish, pending) ",
    )
    parser.add_argument(
        "--inc",
        nargs=2,
        metavar=("BOOK_ID", "PAGES"),
        help="Increse the current page for the book",
    )
    parser.add_argument(
        "--delete",
        nargs=1,
        type=int,
        metavar=("BOOK_ID"),
        help="Delete the book",
    )
    parser.add_argument(
        "--cat",
        nargs=1,
        metavar=("CATEGORY"),
        help="List books with the specific category",
    )
    parser.add_argument(
        "--track",
        nargs=1,
        metavar=("BOOK_ID"),
        help="Show dates and pages in which the book has been reading",
    )

    args = parser.parse_args()

    # Init db
    path = os.path.join(os.path.expanduser("~"), ".local/share/pirtuk/books.db")
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    cursor.execute(DB_ENABLE_FOREIGN_KEYS)
    cursor.execute(DB_INIT_BOOKS)
    cursor.execute(DB_INIT_BOOK_TRACK)

    progress_bar = False
    category = None
    state = BookState.OPEN

    if args.v:
        progress_bar = True

    if args.a:
        state = BookState.NONE

    if args.add:
        add(cursor, args.add[0], args.add[1], args.add[2])

    if args.set_state:
        state = parse_state(args.set_state[1])
        if state == BookState.NONE:
            print("invalid state")
            exit(1)
        set_state(cursor, args.set_state[0], state)

    if args.inc:
        inc(cursor, args.inc[0], args.inc[1])

    if args.delete:
        delete(cursor, args.delete[0])

    if args.state:
        state = parse_state(args.state[0])

    if args.cat:
        category = args.cat[0]

    if args.track:
        get_book_track(cursor, args.track[0])
    else:
        books(cursor, progress_bar, state, category)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
