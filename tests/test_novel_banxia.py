import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bs4 import BeautifulSoup

from crawl_utils import append_to_file, save_to_file
from parsers import novel_banxia
from parsers.novel_banxia import extract_chapter_links, extract_content


class BanxiaParserTests(unittest.TestCase):
    def test_extracts_traditional_chapter_links(self):
        soup = BeautifulSoup(
            '<ul><li><a href="/books/342243/1.html">第一章</a></li></ul>',
            "lxml",
        )

        links = extract_chapter_links(soup)

        self.assertEqual([link["href"] for link in links], ["/books/342243/1.html"])

    def test_extracts_simplified_chapter_content(self):
        soup = BeautifulSoup(
            '<body><div id="reader-body" class="reader-body">章节正文</div></body>',
            "lxml",
        )

        self.assertEqual(extract_content(soup), "章节正文")

    def test_extracts_simplified_paragraphs_on_separate_lines(self):
        soup = BeautifulSoup(
            '<body><div id="reader-body" class="reader-body">'
            "<p>第一段</p><p>第二段</p><p>   </p>"
            "</div></body>",
            "lxml",
        )

        self.assertEqual(extract_content(soup), "第一段\n第二段")

    def test_extracts_simplified_chapter_links(self):
        soup = BeautifulSoup(
            '<div class="book-list"><a href="/chapter/3h6mc3ib4nrMHpcl1nr8pC/1">'
            "第一章</a></div>",
            "lxml",
        )

        links = extract_chapter_links(soup)

        self.assertEqual(
            [link["href"] for link in links],
            ["/chapter/3h6mc3ib4nrMHpcl1nr8pC/1"],
        )

    def test_extracts_simplified_links_outside_book_list(self):
        soup = BeautifulSoup(
            '<section class="chapters"><a href="/chapter/book-id/chapter-id">'
            "第一章</a></section>",
            "lxml",
        )

        links = extract_chapter_links(soup)

        self.assertEqual([link["href"] for link in links], ["/chapter/book-id/chapter-id"])

    def test_main_fetches_simplified_chapters(self):
        book_page = BeautifulSoup(
            '<title>测试小说</title><div class="book-list">'
            '<a href="/chapter/book-id/1">第一章</a></div>',
            "lxml",
        )
        chapter_pages = [
            BeautifulSoup('<body><div id="nr1">章节正文</div></body>', "lxml")
        ]
        output = io.StringIO()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "book.txt"
            with (
                patch.object(sys, "argv", ["novel_banxia.py", "https://www.banx.la/book/book-id"]),
                patch.object(novel_banxia, "fetch_page", side_effect=[book_page, *chapter_pages]),
                patch.object(novel_banxia, "get_output_path", return_value=str(output_path)),
                patch.object(novel_banxia, "append_to_file", wraps=append_to_file) as append,
                patch.object(novel_banxia.time, "sleep") as sleep,
                patch.object(novel_banxia, "save_to_file") as save,
                contextlib.redirect_stdout(output),
            ):
                novel_banxia.main()

            self.assertIn("正在抓取: 第一章", output.getvalue())
            save.assert_called_once()
            self.assertEqual(save.call_args.args[2], {0: "\n第一章\n章节正文"})
            self.assertEqual(save.call_args.kwargs["save_path"], str(output_path))
            append.assert_called_once_with(str(output_path), "\n第一章\n章节正文", overwrite=True)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "\n第一章\n章节正文\n")
            sleep.assert_not_called()

    def test_waits_configured_interval_between_chapters(self):
        book_page = BeautifulSoup(
            '<title>测试小说</title><div class="book-list">'
            '<a href="/chapter/book-id/1">第一章</a>'
            '<a href="/chapter/book-id/2">第二章</a></div>',
            "lxml",
        )
        chapter_pages = [
            BeautifulSoup('<body><div id="nr1">第一章正文</div></body>', "lxml"),
            BeautifulSoup('<body><div id="nr1">第二章正文</div></body>', "lxml"),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "book.txt"

            def verify_first_chapter(delay):
                self.assertEqual(delay, novel_banxia.CHAPTER_REQUEST_INTERVAL_SECONDS)
                self.assertEqual(
                    output_path.read_text(encoding="utf-8"),
                    "\n第一章\n第一章正文\n",
                )

            with (
                patch.object(sys, "argv", ["novel_banxia.py", "https://www.banx.la/book/book-id"]),
                patch.object(novel_banxia, "fetch_page", side_effect=[book_page, *chapter_pages]),
                patch.object(novel_banxia, "get_output_path", return_value=str(output_path)),
                patch.object(novel_banxia.time, "sleep", side_effect=verify_first_chapter) as sleep,
                patch.object(novel_banxia, "save_to_file"),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                novel_banxia.main()

            sleep.assert_called_once_with(novel_banxia.CHAPTER_REQUEST_INTERVAL_SECONDS)
            self.assertEqual(
                output_path.read_text(encoding="utf-8"),
                "\n第一章\n第一章正文\n\n第二章\n第二章正文\n",
            )

    def test_save_creates_missing_output_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "Downloads" / "Book-Author.txt"
            with (
                patch("crawl_utils.os.getcwd", return_value=temp_dir),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                save_to_file("Book", "Author", {0: "Chapter content"})

            self.assertEqual(output_path.read_text(encoding="utf-8"), "Chapter content\n")

    def test_empty_result_does_not_create_output_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "Downloads" / "book.txt"
            with contextlib.redirect_stdout(io.StringIO()):
                save_to_file("Book", "Author", {}, save_path=output_path)

            self.assertFalse(output_path.exists())


if __name__ == "__main__":
    unittest.main()
