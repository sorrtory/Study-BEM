import os
import shutil
from pathlib import Path
from typing import Self, Any


class BEM:
    """
    BEM structure controller
    """
    @classmethod
    def get_default_bem(cls) -> Self:
        """
        Return default setting of BEM
        """
        root = Path(__file__).parent.parent     # Project folder
        blocks = root.joinpath("src", "blocks") # Blocks folder
        css = root.joinpath("src", "index.css") # CSS file where you use imports
        return cls(root, blocks, css)

    @staticmethod
    def _choose_option(hint: str, commands: list[str], variations: list[list[str]], prompt: str = "") -> str:
        """
        Let user pick once from options
        Args:
            hint: Display for ?
            commands: Possible commands
            variations: For each command here is a list of variations
        """
        inp = None

        # Build a dict to reduce commands variations
        all_options = dict()
        for x in commands:
            all_options[x] = x

        for i in range(len(variations)):
            for x in variations[i]:
                all_options[x] = commands[i]

        while True:
            inp = input(prompt + "> ").lower()
            if inp == "?" or inp == "help":
                print(hint)
            else:
                if inp in all_options:
                    break
                else:
                    if inp.strip() != "":
                        print("Unknown option! Try ?")

        return all_options.get(inp)

    def __init__(self, root: Path, blocks: Path, css: Path):
        """
        Initialize controller

        Args:
            root:   Project folder path
            blocks: Blocks folder path related to root
            css:    Path to main css file where others are imported
        """

        # Check paths existence
        if not root.exists():
            raise FileNotFoundError("Can't find root folder")
        if not blocks.exists():
            raise FileNotFoundError("Can't find blocks folder")
        if not css.exists():
            raise FileNotFoundError("Can't find css file")

        self.rootDir = root         # Project folder path
        self.blocksDir = blocks     # Blocks folder path related to root
        self.cssFile = css          # Path to main css file where others are imported

        self.blocks = []            # List of all current blocks

        self.autolaunch = False     # Launch vs code after creation


        # Find existing blocks
        self.parse(False)

    def start_loop(self, cond: bool = True):
        """
        Launch a console
        Args:
            cond: Just a condition to be cycled
        """
        print("Use ? for hint")
        while cond:
            self.action()

    def action(self):
        """
        Pick working mode and perform it
        """
        mode = self._choose_option(
            "Exit(0) / Create(1) / Remove(2) / Rename(3) / Show(4) / Fix(5) / Parse(6) / Code(7) / Backup(8)",
            ["exit", "create", "remove", "rename", "show", "fix", "parse", "code", "backup"],
            [
                ["0", "q"],
                ["1", "new"],
                ["2", "delete", "rm"],
                ["3", "rn"],
                ["4", "ls"],
                ["5", "fx"],
                ["6", "prs", "update", "scan", "rescan"],
                ["7", "vscode", "vs code"],
                ["8"]
            ]
        )

        if mode == "exit":
            self.exit()
            return
        elif mode == "backup":
            css_copy = self.make_import_backup()
            print(f"{self.cssFile} copied as {css_copy}")
        elif mode == "code":
            self.autolaunch = not self.autolaunch
            print("Autolaunch status:", self.autolaunch)
        elif mode == "fix":
            c = self.fix_imports()
            print(f"Updated {c} lines")
        elif mode == "parse":
            self.parse(False)
        elif mode == "show":
            obj_type = self._choose_option(
                "Back(0) / Block(1) / Element(2) / Modifier(3) / Everything(4): ",
                ["back", "block", "element", "modifier", "all"],
                [["0", "q", "back"], ["1", "b"], ["2", "e", "el"],
                    ["3", "m", "mod"], ["4", "a", "everything"]],
                prompt="- " + mode + " "
            )
            if obj_type == "back":
                return
            self.show(obj_type)
        else:
            obj_type = self._choose_option(
                "Back(0) / Block(1) / Element(2) / Modifier(3): ",
                ["back", "block", "element", "modifier"],
                [["0", "q", "back"], ["1", "b"], [
                    "2", "e", "el"], ["3", "m", "mod"]],
                prompt="- " + mode + " "
            )
            if obj_type == "back":
                return
            # Ask the object name
            if mode == "create":
                data = self._resolve_type(obj_type, True)
                if data[1] is None:
                    return
                try:
                    self.create(*data)
                    print("Created")
                except FileExistsError:
                    print("Already exists!")

            else:
                data = self._resolve_type(obj_type, False)
                if data[1] is None:
                    return
                try:
                    if mode == "remove":
                        self.remove(*data)
                        print("Removed")
                    if mode == "rename":
                        new_name = input("Enter new name: ")
                        self.rename(new_name, *data)
                        print("Renamed")
                except FileNotFoundError:
                    print("Not exist!")

    @staticmethod
    def exit():
        """
        Early exit
        """
        print("Exit")
        exit()

    @staticmethod
    def _get_object(obj_name, arr) -> Any | None:
        """
        Find obj_name in referred list.
        Args:
            obj_name: Name of arr element
            arr: Array to be searched
        """
        if obj_name is None:
            return None
        obj = None
        for x in arr:
            if x.name == obj_name:
                obj = x
        if obj is None:
            print(f"{obj_name} doesn't exist!. Try parse")
        return obj

    def _remove_block(self, block_name: str):
        """
        Remove block from self.blocks by name.

        Raise error if it has no such a name.
        """
        ind = None
        for i in range(len(self.blocks)):
            if self.blocks[i].name == block_name:
                ind = i
        self.blocks.pop(ind)

    @staticmethod
    def _input(prompt: str) -> str | None:
        """
        Input name.
        If name is 0 then return None
        """
        while True:
            s = input(prompt)
            if s == "0":
                print("Going back")
                return None
            elif s == "?" or s == "help":
                print("Type 0 to go back")
            else:
                return s

    def _resolve_type(self, obj_type: str, create: bool) -> tuple:
        """
        Input object's and its ancestor's names
        Args:
            obj_type: 1/2/3
            create: Ask modifier values or not
        """
        # Signature of object:  type, name, ancestor, values
        data = [obj_type, None, None, None]

        if obj_type == "block":
            block_name = self._input("Set block name: ")
            data[1] = block_name
        if obj_type == "element":
            block = self._get_object(self._input(
                f"Set parent block name: "), self.blocks)
            if block:
                element_name = self._input("Set element name: ")
                data[1] = element_name
                data[2] = block
        if obj_type == "modifier":
            block = self._get_object(self._input(
                f"Set parent block name: "), self.blocks)
            if block:
                element = self._input("Set element name(empty for block modifier): ")
                element = "__" + element.lstrip("_")
                ancestor = None
                if element == "__":
                    ancestor = block
                else:
                    ancestor = self._get_object(element, block.elements)
                if ancestor:
                    modifier_name = self._input("Set modifier name: ")

                    if create:
                        values = self._input("Set modifier values by spaces(empty for bool): ")
                        if values != "":
                            data[3] = values.split(" ")
                    data[1] = modifier_name
                    data[2] = ancestor

        return tuple(data)

    def get_blocks(self) -> tuple:
        """
        Return the list of blocks in BEM.

        Could parse() before to update the list.
        """
        return tuple(self.blocks)

    def get_elements(self) -> tuple:
        """
        Return the list of elements

        Could parse() before to update the list.
        """
        els = []
        for x in self.blocks:
            els.extend(x.elements)
        return tuple(els)

    def get_modifiers(self) -> tuple[tuple, tuple]:
        """
        Return the list of block modifiers and the list of element modifiers

        Could parse() before to update the list.
        """
        els = self.get_elements()
        block_mods = []
        for x in self.blocks:
            block_mods.extend(x.modifiers)
        el_mods = []
        for x in els:
            el_mods.extend(x.modifiers)
        return tuple(block_mods), tuple(el_mods)

    def fix_imports(self) -> int:
        """
        Call update_import_line method of every object
        """
        self.parse()
        c = 0
        for x in self.get_blocks():
            c += x.update_import_line()
            for xe in x.elements:
                c += xe.update_import_line()
                for xm in xe.modifiers:
                    c += xm.update_import_line()
            for xm in x.modifiers:
                c += xm.update_import_line()
        return c

    def show(self, objs_type):
        """
        Print the list of requested type
        Args:
            objs_type: block / element / modifier
        """
        if objs_type == "" or objs_type == "all":
            objs_type = "block"+"element"+"modifier"
        delimiter = " || "
        if objs_type.find("block") != -1:
            print(f"{'Blocks:':18} ", end="\t")
            for x in self.get_blocks():
                print(x.name, end=delimiter)
            print()
        if objs_type.find("element") != -1:
            print(f"{'Elements:':18} ", end="\t")
            for x in self.get_elements():
                print(f"{x.ancestor.name}<-{x.name}", end=delimiter)
            print()
        if objs_type.find("modifier") != -1:
            block_mods, element_mods = self.get_modifiers()
            print(f"{'Block modifiers:':18} ", end="\t")
            for x in block_mods:
                print(f"{x.ancestor.name}<-{x.name}", end=delimiter)
            print()
            print(f"{'Element modifiers:':18} ", end="\t")
            for x in element_mods:
                print(
                    f"{x.ancestor.ancestor.name}<-{x.ancestor.name}<-{x.name}", end=delimiter)
            print()

    def parse(self, quiet: bool = True):
        """
        Find all the blocks and save them.
        Blocks parse their descendants too.
        """
        self.blocks.clear()
        if not quiet:
            print("Parsed blocks:", end="\t")
        for x in self.blocksDir.iterdir():
            self.blocks.append(Block(self, x.name))
            if not quiet:
                print(f"{x.name}", end=" | ")
            self.blocks[-1].parse_descendants()
        if not quit:
            print()

    def make_obj(self, obj_type: str, obj_name: str, ancestor=None, values=None):
        """
        Make a new object but not create it
        Args:
            obj_type: block / element / modifier
            obj_name: Name of the new object
            ancestor: Block / Element instance
            values: list of modifier values (None for bool)
        """
        obj = None

        if obj_type == "block":
            obj = Block(self, obj_name)
        elif obj_type == "element":
            obj = Element(self, ancestor, obj_name)
        elif obj_type == "modifier":
            obj = Modifier(self, ancestor, obj_name, values)

        return obj

    @staticmethod
    def launch_editor(obj, editor: str = "code"):
        """
        Start editing the obj css file
        :param obj: Instance of object
        :param editor: Not implemented. Vs code is default
        """
        os.system(f"code {obj.cssFile}")

    def create(self, obj_type: str, obj_name: str, ancestor=None, values=None):
        """
        Make a new object. Create file and add import css
        """
        obj = self.make_obj(obj_type, obj_name, ancestor, values)
        obj.create()

        if obj_type == "block":
            self.blocks.append(obj)

        if self.autolaunch:
            self.launch_editor(obj)

    def remove(self, obj_type: str, obj_name: str, ancestor=None, values=None):
        """
        Remove file and import from css
        """
        obj = self.make_obj(obj_type, obj_name, ancestor, values)
        res = obj.remove()
        if res:
            if obj_type == "block":
                self._remove_block(obj_name)

    def rename(self, new_name: str, obj_type: str, obj_name: str, ancestor=None, values=None):
        """
        Rename file and change css import
        """
        obj = self.make_obj(obj_type, obj_name, ancestor, values)
        obj.rename(new_name)

    def append_import(self, line: str):
        """
        Add line to the end of css file
        """

        with open(self.cssFile, "a") as f:
            f.write(line)

    def make_import_backup(self) -> Path:
        """
        Just copy main css file in case
        """
        css_copy = Path(__file__).parent / self.cssFile.name
        shutil.copyfile(self.cssFile, css_copy)
        css_copy = css_copy.rename(css_copy.with_suffix(".css.old"))
        return css_copy

    def has_import(self, line: str) -> bool:
        """
        Check import file
        Args:
            line: Line that will be found in the css import file
        """
        with open(self.cssFile, "r") as f:
            text = f.read()
            return text.find(line) != -1

    def remove_import(self, line: str):
        """
        Open css file and delete line.

        Also delete comment before it.
        Be sure to keep the script proposed formatting.
        """
        # Backup css import file
        # Don't think it is neccesary
        # self.make_import_backup()

        # Remove line and commenting line before it if possible
        with open(self.cssFile, "r") as f:
            text = f.read()
            # Raises ValueError if cssFile has no such line
            ind = text.index(line)
            new_text = text[:ind] + text[ind+len(line):]
        with open(self.cssFile, "w") as f:
            f.write(new_text)


class _BEMGen:
    """
    This is the ancestor of Block / Element / Modifier classes
    """
    # I call the Block / Element / Modifier node as object further

    # Must be set with override
    # "block" / "element" / "modifier"
    type = ""
    # Block / Element instance. Blocks have None
    ancestor = None

    def __init__(self, bem: BEM, name: str):
        self.BEM = bem                      # BEM class instance
        self.name = name                    # Name of object
        self.cssName = ""                   # CSS class name
        self.path = Path()                  # Absolute path to object location
        self.cssFile = Path()               # Abs path to object's css file
        self.css = ""                       # CSS code. Not live time

        # Set the mentioned vars
        self.update_name(name)

    def error(self, err: BaseException):
        """
        Called when something is wrong
        """
        err.add_note(f"Object name: {self.name}")
        err.add_note(f"Object path: {self.path}")
        err.add_note(f"Object's css file path: {self.cssFile}")
        raise err

    def warning(self, msg: str):
        """
        Called when something is strange
        """
        print(f"Warning {self.name}!", msg)

    def exists(self) -> bool:
        """
        Check creation and removal possibility
        """
        return self.path.exists()

    def build_import_line(self) -> str:
        """
        Construct lines used as css import
        """
        # Comment line
        line = "/* %s %s */\n" % (self.name,
                                  self.type)

        relative_path = os.path.relpath(self.cssFile, self.BEM.cssFile.parent)

        # Import line
        line += f"@import url(\"{relative_path}\");\n"

        return line

    def get_default_content(self) -> str:
        """
        Make a string that is written to BEM object's css file.
        """
        content = ".%s {\n\t\n}\n" % self.cssName
        return content

    def _get_remove_permission(self) -> bool:
        """
        Read object's css file. Compare with default.
        Count objects inside.
        Type yes to remove the WHOLE OBJECT
        """
        if self.cssFile.exists():
            content = self.cssFile.read_text("utf-8")
            if content != self.get_default_content():
                print(f"{self.name} css content is changed: ")
                width = shutil.get_terminal_size().columns  # Get terminal width dynamically
                file_name = f"[{self.cssFile.name}]"
                print(f"FILE {file_name.center(width - 5, "-")}")
                print(self.cssFile.read_text("utf-8"))
                print("ENDFILE".rjust(width, "-"))

        print(f"{self.name} has {len(list(self.path.iterdir()))} objects inside")
        answer = input("Is it okay to remove? Type \"yes\": ")
        if answer.strip().lower() == "yes":
            return True

        return False

    def get_descendant_modifiers(self) -> list:
        """
        Find object modifiers.
        """
        modifiers = []
        for x in self.path.glob("_[!_]*"):
            modifiers.append(Modifier(self.BEM, self, x.name))
            modifiers[-1].parse_values()
        return modifiers

    def _create_resolve_css(self):
        """
        Make css file and import
        """
        if self.exists():
            if self.cssFile.exists():
                self.error(FileExistsError(f"{self.cssFile} already exists!"))
            else:
                if self.css == "":
                    content = self.get_default_content()
                else:
                    content = self.css

                # Write content to object css
                self.cssFile.write_text(content, "utf-8")
                # Import it to main css file
                self.BEM.append_import(self.build_import_line())
        else:
            self.error(FileNotFoundError(f"Cannot find {self.path}"))

    def _create(self, nocss: bool = False):
        """
        Create object directory, css file and import it to main css file

        Throw warning if directory already exist
        Args:
            nocss: Just create directory
        """
        self.update_name(self.name)
        if self.exists():
            self.warning(f"{self.type} already exists!")
            self._create_resolve_css()      # Add css file
        else:
            self.path.mkdir()               # Create block folder
            if not nocss:
                self._create_resolve_css()  # Add css file

    def _remove(self, force: bool = False) -> bool:
        """
        Remove object directory, css file and import line from main css file

        Directory will not be removed if there are other files
        Args:
            force: Do not ask for removal confirmation
        Returns true if deleted
        """
        if not self.exists():
            self.error(FileNotFoundError(f"{self.type} doesn't exist!"))
        else:
            # Save css
            self.css = self.get_css()

            # Ask for permission and remove the directory
            if force or self._get_remove_permission():
                # Remove css file
                self.cssFile.unlink()
                # Remove folder if possible
                if self.path.exists():
                    if len(list(self.path.iterdir())) == 0:
                        self.path.rmdir()
                    else:
                        # todo: Will be nice to throw a warning if cannot remove a folder
                        # but now it is used in rename.
                        # self.warning("Cannot remove the directory. It is not empty!")
                        pass
                # Remove import from cssFile
                self.BEM.remove_import(self.build_import_line())
                return True
        return False

    def update_name(self, new_name: str):
        """
        Update object variables with new name.

        Must be overridden to change path and css naming
        """
        self.name = new_name
        self.cssFile = self.path / f"{self.cssName}.css"

    def get_conf(self) -> list:
        """
        Return the state of object
        """
        conf = [self.BEM, self.type, self.ancestor,
                self.name, self.path, self.cssName, self.cssFile]
        return conf

    def set_conf(self, conf: list):
        """
        Set the state of object
        Args:
            conf: List of settings in order like [BEM, type, ancestor, name, path, cssName, cssFile]
        """
        if len(conf) < 7:
            self.error(ValueError("Bad conf. Check on .get_conf() type"))
        else:
            self.BEM, self.type, self.ancestor, self.name, self.path, self.cssName, self.cssFile = conf

    def _rename_check_existence(self, new_name: str) -> bool:
        """
        Check old name and new name folder existence

        Throw FileNotFoundError and FileExistsError in case
        Args:
             new_name: New object and folder name
        """
        if not self.exists():
            self.error(FileNotFoundError(
                f"Cannot rename! {self.name} doesn't exist!"))
            return False

        old_name = self.name
        self.update_name(new_name)
        if self.exists():
            self.error(FileExistsError(
                f"Cannot rename! {self.name} already exists!"))
            self.update_name(old_name)
            return False
        self.update_name(old_name)
        return True

    def get_css(self) -> str:
        """
        Read cssFile and return it
        """
        if self.cssFile.exists():
            css = self.cssFile.read_text("utf-8")
            return css
        else:
            self.error(FileNotFoundError(f"Can't read {self.cssFile}"))
            return "error"

    def update_import_line(self) -> int:
        """
        Try to remove old and paste a new css import line
        Return was updated or was not
        """
        line = self.build_import_line()
        if not self.BEM.has_import(line):
            self.BEM.append_import(line)
            return 1
        return 0

    def _rename_change_css(self, new_name: str, old_css: str) -> str:
        """
        Parse css and change old class names to new ones
        Args:
            new_name: New name of css class
            old_css: String of css

        returns: Changed string of raw css
        """
        new_css = old_css.replace(self.name, new_name)
        # I'm afraid it could corrupt css code somehow
        # Replace should be changed to parser
        return new_css

    def set_css(self, new_css: str):
        """
        Update css file
        Args:
            new_css: Raw string that will be written in the cssFile
        """
        if self.cssFile.exists():
            self.cssFile.write_text(new_css, "utf-8")   # Write new css
        else:
            self.error(FileNotFoundError(f"Can't find {self.cssFile}"))

    def _rename(self, new_name: str):
        """
        Remove the old object.
        Make a new object but keep the code.
        Update imports.
        """
        if self._rename_check_existence(new_name):
            self.update_name(self.name)
            css = self._rename_change_css(new_name, self.get_css())
            # Remove old object
            self._remove(True)
            # Update object variables
            self.update_name(new_name)
            # Create new object
            self._create()
            self.set_css(css)


class Block(_BEMGen):
    type = "block"

    def __init__(self, bem: BEM, name: str):
        """
        Block object
        Args:
            bem: BEM class instance
            name: Name of object
        """
        super().__init__(bem, name)
        # todo Maybe make them sets
        self.elements = []
        self.modifiers = []

    def get_descendant_elements(self) -> list:
        """
        Find block elements.
        """
        elements = []

        for x in self.path.glob("__*"):
            elements.append(Element(self.BEM, self, x.name))
            elements[-1].modifiers = elements[-1].get_descendant_modifiers()
        return elements

    def parse_descendants(self):
        """
        Set block modifiers and block elements

        Only the nearest
        """
        self.modifiers = self.get_descendant_modifiers()
        self.elements = self.get_descendant_elements()

    def update_name(self, new_name: str):
        """
        Set the rules of naming.

        Overrides the _BEMGen method.
        Args:
            new_name: new name of object
        """
        self.path = self.BEM.blocksDir / new_name
        self.cssName = new_name
        super().update_name(new_name)

    def create(self):
        """
        Create block folder and css file.

        Also create descendants
        """
        super()._create()
        for x in self.modifiers:
            x.ancestor = self
            x.create()

        for x in self.elements:
            x.ancestor = self
            x.create()

    def remove(self, force: bool = False):
        """
        Remove the block with elements and modifiers.

        Keep them in self.elements and self.modifiers
        Args:
              force: Do not ask for confirmation
        """

        self.parse_descendants()
        if force or self._get_remove_permission():
            for x in self.modifiers:
                x.remove(True)
            for x in self.elements:
                x.remove(True)
            return super()._remove(True)

    def rename(self, new_name: str):
        """
        Rename block, update naming and imports
        """
        if self._rename_check_existence(new_name):
            self.remove(True)
            self.update_name(new_name)
            self.create()


class _BemGenBM(_BEMGen):
    def __init__(self, bem: BEM, ancestor: _BEMGen, name: str):
        """
        Ancestor of Element and Modifier
        Args:
            bem: BEM class instance
            ancestor: Block or Element instance
            name: Name of object
        """
        self.ancestor = ancestor
        super().__init__(bem, name)

    def update_name(self, new_name: str):
        """
        Updates paths and names of object.

        Overrides the _BEMGen method.
        """
        self.path = self.ancestor.path / new_name        # Object location
        self.cssName = self.ancestor.cssName + new_name  # CSS naming rules
        super().update_name(new_name)

    def check_ancestor(self) -> bool:
        """
        Verify the ancestor availability
        :return: Existence state of ancestor
        """
        if not self.ancestor.exists():
            self.error(FileNotFoundError(
                f"{self.ancestor.name} ancestor doesn't exist!"))
            return False
        return True

    def _create(self, nocss: bool = False):
        """
        Create folder, css files and imports
        Including values
        """
        if self.check_ancestor():
            super()._create(nocss)


class Element(_BemGenBM):
    type = "element"

    def __init__(self, bem: BEM, ancestor: Block, name: str):
        """
        Element object
        Args:
            bem: BEM class instance
            ancestor: The parent block of element.
            name: The name of object. Starts with "__"
        """
        name = "__" + name.lstrip("_")
        super().__init__(bem, ancestor, name)
        self.modifiers = []

    def parse_descendants(self):
        """
        Set element modifiers
        """
        self.modifiers = self.get_descendant_modifiers()

    def create(self):
        """
        Create element folder and css file
        """
        super()._create()
        for x in self.modifiers:
            x.ancestor = self
            x.create()

    def remove(self, force: bool = False):
        """
        Remove the element with modifiers
        """
        self.parse_descendants()
        if force or self._get_remove_permission():
            for x in self.modifiers:
                x.remove(True)
            return super()._remove(True)

    def rename(self, new_name: str):
        """
        Rename element. Change imports.
        """
        new_name = "__" + new_name.lstrip("_")
        self.parse_descendants()
        if self._rename_check_existence(new_name):
            old_names = []
            for i in range(len(self.modifiers)):
                old_names.append(self.modifiers[i].cssName)

            self.remove(True)
            self.update_name(new_name)
            self.create()

            for i in range(len(self.modifiers)):
                self.modifiers[i].update_css(old_names[i])


class Modifier(_BemGenBM):
    type = "modifier"

    def __init__(self, bem: BEM, ancestor: Block | Element, name: str, values=None):
        """
        Modifier object
        Args:
            bem: BEM class instance
            ancestor: The parent of the modifier
            name: Name of the modifier. Starts with "_"
            values: If passed the modifier isn't bool
        """
        name = "_" + name.lstrip("_")

        # The modifier with values has got some own variables
        if values is not None:
            self.values = values
            self.values_css = {x: "" for x in self.values}
        else:
            self.values = []
            self.values_css = dict()

        super().__init__(bem, ancestor, name)

    def _set_value(self, value: str):
        """
        Set css variables on value.

        Needed by key-value modifiers to get access to values
        """
        self.cssName = self.ancestor.cssName + self.name + "_" + value
        self.cssFile = self.path / f"{self.cssName}.css"
        self.css = self.values_css.get(value)

    def parse_values(self):
        """
        Iterate over the directory(self.path).
        Set values if they exist
        """
        contents = list(self.path.iterdir())
        # Do not support single key-value
        if len(contents) != 1:
            for x in contents:
                value = str(x.stem)
                value = value[value.rfind("_")+1:]
                self.values.append(value)

    def create(self):
        """
        Create modifier folder and css file.

        If values are available. Then modifier is key-value
        """
        if len(self.values) == 0:
            super()._create()
        else:
            super()._create(True)
            for value in self.values:
                self._set_value(value)      # Change css to focus on value
                self._create_resolve_css()  # Make css file
            self.update_name(self.name)     # Remove _set_value effect

    def remove_values(self, values: list[str], force: bool = False):
        """
        Remove only given values
        Args:
            values: List of values
            force: Prompt for removal permission
        """
        if force or self._get_remove_permission():
            for value in values:
                self._set_value(value)  # Change css to focus on value
                super()._remove(True)   # Remove, which updates self.css
                self.values_css[value] = self.css   # Save css

            self.update_name(self.name)  # Remove _set_value effect

    def remove(self, force: bool = False):
        """
        Delete modifier directory, css files and imports.

        Don't remove with no values given
        Args:
            force: Prompt for removal permission
        """
        if len(self.values) == 0:
            if not self.cssFile.exists():
                self.error(TypeError(
                    "Can't remove. Modifier is key-value. Call parse_values() at first!"))
            else:
                return super()._remove(force)
        else:
            self.remove_values(self.values, force)

    def rename_value(self, value: str, new_value: str):
        """
        Rename single value file and css class
        Args:
            value: The old value name
            new_value: The new value name
        """
        # Rename css class
        self._set_value(new_value)
        new_css_name = self.cssName
        self._set_value(value)
        css = self.get_css().replace(self.cssName, new_css_name)  # Probably can corrupt css
        # Focus on new css file
        self._set_value(new_value)
        if self.cssFile.exists():
            self.error(FileExistsError(
                f"Cannot update value from {value} to {new_value}"))
        else:
            # Make new css file
            self._create_resolve_css()
            self.set_css(css)
            # Remove old one
            self._set_value(value)
            self.cssFile.unlink()
        # Set modifier paths to default
        self.update_name(self.name)

    def update_css(self, old_name: str):
        """
        Update css file (or files if it's a value type)
        Args:
            old_name:  Old css name to be replaced
        """
        if len(self.values) == 0:
            self.css = self.get_css().replace(old_name, self.cssName)
            self.set_css(self.css)
        else:
            for x in self.values:
                self._set_value(x)
                self.values_css[x] = self.get_css().replace(
                    old_name, self.cssName)
                self.set_css(self.values_css[x])
            self.update_name(self.name)

    def get_css_with_values(self) -> dict:
        """
        Read values css files and return the resulting dict, where key is name of value
        """
        d = dict()
        for x in self.values:
            self._set_value(x)
            d[x] = self.get_css()
        self.update_name(self.name)
        return d

    def set_css_with_values(self):
        """
        Write self.values_css matter to their files
        """
        for x in self.values:
            self._set_value(x)
            self.set_css(self.values_css[x])
        self.update_name(self.name)

    def _rename_with_values(self, new_name: str):
        """
        Rename the modifier. Keep values.
        Args:
            new_name: New name of modifier
        """
        if self._rename_check_existence(new_name):
            old_name = self.name
            self.update_name(new_name)
            self._create(True)  # Create new_name folder
            for value in self.values:
                # Get css of old value
                self.update_name(old_name)
                self._set_value(value)
                # Update css with a new name
                css = self._rename_change_css(new_name, self.get_css())
                # Make new css value file
                self.update_name(new_name)
                self._set_value(value)
                self._create_resolve_css()
                # Write updated css in new file
                self.set_css(css)
            # Remove old files
            self.update_name(old_name)
            self.remove(True)
            # Update variables with a new name
            self.update_name(new_name)

    def rename(self, new_name: str):
        """
        Rename modifier files. Change imports.
        """
        new_name = "_" + new_name.lstrip("_")
        if len(self.values) == 0:
            if not self.cssFile.exists():
                self.error(TypeError(
                    "Can't rename. Modifier is key-value. Call parse_values() at first!"))
            else:
                super()._rename(new_name)
        else:
            self._rename_with_values(new_name)

    def update_import_line(self) -> int:
        c = 0
        if len(self.values) == 0:
            c = super().update_import_line()
        else:
            for value in self.values:
                self._set_value(value)  # Change css to focus on value
                if super().update_import_line():
                    c += 1
            self.update_name(self.name)  # Remove _set_value effect
        return c


# Launch console as a default
if __name__ == "__main__":
    bem = BEM.get_default_bem()
    bem.start_loop()
