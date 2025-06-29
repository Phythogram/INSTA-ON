import os
import json
import random
import string
import time
import uuid
import names
import httpx
from curl_cffi import requests as req
from instagrapi import Client

insta = req.Session()
insta.impersonate = 'chrome110'

def generate_temp_mail():
    with httpx.Client() as client:
        domain = client.get("https://api.mail.tm/domains").json()['hydra:member'][0]['domain']
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        email = f"{username}@{domain}"
        password = uuid.uuid4().hex

        reg = client.post("https://api.mail.tm/accounts", json={"address": email, "password": password})
        if reg.status_code != 201:
            raise Exception("Mail.tm account creation failed")

        token = client.post("https://api.mail.tm/token", json={"address": email, "password": password}).json()['token']
        return email, password, token

def get_code_from_mail(token, subject_keyword="Instagram"):
    import re
    headers = {"Authorization": f"Bearer {token}"}
    for attempt in range(30):
        try:
            with httpx.Client(timeout=10.0) as client:
                inbox = client.get("https://api.mail.tm/messages", headers=headers).json()
                for msg in inbox.get('hydra:member', []):
                    if subject_keyword.lower() in msg['subject'].lower():
                        content = client.get(f"https://api.mail.tm/messages/{msg['id']}", headers=headers).json()
                        match = re.search(r'\b(\d{6})\b', content['text'])
                        if match:
                            return match.group(1)
            time.sleep(2)
        except:
            time.sleep(2)
    return None

def get_headers(Country, Language):
    while True:
        try:
            android_ver = random.randint(9, 13)
            ua = f'Mozilla/5.0 (Linux; Android {android_ver}; ' \
                 f'{"".join(random.choices(string.ascii_uppercase, k=3))}{random.randint(111,999)}) ' \
                 f'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Mobile Safari/537.36'

            r = insta.get('https://www.instagram.com/', headers={'user-agent': ua})
            csrftoken = r.cookies["csrftoken"]
            datr = r.cookies["datr"]
            mid = r.text.split('{"mid":{"value":"')[1].split('"')[0]
            ig_did = r.cookies["ig_did"]
            rollout = r.text.split('rollout_hash":"')[1].split('"')[0]
            app_id = r.text.split('APP_ID":"')[1].split('"')[0]

            cookies = f'dpr=3; csrftoken={csrftoken}; mid={mid}; ig_nrcb=1; ig_did={ig_did}; datr={datr}'

            return {
                'authority': 'www.instagram.com',
                'accept': '*/*',
                'accept-language': f'{Language}-{Country},en;q=0.9',
                'content-type': 'application/x-www-form-urlencoded',
                'cookie': cookies,
                'origin': 'https://www.instagram.com',
                'referer': 'https://www.instagram.com/accounts/signup/email/',
                'sec-ch-ua': '"Chromium";v="111", "Not(A:Brand";v="8"',
                'sec-ch-ua-mobile': '?1',
                'sec-ch-ua-platform': '"Android"',
                'user-agent': ua,
                'x-asbd-id': '198387',
                'x-csrftoken': csrftoken,
                'x-ig-app-id': app_id,
                'x-ig-www-claim': '0',
                'x-instagram-ajax': rollout,
                'x-requested-with': 'XMLHttpRequest',
                'x-web-device-id': ig_did,
            }
        except:
            pass

def get_username(headers, name, email):
    data = {'email': email, 'name': name}
    r = insta.post('https://www.instagram.com/api/v1/web/accounts/username_suggestions/',
                   headers=headers, data=data)
    if r.ok and 'suggestions' in r.text:
        return random.choice(r.json()['suggestions'])
    return None

def send_verification(headers, email):
    data = {
        'device_id': headers['cookie'].split('mid=')[1].split(';')[0],
        'email': email
    }
    r = insta.post('https://www.instagram.com/api/v1/accounts/send_verify_email/',
                   headers=headers, data=data)
    return r.text

def validate_code(headers, email, code):
    headers['referer'] = 'https://www.instagram.com/accounts/signup/emailConfirmation/'
    data = {
        'code': code,
        'device_id': headers['cookie'].split('mid=')[1].split(';')[0],
        'email': email
    }
    return insta.post('https://www.instagram.com/api/v1/accounts/check_confirmation_code/',
                      headers=headers, data=data)

def create_account(headers, email, signup_code):
    fname = names.get_first_name()
    uname = get_username(headers, fname, email)
    password = f"{fname}@{random.randint(111,999)}"
    headers['referer'] = 'https://www.instagram.com/accounts/signup/username/'

    data = {
        'enc_password': f"#PWD_INSTAGRAM_BROWSER:0:{round(time.time())}:{password}",
        'email': email,
        'username': uname,
        'first_name': fname,
        'month': random.randint(1, 12),
        'day': random.randint(1, 28),
        'year': random.randint(1990, 2001),
        'client_id': headers['cookie'].split('mid=')[1].split(';')[0],
        'seamless_login_enabled': '1',
        'tos_version': 'row',
        'force_sign_up_code': signup_code,
    }

    r = insta.post('https://www.instagram.com/api/v1/web/accounts/web_create_ajax/',
                   headers=headers, data=data)
    if '"account_created":true' in r.text:
        print("✅ Account Created:", uname)

        # login and upload posts
        client = Client()
        client.login(uname, password)

        # Set profile photo
        avatar_file = random.choice(os.listdir("avatars"))
        client.account_change_profile_picture(open(f"avatars/{avatar_file}", "rb"))

        # Set humanized bio
        bios = [
            "Exploring the world through pixels 🌍📸",
            "Nature. Code. Coffee. Repeat 🌿💻☕",
            "Documenting digital and natural adventures 🍃🧠",
            "Engineer by logic, artist by soul 🛠️✨",
            "Waves, woods and wonders 🌊🌲🌌"
        ]
        client.account_edit_biography(random.choice(bios))

        # Upload posts with captions
        with open("captions.txt") as f:
            captions = f.read().splitlines()
        post_imgs = random.sample(os.listdir("posts"), k=random.randint(4, 6))
        for img in post_imgs:
            caption = random.choice(captions)
            client.photo_upload(f"posts/{img}", caption)

        # Save to accounts.json
        log = {"username": uname, "email": email, "password": password}
        if os.path.exists("accounts.json"):
            with open("accounts.json", "r") as f:
                data = json.load(f)
        else:
            data = []
        data.append(log)
        with open("accounts.json", "w") as f:
            json.dump(data, f, indent=2)

    else:
        print("❌ Account creation failed:", r.text)

if __name__ == "__main__":
    print("🛡️ Secure InstaGen by @NamasteHacker")
    email, _, mailtm_token = generate_temp_mail()
    print("📧 Email Created:", email)

    headers = get_headers('US', 'en')
    response = send_verification(headers, email)
    print("📨 Sent Verification:", response)

    if '"email_sent":true' in response:
        code = get_code_from_mail(mailtm_token)
        if code:
            print("✅ Verification Code Received:", code)
            r = validate_code(headers, email, code)
            if 'signup_code' in r.text:
                signup_code = r.json()['signup_code']
                create_account(headers, email, signup_code)
            else:
                print("❌ Code validation failed:", r.text)
        else:
            print("❌ No code received.")
    else:
        print("❌ Verification not sent.")
