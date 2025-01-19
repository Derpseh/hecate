import requests
from bs4 import BeautifulSoup
import time
import toml
global target_dict
target_dict = {}
global headers
global prev_list
prev_list = {}
global send_queue
send_queue = []
global sent_dict
sent_dict = {}
try:
	with open('config.toml', 'r') as f:
		toml_config = toml.load(f)
except:
	print("something went wrong loading the config file; please make sure you have an appropriate 'config.toml' in the same folder you're running hécate in")
	exit()
if ("main_nation" in toml_config) and (len(toml_config["main_nation"])>2):
	headers = {"User-Agent": f"Hécate API client, currently in use by {toml_config['main_nation']}"}
else:
	print("no appropriate main nation could be found in the config file, please make sure you have a configured 'config.toml' in the same folder you're running hécate in")
	exit()
if ("targeting" in toml_config) and (len(toml_config["targeting"])>0):
	for a in toml_config["targeting"]:
		if len(toml_config["targeting"][a]) == 4:
			target_dict[toml_config["targeting"][a][0]] = toml_config["targeting"][a][1:]
		else:
			print("target list is incorrectly formatted, please check your 'config.toml' file")
			exit()
else:
	print("no target regions could be found in the config file, please make sure you have a configured 'config.toml' in the same folder you're running hécate in")
	exit()
target_string = ""
for a in target_dict:
	target_string += a + ","
target_string = target_string[:-1]
req2 = requests.get(f"https://www.nationstates.net/cgi-bin/api.cgi?q=happenings&view=region.{target_string}&filter=move+founding+member", headers = headers)
soup2 = BeautifulSoup(req2.text, "lxml-xml")
time.sleep(0.6)
while True:
	for a in target_dict:
		req = requests.get(f"https://www.nationstates.net/cgi-bin/api.cgi?region={a}&q=nations+wanations", headers = headers)
		soup = BeautifulSoup(req.text, "lxml-xml")
		nation_list = soup.NATIONS.string.split(':')
		try:
			wa_list = soup.UNNATIONS.string.split(',')
		except:
			print(f"{a.replace('_',' ')} has no usable WA nations, moving on")
		if toml_config["wa_nations"] == False:
			if a in prev_list:
				for nat in nation_list:
					if (nat not in prev_list[a][0]) and ([nat, a] not in send_queue):
						send_queue.append([nat, a])
						print(f"located target {nat} from {a}")
			else:
				if toml_config["new_nations"] == True:
					print(f"no previous data found for {a.replace('_',' ')}, generating targets from happenings")
					happening_list = soup2.find_all("EVENT")
					for event in happening_list:
						if ((f"founded in %%{a}%%" in event.TEXT.text) or (f"%%to %%{a}%%" in event.TEXT.text)) and ([event.TEXT.text.split("@@")[1], a] not in send_queue):
							send_queue.append([event.TEXT.text.split("@@")[1], a])
							print(f"located target {event.TEXT.text.split('@@')[1]} from {a}")
				else:
					for nat in nation_list:
						send_queue.append([nat, a])
			
		else:
			if a in prev_list:
				for nat in wa_list:
					if (nat not in prev_list[a][1]) and ([nat, a] not in send_queue):
						send_queue.append([nat, a])
						print(f"located target {nat} from {a}")
			else:
				if toml_config["new_nations"] == True:
					print(f"no previous data found for {a.replace('_',' ')}; generating targets from happenings")
					happening_list = soup2.find_all("EVENT")
					for event in happening_list:
						if ("was admitted" in event.TEXT.text) and ([event.TEXT.text.split("@@")[1], a] not in send_queue) and (event.TEXT.text.split("@@")[1] in wa_list):
							send_queue.append([event.TEXT.text.split("@@")[1], a])
							print(f"located target {event.TEXT.text.split('@@')[1]} from {a}")
				else:
					for nat in wa_list:
						send_queue.append([nat, a])
		prev_list[a] = [nation_list, wa_list]
		time.sleep(0.6)
	if len(send_queue)>0:
		send_queue2 = []
		for a in send_queue:
			if a[0] not in sent_dict:
				send_queue2 = [a] + send_queue2
		for a in send_queue2:
			print(f"checking {a[0]}")
			req3 = requests.get(f"https://www.nationstates.net/cgi-bin/api.cgi?nation={a[0]}&q=region+tgcanrecruit", headers=headers)
			time.sleep(0.6)
			soup3 = BeautifulSoup(req3.text, "lxml-xml")
			if soup3.REGION.text.lower().replace(' ','_') == a[1] and soup3.TGCANRECRUIT.text == "1":
				print(f"sending recruitment tg to {a[0]}")
				sent_dict[a[0]] = [1, time.time()]
				req4 = requests.get(f"https://www.nationstates.net/cgi-bin/api.cgi?a=sendTG&client={target_dict[a[1]][0]}&tgid={target_dict[a[1]][1]}&key={target_dict[a[1]][2]}&to=(a[1])", headers=headers)
				break
			else: 
				print(f"{a[0]} is not recruitable, trying the next nation")
				sent_dict[a[0]] = [0, time.time()]
	time.sleep(180)