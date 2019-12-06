import time
import json
from getpass import getpass
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

class SeleniumManager(object):
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('window-size=1200x600')
        options.add_argument('disable-gpu')
        options.add_argument('--log-level=3')
        options.add_argument('no-proxy-server')
        options.add_argument('remote-debugging-port=9621')
        prefs = {'profile.default_content_setting_values': {'cookies': 2, 'images': 2, 'javascript': 2, 
                            'plugins': 2, 'popups': 2, 'geolocation': 2, 
                            'notifications': 2, 'auto_select_certificate': 2, 'fullscreen': 2, 
                            'mouselock': 2, 'mixed_script': 2, 'media_stream': 2, 
                            'media_stream_mic': 2, 'media_stream_camera': 2, 'protocol_handlers': 2, 
                            'ppapi_broker': 2, 'automatic_downloads': 2, 'midi_sysex': 2, 
                            'push_messaging': 2, 'ssl_cert_decisions': 2, 'metro_switch_to_desktop': 2, 
                            'protected_media_identifier': 2, 'app_banner': 2, 'site_engagement': 2, 
                            'durable_storage': 2}}
        options.add_experimental_option('prefs', prefs)
        options.add_argument("start-maximized")
        options.add_argument("disable-infobars")
        options.add_argument("disable-extensions")
        #No images
        #chrome_prefs = {}
        #chrome_prefs['profile.default_content_settings'] = {'images': 2}
        #chrome_prefs['profile.managed_default_content_settings'] = {'images': 2}
        #options.experimental_options['prefs'] = chrome_prefs
        self.browser = webdriver.Chrome(ChromeDriverManager().install(),options = options)

    def tryLogin(self, email:str, password:str):
        self.browser.get('https://www.linkedin.com/login')
        emailElement = self.browser.find_element_by_name('session_key')
        passwordElement = self.browser.find_element_by_name('session_password')
        loginBtn = self.browser.find_element_by_xpath('//*[@id=\'app__container\']/main/div/form/div[3]/button')
        emailElement.send_keys(email)
        passwordElement.send_keys(password)
        loginBtn.click()


    def scrollPageToEnd(self):
        lenOfPage = self.browser.execute_script('window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;')
        match=False
        while(match==False):
                lastCount = lenOfPage
                time.sleep(1.5)
                lenOfPage = self.browser.execute_script('window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;')
                if lastCount==lenOfPage:
                    match=True

    def cardToLink(self, card) -> str:
        return card.find('a').get('href')

    def textNormalizer(self,text) -> str:
        return text.replace('\n','').replace('  ','')

    def getPersonFromLink(self, link):
        self.browser.get(link + 'detail/contact-info/')
        person = Person()
        profileHtml = self.browser.page_source
        soup = BeautifulSoup(profileHtml, 'lxml')
        person.link = link
        person.fullName = self.textNormalizer(soup.find('li', class_ = 'inline t-24 t-black t-normal break-words').text)
        person.status = self.textNormalizer(soup.find('h2', class_='mt1 t-18 t-black t-normal').text)
        person.country = self.textNormalizer(soup.find('li', class_='t-16 t-black t-normal inline-block').text)
        cis = soup.find('div', class_ = 'pv-profile-section__section-info section-info').find_all('section')
        cis.pop(0)
        for ci in cis:
            header = ci.find('header').text
            if(header == 'Phone'):
                phones = ci.find('ul').find_all('li')
                for phone in phones:
                    person.phoneNumber += phone.find('span', class_ = 't-14 t-black t-normal').text + ' , '
            elif(header == 'Address'):
                person.adress = self.textNormalizer(ci.find('div').find('a').text)
            elif(header == 'Email'):
                person.email = self.textNormalizer(ci.find('div').find('a').text)
            elif(header == 'Birthday'):
                person.birthDay = ci.find('div').find('span').text
        return person

class Person(object):
    def __init__(self):
        self.link = ''
        self.fullName = ''
        self.status = ''
        self.twitter = ''
        self.country = ''
        self.link = ''
        self.phoneNumber = ''
        self.adress = ''
        self.email = ''
        self.birthDay = ''
        self.mainSkills = ''


def obj_dict(obj):
    return obj.__dict__

def main():
    

    browserManager = SeleniumManager()
    companyLink = input('Enter company id(w: https://www.linkedin.com/company/*here*/):')
    while(True):
        companyLink = 'https://www.linkedin.com/company/' + companyLink + '/people/'
        login = input('Enter your LinkedIn mail or phone num: ')
        password = getpass('Enter your LinkedIn password: ')
        browserManager.tryLogin(login, password)
        browserManager.browser.get(companyLink)
        if(browserManager.browser.current_url != companyLink):
            print('Bad login, try again...')
        else:
            break
    print('Login sucessful.')

    
    browserManager.scrollPageToEnd()
    requiredHtml = browserManager.browser.page_source
    soup = BeautifulSoup(requiredHtml, 'lxml')                                                                                
    cards = soup.find('div', class_ = 'org-people-profiles-module ember-view').find_all('artdeco-entity-lockup-image', class_='artdeco-entity-lockup__image artdeco-entity-lockup__image--type-circle ember-view')
    links = []
    for card in tqdm(cards):
        try:
            links.append(browserManager.cardToLink(card))
        except:
            print('Wrong card.')
    persons = []
    for link in tqdm(links):
        persons.append(browserManager.getPersonFromLink('https://www.linkedin.com' + link))
    fileName = companyLink.replace('https://www.linkedin.com/company/','').replace('/people/', '') + '.json'
    jsonData = json.dumps(persons, default = obj_dict)
    f = open(fileName, 'w')
    f.write(jsonData)


if(__name__ == '__main__'):
    main()