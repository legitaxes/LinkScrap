# IMPORT LIBRARIES
import credentials
import pyshorteners
import telegram
from bs4 import BeautifulSoup
from selenium import webdriver
from telegram.error import RetryAfter
import urllib.parse
import time
import os.path
import asyncio


# CONSTANTS
BOT_ID = credentials.bot_id ### replace this with the Bot ID of your telegram bot (i.e. 5927402841:) ###
TOKEN = credentials.telegram_token ### replace this with your telegram bot token (i.e. fidsughawpsdoig_sdfuisghdfsDFsuihsd) ###
CHANNEL_ID = credentials.channel_id ### replace this with the channel ID of your telegram channel (i.e. @TheAtForYourBot) ###

FILENAME = "trustbank.txt"
URL = "https://trustbank.sg/partner-offers/deals"
TINY_URL = pyshorteners.Shortener()
BOT = telegram.Bot(token=BOT_ID+TOKEN)


# FUNCTIONS
def check_if_file_exists(filename:str) -> None:
    """
    Checks if file exists. If it does, it will delete the file.
    Args:
        filename (str): filename of the file to check
    """
    # checks if file exists
    if os.path.exists(filename):
        print("Previous copy of the file already exist.")
        print("Preparing to delete the file...")
        os.remove(filename)
        print("File deleted.")


def check_user_scrap_choice(filename:str) -> None:
    """
    Checks if user wants to scrap the website.
    Args:
        filename (str): filename of the file to write to
    """
    choice = input("Do you want to scrape the website? (y): ")
    if choice == "y" or choice == "Y":
        check_if_file_exists(filename) # calls the above function to check if file exists
        driver = webdriver.Edge()
        driver.get(URL)

        time.sleep(5)

        html = driver.page_source

        soup = BeautifulSoup(html, "html.parser")

        results = soup.find_all("div", class_="mt-2 inline-block hover:cursor-pointer")

        # write the scrapped data to a file
        for result in results:
            # write result to a file 
            with open(filename, "a") as f:
                f.write(result.prettify())
        print("Successfully written scrapped data to file.")
        

async def read_data_from_file(filename:str) -> None:
    """
    Reads the data from the file and parse it into a string format.
    It also calls the send_telegram_message function to send the message to the telegram channel for each promotion in the file
    Args:
        filename (str): filename of the file to read from
    """
    counter = 0
    # read the file and parse the previous data
    # parse the text into a string format
    with open(filename, "r") as f:
        html_element = f.read()

    # parse every element of div class="mt-2 inline-block hover:cursor-pointer" into a list
    list_of_elements = html_element.split("<div class=\"mt-2 inline-block hover:cursor-pointer\">")

    # iterate through the list and parse the data into proper format
    for element in list_of_elements:
        fully_redeemed = False
        if(element):
            counter += 1
            # print(element)
            promo = element.split('<h2 class="mt-3 font-GTMedium text-lg font-medium tracking-tight">')
            redeemed = promo[0].split('<img class="w-full h-full object-cover" src="')[0]
            if "Fully Redeemed Banner" in redeemed:
                fully_redeemed = True
            picture = promo[0].split('<img class="w-full h-full object-cover" src="')[0].split('src="')[1].split('"/>')[0]
            promo = promo[1].split('<p class="mt-1 truncate text-ellipsis font-GTRegular text-[14px] font-normal">')
            name_of_promo = promo[0].split("</h2>")[0].strip()
            desc_of_promo = promo[1].split("</p>")[0].strip()
            url_encoded = urllib.parse.quote(desc_of_promo)
            promo_url = TINY_URL.tinyurl.short(f"{URL}#:~:text={url_encoded}")
            # print(f"Promo {counter}: {name_of_promo}: {desc_of_promo} \n{picture}") # debug
            # print(promo_url) # debug
            try:
                await send_telegram_message(name_of_promo, desc_of_promo, promo_url, picture, fully_redeemed)
            except RetryAfter as e:
                print(f"Telegram is busy. Retrying in {e.retry_after} seconds...")
                await asyncio.sleep(e.retry_after)
                await send_telegram_message(name_of_promo, desc_of_promo, promo_url, picture, fully_redeemed)
            

async def send_telegram_message(name_of_promo:str, desc_of_promo:str, promo_url:str, picture:str, fully_redeemed:bool) -> None:
    """
    Sends a message to the telegram channel.
    Args:
        name_of_promo (str): Name of the promotion
        desc_of_promo (str): Description of promotion
        promo_url (str): the url to direct user to check more information about the promotion
        picture (str): an online url link to the picture of the promotion
        fully_redeemed (bool): True if promotion is fully redeemed, False otherwise
    """
    if fully_redeemed:
        await BOT.sendPhoto(chat_id=CHANNEL_ID, photo=picture, caption=f"[[FULLY REDEEEMED]]\n{name_of_promo}\n{desc_of_promo}\n{promo_url}")
    else:
        await BOT.sendPhoto(chat_id=CHANNEL_ID, photo=picture, caption=f"{name_of_promo}\n{desc_of_promo}\n{promo_url}")
    print("Message sent to telegram channel.")


async def main():
    check_user_scrap_choice(FILENAME) # remember to uncomment
    await read_data_from_file(FILENAME)
    

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
        
