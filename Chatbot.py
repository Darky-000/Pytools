#!/usr/bin/python3
import os, argparse, sys, time
from pytools import Json
from pytools.Ascii import Beautifulizer, Colors
from pytools import FileManager
from rapidfuzz import fuzz
import random

VERSION = "1.0"
Json.store_cache = False
database = os.getenv("chats_data_storage_path")
if database is None:
	HOME = os.getenv("HOME")
	database = os.path.join(HOME, ".database", "chats.json")

class Chatbot:
	def __init__(self, name="Lily"):
		self.database = FileManager.Open(database)
		if not self.database.exists():
			Json.write_json(str(self.database))
		
		self.data = Json.load(str(self.database))
		self.name = name
		self.temperature = 30
		self.seed = -1
	
	def replacer(self, text):
		current_time = time.strftime("%H:%M")
		
		text = text.replace("[%TIME%]", current_time)
		text = text.replace("[%BOT_NAME%]", self.name)
		
		return text
	
	def _save(self, data):
		Json.write_json(str(self.database), data=data)
	
	def learn(self, question, answer):
		if question in self.data:
			_resp = self.data.get(question)
			if isinstance(_resp, list):
				if not answer in _resp:
					self.data[question].append(answer)
			elif isinstance(_resp, str):
				if not answer == _resp:
					self.data[question] = [self.data[question]]
					self.data[question].append(answer)
		else:
			self.data[question] = answer
		self._save(self.data)
	
	def match(self, question, questions):
		if self.temperature > 100 or self.temperature <= 0:
			raise ValueError("Temperature can only be under 1-100 (Temperature decides, How fuzzy the AI could be. Lower for strict matches and higher for more fuzzy match)")
		threshold = 100-self.temperature
		matches = {}
		for q in questions:
			match = fuzz.ratio(question.strip().lower(), q.strip().lower())
			if match >= threshold:
				matches[match] = q
		if matches:
			return matches.get(max(matches))
	
	def ask(self, query):
		beautiful = Beautifulizer()
		if self.seed != -1:
			random.seed(self.seed)
		query = self.match(query, self.data)
		answer = self.data.get(query)
		if answer is not None:
			if isinstance(answer, str):
				return beautiful.pretty(self.replacer(answer))
			elif isinstance(answer, list):
				answer = random.choice(answer)
				return beautiful.pretty(self.replacer(answer))
			else:
				return answer
	
	def forget(self):
		self._save(None)
		self.data = {}

def Chat(object):
	"""CLI AI chat"""
	bot = object
	try:
		while True:
			question = input("> ")
			response = bot.ask(question)
			if response is not None:
				if "[EXIT]" in response:
					response = response.replace("[EXIT]", "")
					print(response)
					sys.exit(0)
				else:
					print(response)
			else:
				print(f"Sorry, I don't know how to respond on {question!r}")
	except (KeyboardInterrupt, EOFError):
		sys.exit(1)
	except Exception as e:
		print(f"{type(e).__name__}: {e}")
	
def main():
	parser = argparse.ArgumentParser(
		prog="Chatbot",
		description="Simple CLI Chatbot, created for answering prelearned questions"
	)
	bot = Chatbot()
	
	parser.add_argument(
		"-l",
		"--learn",
		nargs=2,
		metavar=("QUESTION", "ANSWER"),
		help="Teach the bot new answers"
	)
	
	parser.add_argument(
		"-f",
		"--forget",
		action="store_true",
		help="Delete all learned answers"
	)
	
	args = parser.parse_args()
	if args.learn:
		question, answer = args.learn
		bot.learn(question, answer)
		print(f"Bot learned {question!r} -> {answer!r}")
	
	elif args.forget:
		bot.forget()
		print("All learned answers are forgotten!")
	
	else:
		Chat(bot)

if __name__=="__main__":
	main()