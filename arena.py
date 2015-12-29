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

# This compares histograms by calculating Bhattacharyya distance. Seems to be the
#   most accurate algorithm.
METHOD = 2

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

for rarity in RARITIES:
    print("\nNow pulling %s cards" % rarity)

    cards[rarity] = list()
    for tier in tierlist.findAll(class_="tier %s" % rarity):
        for card in tier.find('ol').findAll('dt'):

            if card.get_text() == u'\xa0':
                break

            cards[rarity].append(card.get_text()[:-1])

# print(cards['beyond-great'])

coords = [(385,390,610,440),(670,390,895,440),(950,390,1175,440)]

triplet = list()
for i in range(3):
    image = ImageGrab.grab(bbox=coords[i])
    image.save("img/original_card%d.jpg" % i)
    # image = ImageOps.invert(image)
    # image.save("img/inverted_card%d.jpg" % i)

    #contrast 1.5, brightness 3, contrast 10
    # c = ImageEnhance.Contrast(image)
    # image = c.enhance(1.5)
    #
    # b = ImageEnhance.Brightness(image)
    # image = b.enhance(3)
    #
    # image = image.convert('L')
    #
    # c = ImageEnhance.Contrast(image)
    # image = c.enhance(10)

    # image = ImageEnhance.Contrast(ImageEnhance.Brightness(image).enhance(.15)).enhance(5.6).convert('1', dither=0)
    # image = ImageOps.invert(image.convert('RGB')).convert('1', dither=0)
    # image = ImageOps.invert(ImageOps.invert(image).point(lambda x: x*6 if x < 255/6 else 255))
    image = ImageEnhance.Contrast(image.convert('L')).enhance(1.4).point(
        lambda x: 0 if (x > 220 and 255) else 255, '1')

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

    print("Detected card was %s, confidence %f" % (cardMatch, score))
    triplet.append(cardMatch)

print("Available cards are %s, %s, and %s" % (triplet[0], triplet[1], triplet[2]))

# # Capture images of cards
# image = ImageGrab.grab(bbox=(385,390,610,440))
#
# image = ImageOps.invert(image)
# image.save("card1.jpg")
# url = uploader.upload("testimage.jpg")
#
# #Construct URL to raw image
# imgurl = url[:20] + 'extpics/' + url[20:]
#
# # OCR card names from images
# textresult = urllib.urlopen(AWS_URL_START + imgurl + AWS_URL_END).read()
# print("OCR Result: %s" % textresult)
# # print("Image URL: %s" % imgurl)
#
# #Find which card the OCRed text corresponds to
# bestMatch = 0
#
# for rarity in RARITIES:
#     for card in cards[rarity]:
#         score = SM(None, textresult, card).ratio()
#         if score > bestMatch:
#             bestMatch = score
#             cardMatch = card
#
# print("Detected card was %s" % cardMatch)

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
