from setuptools import setup, find_packages

with open('requirements.txt') as file:
    requirements = file.read()

setup_requirements = []

setup(
    name="qnodeeditor",
    author='Jasper Jeuken',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11'
    ],
    description='Node editor for PyQt5, with nodes and connections between them',
    install_requires=requirements,
    license='MIT license',
    include_package_data=True,
    keywords='node,editor,pyqt5,pyqt,pyside2,pyside,socket,edge,connection,nodes,qnode,qnodeeditor',
    packages=find_packages(include=['QNodeEditor']),
    package_data={'QNodeEditor': ['QNodeEditor/themes/fonts/**/*.ttf',
                                  'QNodeEditor/themes/img/*.svg']},
    setup_requirements=setup_requirements,
    version='1.0.0',
    zip_safe=False
)
