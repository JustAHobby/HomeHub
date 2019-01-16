#!/usr/bin/env python

from papirus import Papirus
from time import sleep
from PIL import Image, ImageDraw, ImageFont

import RPi.GPIO as GPIO
import ConfigParser
import requests
import json
import sys

class HomeHub():

	def __init__(self):
		#button setup
	        self.SW1 = 21
	        self.SW2 = 16
		self.SW3 = 20
		self.SW4 = 19
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(self.SW1, GPIO.IN)
		GPIO.setup(self.SW2, GPIO.IN)
                GPIO.setup(self.SW3, GPIO.IN)
                GPIO.setup(self.SW4, GPIO.IN)

		#config file
		self.Config = ConfigParser.ConfigParser()
		self.Config.read('./config.ini')

		rotation = int(self.Config.get('PAPIRUS', 'rotation'))
		fontPath = self.Config.get('PAPIRUS', 'fontPath')
		self.fontSize = int(self.Config.get('PAPIRUS', 'fontSize'))
		backgroundPath = self.Config.get('PAPIRUS', 'backgroundPath')
		defaultDisplayOption = self.Config.get('HOMEHUB', 'defaultDisplayOption')

                url = self.Config.get('HOMEHUB', 'url')
                self.currentLightGroup = 0
		self.jsonLightGroups = self.QueryLightList(url)
                self.lightGroups = self.JsonLightToLightGroupNames(self.jsonLightGroups, defaultDisplayOption)

		#papirus setup
                self.initX = 15
                self.initY = 40

                self.papirusDisplay = Papirus(rotation = rotation)
                self.papirusDisplay.clear()

                #papirus screen setup
                rsimg = Image.open(backgroundPath)
                self.image = Image.new('1', self.papirusDisplay.size, 1)
                self.image.paste(rsimg, (0,0))

                self.draw = ImageDraw.Draw(self.image)
                self.font = ImageFont.truetype(fontPath, self.fontSize)
                self.CreateTextObject(self.lightGroups[self.currentLightGroup])

		self.ButtonRead()

	#initial homehub query to retrieve light list
	def QueryLightList(self, url):
		queryParams = {self.Config.get('HOMEHUB', 'queryValue'):self.Config.get('HOMEHUB', 'paramValue')}
		page = requests.get(url, queryParams)

		#light group setup
		return json.loads(page.text)

	def JsonLightToLightGroupNames(self, jsonObject, default):
                lightGroups = []
		for key in jsonObject:
			lightGroups.append(key)
			if key == default:
        			self.currentLightGroup = len(lightGroups)-1

		return lightGroups

	def CreateTextObject(self, textToDisplay):
		self.draw.text( (self.initX, self.initY), textToDisplay, font=self.font, fill=0)
		self.papirusDisplay.display(self.image)
		self.papirusDisplay.update()
		self.TextCleanupForFutureDelete(textToDisplay)

	def TextCleanupForFutureDelete(self, textToDisplay):
		#calculate some text values for when we want to clear this object
		textSize = self.draw.textsize(textToDisplay, font=self.font)
		self.endX = self.initX+textSize[0]
		self.endY = self.initY+self.fontSize

	def ClearExistingTextNoUpdate(self):
		self.draw.rectangle([self.initX, self.initY, self.endX, self.endY], fill='white')

	def UpdateText(self, textToDisplay):
		self.ClearExistingTextNoUpdate()
		self.draw.text( (self.initX, self.initY), textToDisplay, font=self.font, fill=0)

		self.papirusDisplay.display(self.image)
		self.papirusDisplay.partial_update()

	def ButtonRead(self):
		while True:
			if GPIO.input(self.SW1) == False and GPIO.input(self.SW2) == False:
				sleep(0.2)
				self.papirusDisplay.clear()
				break

		        if GPIO.input(self.SW1) == False:
				self.currentLightGroup -= 1
		                if self.currentLightGroup < 0:
		                        self.currentLightGroup = len(self.lightGroups)-1
		                self.UpdateText(self.lightGroups[self.currentLightGroup])
				sleep(0.1)

                        if GPIO.input(self.SW2) == False:
                                self.currentLightGroup += 1
                                if self.currentLightGroup >= len(self.lightGroups):
                                        self.currentLightGroup = 0
                                self.UpdateText(self.lightGroups[self.currentLightGroup])
				sleep(0.1)

			if GPIO.input(self.SW3) == False:
				sleep(0.1)

			if GPIO.input(self.SW4) == False:
				currentLightStatus = self.jsonLightGroups[self.lightGroups[self.currentLightGroup]][0]['is_on']
				newLightStatus = 'true'
				if currentLightStatus:
					newLightStatus = 'false'
				updateParams = {self.Config.get('HOMEHUB', 'queryValue'):self.Config.get('HOMEHUB', 'updateParamValue'),self.Config.get('HOMEHUB', 'updateGroupQueryValue'):self.lightGroups[self.currentLightGroup],self.Config.get('HOMEHUB', 'updateStatusQueryValue'):newLightStatus}
				url = self.Config.get('HOMEHUB', 'url')
				toggle = requests.get(url, updateParams, timeout=5)
				sleep(0.1)

			sleep(0.1)

homeHub = HomeHub()
sys.exit
