# Claudia's Moving Object Tool 🌠

## Project Description

This tool provides a graphic user interface (GUI) that will allow the user to request ephemeris files from the Minor Planet Center (MPC) of different moving objects during a certain time window. The main objective of this tool is to prevent stellar contamination in moving objects
and to ensure optimal observing time for the target in question. The tool can currently:

* Display an interactive mosaic of the sky during this time frame so the user can know what to expect during the observation of their target. 
The target location is displayed with a blue cross.
* The tool will estimate the best dates to observe the target. 
* Calculate the distances of nearby sources.
* Detect the brightest sources in the sky. 
* Display this information alongside the mosaic.

Current features that need to be fixed:

* Source detection not working correctly, leading to errors in the information displayed on the GUI regarding nearby and/or bright sources.
* GUI freezing.
* Compass not functional nor adapting to user interaction.
* Incomplete implementation of the catalog changing function.
* Exception handling not as robust yet.

Incomplete features:

* Time format radio buttons not functional yet.

Future features:

* Plotting FOV visualization and rotation.
* Changing FOV according to the selected instrument.
* Working progress bar.
* Opening, reading, and loading Observation Block (OB) information.
* Date displayed after hovering mouse over target location.



