import base64
import urllib

MAILGUN_API_URL = "<api-url>"
MAILGUN_API_TOKEN = "<api-token>"

def send_mail(from_email, to_email, subject, message):

  data = urllib.parse.urlencode({
    "from": from_email,
    "to": to_email,
    "subject": subject,
    "text": message,
  }, doseq=True).encode()

  request = urllib.request.Request(MAILGUN_API_URL, data=data)
  request.add_header('Content-Type', 'application/x-www-form-urlencoded')
  encoded_token = base64.b64encode(("api:" + MAILGUN_API_TOKEN).encode("ascii")).decode("ascii")
  request.add_header("Authorization", "Basic {}".format(encoded_token))

  try:
    response = urllib.request.urlopen(request)
    print(response.read())
  except Exception as err:
    print(err)
