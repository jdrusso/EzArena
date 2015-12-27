This library intends to provide a way to automatically indicate the most
advantageous card to select when constructing a draft deck for Arena mode in
Hearthstone.

## Overview
When in the Arena draft screen, you're presented with 3 cards to choose from at
a time, in addition to a number of statistics about mana curve at the bottom,
your class portrait, and your current deck list on the right. The

## Implemented

- [x] Recognize class from portrait
    - `arena.py` grabs an image of the portrait, uses PIL to generate a histogram,
    then compares it to the histograms of all the basic class portraits. histograms
    are compared per-channel, and the square sum of the R/G/B channels is used
    to determine a match score.


- [x] Pull tier lists for your class
    - BeautifulSoup is used to pull the card data from HearthstoneArena.com's
    tier list. These are organized into a dict `cards`, where the keys are rarities
    and the values are lists of all the cards of that rarity.


- [x] Grab text of card name
    - PIL is used to take a screenshot of the card text.


## TODO
- [ ] Clean up card image so that OCR can be used
- [ ] Run OCR on card text
- [ ] Read all 3 cards instead of just leftmost
- [ ] Verify accuracy of class detection
- [ ] Remove dependence on absolute coordinates
- [ ] Colored overlays for choosing the best card
