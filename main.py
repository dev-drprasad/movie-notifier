#!/usr/bin/env python3

import base64
import json
import os

import urllib.request
from lxml import etree

with open("mailgun.json", "r") as file:
  mailgun = json.load(file)


DIR = os.path.dirname(os.path.realpath(__file__))


headers = { 'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36' }

valid_screen_types = ["2D", "3D", "IMAX 2D", "IMAX 3D", "4DX", "IMAX"]
cinema_list_urls = []

# Try running this locally.
def send_mail(to_email, subject, message):
  # data = urllib.parse.urlencode({
  #   "from": from_email,
  #   "to": to_email,
  #   "subject": subject,
  #   "text": message
  # }).encode()

  # data = json.dumps({
  #   "from": from_email,
  #   "to": [to_email],
  #   "subject": subject,
  #   "text": message
  # }).encode()

  data = urllib.parse.urlencode({
    "from": mailgun["fromEmail"],
    "to": to_email,
    "subject": subject,
    "text": message,
  }, doseq=True).encode()
  request = urllib.request.Request(mailgun["apiURL"], data=data)
  request.add_header('Content-Type', 'application/x-www-form-urlencoded')
  # request.add_header('Content-Type', 'application/json')
  request.add_header(
    "Authorization",
    "Basic %s" % base64.b64encode(("api:" + mailgun["apiToken"]).encode("ascii")).decode("ascii"))

  try:
    response = urllib.request.urlopen(request)
    print(response.read())
  except Exception as err:
    print(err)
  
def list(to_email, movie_keywords, cinema_keyword):
  movie_list_url = "https://paytm.com/movies/bengaluru"

  try:
    request = urllib.request.Request(movie_list_url, headers=headers)
  except Exception as err:
    send_mail(to_email, "Error", err)
  response = urllib.request.urlopen(request)


  htmlparser = etree.HTMLParser()
  tree = etree.parse(response, htmlparser)

  scope = tree.xpath("//div[@id='popular-movies']/ul//li")

  if not len(scope):
    send_mail(to_email, "Error", "movie_list selector failing")

  for el in scope:
    el_text = " ".join(el.xpath("a//text()")).lower()
    # print(el_text)
    match = all(kw.lower() in el_text for kw in movie_keywords)

    if match:
      rel_cinema_url = " ".join(el.xpath("a/@href"))
      cinema_list_url = "https://paytm.com" + rel_cinema_url
      cinema_list_urls.append(cinema_list_url)

  print(cinema_list_urls)
  detail(to_email, movie_keywords, cinema_keyword)

def detail(to_email, movie_keywords, cinema_keyword):
  cinemas = []
  for url in cinema_list_urls:
    request = urllib.request.Request(url, headers=headers)
    try:
      response = urllib.request.urlopen(request)
      htmlparser = etree.HTMLParser()
      tree = etree.parse(response, htmlparser)
      doc_title = "".join(tree.xpath("/html/head/title/text()") )
      scope = tree.xpath("//div/ul/li[@class]")

      for el in scope:
        cinema_name = " ".join(el.xpath("div[1]/text()"))
        if cinema_name:
          if cinema_keyword.lower() in cinema_name.lower():

            show_times = []
            for el in el.xpath("div[2]/a"):
              show_time = "".join(el.xpath("./text()"))
              screen_type = "".join(el.xpath("span[1]/text()"))
              show_times.append({ "time" : show_time, "screenType": screen_type if screen_type in valid_screen_types else "" })
            cinemas.append({ "name": cinema_name, "showTimes" : show_times })
        else:
          print("Wrong element hit for cinema_name")
    except Exception as err:
      print(str(err) + " : " + url)
      send_mail(to_email, "Error", str(err) + url)

  if len(cinemas):
    message = "Search result for {}, {} \n".format(movie_keywords, cinema_keyword)
    message += json.dumps(cinemas, indent=2)
    print(message)
    send_mail(to_email, doc_title, message)

try:
  with open(os.path.join(DIR, "config.json"), "r") as file:
    config = json.load(file)
    list(config["notifyTo"], config["movieKeywords"], config["cinemaKeyword"])
except FileNotFoundError as err:
  print(err)



# https://stackoverflow.com/questions/29708708/http-basic-authentication-not-working-in-python-3-4
# https://stackoverflow.com/questions/36484184/python-make-a-post-request-using-python-3-urllib
