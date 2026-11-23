import unittest

from check import Homepage, ORIGIN


class HomepageTests(unittest.TestCase):
    canonical = f'<link href="{ORIGIN}" rel="canonical">'
    heading = '<h1>Find <span>a useful tool</span></h1>'
    directory = '<a href="/tools">Browse tools</a>'

    def test_accepts_editorial_copy_changes(self):
        self.assertTrue(Homepage().matches(self.canonical + self.heading + self.directory))
        self.assertTrue(Homepage().matches(
            f'<link rel="canonical" href="{ORIGIN}/"><h1>New headline</h1>'
            f'<a href="{ORIGIN}/tools">Choose a calculator</a>'
        ))

    def test_rejects_wrong_page_or_missing_visible_navigation(self):
        wrong = f'<link rel="canonical" href="{ORIGIN}/tools">'
        for body in (
            wrong + self.heading + self.directory,
            self.canonical + wrong + self.heading + self.directory,
            self.canonical + '<h1> </h1>' + self.directory,
            self.canonical + self.heading,
            f'<script type="text/plain">{self.canonical}{self.heading}{self.directory}</script>',
        ):
            with self.subTest(body=body):
                self.assertFalse(Homepage().matches(body))
