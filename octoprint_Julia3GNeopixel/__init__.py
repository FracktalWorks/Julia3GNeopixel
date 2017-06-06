from __future__ import absolute_import
import smbus
import time
import octoprint.plugin
from octoprint.events import eventManager, Events
from threading import Timer
import octoprint.printer

bus=smbus.SMBus(1)

class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

class Julia3GNeopixel(octoprint.plugin.StartupPlugin,octoprint.plugin.EventHandlerPlugin,octoprint.plugin.SettingsPlugin):
	def on_after_startup(self):
		self._logger.info("Neopixel Plugin Started")
		self.neopixeladdr = 0x04
		self._event = {"PRINTING": 10, "PAUSED": 14, "BOOT": 12, "BREATHE": 13, "ERROR": 11}
		bus.write_byte(self.neopixeladdr, self._event["BOOT"])

	def on_event(self, event, payload):
		if event == Events.PRINT_STARTED:
			#start thread to check and display progress
			self._timer=RepeatedTimer(5,self.displayProgressPrinting)
		elif event == Events.PRINT_DONE:
			#display leds to print done
			self._logger.info("Printing stopped")
			bus.write_byte(self.neopixeladdr,self._event["BREATHE"])
			self._timer.stop()
		elif event == Events.PRINT_FAILED:
			#display urgency
			self._logger.info("Printing failed")
			bus.write_byte(self.neopixeladdr,self._event["ERROR"])
			self._timer.stop()
		elif event == Events.PRINT_PAUSED:
			#display paused print led
			bus.write_byte(self.neopixeladdr,self._event["PAUSED"])
			self._timer.stop()
		elif event == Events.CONNECTED:
			bus.write_byte(self.neopixeladdr,self._event["BREATHE"])
		elif event == Events.ERROR:
			bus.write_byte(self.neopixeladdr,self._event["ERROR"])

	def displayProgressPrinting(self):
		data=self._printer.get_current_data()
		#get progress from this data
		progress=data["progress"]["completion"]
		self._logger.info("Progress " + str(progress))
		progress=int(progress)
		bus.write_byte(self.neopixeladdr,progress)
		time.sleep(0.1)
		bus.write_byte(self.neopixeladdr,self._event["PRINTING"])


	def get_update_information(self):
		return dict(
			Julia3GTouchUI=dict(
				displayName="Julia3GNeoPixel",
				displayVersion=self._plugin_version,
				# version check: github repository
				type="github_release",
				user="FracktalWorks",
				repo="Julia3GNeopixel",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/FracktalWorks/Julia3GNeopixel/archive/{target_version}.zip"
			)
		)


__plugin_name__ = "Julia3GNeoPixel"
__plugin_version__ = "0.0.7"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = Julia3GNeopixel()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
	}

