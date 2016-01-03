This library intends to provide a way to automatically indicate the most
advantageous card to select when constructing a draft deck for Arena mode in
Hearthstone.

## Overview
When in the Arena draft screen, you're presented with 3 cards to choose from at
a time, in addition to a number of statistics about mana curve at the bottom,
your class portrait, and your current deck list on the right. Ideally, this
library aims to recognize your class, and then identify the highest-tier card available.

### Class Recognition
Class recognition is done by capturing the area of the screen where the hero portrait
is, and then comparing the square sums of the R/G/B channel histograms against
a set of all the class portraits, stored in `heroes/`. These were pulled from
the Hearthstone wiki. Calculating similarity using the histograms was a quick-n-dirty
solution - a cheaper, better, faster way may exist, but this works for now.

### Tierlist
Once class recognition is finished, the most recent tierlist is pulled from
[Heartharena](heartharena.net). The entire page at `heartharena.com/tierlist` is
pulled, and then parsed with BeautifulSoup. A dictionary of cards is constructed
where the cards are stored by their tier (beyond great, great, average, etc.)
regardless of rarity. (Rarity was ignored since all cards in the triplet presented
during draft are the same rarity.)

### Card Recognition
Card recognition is accomplished by capturing the screen area where each of the
three cards' texts are, and sending that to a URL at Amazon AWS. In AWS, I have
a small server running Tesseract OCR that has been trained on a dataset of all the
card names, using the `Belwe BD BT` which is what Blizzard uses on the card graphics.

To make the OCR more accurate and to use bandwidth more efficiently, the images
are preprocessed beforehand.
1. The image is inverted, such that white is
represented by RGB (0,0,0), and each pixel value
for every color channel is multiplied by a constant, and the image is again inverted
back to the original color palette. The intent here is to increase
color saturation.
2. The image is converted to grayscale and the contrast increased.
3. A thresholding filter is applied on each (now monochrome) pixel channel
to translate the image to black and white.

The goal of this is to leave a plain white image with black text, which is what
Tesseract works best with. The image is uploaded to [picpaste](www.picpaste.com),
and the URL to the uploaded image is passed as an argument to a PHP script running
on an OCR server hosted in AWS.

### Card Ranking
Once all three cards in the presented triplet are identified, they are ranked by
iterating through each card in the cards dictonary and sorting the triplet cards
into the order they appear. This has the side benefit of preserving ranking within
tiers - HearthArena ranks cards internally, within tiers, which is useful if
multiple cards would appear in the same tier.

Tkinter is used to draw an overlay above the cards, where the first, second, and
third best choice cards are highlighted in green, yellow, and red respectively.

## Requirements

- Internet access (to communicate with AWS OCR engine)
- Windows
- Beautiful Soup 4
- Python Imaging Library (PIL)
- win32api
- OpenCV

You can install these **except OpenCV** with
`pip install bs4 Pillow pywin32`.

To install OpenCV, follow
[this link to their website](http://docs.opencv.org/2.4/doc/tutorials/introduction/windows_install/windows_install.html#installation-by-using-the-pre-built-libraries),
which guides you through using their prebuilt binaries on Sourceforge.

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

## Future Work

- [ ] Better ranking algorithm

- [ ] Loop, so that you don't need to rerun the program between each triplet.

- [ ] Figure out if there's an actual term for the triplets.

- [ ] Either hide overlays on mouseover, or pass clicks through.


## TODO
- [x] Clean up card image so that OCR can be used
- [x] Run OCR on card text
- [x] Read all 3 cards instead of just leftmost
- [ ] Verify accuracy of class detection
- [ ] Remove dependence on absolute coordinates
- [x] Colored overlays for choosing the best card
- [ ] Hide overlay on mouseover, or add some kind of click through
- [ ] Make REQUIREMENTS file
- [ ] Test portrait recognition with all classes (currently only tested with rogue)
- [ ] Play with raising to a power instead of multiplying for the first image preprocessing step.
- [ ] Test disabling Tesseract dictionaries by setting `load_system_dawg` and `load_freq_dawg` to false.
