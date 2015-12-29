import requests
from bs4 import BeautifulSoup as BS

def upload(file):
    with open(file, 'rb') as f:
        r = requests.post('http://picpaste.com/upload.php',
            files={'MAX_FILE_SIZE':"7168000",
            'upload':('card.jpg',f,'image/jpeg'),
            'storetime':(None,'1'),
            'addprivacy':(None,'1'),
            'rules':(None,'yes')},
            cookies={'PICPASTE_RULES':'TRUE', 'PICPASTE_PRIVACY':'1', 'PICPASTE_RULES_VER':'20101001'})

    soup = BS(r.text, 'html.parser')

    url = soup.find(class_='picture').findAll('td')[1].get_text()

    return url

if __name__ == '__main__':
    print(upload("testimage.jpg"))
    print ("Image uploaded.")
