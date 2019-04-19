#!/usr/bin/env python3

import base64
import json
import logging
import os
import traceback

import urllib.request
from lxml import etree

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))

logging.basicConfig(filename=os.path.join(PROJECT_ROOT, "movienotifier.log"), level=logging.DEBUG, format="%(asctime)s:%(levelname)s:%(message)s")

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
  except Exception as err:
    logging.error(err)

def scrape_list(to_email, movie_keywords, cinema_keyword):
  movie_list_urls = []
  movie_list_url = "https://paytm.com/movies/bengaluru"

  request = urllib.request.Request(movie_list_url, headers=headers)
  try:
    response = urllib.request.urlopen(request)
    htmlparser = etree.HTMLParser()
    tree = etree.parse(response, htmlparser)

    scope = tree.xpath("//div[@id='popular-movies']/ul//li")

    if not len(scope):
      send_mail(to_email, "Error", "movie_list selector failing")

    for el in scope:
      el_text = " ".join(el.xpath("a//text()")).lower()
      match = all(kw.lower() in el_text for kw in movie_keywords)

      if match:
        rel_movie_url = " ".join(el.xpath("a/@href"))
        movie_list_url = "https://paytm.com" + rel_movie_url
        movie_list_urls.append(movie_list_url)

    logging.info('matched movies with keyword: {}'.format(movie_list_urls))
    return detail(movie_list_urls, to_email, movie_keywords, cinema_keyword)
  except Exception as e:
    logging.error("traceback={}".format(format_traceback(e)))
    send_mail(to_email, "Error", e)
    return []



def detail(movie_list_urls, to_email, movie_keywords, cinema_keyword):
  movies_info = []
  for url in movie_list_urls:
    cinemas = []
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
          logging.warning("Wrong element hit for cinema_name")
      movies_info.append({ "doc_title": doc_title, "cinemas": cinemas })
    except Exception as err:
      logging.error("traceback={}".format(format_traceback(err)))
      send_mail(to_email, "Error", str(err) + url)

  return movies_info

if __name__ == "__main__":
  try:
    with open(os.path.join(PROJECT_ROOT, "config.json"), "r") as file:
      config = json.load(file)
      configs = config if isinstance(config, list) else [config]
      for config in configs:
        movie_keywords = config["movieKeywords"]
        cinema_keyword = config["cinemaKeyword"]
        to_email = config["notifyTo"]
        movies_info = scrape_list(to_email, movie_keywords, cinema_keyword)
        if len(movies_info):
          message = "Search result for {}, {} \n".format(movie_keywords, cinema_keyword)
          message += json.dumps(movies_info, indent=2)
          logging.info("Result for movie_keywords={}, cinema_keyword={} is movies={}".format(movie_keywords, cinema_keyword, json.dumps(movies_info)))
          send_mail(to_email, "Found matches for {}".format(" ".join(movie_keywords)), message)
  except FileNotFoundError as err:
    logging.error(err)



# https://stackoverflow.com/questions/29708708/http-basic-authentication-not-working-in-python-3-4
# https://stackoverflow.com/questions/36484184/python-make-a-post-request-using-python-3-urllib

