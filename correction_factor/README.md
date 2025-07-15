# Experiments to estimate the correction factor for the thrust stand
 
 The scripts that process the data for real flights to compute the correction factor curve and use it with the thrust map.
<div align="center">
 <img src="../figures/fit-correction-factor.png" alt="SR-TM" width="335"/> 
</div>

## Usage
These scripts enable you to work with ROSBags from flight tests, using either a linear or a second-order approximation of the thrust map and compute the corresponding correction factor. If the flights were recorded with the correction factor active, the scripts can also generate results for comparison.

### Obtain the correction factor
To obtain the correction factor, first you must either configure the default configuration or create a custom one. 
The configuration file must include these parameters:
```
rosbags:
  file1: 'path1'  
  file2: 'path2'  
    .
    .
    .
folder_experiment: 'folder_name'   
T_max: false  # False to disable or maximum thrust
cf_parameters: False     # Put False and comment the parameters if the correction factor have not been yet computed
  # a2: 5.91892324          
  # a1: -0.42842818
  # a0:  0.00880309
tm_parameters:           # Parameters for the thrust map surface      
  a: 368.38174446706694
  b: 275.9120443657675
  c: 64.33013450010587
  d: -8.020752230795884
  e: -7.162085176021985
  f: -1.3041691088519118
```
The field rosbags should have the paths to the folders with the experiment data recorded with the same thrust map.

"folder_experiment" is the name of the folder where the CSV files for this experiment will be saved inside a data folder.

In order to compute the correction factor, "cf_parameters" must be False and the parameters disable.

If you use the linear aproximation you must add the maximum thrust of the curve in the " T_max". If you use the thrust map, set it to false and edit the thrust map parameters.

Finally, run:

 `
python3 correction_factor/scripts/main.py --config correction_factor/config/my_config.yaml
`

This process will access the data from the ROS bags and convert it into a CSV file for each experiment, saved in a data folder. Then, it will combine them into a single CSV file saved in data/results under the experiment’s name, in order to compute the correction factor and plot the corresponding curve.

It will also compute the error between the commanded throttle and the computed throttle with respect to the battery level, as well as with respect to the commanded thrust. Additionally, it will compute the error between the commanded thrust and the measured thrust. All these results will be saved in the data/errors folder under the experiment’s name, with the suffix _errors.


### Experiments record with correction factor

If the recorded experiments have already used a correction factor curve, you must edit the configuration file.

```
cf_parameters: 
    a2: 5.91892324          
    a1: -0.42842818
    a0:  0.00880309
```
The "cf_parameters" parameter must contain the second-degree curve variables of the correction factor.

γ = a0 · B² + a1 · B + a2

Add the parameters of the corresponding thrust map or the linear approximation.

Then run:

 `
python3 correction_factor/scripts/main.py --config correction_factor/config/my_config.yaml
`

## Compare results from different experiments

To compare the results of different experiments using various thrust maps—with or without a correction factor or a linear approximation, run:

 ```
python3 correction_factor/scripts/compare_results.py 
```
This will access the errors folder and plot the error metrics from the different experiments.