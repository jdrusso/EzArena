#Requires:
# scikit-image
# BeautifulSoup
# cv2
from bs4 import BeautifulSoup as BS
# from skimage.measure import structural_similarity as ssim
from PIL import ImageGrab, Image, ImageOps
import cv2, math, urllib
import pytesser as pyt

# This compares histograms by calculating Bhattacharyya distance. Seems to be the
#   most accurate algorithm.
METHOD = 2

CLASSES = ["druid", "hunter", "mage", "paladin",
            "priest", "rogue", "shaman", "warlock", "warrior"]

RARITIES = ['beyond-great', 'great', 'good', 'above-average', 'average',
            'below-average', 'bad', 'terrible']


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

tierlist = soup.find(id="rogue")

cards = dict()

for rarity in RARITIES:
    print("\nNow pulling %s cards" % rarity)

    cards[rarity] = list()
    for tier in tierlist.findAll(class_="tier %s" % rarity):
        for card in tier.find('ol').findAll('dt'):

            if card.get_text() == u'\xa0':
                break

            cards[rarity].append(card.get_text()[:-1])

print(cards['beyond-great'])

# Capture images of cards

image = ImageGrab.grab(bbox=(385,390,610,440))
image = ImageOps.invert(image)
image.save("card1.jpg")
pyt.image_to_string("card1.jpg")

# OCR card names from images

# Draw colored overlay on screen over cards, i.e. green for best choice, red for worst

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
