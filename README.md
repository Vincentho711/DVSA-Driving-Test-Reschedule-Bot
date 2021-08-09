# DVSA Driving Test Reshedule Bot 🤖
A Python bot which will search and reschedule driving tests for you using the DVSA website. 

## Features ✨
- Check DVSA driving test availability automatically
- Reschedule earlier tests for you automatically
- Can bypass DVSA firewalls using chrome extensions
- Notify through SMS using Twilio
- Seach for multiple bookings
- Waits in the queue for you when the site is busy

## Cloud Connection ☁️
Can be deployed onto cloud services like Azure or Google Cloud Platform and run script as cron job at a regular interval.

## About 📃
This builds on the work of [tp223](https://github.com/tp223), additional improvements and modification have been introduced to streamline the process for cloud operation. Due to current high demand for driving tests, this python script aims to quickly check the driving test booking page for any available tests. Simply enter your details in `config.ini` and set up your Twilio account and it will do the rest for you. This can also be deployed on linux server and be run as a cron job.

## Requirements 🔧
- An activated Twilio account (https://www.twilio.com/)
- Google Chrome (https://www.google.com/intl/en_uk/chrome/) or Chromium
- PIP packages:
  - selenium
  - undetected-chromedriver
  - configparser
