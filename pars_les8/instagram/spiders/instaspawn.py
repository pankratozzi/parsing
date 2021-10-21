import scrapy
import re
import json
from scrapy.http import HtmlResponse
from instagram.items import InstagramItem


class InstaspawnSpider(scrapy.Spider):
    name = 'instaspawn'
    allowed_domains = ['instagram.com']
    start_urls = ['http://instagram.com/']
    inst_login_link = 'https://www.instagram.com/accounts/login/ajax/'
    inst_login = 'Onliskill_udm'
    inst_pwd = '#PWD_INSTAGRAM_BROWSER:10:1634577477:AWdQAK0AEOF+wFwWVYjoEuu8uCHn+Pabck9vUxQlFS3/o3VdiZCGuEm4HaF+MLP9EwSytUXe+VNGZWVqv/Pz+z14vr8gT4dClBa6OPYXzPbHCHcU0fUqrO731Bcf4OCxjIcxB4lurkTpWrZPz+Ir'

    def __init__(self, users_for_parse):
        super(InstaspawnSpider, self).__init__()
        self.users_for_parse = users_for_parse

    def parse(self, response: HtmlResponse):
        csrf = self.fetch_csrf_token(response.text)
        yield scrapy.FormRequest(
            self.inst_login_link,
            method='POST',
            callback=self.login,
            formdata={'username': self.inst_login,
                      'enc_password': self.inst_pwd},
            headers={'x-csrftoken': csrf})

    def login(self, response: HtmlResponse):
        j_data = response.json()
        if j_data['authenticated']:
            for user in self.users_for_parse:
                yield response.follow(
                    f'/{user}',
                    callback=self.user_parse,
                    cb_kwargs={'username': user})

    def user_parse(self, response: HtmlResponse, username):
        user_id = self.fetch_user_id(response.text, username)
        followers_url = f'https://i.instagram.com/api/v1/friendships/{user_id}/followers/?count=12&search_surface=follow_list_page'
        yield response.follow(followers_url,
                              callback=self.users_followers,
                              cb_kwargs={'username': username,
                                         'user_id': user_id})

        following_url = f'https://i.instagram.com/api/v1/friendships/{user_id}/following/?count=12'
        yield response.follow(following_url,
                              callback=self.users_following,
                              cb_kwargs={'username': username,
                                         'user_id': user_id})

    def users_followers(self, response: HtmlResponse, username, user_id):
        j_data = response.json()
        next_roll = j_data.get('next_max_id')
        if next_roll:
            followers_url = f'https://i.instagram.com/api/v1/friendships/{user_id}/followers/?count=12&max_id={next_roll}&search_surface=follow_list_page'
            yield response.follow(followers_url,
                                  callback=self.users_followers,
                                  cb_kwargs={'username': username,
                                             'user_id': user_id})
        users = j_data.get('users')
        for user in users:
            item = InstagramItem(main_username=username,
                                 main_user_id=user_id,
                                 username=user.get('username'),
                                 user_id=user.get('pk'),
                                 user_avatar=user.get('profile_pic_url'),
                                 follow_flag=True)
            yield item

    def users_following(self, response: HtmlResponse, username, user_id):
        j_data = response.json()
        next_roll = j_data.get('next_max_id')
        if next_roll:
            following_url = f'https://i.instagram.com/api/v1/friendships/{user_id}/following/?count=12&max_id={next_roll}'
            yield response.follow(following_url,
                                  callback=self.users_following,
                                  cb_kwargs={'username': username,
                                             'user_id': user_id})
        users = j_data.get('users')
        for user in users:
            item = InstagramItem(main_username=username,
                                 main_user_id=user_id,
                                 username=user.get('username'),
                                 user_id=user.get('pk'),
                                 user_avatar=user.get('profile_pic_url'),
                                 follow_flag=False)
            yield item

    def fetch_csrf_token(self, text):
        ''' Get csrf-token for auth '''
        matched = re.search('\"csrf_token\":\"\\w+\"', text).group()
        return matched.split(':').pop().replace(r'"', '')

    def fetch_user_id(self, text, username):
        try:
            matched = re.search(
                '{\"id\":\"\\d+\",\"username\":\"%s\"}' % username, text).group()
            return json.loads(matched).get('id')
        except:
            matched = re.findall('\"id\":\"\d+\"', text)[1].split(':')[1].replace('"', '')
            return matched
