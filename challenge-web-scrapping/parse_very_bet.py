# Author: Ricardo Pereira Lins
# You can see the games in the console and in the exportated_games.json file
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime, timezone

# Initialize Chrome WebDriver options to run headlessly (without opening a browser window)
options = webdriver.ChromeOptions()
options.add_argument('--headless')

# Initialize the WebDriver using the ChromeDriverManager to automatically download the required driver
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

# URL to scrape the sports betting picks
url = 'https://sportsbetting.dog/picks'
driver.get(url)

# Wait until the element with ID 'x-picks' is present to ensure the page has loaded
try:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'x-picks'))
    )
except Exception as e:
    print(f"Error loading page: {e}")
    driver.quit()
    exit()

# Pause for a few seconds to let the page load completely
time.sleep(3)

# Get the page source and close the browser
page_source = driver.page_source
driver.quit()

# Parse the page content using BeautifulSoup
soup = BeautifulSoup(page_source, 'html.parser')

# Find all game events using a regex pattern for their class
events = soup.find_all('div', class_=re.compile('card shadow'))
all_games = []  # List to store all the games data

# Iterate over all the game events found on the page
for event in events:
    # Get the league name (or set 'League' as a placeholder if not found)
    game_league = event.find('a')
    game_league = game_league.get_text().strip() if game_league else 'League'
    
    # Get the game date and convert it into the correct format (UTC)
    game_date = event.find('span', style='opacity: .75')
    game_date = game_date.get_text().strip('( )') if game_date else '01/01/2002'
    data_obj = datetime.strptime(game_date, "%m/%d/%Y").replace(tzinfo=timezone.utc)
    formated_date = data_obj.strftime("%Y-%m-%dT%H:%M:%S%z")
    
    # Get all fields containing betting options
    fields = event.find_all('span', class_='text-secondary')
    field = [p.get_text().strip().split() for p in fields]

    # Skip events where there aren't enough fields to make sense of the game
    if len(field) < 8:
        continue

    n = 0  # Index for iterating over the game fields
    while n < len(field):
        if n + 7 >= len(field):  # If there aren't enough fields for a complete set, stop
            break
        
        # Check if the game has started or not by looking for a specific element
        not_started = event.find('span', class_='text-info')
        
        if not_started:
            # If the game hasn't started yet, prepare a set of games with the "Not Started" status
            games = [
                {
                    "sport_league": game_league,
                    "event_date_utc": formated_date,
                    "team1": " ".join(field[n]),
                    "team2": " ".join(field[n + 4]),
                    "pitcher": "",
                    "period": "Not Started",
                    "line_type": "moneyline",
                    "price": field[n + 1][0] if len(field[n + 1]) > 0 else None,
                    "side": " ".join(field[n]),
                    "team": " ".join(field[n]),
                    "spread": 0
                },
                # Similar structure for other betting options (spread, over/under, etc.)
                {
                    "sport_league": game_league,
                    "event_date_utc": formated_date,
                    "team1": " ".join(field[n]),
                    "team2": " ".join(field[n + 4]),
                    "pitcher": "",
                    "period": "Not Started",
                    "line_type": "spread",
                    "price": field[n + 2][1] if len(field[n + 2]) > 1 else None,
                    "side": " ".join(field[n]),
                    "team": " ".join(field[n]),
                    "spread": field[n + 2][0] if len(field[n + 2]) > 0 else None
                },
                # Over/Under betting option
                {
                    "sport_league": game_league,
                    "event_date_utc": formated_date,
                    "team1": " ".join(field[n]),
                    "team2": " ".join(field[n + 4]),
                    "pitcher": "",
                    "period": "Not Started",
                    "line_type": "over/under",
                    "price": field[n + 3][2] if len(field[n + 3]) > 2 else None,
                    "side": field[n + 3][0] if len(field[n + 3]) > 0 else None,
                    "team": "total",
                    "spread": field[n + 3][1] if len(field[n + 3]) > 1 else None
                }
            ]
        else:
            # If the game has started, prepare a different set of data
            games = [
                {
                    "sport_league": game_league,
                    "event_date_utc": formated_date,
                    "team1": " ".join(field[n]),
                    "team2": " ".join(field[n + 5]),
                    "pitcher": "",
                    "period": "Started",
                    "line_type": "moneyline",
                    "price": field[n + 2][0] if len(field[n + 2]) > 0 else None,
                    "side": " ".join(field[n]),
                    "team": " ".join(field[n]),
                    "spread": 0
                },
                # Additional betting options (moneyline, spread, over/under) for started games
                {
                    "sport_league": game_league,
                    "event_date_utc": formated_date,
                    "team1": " ".join(field[n]),
                    "team2": " ".join(field[n + 5]),
                    "pitcher": "",
                    "period": "Started",
                    "line_type": "spread",
                    "price": field[n + 3][1] if len(field[n + 3]) > 1 else None,
                    "side": " ".join(field[n]),
                    "team": " ".join(field[n]),
                    "spread": field[n + 3][0] if len(field[n + 3]) > 0 else None
                }
            ]

        # Add the extracted games to the list of all games
        all_games.extend(games)
        
        # Move to the next set of fields (increment by 10 to skip to the next game)
        n += 10
        #go to print in the console the games
        print(games)

# Save all games to a JSON file
with open("exportated_games.json", "w", encoding="utf-8") as f:
    json.dump(all_games, f, indent=2, ensure_ascii=False)
