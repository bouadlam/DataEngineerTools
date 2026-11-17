"""Vérifications hors ligne : uv run python -m unittest discover -s 1Introduction -p 'test_*.py' -v"""
import ast
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
import requests
import intro_solutions as s

class IntroductionTests(unittest.TestCase):
    def test_retry_then_success(self):
        client = s.HttpClient()
        response = Mock()
        client.session.get = Mock(side_effect=[requests.Timeout(), response])
        with patch.object(s.time, 'sleep'):
            self.assertIs(client.get('https://example.org', timeout=3), response)
        self.assertEqual(client.session.get.call_count, 2)
        for call in client.session.get.call_args_list:
            self.assertEqual(call.kwargs['timeout'], 3)
            self.assertEqual(call.kwargs['headers']['User-Agent'], client.user_agent)

    def test_retry_exhaustion(self):
        client = s.HttpClient()
        client.session.get = Mock(side_effect=requests.ConnectionError())
        with patch.object(s.time, 'sleep'), self.assertRaises(requests.ConnectionError):
            client.get('https://example.org', retries=2)
        self.assertEqual(client.session.get.call_count, 3)

    def test_404_no_retry(self):
        client = s.HttpClient()
        response = requests.Response()
        response.status_code = 404
        client.session.get = Mock(return_value=response)
        with self.assertRaises(requests.HTTPError):
            client.get('https://example.org')
        self.assertEqual(client.session.get.call_count, 1)

    def test_html(self):
        page = s.scraper.parse_page('<title>Café</title><nav>Menu</nav><article><h1>Titre</h1><p>A &amp; B</p><script>evil</script><img src="/a.png"><a href="/local">local</a><a href="https://other.org">autre</a></article>', 'https://example.org/news')
        self.assertEqual(page['images'], ['https://example.org/a.png'])
        self.assertEqual(page['outgoing_links'], ['https://other.org'])
        self.assertEqual(page['h1'], ['Titre'])
        self.assertNotIn('evil', page['text'])
        self.assertNotIn('Menu', page['text'])
        self.assertIn('A & B', page['text'])

    def test_google_redirect_dedup(self):
        html = '<a href="/url?q=https%3A%2F%2Fexample.org"><h3>A</h3></a><a href="https://example.org"><h3>A</h3></a><a href="/search?q=b"><h3>B</h3></a>'
        self.assertEqual(s.parse_google_results(html), [{'title':'A', 'url':'https://example.org'}])

    def test_rss_errors_and_limit(self):
        response = Mock(content=b'<rss><channel><item><title>A</title><link>https://example.org/a</link></item><item><link>https://example.org/b</link></item><item><link>https://example.org/c</link></item></channel></rss>')
        page = {'url':'https://example.org/a', 'domain':'example.org','text':'Article','h1':['Titre'],'title':'Page','images':[]}
        with patch.object(s.scraper, 'get', return_value=response), patch.object(s.scraper, 'scrape', side_effect=[page, requests.Timeout()]) as scrape:
            result = s.collect_news('https://example.org/rss', 'Sciences', limit=2, delay=0)
        self.assertEqual(scrape.call_count, 2)
        self.assertEqual(result['articles'][0]['category'], 'Sciences')
        self.assertEqual(len(result['errors']), 1)

    def test_selenium_extractors(self):
        # Exécute les vraies fonctions du notebook sans ouvrir de navigateur.
        nb = json.loads(Path(__file__).with_name('Part5_Web_Scraping_WebDriver.ipynb').read_text())
        from decimal import Decimal
        import re
        from selenium.webdriver.common.by import By
        scope = {'Decimal': Decimal, 're': re, 'By': By}
        for cell in nb['cells']:
            if cell['cell_type'] != 'code': continue
            for node in ast.parse(''.join(cell['source'])).body:
                if isinstance(node, ast.FunctionDef) and node.name.startswith('extract_'):
                    exec(compile(ast.Module(body=[node], type_ignores=[]), '<notebook>', 'exec'), scope)
        book = Mock()
        book.find_element.return_value.text = '£12.50'
        self.assertEqual(scope['extract_price'](book), Decimal('12.50'))
        book.find_element.return_value.get_attribute.return_value = 'star-rating Three'
        self.assertEqual(scope['extract_rating'](book), 3)
        book.find_element.return_value.get_attribute.return_value = 'https://example.org/a.jpg'
        self.assertEqual(scope['extract_image'](book), 'https://example.org/a.jpg')

if __name__ == '__main__': unittest.main()
