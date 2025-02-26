from BEM import *
import unittest
import time

class Tests(unittest.TestCase):

    def test_remove_modifier(self):
        """
        Make block, element and modifiers for element. Then remove modifier
        """
        b = BEM.get_default_bem()
        block = Block(b, "aboba1")
        if block.path.exists():
            shutil.rmtree(block.path)

        with open(block.BEM.cssFile, "w") as f:
            f.write("")

        block.create()
        el = Element(b, block, "hello2")
        el.create()
        mod1 = Modifier(b, el, "greet", ["Joe", "Alex", "Bar"])
        mod1.create()
        mod2 = Modifier(b, el, "nokey",)
        mod2.create()
        mod1.remove(True)

    def test_create_block(self):
        """
        Create complex block structure
        """
        b = BEM.get_default_bem()
        block = Block(b, "block1")
        block.create()
        mod = Modifier(b, block, "boolmod")
        mod.create()
        for i in range(3):
            element = Element(b, block, f"el{i}")
            element.create()

        element = Element(b, block, "el-with-mods")
        element.create()
        mods = Modifier(b, element, "mods", [str(i) for i in range(5)])
        mods.create()

        ent = Element(b, block, "el-mod")
        ent.create()
        mods = Modifier(b, ent, "modded")
        mods.create()

    def test_rename_block(self):
        """
        Rename block1 to block2
        """
        b = BEM.get_default_bem()
        block = Block(b, "block1")
        block.rename("block2")

    def test_remove_block(self):
        """
        Remove block2
        """
        b = BEM.get_default_bem()
        block = Block(b, "block2")
        block.remove(True)

if __name__ == "__main__":
    # Nothing should appear
    suite = unittest.TestSuite()
    suite.addTest(Tests("test_create_block"))
    suite.addTest(Tests("test_rename_block"))
    suite.addTest(Tests("test_remove_block"))

    unittest.TextTestRunner().run(suite)

