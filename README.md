# SC2 Replay Extractor

This project extracts information from StarCraft 2 replay files into a more digestable CSV format.
This creates the following files:

 - **actionCount.csv**: A log of all actions performed by both players during the game, grouped according to action type (1: command event, 2: selection event, 3: control group event).
 - **camera.csv**: A log of all camera movements by both players.
 - **injectAction.csv**: A log of each time an inject action was issued (for Zerg players only).
 - **injectPop.csv**: A log of each time an injection completed (for Zerg players only).
 - **replayMeta.csv**: Metadata about the players and replays, such as the League, Race, Result, etc.
 - **unitDeaths.csv**: A log of each time a unit died, including its associated costs.

Only parses Heart of the Swarm replays.

## Installation

Requires sc2reader (version from ggtracker is recommended, as the GralinKim repository has not been updated for years):

```
sudo -H pip install git+https://github.com/ggtracker/sc2reader
```

## Usage

Point the script to the input directory, as well as the directory you want the csv outputs to be located.

```
python extractor.py [in_dir] [out_dir]
```
