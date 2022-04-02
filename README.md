# Pirtuk: Book Tracker CLI 

show reading list, keep a reading log, track the progress

## install:

```shell
$ make install 
```

## example:

### add a book

```shell
$ pirtuk --add "rust for rustaceans" 280 rust 
```

## cli help 

```shell
$ pirtuk --help

options:
  -h, --help            show this help message and exit
  --add TITLE PAGES CATEGORY
                        Add new book
  --state STATE         List books with specific state (ex: open, finish, pending)
  -v                    Show progress bar
  -a                    List all books
  --set-state BOOK_ID STATE
                        Set state for the book (ex: open, finish, pending)
  --inc BOOK_ID PAGES   Increse the current page for the book
  --delete BOOK_ID      Delete the book
  --cat CATEGORY        List books with the specific category
  --track BOOK_ID       Show dates and pages in which the book has been reading
```



