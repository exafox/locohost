import unittest
import os
import shutil
from locohost_cli.locohost import _create_cot, _update_cot, _compress_cot

class TestCoTOperations(unittest.TestCase):
    def setUp(self):
        self.project_name = "test_project"
        self.project_dir = os.path.join(os.getcwd(), self.project_name)
        self.context_dir = os.path.join(self.project_dir, '.context')
        
        # Create project directory
        os.makedirs(self.context_dir, exist_ok=True)

    def tearDown(self):
        # Clean up: remove the test project directory
        shutil.rmtree(self.project_dir)

    def test_create_cot(self):
        _create_cot(self.project_name, "Initial CoT entry")
        cot_files = [f for f in os.listdir(self.context_dir) if f.startswith('cot_') and f.endswith('.md')]
        self.assertEqual(len(cot_files), 1)
        
        with open(os.path.join(self.context_dir, cot_files[0]), 'r') as f:
            content = f.read()
        self.assertIn("Initial CoT entry", content)

    def test_update_cot(self):
        _create_cot(self.project_name, "Initial CoT entry")
        _update_cot(self.project_name, "Updated CoT entry")
        
        cot_files = [f for f in os.listdir(self.context_dir) if f.startswith('cot_') and f.endswith('.md')]
        self.assertEqual(len(cot_files), 1)
        
        with open(os.path.join(self.context_dir, cot_files[0]), 'r') as f:
            content = f.read()
        self.assertIn("Initial CoT entry", content)
        self.assertIn("Updated CoT entry", content)

    def test_compress_cot(self):
        _create_cot(self.project_name, "Initial CoT entry")
        _update_cot(self.project_name, "Updated CoT entry")
        _compress_cot(self.project_name)
        
        snapshot_file = os.path.join(self.context_dir, 'snapshot.md')
        self.assertTrue(os.path.exists(snapshot_file))
        
        with open(snapshot_file, 'r') as f:
            content = f.read()
        self.assertIn("Initial CoT entry", content)
        self.assertIn("Updated CoT entry", content)

if __name__ == '__main__':
    unittest.main()
