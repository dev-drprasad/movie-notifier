#!/usr/bin/env python3

import base64
import hashlib
import json
import logging
import os
import traceback

import urllib.request
from lxml import etree

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))

logging.basicConfig(filename=os.path.join(PROJECT_ROOT, "bookmyshow.log"), level=logging.DEBUG, format="%(asctime)s:%(levelname)s:%(message)s")

with open(os.path.join(PROJECT_ROOT, "mailgun.json"), "r") as file:
  mailgun = json.load(file)


headers = { 'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36' }

valid_screen_types = ["2D", "3D", "IMAX 2D", "IMAX 3D", "4DX", "IMAX"]

def format_traceback(ex):
  tblines = []
  for line in traceback.format_exception(ex.__class__, ex, ex.__traceback__):
    tblines.extend(line.splitlines())
  return tblines.__str__()
  


def send_mail(to_email, subject, message):

  is_same_message = False
  message_hash = hashlib.md5((subject + message).encode()).hexdigest()
  try:
    with open(os.path.join(PROJECT_ROOT, "sent_bookmyshow.txt"), "r") as file:
      sent_message_hashes = file.read()
      is_same_message = message_hash in sent_message_hashes
      logging.info('is_same_message={}'.format(is_same_message))
  except Exception as err:
    pass

  if not is_same_message:
    data = urllib.parse.urlencode({
      "from": mailgun["fromEmail"],
      "to": to_email,
      "subject": subject,
      "text": message,
    }, doseq=True).encode()
    request = urllib.request.Request(mailgun["apiURL"], data=data)
    request.add_header('Content-Type', 'application/x-www-form-urlencoded')

    request.add_header(
      "Authorization",
      "Basic %s" % base64.b64encode(("api:" + mailgun["apiToken"]).encode("ascii")).decode("ascii"))

    try:
      response = urllib.request.urlopen(request)
      logging.info(response.read().decode())
      with open(os.path.join(PROJECT_ROOT, "sent_bookmyshow.txt"), "a+") as file:
        file.write(message_hash + '\n')
    except Exception as err:
      logging.error(err)

def scrape_list():
  movie_list_url = "https://in.bookmyshow.com/buytickets/avengers-endgame-bengaluru/movie-bang-ET00100559-MT/20190427"

  request = urllib.request.Request(movie_list_url, headers=headers)
  try:
    response = urllib.request.urlopen(request)
    htmlparser = etree.HTMLParser()
    tree = etree.parse(response, htmlparser)

    scope = tree.xpath("//ul[@id='venuelist']/li")

    cinema_list = []
    for el in scope:
      cinema = " ".join(el.xpath("./@data-name")).strip()
      cinema_list.append(cinema)
    
    if "koramangala" in " ".join(cinema_list).lower():
      send_mail("dev.drprasad@aim.com", "BookMyShow Result", "\n".join(cinema_list))

    print(cinema_list)
      

  except Exception as e:
    logging.error("traceback={}".format(format_traceback(e)))
    return []


if __name__ == "__main__":
  scrape_list()


# https://stackoverflow.com/questions/29708708/http-basic-authentication-not-working-in-python-3-4
# https://stackoverflow.com/questions/36484184/python-make-a-post-request-using-python-3-urllib

