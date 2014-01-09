expressionTopology
==================

A class project playing with the idea of visualizing gene expression data parametrically in an n-dimensional space. Data in .SOFT format, that can be downloaded from the [NCBI Geo Database](http://www.ncbi.nlm.nih.gov/geo/), can be visualized, as well as simulation outputs from [iBioSim](http://www.async.ece.utah.edu/iBioSim/) in .tsd format. For example, try [this](ftp://ftp.ncbi.nlm.nih.gov/geo/datasets/GDS1nnn/GDS1963/soft/GDS1963_full.soft.gz) file.

This tool is designed to compare real and simulated expression levels over time for any two pairs of genes. The visualization is an animated, parametric view, showing fluctuations in expression levels for any two genes at a time. Use the colors on the right to group classes of experiments or simulation runs. Use the sliders at the bottom to adjust animation or specific time intervals. Clicking on a specific plot will show more detail.

Specific use cases include:
 - With enough data, stable states in a 2D vector field could be identified by observing critical points. These critical points can, in turn, inform models.
 - Simulated data can be directly compared to experimental data. If a model is learned from experimental data, the resulting simulations should show similar behavior. Discrepancies should be obvious, and the nature of the discrepancies should inform which part(s) of the model to adjust.

Running
-------
If possible, you should use these precompiled binaries:

[Mac OS X v1.0](http://cs.utah.edu/~abigelow/Downloads/expressionTopology/Mac/expressionTopology_1.0.dmg)

[Linux v1.0](http://cs.utah.edu/~abigelow/Downloads/expressionTopology/Linux/expressionTopology_1.0.tar.gz)

[Windows v1.0](http://cs.utah.edu/~abigelow/Downloads/expressionTopology/Windows/expressionTopology_1.0.zip)

If you wish to run from the source code, you will need to install Qt, Python 2.7, PySide, and clone this repository. The program can then be launched via:

	python expressionTopology.py

License
-------
Copyright 2013 Alex Bigelow

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.

Questions, comments, ideas, bug reports, and criticisms are more than welcome! Send an email to alex dot bigelow at utah dot edu.
