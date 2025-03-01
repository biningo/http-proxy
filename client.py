import requests

if __name__ == '__main__':
    response = requests.get('https://www.baidu.com',
                            proxies={'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'})
    print(response.content.decode('utf-8'))
