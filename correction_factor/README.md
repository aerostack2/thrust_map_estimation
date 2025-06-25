# Experiments to estimate the correction factor for the thrust stand
 
 The scripts that process the data for real flights to compute the correction factor curve and use it with the thrust map.
<div align="center">
 <img src="../figures/fit-correction-factor.png" alt="SR-TM" width="335"/> 
</div>

## Usage

To obtain the correction factor, add all the paths of the experiments that use the same thrust map to the config file. Then, disable the correction factor parameters, include the parameters used with the thrust map, and assign a name to these experiments. Finally, run:
 ```
python3 correction_factor/scripts/main.py 
```
This process will access the data from the ROS bags and convert it into a CSV file for each experiment, saved in a data folder. Then, it will combine them into a single CSV file saved in data/results under the experiment’s name, in order to compute the correction factor and plot the corresponding curve.

It will also compute the error between the commanded throttle and the computed throttle with respect to the battery level, as well as with respect to the commanded thrust. Additionally, it will compute the error between the commanded thrust and the measured thrust. All these results will be saved in the data/errors folder under the experiment’s name, with the suffix _errors.

If the recorded experiments have already used a correction factor curve or a linear approximation for the thrust map, you can update the config file and compute only the errors.

## Compare results from different experiments

To compare the results of different experiments using various thrust maps—with or without a correction factor or a linear approximation, run:

 ```
python3 correction_factor/scripts/compare_results.py 
```
This will access the errors folder and plot the error metrics from the different experiments.