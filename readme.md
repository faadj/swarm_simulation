# Swarm foraging simulation

this is a simple python simulation built with mesa 3.5.1. it shows a swarm of creatures trying to survive a hot environment by searching for food, managing their temperature, and leaving pheromone trails for each other.

## What you need
make sure you have python installed on your computer.

## How to run it

**step 1: Download the code**
click the green "<> code" button at the top right of this page and choose "download zip". extract that folder to your desktop or documents.

**step 2: Install the packages**
open your terminal (or command prompt), navigate to the folder you just extracted, and copy-paste this exact command to get all the required tools:

pip install mesa==3.5.1 "mesa[viz]" networkx

**step 3: Start the simulation**
once everything is installed, type this in the terminal and hit enter:

solara run create.py

**step 4: Watch it run**
the terminal will give you a local link (usually http://localhost:8765). just click it or paste it into your web browser to watch the swarm! when you're done, just click on your terminal and hit ctrl+c to shut down the server.