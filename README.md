# kombucha-alert

A scraper that sends push notifications when my favorite Kombucha flavor is available on Amazon prime now (the Whole Foods delivery service).

## Background

What even is [Kombucha](https://en.wikipedia.org/wiki/Kombucha "Kombucha")? Excellent question. It's a fermented black or green tea beverage that is bubbly and typically sweetened, either with added sweetener or fruit juice. It is produced by fermentation with a SCOBY (Symbiotic Culture Of Bacteria and Yeast). The living bacteria present in the beverage make it an excellent probiotic.

Kombucha has gotten quite the \~health\~ spotlight recently and the number of different bottles one may find in the appropriate section of their local Whole Foods may make for an overwhelming shopping experience. Having sampled quite a few varieties myself, I can personally say one brand and flavor reigns supreme: **GT's Lemonade Kombucha**.

Other consumers seem to agree, as lately I have seen more sad depleted shelves where this flavor usually stands than full ones. I decided to make this app to notify me when the flavor comes back in stock in my local Whole Foods (according to inventory listed on the Prime Now site). I can then immediately place an order and have my supply back in business before withdrawal settles in.

## Deployment

In production, the app is deployed on Heroku and run every 10 minutes using the Heroku Scheduler add-on.

A .env file is required to both run the Heroku app locally with `heroku local` and to be able to run the script on its own.

With the .env file properly configured in the root directory, the following command will run the script once by making the environment variables accessible and running `app.py`:

`bash run_local.sh`
