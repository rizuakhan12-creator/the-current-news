import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import publish_manual

class ImagePublicationTests(unittest.TestCase):
    def test_binary_image_follows_draft_into_publication_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'static/assets').mkdir(parents=True)
            binary=b'\xff\xd8\xff\x00\x80photo\xff\xd9'
            with patch.object(publish_manual,'ROOT',root),patch.object(publish_manual,'run') as git,patch.object(publish_manual.subprocess,'run',return_value=subprocess.CompletedProcess([],0,stdout=binary)):
                publish_manual.ensure_image({'image':'assets/hubble.jpg'})
            self.assertEqual((root/'static/assets/hubble.jpg').read_bytes(),binary)
            git.assert_called_once_with('git','fetch','origin','automation/news-drafts')

    def test_rejects_traversal_and_remote_images(self):
        for image in ('assets/../../private.jpg','https://example.org/photo.jpg','assets/evil.exe','assets/..\\private.jpg'):
            with self.subTest(image=image),self.assertRaises(ValueError):
                publish_manual.ensure_image({'image':image})

if __name__=='__main__': unittest.main()
