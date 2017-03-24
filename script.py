import requests
from bs4 import BeautifulSoup
import imaplib
import email
import time

def get_authenticityToken(response):
    """ Given a requests response. Look for an input field called authenticityToken and returns it.
    This authenticityToken is used to avoid csrf attacks."""

    soup = BeautifulSoup(response.content, 'html.parser')
    authenticityToken = soup.find('input', { 'name' : "authenticityToken" }).get('value')
    if authenticityToken:
        return authenticityToken
    else:
        raise Exception

def try_login(username, currentPassword):
    url = 'https://account.mojang.com/login'

    s = requests.Session()
    authenticityToken = get_authenticityToken(s.get(url))

    # Login
    response = s.post(url, data={
        'authenticityToken': authenticityToken,
        'password' : currentPassword,
        'username' : username
    })
    
    # If login it's successful. Change the password.
    if response.url == 'https://account.mojang.com/me':
        print("Login success ({})".format(username))
        return s
    else:
        print("Login failed ({})".format(username))
        return None

def change_minecraft_password(username, currentPassword, newPassword):
    """ Given an username, and the accounts's currentPassword, log in into the Mojanj account website
    and change the password with the newPassword provided"""

    s = try_login(username, currentPassword)
    if s:    
        authenticityToken = get_authenticityToken(s.get(password_url))

        response = s.post(password_url, data={
            'authenticityToken': authenticityToken,
            'newPassword' : newPassword,
            'newPasswordAgain' : newPassword,
            'password' : 'true',
            'currentPassword' : currentPassword
        })

        if response.json()['status'] == 'ok':
            print("Password changed for account {}".format(username))
        else:
            print("Failed to change password for account {}. Reason: {}".format(username, response.json()['status']))
    else:
        print("Can't change the password if not logged in.")

def send_reset_password_email(username):
    reset_password_url = 'https://account.mojang.com/resetpassword/request'

    s = requests.Session()
    authenticityToken = get_authenticityToken(s.get(reset_password_url))


    response = s.post(reset_password_url, data={
        'authenticityToken': authenticityToken,
        'email' : username,
    })

    if response.status_code == 200:
        print("Sent password reset to {}".format(username))
    else:
        print("Couldn't send password reset to {}".format(username))

def read_email_from_mojang(username, password):
    """
    Need to turn on: https://www.google.com/settings/security/lesssecureapps
    And: https://accounts.google.com/b/0/DisplayUnlockCaptcha
    Return reset link
    """
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(username, password)
    # print(mail.list())
    mail.select('inbox')

    rv, data = mail.search(None, '(FROM "noreply@mojang.com" SUBJECT "Requested password reset")')
    if rv != 'OK':
        print("No messages found.")
    else:
        rv, data = mail.fetch(data[0].split()[-1], '(RFC822)')
        if rv != 'OK':
            print("ERROR getting message", )
        else:
            raw_email = data[0][1]
            raw_email_string = raw_email.decode('utf-8')
            email_message = email.message_from_string(raw_email_string)
            for part in email_message.walk():
                if part.get_content_type() == "text/html": # ignore attachments/html
                    body = part.get_payload(decode=True).decode('utf-8')
                    
                    soup = BeautifulSoup(body, 'html.parser')
                    reset_link = soup.a.get('href')
                    print("Link found {}".format(reset_link))
                    return reset_link
                    
def change_password_using_reset_link(reset_link, newPassword):
    s = requests.Session()
    authenticityToken = get_authenticityToken(s.get(reset_link))

    response = s.post('https://account.mojang.com/resetpassword', data={
        'authenticityToken': authenticityToken,
        'token' : reset_link.split('/')[-1],
        'password' : newPassword,
        'passwordAgain' : newPassword,
    })
        
    if response.url == "https://account.mojang.com/login":
        print("Password reset successfuly")
    else:
        print("Couldn't reset the password.")     

def reset_password(mojang_username, mojang_new_password, email, password):
    #send_reset_password_email(mojang_username)
    #print("7 seconds before checking email to receive email")
    #time.sleep(7)
    token = read_email_from_mojang(email, password)
    if token:
        change_password_using_reset_link(token, mojang_new_password)
    else:
        print("Error with password reset")
            
def personal_account_test():
    print("== Personal Test ==")
    try_login('email@gmail.com', '')

def continue_try():
    num = 0
    rv = None
    while(rv == None):
        num += 1
        print("Trying log in...#{}".format(num))
        rv = try_login('email@gmail.com', '')
        time.sleep(2)


if __name__ == "__main__":
    # personal_account_test()
    # continue_try()
