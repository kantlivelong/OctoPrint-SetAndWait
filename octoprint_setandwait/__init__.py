# coding=utf-8
from __future__ import absolute_import

__author__ = "Shawn Bruce <kantlivelong@gmail.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2020 Shawn Bruce - Released under terms of the AGPLv3 License"

import octoprint.plugin
from octoprint.events import Events
import threading
import re
import time

class SetAndWait(octoprint.plugin.EventHandlerPlugin):

    def __init__(self):
        self._events = dict(M109=threading.Event(),
                            M190=threading.Event())

    def _poll_temperature_bypass_queue(self):
        # Adapted from octoprint.util.comm._poll_temperature

        if self._printer._comm.isOperational() \
            and not self._printer._comm._temperature_autoreporting \
            and not self._printer._comm._connection_closing \
            and not self._printer._comm.isStreaming() \
            and not self._printer._comm._long_running_command \
            and not self._printer._comm._heating \
            and not self._printer._comm._dwelling_until \
            and not self._printer._comm._manualStreaming:
            self._printer._comm._do_send('M105', gcode='M105')

    def _gcode_setandwait(self, line):
        gcode_from = octoprint.util.comm.gcode_command_for_cmd(line)

        matchS = octoprint.util.comm.regexes_parameters["floatS"].search(line)
        matchR = octoprint.util.comm.regexes_parameters["floatR"].search(line)
        matchT = octoprint.util.comm.regexes_parameters["intT"].search(line)

        if gcode_from == 'M109':
            gcode_to = 'M104'
            heater_type = 'tool'
            heater_identifier = 'Tool'
        elif gcode_from == 'M190':
            gcode_to = 'M140'
            heater_type = 'bed'
            heater_identifier = 'Bed'
        else:
            return

        if matchS:
            mode = 'S'
            target = float(matchS.group("value"))
        elif matchR:
            mode = 'R'
            target = float(matchR.group("value"))
        else:
            return

        if heater_type == 'tool':
            if matchT:
                tool = int(matchT.group("value"))
            else:
                tool = self._printer._comm.getCurrentTool()

            heater_identifier = '{} {}'.format(heater_identifier, tool)
        else:
            tool = None

        cmd = '{} S{}'.format(gcode_to, target)
        if tool:
            cmd += ' T{}'.format(tool)
        self._printer._comm._do_send(cmd, gcode=gcode_to)

        self._events[gcode_from].set()
        while self._events[gcode_from].is_set():
            heaters = self._printer.get_current_temperatures()
            if heater_type == 'tool':
                actual = heaters['tool' + str(tool)]['actual']
            elif heater_type == 'bed':
                actual = heaters['bed']['actual']

            self._logger.debug("Heater: {}, Mode: {}, Target: {}, Actual: {}".format(heater_identifier, mode, target, actual))

            if mode == 'S':
                if actual >= target:
                    break
            elif mode == 'R':
                self._logger.warning("Accurate temperature not yet implemented. line={}".format(line))
                break

            self._poll_temperature_bypass_queue()
            time.sleep(1)

        if not self._events[gcode_from].is_set():
            self._logger.debug("{} aborted".format(gcode_from, heater_identifier))
#            cmd = '{} S0'.format(gcode_to)
#            if tool:
#                cmd += ' T{}'.format(tool)
#            self._printer._comm._do_send(cmd, gcode=gcode_to)
            return

        self._logger.debug("{} - Giving the controller the final say!".format(gcode_from))
        self._printer._comm._do_send(line)

    def hook_gcode_sending(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        if gcode not in ['M104', 'M109', 'M140', 'M190']:
            return

        if gcode in ['M109', 'M190']:
            if not self._printer.is_cancelling():
                self._printer.set_job_on_hold(True, blocking=False)
                self._gcode_setandwait(cmd)
                self._printer.set_job_on_hold(False)

            return None, None

    def on_event(self, event, payload):
        if event in [Events.DISCONNECTING,
                     Events.PRINT_CANCELLING,
                     Events.ERROR]:
            for k, e in self._events.items():
                if e.is_set():
                    self._logger.debug("Aborting {}".format(k))
                    e.clear()

    def get_update_information(self):
        return dict(
            setandwait=dict(
                displayName="SetAndWait",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="kantlivelong",
                repo="OctoPrint-SetAndWait",
                current=self._plugin_version,

                # update method: pip w/ dependency links
                pip="https://github.com/kantlivelong/OctoPrint-SetAndWait/archive/{target_version}.zip"
            )
        )

__plugin_name__ = "SetAndWait"
__plugin_pythoncompat__ = ">=2.7,<4"

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = SetAndWait()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.gcode.sending": __plugin_implementation__.hook_gcode_sending
    }
