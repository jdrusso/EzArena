#Requires:
# scikit-image
# BeautifulSoup
# cv2
from bs4 import BeautifulSoup as BS
# from skimage.measure import structural_similarity as ssim
from PIL import ImageGrab, Image, ImageOps, ImageEnhance
import cv2, math, urllib
import pytesser as pyt
import uploader
from difflib import SequenceMatcher as SM
from Tkinter import *

# This compares histograms by calculating Bhattacharyya distance. Seems to be the
#   most accurate algorithm.
METHOD = 2

LEFT   = 0
CENTER = 1
RIGHT  = 2

CLASSES = ["druid", "hunter", "mage", "paladin",
            "priest", "rogue", "shaman", "warlock", "warrior"]

RARITIES = ['beyond-great', 'great', 'good', 'above-average', 'average',
            'below-average', 'bad', 'terrible']

AWS_URL_START = "http://ec2-52-24-64-160.us-west-2.compute.amazonaws.com/index.php?img="
AWS_URL_END = "&format=txt"


# Capture hero potrait from lower left and compare to saved portraits to determine class
ImageGrab.grab(bbox=(305,700,555,1045)).save("hero.jpg")

#Generate histograms for all 3 color channels
heroPortrait = cv2.imread("hero.jpg")
heroHistr = cv2.calcHist([heroPortrait], [0],None,[256],[0,256])
heroHistg = cv2.calcHist([heroPortrait], [1],None,[256],[0,256])
heroHistb = cv2.calcHist([heroPortrait], [2],None,[256],[0,256])

matches = dict()
for c in CLASSES:

    compare = cv2.imread("heroes/%s.jpg" % c);

    cHistr = cv2.calcHist([compare], [0],None,[256],[0,256])
    cHistg = cv2.calcHist([compare], [1],None,[256],[0,256])
    cHistb = cv2.calcHist([compare], [2],None,[256],[0,256])

    # Compare histograms per channel
    resultsr = cv2.compareHist(heroHistr, cHistr, METHOD);
    resultsg = cv2.compareHist(heroHistg, cHistg, METHOD);
    resultsb = cv2.compareHist(heroHistb, cHistb, METHOD);

    # Calculate squared sum of channels, since some can be negative
    results = resultsr**2 + resultsg**2 + resultsb**2
    print("---%s---" % c)
    print(resultsr, resultsg, resultsb);
    print(results)
    matches[c]=results

hero = max(matches, key=matches.get)
print("Hero appears to be a %s" % hero)

########## Pull card tierlists based on class ##########

# Pull tierlist page
print("\nPulling tier list page...")
html = urllib.urlopen('http://www.heartharena.com/tierlist').read()
soup = BS(html, 'html.parser')
print("Done.\n")

tierlist = soup.find(id=hero)

cards = dict()

print("Extracting card names...")
for rarity in RARITIES:

    cards[rarity] = list()
    for tier in tierlist.findAll(class_="tier %s" % rarity):
        for card in tier.find('ol').findAll('dt'):

            if card.get_text() == u'\xa0':
                break

            cards[rarity].append(card.get_text()[:-1])

cardOutlines = [(378,245,622,583),(656,245,900,583),(940,245,1184,583)]
width = cardOutlines[0][2]-cardOutlines[0][0]
height = cardOutlines[0][3]-cardOutlines[0][1]

windows = list()
for i in range(3):
    obj = Tk()
    windows.append(obj)
    windows[i].resizable(width=FALSE, height=FALSE)
    windows[i].geometry('%dx%d+%d+%d' %
        (width, height, cardOutlines[i][0],cardOutlines[i][1]))
    windows[i].attributes('-alpha',0.2)
    windows[i].overrideredirect(1)

coords = [(385,390,610,440),(670,390,895,440),(950,390,1175,440)]

triplet = list()
for i in range(3):
    image = ImageGrab.grab(bbox=coords[i])
    image.save("img/original_card%d.jpg" % i)

######### Experimental Image Preprocessing ##########
    # image = ImageOps.invert(image)
    # image.save("img/inverted_card%d.jpg" % i)

    #contrast 1.5, brightness 3, contrast 10
    # c = ImageEnhance.Contrast(image)
    # image = c.enhance(1.5)
    #
    # b = ImageEnhance.Contrast(image)
    # image = b.enhance(1.1)
    #
    # image = image.convert('L')
    #
    # c = ImageEnhance.Contrast(image)
    # image = c.enhance(10)

    # image = ImageEnhance.Contrast(ImageEnhance.Brightness(image).enhance(.15)).enhance(5.6).convert('1', dither=0)
    # image = ImageOps.invert(image.convert('RGB')).convert('1', dither=0)
    image = ImageOps.invert(ImageOps.invert(image).point(lambda x: x*2.4 ))
######################################################

    #Preprocess image for OCR.
    #TODO: This algorithm SUCKS.
    image = ImageEnhance.Contrast(image.convert('L')).enhance(1.4).point(
        lambda x: 0 if (x > 220 and 255) else 255, '1')

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

    #Find which card the OCRed text corresponds to
    bestMatch = 0
    for rarity in RARITIES:
        for card in cards[rarity]:
            score = SM(None, str(textresult), str(card)).ratio()
            if score > bestMatch:
                bestMatch = score
                cardMatch = card

    #Store match
    print("Detected card was %s, confidence %f" % (cardMatch, score))
    triplet.append([cardMatch, i])

print("Available cards are %s, %s, and %s" % (triplet[0][0], triplet[1][0], triplet[2][0]))

# Ranking
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

windows[optimal[c][1]].mainloop()

#TODO: weight mana costs with current curve

def getClass():
    pass

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
