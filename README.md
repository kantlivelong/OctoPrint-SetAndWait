# OctoPrint SetAndWait
This OctoPrint plugin implements Set And Wait commands [M109](https://www.reprap.org/wiki/G-code#M109:_Set_Extruder_Temperature_and_Wait) & [M190](https://www.reprap.org/wiki/G-code#M190:_Wait_for_bed_temperature_to_reach_target_temp) into OctoPrint and sends their non-blocking counterparts to the controller.
     

##### Benefits:
- Prints can be canceled during the heating phase without waiting for the temperature to be reached.
- Fixes an issue where Smoothieware only reports temperatures for the probe being heated which in turn causes gaps on the OctoPrint temperature graph for other probes. 
- Works around odd behavior in Klipper where setting the temperature to a lower value will result in waiting for the heater to cool instead of simply continuting (S being treated as R). See [KevinOConnor/klipper#1108](https://github.com/KevinOConnor/klipper/issues/1108)


## Setup
Install the plugin using Plugin Manager from Settings

## Support
Help can be found at the [OctoPrint Community Forums](https://community.octoprint.org)

## Feature Requests
[![Feature Requests](https://feathub.com/kantlivelong/OctoPrint-SetAndWait?format=svg)](https://feathub.com/kantlivelong/OctoPrint-SetAndWait)
