# BEM Controller <img align="right" height="100" src="https://ru.bem.info/S3zKVZJcFfltyiAz-bWVmw4o3IU.svgd" width="100"/> <img height=100 width=100 align="right" src="https://cdn-icons-png.flaticon.com/128/8277/8277654.png">
A python script that helps you with the css naming and importing.
# Introduction
When you use Block Element Modifier strategy you always follow the same steps:
1. Create a folder
2. Create a file
3. Create a css class
4. Create an import line

Finally, you can write css and use a new component in html.
## Problems
- It is slow and repetitive
- It is impossible to remember all the components. You have to check them up again and again
- If you want to rename or delete a component you have to follow the steps one more time. And also do not forget to REPEAT IT FOR EVERY SINGLE DESCENDANT

## IDE plugins
I did not find any plugins taking those exact steps like I mentioned.
Also, these plugins could easily act different and other IDEs.
So, that is the reason why I suggest using a script.

# Quick overview
I implemented 3 classes Block, Element and Modifier. 
They could be used to program a file structure (although css could be injected too)
## Block creation example
```python
from pathlib import Path
from BEM import BEM, Block, Element, Modifier # BEM.py is beside
# Script supposed be placed one level lower than the root folder
root = Path(__file__).parent.parent           # Project folder 
blocks = root.joinpath("src", "blocks")       # Blocks folder
css = root.joinpath("src", "index.css")       # CSS file where you use imports
b = BEM(root, blocks, css)                    # Init the file paths
block = Block(b, "my_programmed_block")       # initialize a block 
block.create()                                # Create it
```
This will produce a new folder, css file and line inside index.css
## Modifier with values example
Modifiers can be bool and valued. The second type instances should have a list of values
```python
mod = Modifier(b, block, "place", ["bot", "mid", "top"])
mod.values_css["bot"] = "raw_css"   # Inject css only "bot" css file
                                    # Others will be default
mod.create()
```

# Functionality
## Objects methods
| Method                     | Description |
|----------------------------|-------------|
| `create`                 | Create an object. Raise an error if it is not possible. |
| `remove`                 | Remove an object. Raise an error if it is not possible. |
| `rename`                 | Rename an object. Raise an error if it is not possible. |
| `parse_descendants` (`parse_values` in modifiers)      | Find the descendant object and save them to lists (`obj.elements`, `obj.modifiers`, `obj.values`). |
| `get_css` (`get_css_with_values` in modifiers)                   | Read CSS file. |
| `obj.css = ""`             | Change the value of CSS. |
| `set_css()`                | Write `obj.css` to the file. |
| `update_import_line()`     | Add import if needed. |

> Modifier with value is slightly different and sometimes has own methods.

## BEM instance
Also, there is a controller class, which serves its own methods. It is essential for objects as a path config and used to write and read css import file as well.

BEM instance has interactive console, which allow you to serve objects on the fly:
| Method               | Description |
|----------------------|-------------|
| `get_default_bem`  | Use default config. |
| `start_loop`       | Launch the input console. Print some info. |
| `parse`           | Parse all blocks and their descendants. Save them to `bem.blocks`. |
| `get_blocks`      | Return the list of blocks. |
| `get_elements`    | Return the list of elements. |
| `get_modifiers`   | Return block modifiers list and element modifiers list. |
| `fix_imports`     | Add all missing imports. |
| `launch_editor`   | Start a editor with the last created file |
| `make_import_backup` | Create a copy of css import file. |

# Usage
> Written with python 3.12

Create src, blocks, index.css. 
Launch BEM\.py (change bem default config if needed).
The console serves [previous mentioned](#bem-instance) BEM methods.
At first, choose a method, then define a block / element/ modifier.
Also you can use a ? for some help.
```bash
$ python3 BEM.py 
Parsed blocks:  aboba1 | block1 | element | 
Use ? for hint
> ?
Exit(0) / Create(1) / Remove(2) / Rename(3) / Show(4) / Fix(5) / Parse(6) / Code(7) / Backup(8)
> fix
Updated 17 lines
> 3
- rename > ?
Back(0) / Block(1) / Element(2) / Modifier(3): 
- rename > 1
Set block name: element
Enter new name: el
Renamed
> 

```

# Future functionality
- Add css editing in console
- Existing names autocomplete 
- Console oneline commands support
