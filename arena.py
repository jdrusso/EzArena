from bs4 import BeautifulSoup as BS
from PIL import ImageGrab, Image, ImageOps, ImageEnhance
import cv2, math, urllib
import pytesser as pyt
import uploader
from difflib import SequenceMatcher as SM
from Tkinter import *
import win32api

# Callback methods for mouseover events on the colored card overlays
def hideWindow(event):
    event.widget.withdraw()
    return
def showWindow(event):
    event.widget.deiconify()
    return

# This compares histograms by calculating Bhattacharyya distance. Seems to be the
#   most accurate algorithm. METHOD=2 corresponds to that comparison method.
METHOD = 2

LEFT   = 0
CENTER = 1
RIGHT  = 2

CLASSES = ["druid", "hunter", "mage", "paladin",
            "priest", "rogue", "shaman", "warlock", "warrior"]

RARITIES = ['beyond-great', 'great', 'good', 'above-average', 'average',
            'below-average', 'bad', 'terrible']

# URL to my OCR engine in AWS
AWS_URL_START = "http://ec2-52-24-64-160.us-west-2.compute.amazonaws.com/index.php?img="
AWS_URL_END = "&format=txt"

# Capture hero potrait from lower left and compare to saved portraits to determine class
ImageGrab.grab(bbox=(305,700,555,1045)).save("hero.jpg")

#Generate histograms for all 3 color channels
heroPortrait = cv2.imread("hero.jpg")
heroHistr = cv2.calcHist([heroPortrait], [0],None,[256],[0,256])
heroHistg = cv2.calcHist([heroPortrait], [1],None,[256],[0,256])
heroHistb = cv2.calcHist([heroPortrait], [2],None,[256],[0,256])

# Shitty algorithm to compare the captured hero portrait against the list of
#   saved portraits. I compare the square sum of the RGB channels since the
#   images won't be an exact match. The portrait images I'm using have some
#   health and attack icons at the bottom, so they're slightly different from
#   the captured image.
# I could probably have found more similar class portraits without those icons,
#   but part of my goal for this program was to work a little with fuzzy
#   matching, like I do with the OCRed card texts.
# TODO: Can I use difflib here to compare the images, instead of this?
# TODO: Break this out into a method. You should be ashamed.
matches = dict()
# Iterate through classes
for c in CLASSES:

    # Load that class's portrait
    compare = cv2.imread("heroes/%s.jpg" % c);

    # Generate histograms for it
    cHistr = cv2.calcHist([compare], [0],None,[256],[0,256])
    cHistg = cv2.calcHist([compare], [1],None,[256],[0,256])
    cHistb = cv2.calcHist([compare], [2],None,[256],[0,256])

    # Compare histograms per channel
    resultsr = cv2.compareHist(heroHistr, cHistr, METHOD);
    resultsg = cv2.compareHist(heroHistg, cHistg, METHOD);
    resultsb = cv2.compareHist(heroHistb, cHistb, METHOD);

    # Calculate squared sum of channels, since some can be negative
    results = resultsr**2 + resultsg**2 + resultsb**2

    # Spam up the terminal
    print("---%s---" % c)
    print(resultsr, resultsg, resultsb);
    print(results)
    matches[c]=results

# Find "closest" match to hero potrait
hero = max(matches, key=matches.get)
print("Hero appears to be a %s" % hero)

# Pull tierlist page
print("\nPulling tier list page...")
html = urllib.urlopen('http://www.heartharena.com/tierlist').read()
soup = BS(html, 'html.parser')
print("Done.\n")

# Construct dict of {card tier : card names in that tier}
tierlist = soup.find(id=hero)
cards = dict()
print("Extracting card names...")
# Iterate through all rarities
for rarity in RARITIES:

    cards[rarity] = list()
    # Iterate through all card tiers for that rarity
    for tier in tierlist.findAll(class_="tier %s" % rarity):
        # Iterate through all list entries for each tier
        for card in tier.find('ol').findAll('dt'):

            # This is a nonbreaking space character that shows up in blank
            #   tierlist entries. Obviously we don't want blank entries.
            if card.get_text() == u'\xa0':
                break

            # Add card to the list of cards of its rarity.
            cards[rarity].append(card.get_text()[:-1])

# Identify triplet of cards
# This list of tuples corresponds to the bounding boxes of each of the 3 cards
#   given a fullscreen 1920x1080 window. Yes, it's completely static and depends
#   on that resolution and window mode. No, it wouldn't be trivial to change that.
coords = [(385,390,610,440),(670,390,895,440),(950,390,1175,440)]
triplet = list()
for i in range(3):
    # Capture the image of a card in the triplet
    image = ImageGrab.grab(bbox=coords[i])
    # TODO: I can probably be more efficient with not saving these.
    image.save("img/original_card%d.jpg" % i)

######### Experimental Image Preprocessing ##########

    #Preprocess image for OCR.
    #TODO: This algorithm SUCKS.
    image = ImageOps.invert(ImageOps.invert(image).point(lambda x: x*2.4 ))
    image = ImageEnhance.Contrast(image.convert('L')).enhance(1.4).point(
        lambda x: 0 if (x > 220 and 255) else 255, '1')
######################################################

    #Send image to OCR server
    #TODO: Verify server address
    image.save("img/card%d.jpg" % i)
    url = uploader.upload("img/card%d.jpg" % i)

    #Construct URL to raw image
    imgurl = url[:20] + 'extpics/' + url[20:]

    # OCR card names from images
    textresult = urllib.urlopen(AWS_URL_START + imgurl + AWS_URL_END).read()
    print("OCR Result: %s" % textresult)
    # print("Image URL: %s" % imgurl)

    #Find which card the OCRed text corresponds to. Attempt to determine the
    #   MOST SIMILAR match, since the OCR result is far from perfect.
    bestMatch = 0
    for rarity in RARITIES:
        for card in cards[rarity]:
            score = SM(None, str(textresult), str(card)).ratio()
            if score > bestMatch:
                bestMatch = score
                cardMatch = card

    #Store matched card
    print("Detected card was %s, confidence %f" % (cardMatch, score))
    triplet.append([cardMatch, i])


# Define card geometry on window
# TODO: Make this resolution-independent.
cardOutlines = [(378,245,622,583),(656,245,900,583),(940,245,1184,583)]
width = cardOutlines[0][2]-cardOutlines[0][0]
height = cardOutlines[0][3]-cardOutlines[0][1]

# Build the colored card overlays.
# TODO: Don't hide overlay. Just capture clicks on it and simulate them on the
#       card below.
master = Tk()
master.withdraw()
windows = list()
for i in range(3):
    obj = Toplevel()
    windows.append(obj)
    windows[i].wait_visibility(windows[i])

    # No need for the window to be resizeable
    windows[i].resizable(width=FALSE, height=FALSE)

    # Set window position and size
    windows[i].geometry('%dx%d+%d+%d' %
    (width, height, cardOutlines[i][0],cardOutlines[i][1]))

    # Add transparency
    windows[i].attributes('-alpha',0.2)
    windows[i].bind("<Enter>", hideWindow)
    windows[i].bind("<Leave>", showWindow)

    # TODO: Do I need this?
    windows[i].overrideredirect(1)

print("Available cards are %s, %s, and %s" % (triplet[0][0], triplet[1][0], triplet[2][0]))

# Ranking. This will construct a list 'optimal' of each card in the triplet in
#   order of how they appear in the tierlist.
optimal = list()
for rarity in RARITIES:
    for card in cards[rarity]:

        for c in triplet:
            if c[0] == card:
                c.append(rarity)
                optimal.append(c)
                triplet.remove(c)

print("\nCard ranking:")
for i in range(3):
    print("[%d] %s \t %s" % (i+1, optimal[i][0], optimal[i][2]))

# Draw colored overlay on screen over cards, i.e. green for best choice, red for worst
colors = ["green", "yellow", "red"]
for c in range(3):
    windows[optimal[c][1]]["bg"] = colors[c]

#TODO: weight mana costs with current curve

master.mainloop()



# This function courtesy of (http://www.pyimagesearch.com/2014/09/15/python-compare-two-images/)
def mse(imageA, imageB):
	# the 'Mean Squared Error' between the two images is the
	# sum of the squared difference between the two images;
	# NOTE: the two images must have the same dimension
	err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
	err /= float(imageA.shape[0] * imageA.shape[1])

	# return the MSE, the lower the error, the more "similar"
	# the two images are
	return err
