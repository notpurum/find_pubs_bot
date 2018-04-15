#! /var/www/user538/data/.local/bin/python3
# -*- coding: utf-8 -*-

import logging
import requests
import re
import json
from time import sleep

from python_config import read_config
from vk_telegram import BotHandler

tokens = read_config(section='tokens')

API_TOKEN = tokens['telegram']
client_id = tokens['client_id']
client_secret = tokens['client_secret']

info_sticker_id = "CAADAgADiAMAAln0dAABFiYPQB5lPdQC"

def find_bars(lat, lng, radius):
	url = 'https://api.foursquare.com/v2/venues/explore'
	location = str(lat) + ',' + str(lng)
	params = dict(
	  client_id=client_id,
	  client_secret=client_secret,
	  v='20180323',
	  ll=location,
	  radius=radius,
	  query='паб',
	  # openNow=1,
	  limit=5
	)
	resp = requests.get(url=url, params=params).json()

	try:
		venues = resp['response']['groups'][0]['items']
		result = []
		for venue in venues:
			venue = venue['venue']
			name = venue['name']
			location = {
			'lat': venue['location']['lat'],
			'lng': venue['location']['lng']
			}
			try:
				rating = venue['rating']
			except:
				rating = None

			try:
				address = venue['location']['address']
			except:
				address = None

			try:
				price = venue['price']['tier']
			except:
				price = None

			site = 'https://foursquare.com/v/' + venue['id']
			distance = venue['location']['distance']

			data = {
			'name': name,
			'location': location,
			'rating':rating,
			'distance': distance,
			'address': address,
			'price': price,
			'site': site
			}

			result.append(data)
		return result
	except:
		return None

def send_bars(chat_id, latitude, longitude):
	global radius
	if chat_id in users:
		radius = users[chat_id]
	else:
		radius = 500

	bars = find_bars(latitude, longitude, radius)
	if bars:
		j = 0
		for bar in bars:
			location = bar['location']
			lat = location['lat']
			lon = location['lng']
			name = bar['name']
			distance = bar['distance']
			address = bar['address']
			rating = bar['rating']
			price = bar['price']
			site = bar['site']

			text_name = '[' + name.title() + '](' + site + ')' + ' (' + str(distance) + ' м)'  + '\n'
			text_rating = ('Рейтинг: ' + str(rating)) if rating else 'Рейтинг неизвестен'
			text_address = (address.replace('. ', '.\xa0') + '\n') if address else ''
			
			if price:
				text_price = ', *' + ('₽' * price ) + '*'
			else:
				text_price = '.'

			text = text_name + text_address + text_rating + text_price

			bot.send_location(chat_id, lat, lon)
			bot.send_message(chat_id, text, parse_mode='Markdown', disable_web_page_preview=True)
			j += 1
		if j < 5:
			bot.send_message(chat_id, 'Больше в радиусе *' + str(radius) + '\xa0м* пабов нет.', parse_mode='Markdown')
	else:
		bot.send_message(chat_id, 'Нет пабов в радиусе *' + str(radius) + '\xa0м*', parse_mode='Markdown')

def set_radius(chat_id, text):
	global radius
	set_radius = re.search('\d+', text).group()
	if int(set_radius) > 0:
		radius = int(set_radius)
	else:
		radius = -int(set_radius)

	ok = 'Ок'
	if radius > 100000:
		radius = 100000
		ok = 'Максимальный радиус *100000\xa0м*'

	users[chat_id] = radius

	with open ('users.txt', 'w') as f:
		for user in users:
			text = str(user) + ',' + str(users[user]) + '\n'
			f.write(text.strip() + '\n')

	bot.send_message(chat_id, ok + ', теперь буду искать пабы в\xa0радиусе *' + str(radius) + '\xa0м.*', parse_mode='Markdown')

def has_number(text):
	pattern = re.compile('\d+')
	if pattern.match(text):
		return True
	else:
		return False

def keyboard():
	button = {"text":"Отправить геопозицию", "request_location":True}
	keyboard = json.dumps({"keyboard":[[button]], "resize_keyboard":True})
	return keyboard

def answer_start(chat_id):
	if chat_id in users:
		radius = users[chat_id]
	else:
		radius = 500

	# markup = keyboard()
	bot.send_message(chat_id, 'Для того, чтобы найти ближайшие пабы в\xa0радиусе *' + str(radius) + '\xa0м,* отправьте геопозицию. \n\n\
Чтобы изменить радиус поиска, отправьте число, например, *1000*', parse_mode='Markdown')
	bot.send_sticker(chat_id, info_sticker_id)

def answer(chat_id):
	if chat_id in users:
		radius = users[chat_id]
	else:
		radius = 500

	# markup = keyboard()
	bot.send_message(chat_id,
		'Для того, чтобы найти ближайшие пабы в\xa0радиусе *' + str(radius) + '\xa0м,* отправьте геопозицию. \n\n\
Чтобы изменить радиус поиска, отправьте число, например, *1000*', parse_mode='Markdown')




###################################################



bot = BotHandler(API_TOKEN)
bot.send_message(7664729, 'Я живой!')

users = {}
with open ('users.txt', 'r') as f:
	output = f.read().split('\n')
	for line in output:
		try:
			chat_id = int(line.split(',')[0])
			radius = int(line.split(',')[1])
			users[chat_id] = radius
		except:
			break

logging.basicConfig(level=logging.WARNING, filename='myapp.log')

def main():
	offset = bot.get_offset()
	while True:
		updates = bot.get_updates(offset, timeout=30)

		if updates:
			for update in updates:
				last_chat_value = update['last_chat_value']
				last_chat_id = update['last_chat_id']
				last_update_id = update['last_update_id']
				if last_chat_value:
					if 'location' in last_chat_value:
						send_bars(last_chat_id, last_chat_value['location']['latitude'], last_chat_value['location']['longitude'])
						offset += 1
					elif 'text' in last_chat_value:
						text = last_chat_value['text']
						if text.lower() == '/start':
							answer_start(last_chat_id)
							offset += 1
						elif has_number(text):
							set_radius(last_chat_id, text)
							offset += 1
						else:
							answer(last_chat_id)
							offset += 1
				else:
					answer(last_chat_id)
					offset += 1
		sleep(3)

if __name__ == '__main__':
	try:
		main()
	except:
		# bot.send_message(7664729, "Я умер!")
		logging.exception("Oops:")