#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `skipchunk` package."""


import unittest
from click.testing import CliRunner

from skipchunk import skipchunk
from skipchunk import cli

import json
import jsonpickle
def pretty(obj):
    for c in obj:
        print(c.label,c.total)
    #print(jsonpickle.encode(obj,indent=2))

def getDocsToEnrich(filename):
    spacer = '.  '
    texts = []
    posts = []
    for post in json.load(open(filename)):
        text = post['title'] + spacer + spacer.join(post['content'])
        texts.append(text)
        posts.append(post)
    return texts,posts

class TestSkipchunk(unittest.TestCase):
    """Tests for `skipchunk` package."""

    def setUp(self):
        """Set up test fixtures, if any."""
        self.texts,self.posts = getDocsToEnrich('tests/blog-posts.json')

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_000_something(self):
        """Test something."""
        enriched,concepts,predicates = skipchunk.enrichDocuments(self.texts,self.posts)
        pretty(skipchunk.groupconcepts(concepts,minlabels=10))
        pretty(skipchunk.groupconcepts(predicates,minlabels=10))

    def test_command_line_interface(self):
        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.main)
        assert result.exit_code == 0
        assert 'skipchunk.cli.main' in result.output
        help_result = runner.invoke(cli.main, ['--help'])
        assert help_result.exit_code == 0
        assert '--help  Show this message and exit.' in help_result.output
