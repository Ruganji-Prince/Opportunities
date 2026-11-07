from pathlib import Path
import sys
import unittest
root=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(root),str(root/'.tools/python')]
suite=unittest.defaultTestLoader.discover(str(root/'tests'))
result=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(not result.wasSuccessful())
