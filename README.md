# QNodeEditor

![pylint](https://img.shields.io/badge/pylint-9.84-yellow?logo=python&logoColor=white)
[<img src="https://img.shields.io/badge/github--blue?logo=github" alt="Github badge">](https://github.com/JasperJeuken/QNodeEditor)
[<img src="https://img.shields.io/badge/PyPi--blue?logo=pypi" alt="PyPi badge">](https://pypi.org/project/QNodeEditor/)
[<img src="https://img.shields.io/badge/Documentation--blue?logo=readthedocs" alt="readthedocs badge">](https://qnodeeditor.readthedocs.io/en/latest/)

QNodeEditor is a collection of widgets that enables you to easily create 
and use a node editing environment in PyQt5.

| <img src="https://raw.githubusercontent.com/JasperJeuken/QNodeEditor/main/images/demo.gif" alt="Example node scene being edited" width="100%"/> |
|:---------------------------------------------------------------------------------:|
|             <div width="100%">*Example node scene being edited*</div>             |

|  <img src="https://raw.githubusercontent.com/JasperJeuken/QNodeEditor/main/images/themes.jpg" alt="drawing" width="100%"/>   |
|:----------------------------------------------------------------------------------------------------------------------------:|
|                                <div width="100%">*QNodeEditor supports flexible themes*</div>                                |


## Installing
Install the package using the following command:

```
pip install QNodeEditor
```

## Requirements
The QNodeEditor package requires the following packages:
- [PyQt5](https://pypi.org/project/PyQt5/)
- [networkx](https://pypi.org/project/networkx/)

## Usage
For a full guide on how to use QNodeEditor, check out the [Documentation](https://qnodeeditor.readthedocs.io/en/latest/).
Here you can find tips on how to get started, as well as the API documentation for QNodeEditor.

### Example
Below is some sample code for creating a node that performs an addition of two values.
```python
from QNodeEditor import Node

class AddNode(Node):
    code = 0  # Unique code for each node type
    
    def create(self):
        self.title = 'Addition'  # Set the node title
        
        self.add_label_output('Output')  # Add output socket
        self.add_value_input('Value 1')  # Add input socket for first value
        self.add_value_input('Value 2')  # Add input socket for second value
        
    def evaluate(self, values: dict):
        result = values['Value 1'] + values['Value 2']  # Add 'Value 1' and 'Value 2'
        self.set_output_value('Output', result)         # Set as value for 'Output'
```
<img src="https://raw.githubusercontent.com/JasperJeuken/QNodeEditor/main/images/addition_node.jpg" alt="Example node" width="300">

This node can now be used in a scene. When it is evaluated, it will take `Value 1` and `Value 2`, add them, and set it as the value of `Output`.

This is a simple node, but the package is flexible. You can place any widgets inside the node, and define the logic as you wish. You can also attach
to signals emitted by the scene, such as when two nodes are connected together.

A node scene evaluates the scene asynchronously, meaning the interface will not freeze while a calculation is performed. If an error occurs, it is signalled,
and you can handle it as you want.

## License
The package is inspired by the [pyqt-node-editor](https://gitlab.com/pavel.krupala/pyqt-node-editor)
(MIT license) package by Pavel Křupala.
